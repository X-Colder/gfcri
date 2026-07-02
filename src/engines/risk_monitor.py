"""
Risk monitoring and early-warning engine.

Detects regime jumps, node velocity spikes, multi-chain co-activation,
and cross-references internet-observable macro events to produce
actionable alerts in plain language.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from src.models.graph import MacroRiskCausalGraph


@dataclass
class Alert:
    level: str  # "warning" | "danger" | "critical"
    title: str
    detail: str
    affected_nodes: list[str] = field(default_factory=list)
    chain_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "title": self.title,
            "detail": self.detail,
            "affected_nodes": self.affected_nodes,
            "chain_id": self.chain_id,
        }


_LEVEL_EMOJI = {"warning": "⚠️", "danger": "\U0001f6a8", "critical": "\U0001f534"}
_LEVEL_LABEL = {"warning": "注意", "danger": "警告", "critical": "紧急"}


class RiskMonitor:
    """Detects non-routine risk transitions and generates alerts."""

    def __init__(
        self,
        graph: "MacroRiskCausalGraph",
        gfcri_result: dict[str, Any],
        prev_gfcri: dict[str, Any] | None = None,
        prev_node_zscores: dict[str, float] | None = None,
        structural_breaks: list[dict[str, Any]] | None = None,
        upcoming_events: list[dict[str, Any]] | None = None,
    ) -> None:
        self.graph = graph
        self.gfcri = gfcri_result
        self.prev_gfcri = prev_gfcri
        self.prev_z = prev_node_zscores or {}
        self.breaks = structural_breaks or []
        self.events = upcoming_events or []

    def run_all_checks(self) -> list[Alert]:
        alerts: list[Alert] = []
        alerts.extend(self._check_gfcri_jump())
        alerts.extend(self._check_node_velocity())
        alerts.extend(self._check_multi_chain_coactivation())
        alerts.extend(self._check_threshold_breach())
        alerts.extend(self._check_event_collision())
        alerts.extend(self._check_structural_break_recent())
        alerts.extend(self._check_divergence())
        alerts.sort(key=lambda a: {"critical": 0, "danger": 1, "warning": 2}[a.level])
        if alerts:
            logger.info(f"RiskMonitor: {len(alerts)} alerts generated")
        return alerts

    # --- Check 1: GFCRI regime jump ---

    def _check_gfcri_jump(self) -> list[Alert]:
        alerts = []
        curr = self.gfcri["gfcri"]
        if not self.prev_gfcri:
            return alerts

        prev = self.prev_gfcri.get("gfcri_value")
        if prev is None:
            return alerts
        prev = float(prev)
        delta = curr - prev

        if delta >= 20:
            alerts.append(Alert(
                level="critical",
                title="风险指数急剧飙升",
                detail=(
                    f"GFCRI 一天之内从 {prev:.0f} 跳升到 {curr:.0f}，涨了 {delta:.0f} 点。"
                    f"这意味着全球金融系统在短时间内承受了巨大压力，"
                    f"类似于 2008 年金融危机前夕的信号强度。"
                ),
            ))
        elif delta >= 10:
            alerts.append(Alert(
                level="danger",
                title="风险指数快速上升",
                detail=(
                    f"GFCRI 从 {prev:.0f} 上升到 {curr:.0f}（+{delta:.0f}），"
                    f"速度异常。通常这意味着多个市场同时恶化，需要密切关注。"
                ),
            ))
        elif delta >= 5:
            alerts.append(Alert(
                level="warning",
                title="风险指数明显上升",
                detail=(
                    f"GFCRI 从 {prev:.0f} 上升到 {curr:.0f}（+{delta:.0f}），"
                    f"虽然还在可控范围内，但趋势值得关注。"
                ),
            ))

        prev_alert = self.prev_gfcri.get("alert_level", "green")
        curr_alert = self.gfcri["alert_level"]
        level_order = {"green": 0, "yellow": 1, "orange": 2, "red": 3}
        if level_order.get(curr_alert, 0) - level_order.get(prev_alert, 0) >= 2:
            alerts.append(Alert(
                level="critical",
                title="预警级别跨级跳升",
                detail=(
                    f"预警级别从「{prev_alert}」直接跳到「{curr_alert}」，"
                    f"跳过了中间级别。这种跨级跃迁说明风险不是渐进积累的，"
                    f"而是突然爆发的——需要立即关注是什么事件触发了这个变化。"
                ),
            ))

        return alerts

    # --- Check 2: Node z-score velocity ---

    def _check_node_velocity(self) -> list[Alert]:
        alerts = []
        contribs = self.gfcri.get("node_contributions", {})

        for nid, info in contribs.items():
            curr_z = info.get("zscore", 0)
            prev_z = self.prev_z.get(nid)
            if prev_z is None:
                continue

            delta_z = abs(curr_z) - abs(float(prev_z))
            name = info.get("display_name", nid)

            if abs(curr_z - float(prev_z)) >= 2.0:
                alerts.append(Alert(
                    level="danger",
                    title=f"{name} 发生剧烈异动",
                    detail=(
                        f"{name} 的偏离程度一天之内变化了 "
                        f"{curr_z - float(prev_z):+.1f} 倍。"
                        f"打个比方：如果身高的平均值是 170cm、正常波动范围是 5cm，"
                        f"这相当于一天之内「身高」变化了 10cm 以上——极不正常。"
                    ),
                    affected_nodes=[nid],
                ))
            elif abs(curr_z - float(prev_z)) >= 1.0 and abs(curr_z) > 2.0:
                alerts.append(Alert(
                    level="warning",
                    title=f"{name} 加速偏离正常范围",
                    detail=(
                        f"{name} 已经处于异常区间（偏离{curr_z:+.1f}倍），"
                        f"而且还在继续偏离，一天又多偏了 "
                        f"{curr_z - float(prev_z):+.1f} 倍。"
                    ),
                    affected_nodes=[nid],
                ))

        return alerts

    # --- Check 3: Multi-chain co-activation ---

    def _check_multi_chain_coactivation(self) -> list[Alert]:
        alerts = []
        chains = self.gfcri.get("chains", [])
        active = [c for c in chains if c.get("active")]

        if len(active) >= 4:
            names = "、".join(c["name"] for c in active)
            alerts.append(Alert(
                level="critical",
                title="多条风险传导链同时激活",
                detail=(
                    f"有 {len(active)} 条传导链同时处于活跃状态（{names}），"
                    f"这意味着风险正在多个渠道同时传导，类似于多米诺骨牌同时倒下。"
                    f"历史上，2008年金融危机和2020年3月市场恐慌时都出现过类似信号。"
                ),
            ))
        elif len(active) >= 3:
            names = "、".join(c["name"] for c in active)
            alerts.append(Alert(
                level="warning",
                title="多条传导链同时活跃",
                detail=(
                    f"{len(active)} 条传导链同时活跃（{names}），"
                    f"风险正在通过多个渠道扩散。如果再有一条链被激活，"
                    f"系统可能进入「风险共振」状态。"
                ),
            ))

        return alerts

    # --- Check 4: Key threshold breaches ---

    def _check_threshold_breach(self) -> list[Alert]:
        alerts = []
        contribs = self.gfcri.get("node_contributions", {})

        vix = contribs.get("vix", {})
        vix_val = vix.get("current_value")
        if vix_val is not None:
            if vix_val >= 35:
                alerts.append(Alert(
                    level="critical",
                    title="VIX 恐慌指数进入极端区间",
                    detail=(
                        f"VIX 当前为 {vix_val:.1f}，超过 35 意味着市场处于极度恐慌状态。"
                        f"上一次 VIX 到这个水平是在重大市场崩盘期间。"
                        f"在这个水平下，VIX→韩元→韩股 的传导链会被强力激活。"
                    ),
                    affected_nodes=["vix", "krw_usd", "kospi"],
                ))
            elif vix_val >= 25:
                alerts.append(Alert(
                    level="warning",
                    title="VIX 恐慌指数升高",
                    detail=(
                        f"VIX 当前为 {vix_val:.1f}，市场开始感到紧张。"
                        f"VIX 超过 20 后「波动率传染」链条就会激活。"
                    ),
                    affected_nodes=["vix"],
                ))

        dxy = contribs.get("dxy", {})
        dxy_z = dxy.get("zscore", 0)
        if abs(dxy_z) > 3.0:
            direction = "过强" if dxy_z > 0 else "过弱"
            alerts.append(Alert(
                level="danger",
                title=f"美元指数极端{direction}",
                detail=(
                    f"美元指数 DXY 的偏离程度达到 {dxy_z:+.1f} 倍，"
                    f"这是一个极端水平。美元过强会像抽水机一样，"
                    f"把新兴市场的资金吸走，导致韩元贬值、韩股下跌。"
                ),
                affected_nodes=["dxy", "krw_usd", "kospi"],
            ))

        oil = contribs.get("oil_wti", {})
        oil_val = oil.get("current_value")
        if oil_val is not None and oil_val >= 90:
            alerts.append(Alert(
                level="warning",
                title="油价攀升至高位",
                detail=(
                    f"WTI 原油 {oil_val:.0f} 美元/桶，接近或超过韩国经常账户承压线。"
                    f"韩国 100% 依赖石油进口，高油价会恶化贸易逆差，"
                    f"进而推高韩国主权信用风险（CDS 走阔）。"
                ),
                affected_nodes=["oil_wti", "kr_cds_5y"],
            ))

        # HYG credit stress
        hyg = contribs.get("hyg", {})
        hyg_z = hyg.get("zscore", 0)
        if hyg_z < -2.0:
            alerts.append(Alert(
                level="critical" if hyg_z < -3.0 else "danger",
                title="垃圾债市场出现信用恐慌",
                detail=(
                    f"高收益债ETF(HYG) 偏离正常范围{abs(hyg_z):.1f}倍，大幅低于正常水平。"
                    f"这意味着企业借钱的成本正在飙升，投资者担心企业违约。"
                    f"历史上这个信号在 2008 年金融危机前 15 个月就已亮起。"
                ),
                affected_nodes=["hyg", "kr_cds_5y", "vix"],
            ))

        # KRE bank stress
        kre = contribs.get("kre", {})
        kre_z = kre.get("zscore", 0)
        if kre_z < -2.0:
            alerts.append(Alert(
                level="critical" if kre_z < -3.0 else "danger",
                title="区域银行股大跌，银行系统承压",
                detail=(
                    f"区域银行ETF(KRE) 偏离正常范围{abs(kre_z):.1f}倍，银行股正在被抛售。"
                    f"2023年硅谷银行倒闭前，KRE 的偏离程度就曾达到 4.4 倍。"
                    f"银行是经济的血管——银行出问题，整个经济都会缺血。"
                ),
                affected_nodes=["kre", "vnq", "vix"],
            ))

        # VNQ real estate stress
        vnq = contribs.get("vnq", {})
        vnq_z = vnq.get("zscore", 0)
        if vnq_z < -2.0:
            alerts.append(Alert(
                level="danger" if vnq_z < -3.0 else "warning",
                title="房地产市场显著走弱",
                detail=(
                    f"房地产ETF(VNQ) 偏离正常范围{abs(vnq_z):.1f}倍。房价下跌会导致银行贷款抵押品贬值，"
                    f"进而引发银行惜贷甚至坏账激增。2008年金融危机就是从房市崩塌开始的。"
                ),
                affected_nodes=["vnq", "kre"],
            ))

        # Gold safe-haven surge
        gold = contribs.get("gold", {})
        gold_z = gold.get("zscore", 0)
        if gold_z > 2.5:
            alerts.append(Alert(
                level="warning",
                title="黄金飙升——资金涌向避风港",
                detail=(
                    f"黄金偏离正常范围{gold_z:.1f}倍，资金正在大量涌入黄金等避险资产。"
                    f"黄金急涨通常意味着投资者对经济前景感到不安，"
                    f"是市场「用脚投票」的早期信号。"
                ),
                affected_nodes=["gold", "dxy"],
            ))

        # Consumer stress
        cs = contribs.get("consumer_stress", {})
        cs_z = cs.get("zscore", 0)
        if cs_z < -2.0:
            alerts.append(Alert(
                level="danger" if cs_z < -3.0 else "warning",
                title="消费者正在勒紧裤腰带",
                detail=(
                    f"消费压力指标偏离正常范围{abs(cs_z):.1f}倍，消费者正在削减非必需开支。"
                    f"消费占美国GDP的70%——当老百姓不敢花钱的时候，"
                    f"经济衰退往往就不远了。"
                ),
                affected_nodes=["consumer_stress", "us_recession_prob"],
            ))

        return alerts

    # --- Check 5: Event collision ---

    def _check_event_collision(self) -> list[Alert]:
        alerts = []
        today = date.today()

        today_events = [
            e for e in self.events
            if e.get("date") == today.isoformat()
        ]
        if not today_events:
            return alerts

        high_impact = [e for e in today_events if e.get("impact") == "high"]
        if len(high_impact) >= 2:
            names = "、".join(e["name"] for e in high_impact)
            all_nodes = set()
            for e in high_impact:
                all_nodes.update(e.get("affected_nodes", []))
            alerts.append(Alert(
                level="danger",
                title="今日多个重磅数据同时公布",
                detail=(
                    f"今天有 {len(high_impact)} 个高影响力事件同时发生（{names}）。"
                    f"多个重要数据在同一天公布时，市场波动往往会放大，"
                    f"因为交易员需要同时消化多条信息，容易出现过度反应。"
                ),
                affected_nodes=list(all_nodes),
            ))
        elif high_impact:
            e = high_impact[0]
            anomalous_involved = [
                nid for nid in e.get("affected_nodes", [])
                if self.gfcri.get("node_contributions", {}).get(nid, {}).get("is_anomalous")
            ]
            if anomalous_involved:
                names = ", ".join(anomalous_involved)
                alerts.append(Alert(
                    level="warning",
                    title=f"今日关键事件叠加异常节点",
                    detail=(
                        f"今天将公布「{e['name']}」，而它影响的节点 {names} "
                        f"目前已经处于异常状态。这就像给发烧的病人又吹了冷风——"
                        f"本来就不稳定的指标可能被进一步推向极端。"
                    ),
                    affected_nodes=e.get("affected_nodes", []),
                ))

        return alerts

    # --- Check 6: Recent structural breaks ---

    def _check_structural_break_recent(self) -> list[Alert]:
        alerts = []
        today = date.today()

        for b in self.breaks:
            if not b.get("break_detected"):
                continue
            break_date_str = str(b.get("break_date", ""))[:10]
            try:
                break_date = date.fromisoformat(break_date_str)
            except ValueError:
                continue

            days_ago = (today - break_date).days
            if 0 <= days_ago <= 30:
                from src.i18n import cn_name
                src, tgt = b["source"], b["target"]
                src_cn, tgt_cn = cn_name(src), cn_name(tgt)
                ratio = b.get("instability_ratio", 0)
                alerts.append(Alert(
                    level="warning" if ratio < 1.5 else "danger",
                    title=f"「{src_cn} → {tgt_cn}」的传导关系近期发生了结构性变化",
                    detail=(
                        f"在 {break_date_str}（{days_ago} 天前），「{src_cn}」对「{tgt_cn}」"
                        f"的影响方式发生了根本性变化（不稳定性比率 {ratio:.1f}）。"
                        f"这意味着过去的传导规律可能不再适用——"
                        f"就像一条常走的路突然塌方了，绕道可能比原来更远或更近。"
                        f"的影响方式发生了根本性变化（不稳定性比率={ratio:.2f}）。"
                        f"这意味着过去的传导规律可能不再适用——"
                        f"就像一条常走的路突然塌方了，绕道可能比原来更远或更近。"
                    ),
                    affected_nodes=[src, tgt],
                ))

        return alerts

    # --- Check 7: Surface-calm / deep-stress divergence ---

    def _check_divergence(self) -> list[Alert]:
        alerts = []
        divergence = self.gfcri.get("divergence")
        if not divergence:
            return alerts

        status = divergence.get("status", "none")
        details = divergence.get("details", [])

        for d in details:
            dtype = d["type"]

            if dtype == "surface_calm_deep_stress":
                level = "critical" if status == "critical" else "danger"
                alerts.append(Alert(
                    level=level,
                    title="⚡ 暴风雨前的平静——表面平静，底层恶化",
                    detail=(
                        d["detail"] + "\n\n"
                        "历史经验：2008年4-8月，VIX从25降到17、股市反弹了6%，"
                        "看起来危机已经过去。但信用利差（BAA对国债利差）从1.6%飙升到3.3%，"
                        "始终没有回落——5个月后雷曼兄弟倒闭，引爆全面崩盘。"
                        "当「表面指标」与「底层指标」出现这种背离时，"
                        "表面的平静往往是虚假的。"
                    ),
                    affected_nodes=d.get("stressed_indicators", []),
                ))

            elif dtype == "zscore_desensitized":
                level = "danger" if status in ("critical", "significant") else "warning"
                alerts.append(Alert(
                    level=level,
                    title="🐸 温水煮青蛙——市场已习惯异常水平",
                    detail=(
                        d["detail"] + "\n\n"
                        "这就像体温持续38.5°C——因为没有突然升高，"
                        "衡量「变化速度」的指标显示正常。"
                        "但38.5°C本身就不正常，持续低烧比突然高烧更危险，"
                        "因为它意味着免疫系统已经无力控制感染。"
                    ),
                    affected_nodes=d.get("desensitized_indicators", []),
                ))

            elif dtype == "policy_mask":
                level = "danger" if status in ("critical", "significant") else "warning"
                unhealed = d.get("unhealed", [])
                unhealed_names = "、".join(item["label"] for item in unhealed[:3])
                alerts.append(Alert(
                    level=level,
                    title="🌡️ 政策退烧药见效，但病根未除",
                    detail=(
                        d.get("detail", "") + "\n\n"
                        f"尚未改善的结构性指标：{unhealed_names}。"
                        "这些指标需要企业盈利好转、银行坏账出清、实体经济复苏才会真正改善，"
                        "不是央行降息就能解决的。历史上每一次「政策市反弹」中，"
                        "只盯着VIX和股指的投资者都会被这种假象误导。"
                    ),
                    affected_nodes=[item["id"] for item in unhealed],
                ))

        return alerts


def format_alerts_markdown(alerts: list[Alert]) -> str:
    if not alerts:
        return ""

    lines = ["### \U0001f6a8 风险预警"]
    lines.append("")

    for a in alerts:
        emoji = _LEVEL_EMOJI.get(a.level, "")
        label = _LEVEL_LABEL.get(a.level, "")
        lines.append(f"#### {emoji} [{label}] {a.title}")
        lines.append("")
        lines.append(a.detail)
        lines.append("")

    return "\n".join(lines)
