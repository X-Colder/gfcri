"""
Daily GFCRI report generator.

Renders a structured Markdown report in plain, accessible language.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from typing import Any

from loguru import logger


def _load_event_schedule() -> list[dict[str, Any]]:
    path = os.path.join(
        os.path.dirname(__file__), "..", "data", "event_schedule.json"
    )
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("events", [])
    except Exception as exc:
        logger.warning(f"Failed to load event schedule: {exc}")
        return []


def get_upcoming_events(days: int = 7) -> list[dict[str, Any]]:
    today = date.today()
    end = today + timedelta(days=days)
    events = _load_event_schedule()
    upcoming = []
    for ev in events:
        try:
            ev_date = date.fromisoformat(ev["date"])
            if today <= ev_date <= end:
                upcoming.append(ev)
        except (ValueError, KeyError):
            continue
    return sorted(upcoming, key=lambda e: e["date"])


_ALERT_EMOJI = {
    "green": "\U0001f7e2",
    "yellow": "\U0001f7e1",
    "orange": "\U0001f7e0",
    "red": "\U0001f534",
}

_ALERT_LABEL = {
    "green": "平静",
    "yellow": "关注",
    "orange": "警惕",
    "red": "危险",
}

_SI_PLAIN_NAME = {
    "SI_RATES": "利率与央行政策",
    "SI_FX": "汇率与资金流向",
    "SI_EQUITY": "股市与芯片",
    "SI_US_EQUITY": "美国股市",
    "SI_ASIA_EQUITY": "亚洲股市",
    "SI_EUROPE": "欧洲市场",
    "SI_CREDIT": "信用与违约风险",
    "SI_BANKING": "银行与房地产",
    "SI_CONSUMER": "消费者与实体经济",
    "SI_COMMODITY": "商品与贸易",
    "SI_TRADE_SPILLOVER": "贸易依赖传导",
    "SI_SENTIMENT": "市场情绪与避险",
}

_CHAIN_PLAIN = {
    "fed_cascade": {
        "name": "央行加息冲击波",
        "metaphor": "美联储加息 → 美元走强 → 新兴市场货币贬值",
        "explain": "美联储加息就像抬高了全球资金的「门槛」，钱会从其他国家回流美国，导致韩元等货币贬值。",
    },
    "dollar_squeeze": {
        "name": "强美元压垮新兴市场",
        "metaphor": "美元走强 → 韩元贬值 → 外资撤离韩国股市",
        "explain": "美元太强就像一个巨大的吸尘器，把新兴市场的外资吸走。外资一撤，股市就跌。",
    },
    "credit_contagion": {
        "name": "信用风险传染",
        "metaphor": "垃圾债崩盘 → 信用恐慌蔓延 → 主权信用恶化 → 股市暴跌",
        "explain": "当借钱最多、信用最差的公司开始还不起债时，恐慌会像瘟疫一样从企业蔓延到国家层面。2008年金融危机的早期信号就是从这里开始的。",
    },
    "housing_bank_doom": {
        "name": "房地产→银行危机",
        "metaphor": "房价下跌 → 银行坏账增加 → 银行股崩塌 → 系统性恐慌",
        "explain": "房价下跌会让银行手里的抵押品贬值，就像你用来抵押的房子突然不值钱了，银行就会出问题。2008年就是这个剧本。",
    },
    "consumer_recession": {
        "name": "消费崩塌→经济衰退",
        "metaphor": "消费者勒紧裤腰带 → 衰退概率飙升 → 恐慌蔓延 → 资金外逃",
        "explain": "消费占美国经济的70%。当老百姓开始省吃俭用不敢花钱时，经济衰退就不远了。",
    },
    "ai_semi_cycle": {
        "name": "AI 芯片需求链",
        "metaphor": "AI 投资热潮 → 芯片涨价 → 半导体股票上涨",
        "explain": "科技巨头大笔投入 AI，需要大量芯片，推高芯片价格和相关公司股价。但如果 AI 热度退潮，链条会反转。",
    },
    "safe_haven_flight": {
        "name": "避险资金大逃亡",
        "metaphor": "黄金飙升 → 美元波动 → 新兴市场货币承压",
        "explain": "当投资者不信任股市和债市时，资金会涌向黄金等「避风港」。黄金急涨就是市场在喊「我怕了」。",
    },
    "europe_contagion": {
        "name": "欧债危机传染",
        "metaphor": "意大利风险 → 欧元走弱 → 美元走强 → 新兴市场承压",
        "explain": "欧洲的火烧到了亚洲——当意大利等南欧国家出问题时，投资者抛售欧元买美元避险，强美元再把新兴市场的钱吸走。",
    },
    "china_shockwave": {
        "name": "中国冲击波",
        "metaphor": "人民币贬值 → 港股暴跌 → 韩国出口受创",
        "explain": "中国是韩国最大的出口市场。人民币一贬，中国消费力下降，韩国的芯片和汽车就卖不动了。",
    },
    "yen_carry_unwind": {
        "name": "日元套利平仓",
        "metaphor": "日元急升 → 套利交易平仓 → 全球波动率飙升",
        "explain": "全球有几万亿美元的'套利交易'——借便宜的日元、投资高收益资产。日元一急涨，这些交易被迫平仓，引发全球抛售。",
    },
    "crypto_contagion": {
        "name": "加密货币传染",
        "metaphor": "比特币崩盘 → 风险偏好崩塌 → 新兴市场抛售",
        "explain": "比特币已经成了投资者胆量的温度计。比特币暴跌说明大家在疯狂逃命，其他风险资产也跟着遭殃。",
    },
    "food_energy_shock": {
        "name": "粮食能源冲击",
        "metaphor": "粮食/能源价格飙升 → 欧洲成本危机",
        "explain": "天然气和小麦暴涨会推高通胀，挤压企业利润，2022年俄乌冲突时欧洲就经历了这种痛苦。",
    },
}


def _score_bar(score: float, width: int = 20) -> str:
    filled = int(score / 100 * width)
    return "█" * filled + "░" * (width - filled)


def render_gfcri_report(
    gfcri_result: dict[str, Any],
    inference_summary: dict[str, Any],
    structural_breaks: list[dict[str, Any]] | None = None,
    llm_narrative: str | None = None,
    alerts_markdown: str | None = None,
    report_date: str | None = None,
    graph_version: str = "1.0.0",
    crisis_report: dict[str, Any] | None = None,
    stress_results: list[dict[str, Any]] | None = None,
    context_story: str | None = None,
) -> str:
    report_date = report_date or date.today().isoformat()
    gfcri = gfcri_result["gfcri"]
    alert = gfcri_result["alert_level"]
    emoji = _ALERT_EMOJI.get(alert, "")
    label = _ALERT_LABEL.get(alert, "")
    sub_indices = gfcri_result["sub_indices"]
    chains = gfcri_result["chains"]
    contribs = gfcri_result.get("node_contributions", {})

    lines: list[str] = []

    # --- Header ---
    lines.append(f"# 全球金融风险日报")
    lines.append(f"### {report_date} | 风险指数 {gfcri:.0f}/100 {emoji} {label}")
    lines.append("")

    if gfcri < 25:
        lines.append("> 目前全球金融系统运行平稳，没有明显的系统性风险信号。")
    elif gfcri < 45:
        lines.append("> 部分市场出现异常波动，需要保持关注，但尚未构成系统性威胁。")
    elif gfcri < 60:
        lines.append("> **多个市场同时出现异常信号**，风险正在积累，建议减少风险敞口。")
    else:
        lines.append("> **危险！** 全球金融系统承受极大压力，多条风险传导链同时激活，需要立即采取防御措施。")
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- Alerts (from monitor) ---
    if alerts_markdown:
        lines.append(alerts_markdown)
        lines.append("---")
        lines.append("")

    # --- Section 1: Score overview ---
    lines.append("### 1. 一眼看懂今天的风险")
    lines.append("")
    for si_id, si in sub_indices.items():
        name = _SI_PLAIN_NAME.get(si_id, si["name"])
        score = si["score"]
        bar = _score_bar(score)
        lines.append(f"- **{name}**: {score:.0f}/100 `{bar}`")
    lines.append("")

    # --- Section 1.5: Context story ---
    if context_story:
        lines.append(context_story)
        lines.append("")
        lines.append("---")
        lines.append("")

    # --- Section 2: What's abnormal ---
    anomalous = [
        (nid, info) for nid, info in contribs.items()
        if info.get("is_anomalous")
    ]
    if anomalous:
        anomalous.sort(key=lambda x: abs(x[1].get("zscore", 0)), reverse=True)
        lines.append(f"### 2. 今天哪些指标不正常？")
        lines.append("")
        lines.append(f"有 **{len(anomalous)} 个指标** 偏离了正常范围：")
        lines.append("")
        for nid, info in anomalous:
            name = info["display_name"]
            z = info["zscore"]
            direction = "高于" if z > 0 else "低于"
            severity = "显著" if abs(z) < 3 else "严重"
            lines.append(
                f"- **{name}**：{direction}历史正常范围 {abs(z):.1f} 倍（{severity}偏离）"
            )
        lines.append("")
        lines.append(
            "> 💡 **怎么理解偏离倍数？** 偏离 2 倍意味着当前值已经很少见（类似考试偏离平均分很远），"
            "偏离 3 倍以上则是极端罕见，历史上只有重大危机时才会出现。"
        )
        lines.append("")
    else:
        lines.append("### 2. 今天哪些指标不正常？")
        lines.append("")
        lines.append("✅ 所有指标都在正常范围内，没有异常信号。")
        lines.append("")

    # --- Section 2.5: Divergence warning ---
    divergence = gfcri_result.get("divergence", {})
    div_status = divergence.get("status", "none")
    div_details = divergence.get("details", [])
    if div_status != "none" and div_details:
        severity_label = {
            "mild": "⚠️ 轻度背离",
            "significant": "🔶 显著背离",
            "critical": "🔴 严重背离",
        }
        lines.append(f"### ⚡ 「暴风雨前的平静」预警 — {severity_label.get(div_status, '背离')}")
        lines.append("")
        surface_avg = divergence.get("surface_avg", 0) * 100
        deep_avg = divergence.get("deep_avg", 0) * 100
        lines.append(
            f"> 表面指标压力 **{surface_avg:.0f}%** vs 底层指标压力 **{deep_avg:.0f}%**"
            f" — 底层比表面高出 **{deep_avg - surface_avg:.0f} 个百分点**"
        )
        lines.append("")
        for d in div_details:
            title = d.get("title", "")
            detail = d.get("detail", "")
            dtype = d.get("type", "")
            if dtype == "surface_calm_deep_stress":
                lines.append(f"#### 🌊 {title}")
                lines.append("")
                lines.append(detail)
                lines.append("")
                lines.append(
                    "> 💡 **为什么要关注？** 在2008年金融危机中，"
                    "Bear Stearns 被收购后市场曾短暂反弹（VIX从25降到17），"
                    "给人一种「最坏已过」的错觉。但信用利差始终维持在危机前的"
                    "2倍水平，说明银行之间的信任从未恢复。5个月后雷曼倒闭，"
                    "真正的风暴才刚开始。"
                )
            elif dtype == "zscore_desensitized":
                lines.append(f"#### 🐸 {title}")
                lines.append("")
                lines.append(detail)
                lines.append("")
                lines.append(
                    "> 💡 **为什么「变化速度」指标会失灵？** 这个指标衡量的是「最近变化有多快」"
                    "而非「绝对水平有多危险」。当一个指标持续恶化后，它的近期均值也跟着"
                    "抬高，变化速度就会回落——好像情况在好转，但其实只是「习惯了」。"
                    "就像每天加班到凌晨2点，第一天觉得崩溃，一个月后觉得「还行」"
                    "——但你的身体并没有变好。"
                )
            lines.append("")
        lines.append("---")
        lines.append("")

    # --- Section 2.7: Policy mask — "fever chart" ---
    divergence = gfcri_result.get("divergence", {})
    policy_mask = None
    for d in divergence.get("details", []):
        if d.get("type") == "policy_mask":
            policy_mask = d
            break

    if policy_mask:
        pr_avg = policy_mask["policy_responsive_avg"]
        st_avg = policy_mask["structural_avg"]
        ld_avg = policy_mask.get("leading_avg", 0)
        lines.append("### 🌡️ 政策退烧 vs 病根未除")
        lines.append("")
        lines.append(f"| 类别 | 平均压力 | 含义 |")
        lines.append(f"|------|---------|------|")
        lines.append(f"| 💊 政策敏感型 | **{pr_avg}%** | 退烧药能压下去的指标 |")
        lines.append(f"| 🦠 结构性 | **{st_avg}%** | 需要经济真正好转才会改善 |")
        if ld_avg:
            lines.append(f"| 🔮 领先信号 | **{ld_avg}%** | 预告未来6-18个月的方向 |")
        lines.append("")

        healed = policy_mask.get("healed", [])
        unhealed = policy_mask.get("unhealed", [])
        warnings = policy_mask.get("leading_warnings", [])

        if healed:
            lines.append("**💊 退烧药见效（政策已缓解）：**")
            for item in healed:
                lines.append(f"- ✅ {item['label']}（压力{item['score']}%）— {item['why']}")
            lines.append("")

        if unhealed:
            lines.append("**🦠 病根未除（政策无法直接修复）：**")
            for item in unhealed:
                lines.append(f"- ⚠️ {item['label']}（压力{item['score']}%）— {item['why']}")
            lines.append("")

        if warnings:
            lines.append("**🔮 前方预警（领先信号仍在恶化）：**")
            for item in warnings:
                lines.append(f"- 🔮 {item['label']}（压力{item['score']}%）— {item['why']}")
            lines.append("")

        lines.append(
            "> 💡 **怎么看这张表？** 「政策敏感型」指标好转只说明央行的应急措施暂时止血了。"
            "真正决定危机会不会爆发的是「结构性」指标——企业还得起债吗？银行的坏账清理了吗？"
            "2008年4-8月就是典型案例：VIX和股市反弹了（退烧药见效），"
            "但信用利差和银行股从未好转（病根还在），5个月后雷曼倒闭。"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

    # --- Section 2.8: Crisis distance dashboard ---
    if crisis_report:
        overall_d = crisis_report.get("overall_distance", 0)
        prob = crisis_report.get("overall_probability", "low")
        prob_cn = {"low": "低", "medium": "中等", "high": "高", "critical": "极高"}.get(prob, prob)
        lines.append(f"### 📏 距离危机有多远？")
        lines.append("")
        lines.append(f"> 综合距离：**{overall_d:.0f}%**（0%=正常，100%=2008级危机） | 危机概率：**{prob_cn}**")
        lines.append("")

        for tier_num, tier_label in [(1, "全球系统性"), (2, "美国核心"), (3, "区域传导")]:
            tier_d = crisis_report.get(f"tier{tier_num}_distance", 0)
            tier_dists = [d for d in crisis_report.get("distances", []) if d["tier"] == tier_num]
            lines.append(f"**Tier {tier_num} {tier_label}（{tier_d:.0f}%）：**")
            for d in tier_dists:
                bar_filled = int(d["distance_pct"] / 10)
                bar = "▓" * bar_filled + "░" * (10 - bar_filled)
                status_icon = "🔴" if d["status"] == "crisis" else "🟡" if d["status"] == "warning" else "🟢"
                lines.append(
                    f"- {status_icon} {d['name']}：`{bar}` {d['distance_pct']:.0f}%"
                    f"（当前{d['current_value']:.1f} | 危机值{d['crisis_value']:.1f}"
                    f" | 历史最差：{d['worst_event']} {d['worst_value']:.1f}）"
                )
            lines.append("")

        policies = crisis_report.get("policies", [])
        if policies:
            lines.append("**🛡️ 政策缓冲空间：**")
            for p in policies:
                icon = "✅" if p["status"] == "buffer" else "⚠️" if p["status"] == "neutral" else "🔴"
                lines.append(f"- {icon} {p['name']}：{p['detail']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    # --- Section 2.9: Stress test scenarios ---
    if stress_results:
        lines.append("### 🧪 如果最坏情况发生？")
        lines.append("")
        lines.append("以下是几种极端场景的压力测试结果——如果今天发生，GFCRI 会到多少：")
        lines.append("")
        lines.append("| 场景 | 当前GFCRI | → 压力后 | 变化 | 级别变化 |")
        lines.append("|------|----------|---------|------|---------|")
        for sr in sorted(stress_results, key=lambda x: -x.get("gfcri_delta", 0))[:5]:
            baseline = sr.get("baseline_gfcri", 0)
            stressed = sr.get("stressed_gfcri", 0)
            delta = sr.get("gfcri_delta", 0)
            bl_alert = sr.get("baseline_alert", "green")
            st_alert = sr.get("stressed_alert", "green")
            alert_cn = {"green": "平静", "yellow": "关注", "orange": "警惕", "red": "危险"}
            change = f"{alert_cn.get(bl_alert, bl_alert)} → {alert_cn.get(st_alert, st_alert)}"
            lines.append(f"| {sr.get('scenario_name', '')} | {baseline:.0f} | **{stressed:.0f}** | +{delta:.0f} | {change} |")
        lines.append("")

        worst = max(stress_results, key=lambda x: x.get("stressed_gfcri", 0))
        lines.append(
            f"> ⚠️ 最严峻场景「{worst.get('scenario_name', '')}」：{worst.get('scenario_description', '')}"
            f" — GFCRI 将飙升至 **{worst.get('stressed_gfcri', 0):.0f}**"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

    # --- Section 3: Transmission chains ---
    lines.append("### 3. 风险是怎么传导的？")
    lines.append("")
    lines.append("下面是 5 条关键的风险传导链——可以理解为「多米诺骨牌」：")
    lines.append("")

    for chain in chains:
        cid = chain["id"]
        plain = _CHAIN_PLAIN.get(cid, {})
        name = plain.get("name", chain["name"])
        metaphor = plain.get("metaphor", " → ".join(chain["path"]))
        explain = plain.get("explain", chain.get("description", ""))
        active = chain["active"]
        stress = chain["stress"]

        if active:
            lines.append(f"#### \U0001f534 {name}（正在传导！压力 {stress:.0f}/100）")
        else:
            lines.append(f"#### \U0001f7e2 {name}（目前平静，压力 {stress:.0f}/100）")

        lines.append(f"- 传导路径：**{metaphor}**")
        lines.append(f"- 通俗解释：{explain}")
        lines.append("")

    # --- Section 4: Upcoming events ---
    upcoming = get_upcoming_events(days=7)
    lines.append("### 4. 未来一周要关注什么？")
    lines.append("")
    if upcoming:
        lines.append("以下事件可能会显著影响市场：")
        lines.append("")
        for ev in upcoming:
            impact = {"high": "⚡ 影响很大", "medium": "📊 有一定影响", "low": "📝 影响较小"}
            lines.append(f"- **{ev['date']}**：{ev['name']} — {impact.get(ev.get('impact', ''), '')}")
        lines.append("")
    else:
        lines.append("未来 7 天没有重大宏观事件安排。")
        lines.append("")

    # --- Section 5: Structural breaks ---
    if structural_breaks:
        recent = [
            b for b in structural_breaks
            if b.get("break_detected") and b.get("instability_ratio", 0) > 1.5
        ]
        if recent:
            lines.append("### 5. 「游戏规则」变了吗？")
            lines.append("")
            lines.append(
                "以下关系最近发生了结构性变化——过去有效的规律可能不再适用："
            )
            lines.append("")
            for b in recent[:5]:
                lines.append(
                    f"- **{b['source']} → {b['target']}**：不稳定性 {b['instability_ratio']:.1f}x"
                    f"（变化发生在 {str(b.get('break_date', ''))[:10]}）"
                )
            lines.append("")

    # --- Section 6: Inference summary ---
    if inference_summary:
        from src.i18n import cn_name as _cn
        lines.append("### 6. 因果推理要点")
        lines.append("")
        for pair, summary in inference_summary.items():
            src, tgt = pair.split("->")
            src_name = _cn(src)
            tgt_name = _cn(tgt)
            strength = summary.get("net_strength", 0)
            direction = "推高" if strength > 0 else "压低"
            lines.append(
                f"- {src_name} 的变动会{direction} {tgt_name}，"
                f"传导强度 {abs(strength):.2f}"
            )
        lines.append("")

    # --- Section 7: LLM narrative ---
    if llm_narrative:
        lines.append("### 7. 深度分析")
        lines.append("")
        lines.append(llm_narrative)
        lines.append("")

    # --- Footer ---
    lines.append("---")
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    n_nodes = len(contribs)
    n_chains = len(chains)
    lines.append(
        f"*生成时间: {ts} | 数据来源: yfinance ({n_nodes} 个实时市场指标, {n_chains} 条传导链)*"
    )

    report = "\n".join(lines)
    logger.info(f"Report rendered: {len(report)} chars")
    return report
