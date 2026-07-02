"""
Context Signal Engine — derives "the story behind the numbers."

Transforms raw market/FRED/China data into structured narrative signals:
  - Policy actions (Fed rate, QT, PBOC LPR)
  - Credit conditions (spread regime, yield curve)
  - Capital flow (carry trade, EM outflow, gold structural bid)
  - Real economy divergences (consumer paradox, deflation risk)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from loguru import logger


@dataclass
class ContextSignal:
    signal_id: str
    category: str  # "policy" | "credit" | "capital_flow" | "real_economy"
    title: str
    what_happened: str
    data_reaction: str
    deep_meaning: str
    significance: str  # "high" | "medium" | "low"
    affected_nodes: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "category": self.category,
            "title": self.title,
            "what_happened": self.what_happened,
            "data_reaction": self.data_reaction,
            "deep_meaning": self.deep_meaning,
            "significance": self.significance,
            "affected_nodes": self.affected_nodes,
        }


class ContextSignalEngine:

    def __init__(
        self,
        fred_current: dict[str, float],
        fred_history: dict[str, pd.Series],
        china_current: dict[str, float],
        oecd_rates: dict[str, dict[str, float]],
        node_values: dict[str, float],
        node_zscores: dict[str, float],
        prev_node_values: dict[str, float] | None,
        prev_fred: dict[str, float] | None,
        gfcri_value: float,
        prev_gfcri_value: float | None,
    ):
        self.fred = fred_current or {}
        self.fred_hist = fred_history or {}
        self.china = china_current or {}
        self.oecd = oecd_rates or {}
        self.nodes = node_values or {}
        self.zscores = node_zscores or {}
        self.prev_nodes = prev_node_values or {}
        self.prev_fred = prev_fred or {}
        self.gfcri = gfcri_value
        self.prev_gfcri = prev_gfcri_value

    def derive_all_signals(self) -> list[ContextSignal]:
        methods = [
            self._fed_rate_action,
            self._fed_qt_status,
            self._credit_spread_regime,
            self._yield_curve_signal,
            self._cn_deflation_risk,
            self._cn_m2_m1_scissor,
            self._carry_trade_risk,
            self._em_capital_outflow,
            self._gold_structural_bid,
            self._vix_false_calm,
            self._copper_gold_ratio,
            self._consumer_paradox,
        ]
        signals = []
        for m in methods:
            try:
                s = m()
                if s:
                    signals.append(s)
            except Exception as e:
                logger.debug(f"Signal {m.__name__} failed: {e}")
        signals.sort(key=lambda s: {"high": 0, "medium": 1, "low": 2}.get(s.significance, 3))
        return signals

    def _hist_ago(self, key: str, days: int) -> float | None:
        series = self.fred_hist.get(key)
        if series is None or series.empty:
            return None
        cutoff = series.index.max() - pd.Timedelta(days=days)
        older = series[series.index <= cutoff]
        return float(older.iloc[-1]) if not older.empty else None

    # ── 1. Fed rate action ──

    def _fed_rate_action(self) -> ContextSignal | None:
        effr = self.fred.get("fred_effr")
        if effr is None:
            return None
        effr_30d = self._hist_ago("fred_effr", 30)
        effr_90d = self._hist_ago("fred_effr", 90)

        if effr_30d is not None and abs(effr - effr_30d) >= 0.2:
            delta = effr - effr_30d
            action = "加息" if delta > 0 else "降息"
            bps = abs(delta) * 100
            return ContextSignal(
                signal_id="fed_rate_change", category="policy",
                title=f"美联储{action}{bps:.0f}bp",
                what_happened=f"联邦基金利率从{effr_30d:.2f}%变为{effr:.2f}%，{action}{bps:.0f}个基点",
                data_reaction=f"当前利率{effr:.2f}%，{'紧缩力度加大' if delta > 0 else '宽松信号释放'}",
                deep_meaning=f"{'高利率持续挤压企业融资和房贷成本' if delta > 0 else '降息释放流动性，但效果需要6-12个月传导到实体经济'}",
                significance="high",
                affected_nodes=["fed_funds", "ust_10y", "dxy"],
            )

        if effr_90d is not None and abs(effr - effr_90d) < 0.1:
            return ContextSignal(
                signal_id="fed_rate_hold", category="policy",
                title=f"美联储按兵不动（利率{effr:.2f}%）",
                what_happened=f"联邦基金利率维持在{effr:.2f}%，过去3个月未变动",
                data_reaction=f"市场已消化当前利率水平，VIX={self.nodes.get('vix', 0):.1f}",
                deep_meaning="利率不动不代表没风险——高利率持续时间越长，对企业和消费者的累积伤害越大",
                significance="medium",
                affected_nodes=["fed_funds"],
            )
        return None

    # ── 2. Fed QT status ──

    def _fed_qt_status(self) -> ContextSignal | None:
        walcl = self.fred.get("fred_walcl")
        if walcl is None:
            return None
        walcl_4w = self._hist_ago("fred_walcl", 28)
        if walcl_4w is None:
            return None

        delta_monthly = walcl - walcl_4w
        delta_b = delta_monthly / 1000

        if abs(delta_b) < 5:
            return None

        if delta_monthly < 0:
            return ContextSignal(
                signal_id="fed_qt_continuing", category="policy",
                title="美联储缩表持续，流动性被抽走",
                what_happened=f"美联储资产负债表过去一月减少{abs(delta_b):.0f}0亿美元（当前{walcl/1e6:.1f}万亿）",
                data_reaction=f"流动性收紧中，但VIX={self.nodes.get('vix', 0):.1f}暂未反应",
                deep_meaning="缩表是「慢刀子」——不会立刻引爆市场，但持续抽走流动性会让下一次冲击的杀伤力更大",
                significance="high",
                affected_nodes=["vix", "spx", "hyg"],
            )
        else:
            return ContextSignal(
                signal_id="fed_qt_slowing", category="policy",
                title="美联储扩表/放慢缩表",
                what_happened=f"美联储资产负债表过去一月增加{delta_b:.0f}0亿美元（当前{walcl/1e6:.1f}万亿）",
                data_reaction="流动性环境边际改善",
                deep_meaning="如果是主动扩表，说明美联储看到了需要干预的风险",
                significance="medium",
                affected_nodes=["vix", "spx"],
            )

    # ── 3. Credit spread regime ──

    def _credit_spread_regime(self) -> ContextSignal | None:
        bbb = self.fred.get("fred_bbb_spread")
        hy = self.fred.get("fred_hy_spread")
        if bbb is None and hy is None:
            return None

        spread = bbb or hy
        name = "BBB信用利差" if bbb else "高收益债利差"
        prev = self._hist_ago("fred_bbb_spread" if bbb else "fred_hy_spread", 30)
        direction = ""
        if prev and spread:
            delta = spread - prev
            direction = f"，较上月{'扩大' if delta > 0 else '收窄'}{abs(delta):.2f}个百分点"

        if spread and spread > 3.5:
            return ContextSignal(
                signal_id="credit_stress", category="credit",
                title="信用市场进入压力区间",
                what_happened=f"{name}达到{spread:.2f}%{direction}，企业融资成本显著升高",
                data_reaction="弱资质企业借钱越来越贵，违约风险在积累",
                deep_meaning="信用利差是2008年危机最早亮起的红灯——雷曼倒闭前15个月利差就开始扩大",
                significance="high",
                affected_nodes=["hyg", "lqd"],
            )
        elif spread and spread > 2.0:
            return ContextSignal(
                signal_id="credit_widening", category="credit",
                title="信用利差正在扩大",
                what_happened=f"{name}达到{spread:.2f}%{direction}",
                data_reaction="信用市场开始谨慎，但尚未恐慌",
                deep_meaning="利差扩大意味着市场开始区分「好公司」和「差公司」——这是风险定价回归理性，但也可能是压力的前兆",
                significance="medium",
                affected_nodes=["hyg", "lqd"],
            )
        return None

    # ── 4. Yield curve ──

    def _yield_curve_signal(self) -> ContextSignal | None:
        t10y2y = self.fred.get("fred_t10y2y")
        if t10y2y is None:
            return None

        if t10y2y < 0:
            return ContextSignal(
                signal_id="yield_curve_inverted", category="policy",
                title=f"收益率曲线倒挂（{t10y2y:+.2f}%）",
                what_happened=f"10年期-2年期美债利差为{t10y2y:.2f}%，短端高于长端",
                data_reaction="市场预期未来经济将走弱，长端利率被压低",
                deep_meaning="收益率曲线倒挂是过去60年最可靠的衰退领先指标，平均领先6-18个月",
                significance="high",
                affected_nodes=["ust_10y", "ust_2y"],
            )
        elif t10y2y < 0.3:
            return ContextSignal(
                signal_id="yield_curve_flat", category="policy",
                title=f"收益率曲线接近平坦（{t10y2y:.2f}%）",
                what_happened=f"10年期-2年期利差仅{t10y2y:.2f}%，接近倒挂边界",
                data_reaction="债券市场对经济前景持谨慎态度",
                deep_meaning="曲线平坦化通常出现在加息周期末期，是经济放缓的早期信号",
                significance="medium",
                affected_nodes=["ust_10y"],
            )
        return None

    # ── 5. China deflation ──

    def _cn_deflation_risk(self) -> ContextSignal | None:
        cpi = self.china.get("cn_cpi_yoy")
        ppi = self.china.get("cn_ppi_yoy")
        if cpi is None or ppi is None:
            return None

        if cpi <= 0 and ppi <= 0:
            return ContextSignal(
                signal_id="cn_deflation", category="real_economy",
                title="中国陷入通缩——CPI和PPI双负",
                what_happened=f"中国CPI同比{cpi:.1f}%，PPI同比{ppi:.1f}%，消费和生产价格双双下跌",
                data_reaction="人民币承压、港股走弱、大宗商品需求预期下降",
                deep_meaning="通缩意味着企业利润被挤压→裁员→消费更弱→更多通缩，形成恶性循环。中国是全球最大工业品消费国，其通缩会通过贸易链传导到全球",
                significance="high",
                affected_nodes=["cny_usd", "hsi", "copper"],
            )
        elif ppi < -2 and cpi > 0:
            return ContextSignal(
                signal_id="cn_ppi_deflation", category="real_economy",
                title="中国工厂通缩，消费端尚未波及",
                what_happened=f"PPI同比{ppi:.1f}%（工厂端通缩），CPI同比{cpi:.1f}%（消费端仍正）",
                data_reaction="工业品价格下跌压力从中国向全球传导",
                deep_meaning="工厂端通缩是需求不足的早期信号，如果持续将传导到消费端",
                significance="medium",
                affected_nodes=["cny_usd", "copper"],
            )
        return None

    # ── 6. China M2-M1 scissor ──

    def _cn_m2_m1_scissor(self) -> ContextSignal | None:
        m2 = self.china.get("cn_m2_yoy")
        m1 = self.china.get("cn_m1_yoy")
        if m2 is None or m1 is None:
            return None

        gap = m2 - m1
        if gap > 5:
            return ContextSignal(
                signal_id="cn_m2_m1_gap", category="capital_flow",
                title=f"中国资金淤积严重（M2-M1剪刀差{gap:.1f}%）",
                what_happened=f"M2增速{m2:.1f}%远超M1增速{m1:.1f}%，资金停留在定期存款而非活期账户",
                data_reaction="企业和居民宁愿存钱也不投资消费，经济活力低迷",
                deep_meaning="钱印出来了但转不起来——央行放水但水没流到实体经济，这是日本「流动性陷阱」的中国版本",
                significance="high" if gap > 8 else "medium",
                affected_nodes=["cny_usd", "hsi"],
            )
        return None

    # ── 7. Carry trade risk ──

    def _carry_trade_risk(self) -> ContextSignal | None:
        jp_data = self.oecd.get("JP", {})
        jp_short = jp_data.get("oecd_short_rate")
        us_effr = self.fred.get("fred_effr")
        jpy = self.nodes.get("jpy_usd")
        jpy_z = self.zscores.get("jpy_usd", 0)

        if jp_short is None or us_effr is None:
            return None

        differential = us_effr - jp_short
        yen_strengthening = jpy_z < -1.5

        if differential < 3.0 and yen_strengthening:
            return ContextSignal(
                signal_id="carry_unwind_risk", category="capital_flow",
                title="日元套利交易面临平仓压力",
                what_happened=f"美日利差收窄至{differential:.1f}%（日本{jp_short:.2f}% vs 美国{us_effr:.2f}%），日元走强",
                data_reaction=f"日元升值（偏离正常范围{abs(jpy_z):.1f}倍），套利交易的汇率亏损在侵蚀利差收益",
                deep_meaning="全球有数万亿美元的日元套利交易。一旦大规模平仓，资金从全球风险资产撤出，会引发连锁抛售",
                significance="high",
                affected_nodes=["jpy_usd", "nikkei", "vix"],
            )
        elif differential < 3.5:
            return ContextSignal(
                signal_id="carry_differential_narrow", category="capital_flow",
                title=f"美日利差收窄至{differential:.1f}%",
                what_happened=f"日本短期利率{jp_short:.2f}%，美国{us_effr:.2f}%",
                data_reaction="套利交易吸引力下降，但尚未触发平仓",
                deep_meaning="利差继续收窄将增加日元套利平仓风险",
                significance="medium",
                affected_nodes=["jpy_usd"],
            )
        return None

    # ── 8. EM capital outflow ──

    def _em_capital_outflow(self) -> ContextSignal | None:
        eem_z = self.zscores.get("eem", 0)
        emb_z = self.zscores.get("emb", 0)
        dxy_z = self.zscores.get("dxy", 0)

        if eem_z < -1.5 and dxy_z > 1.5:
            return ContextSignal(
                signal_id="em_outflow", category="capital_flow",
                title="新兴市场资金外流信号",
                what_happened=f"新兴市场股票ETF偏低{abs(eem_z):.1f}倍，美元偏强{dxy_z:.1f}倍",
                data_reaction="美元走强→资金从新兴市场回流美国",
                deep_meaning="强美元是新兴市场的「死亡之吻」——以美元计价的债务变贵，外资加速撤离",
                significance="high" if emb_z < -1.5 else "medium",
                affected_nodes=["eem", "emb", "dxy", "krw_usd"],
            )
        return None

    # ── 9. Gold structural bid ──

    def _gold_structural_bid(self) -> ContextSignal | None:
        gold_z = self.zscores.get("gold", 0)
        spx_z = self.zscores.get("spx", 0)
        gold_val = self.nodes.get("gold")

        if gold_z > 1.5 and abs(spx_z) < 1.5 and gold_val:
            return ContextSignal(
                signal_id="gold_structural", category="capital_flow",
                title=f"黄金持续走高（${gold_val:.0f}），非恐慌性上涨",
                what_happened=f"黄金偏高{gold_z:.1f}倍，但股市波动正常（标普偏离仅{spx_z:+.1f}倍）",
                data_reaction="黄金上涨不是因为股市暴跌引发的恐慌，而是结构性买盘",
                deep_meaning="各国央行连续多年增持黄金储备，这是去美元化的长期趋势信号——主权资本在重新定义「安全资产」",
                significance="high",
                affected_nodes=["gold", "dxy"],
            )
        return None

    # ── 10. VIX false calm ──

    def _vix_false_calm(self) -> ContextSignal | None:
        vix = self.nodes.get("vix")
        bbb = self.fred.get("fred_bbb_spread")

        if vix is None:
            return None
        if vix >= 18:
            return None

        if bbb and bbb > 1.8:
            return ContextSignal(
                signal_id="vix_false_calm", category="credit",
                title=f"VIX={vix:.1f}看似平静，但信用市场不买账",
                what_happened=f"VIX恐慌指数仅{vix:.1f}（低于警戒线），但BBB信用利差{bbb:.2f}%仍然偏高",
                data_reaction="股市定价的风险很低，但债市说的是另一个故事",
                deep_meaning="VIX是「情绪温度计」，容易被央行放水压低。信用利差才是「体检报告」——企业真实的偿债压力骗不了人。2008年4-8月就是VIX回落但利差高企的经典案例",
                significance="high",
                affected_nodes=["vix", "hyg", "lqd"],
            )
        return None

    # ── 11. Copper/gold ratio ──

    def _copper_gold_ratio(self) -> ContextSignal | None:
        copper = self.nodes.get("copper")
        gold = self.nodes.get("gold")
        if not copper or not gold or gold == 0:
            return None

        ratio = copper / gold * 1000
        copper_z = self.zscores.get("copper", 0)
        gold_z = self.zscores.get("gold", 0)

        if gold_z > 1.5 and copper_z < -0.5:
            return ContextSignal(
                signal_id="copper_gold_diverge", category="real_economy",
                title="铜金比下降——增长悲观压过通胀担忧",
                what_happened=f"黄金走强（偏离{gold_z:.1f}倍）而铜价走弱（偏离{copper_z:.1f}倍），铜金比下降",
                data_reaction="铜是工业需求的晴雨表，金是避险资产。铜跌金涨=市场押注经济放缓",
                deep_meaning="铜金比是最简单有效的经济周期指标——它说的是「增长比通胀更令人担忧」",
                significance="medium",
                affected_nodes=["copper", "gold"],
            )
        return None

    # ── 12. Consumer paradox ──

    def _consumer_paradox(self) -> ContextSignal | None:
        umcsent = self.fred.get("fred_umcsent")
        unrate = self.fred.get("fred_unrate")
        if umcsent is None or unrate is None:
            return None

        if umcsent < 55 and unrate < 4.5:
            return ContextSignal(
                signal_id="consumer_paradox", category="real_economy",
                title=f"有工作但不敢花钱（失业率{unrate:.1f}% vs 信心{umcsent:.0f}）",
                what_happened=f"失业率{unrate:.1f}%（偏低），但消费者信心指数仅{umcsent:.0f}（远低于80的健康线）",
                data_reaction="就业市场表面健康，但消费者行为已经收缩",
                deep_meaning="「有工作但不敢花钱」是滞胀的典型前兆——人们担心未来收入下降或物价继续上涨。消费占美国GDP的70%，信心崩塌最终会变成真实的经济衰退",
                significance="high",
                affected_nodes=["consumer_stress", "us_recession_prob"],
            )
        return None
