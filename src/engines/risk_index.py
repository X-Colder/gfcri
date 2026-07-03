"""
Global Financial Crisis Risk Index (GFCRI) engine.

Computes a composite 0-100 risk index from sub-indices using dual-track scoring:
  - Z-score track (40%): captures sudden changes and acceleration
  - Absolute-level track (60%): captures sustained deterioration that z-score
    adapts to (the "boiling frog" problem from 2008 backtesting)

Also detects surface-calm / deep-stress divergences where headline indicators
(VIX, equity) look fine but structural indicators (credit spreads, interbank
trust) remain elevated — the "calm before the storm" pattern.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from loguru import logger

from src.engines.trade_dependency import TradeDependencyEngine

if TYPE_CHECKING:
    from src.models.graph import MacroRiskCausalGraph


# Absolute-level benchmarks: (danger_direction, normal, crisis)
# "high" = rising is dangerous; "low" = falling is dangerous
ABS_BENCHMARKS: dict[str, tuple[str, float, float]] = {
    "vix":              ("high", 15, 45),
    "hyg":              ("low",  82, 60),
    "dxy":              ("high", 100, 114),
    "spx":              ("low",  5000, 3500),
    "ust_10y":          ("high", 3.5, 5.2),
    "oil_wti":          ("high", 70, 120),
    "gold":             ("high", 1900, 3000),
    "krw_usd":          ("high", 1250, 1550),
    "jpy_usd":          ("high", 130, 160),
    "kospi":            ("low",  2600, 1800),
    "hsi":              ("low",  22000, 14000),
    "eurusd":           ("low",  1.10, 0.95),
    "lqd":              ("low",  110, 90),
    "kre":              ("low",  50, 30),
    "vnq":              ("low",  85, 55),
    "sox":              ("low",  4000, 2500),
    "stoxx50":          ("low",  4200, 3200),
    "copper":           ("low",  4.0, 3.0),
    "eem":              ("low",  42, 30),
    "btc":              ("low",  60000, 20000),
}

# Divergence detection: "surface" indicators that calm quickly vs
# "deep" indicators that stay elevated during structural crises
SURFACE_INDICATORS = {"vix", "spx", "kospi", "hsi", "sox", "stoxx50"}
DEEP_INDICATORS = {"hyg", "lqd", "kre", "vnq", "dxy", "ust_10y", "oil_wti", "krw_usd"}

# Policy sensitivity classification for "fever chart" diagnosis
# policy_responsive: Fed/central bank action can quickly suppress these
# structural: requires real economy healing, policy alone can't fix
# leading: forward-looking, warns of what's coming 6-18 months ahead
INDICATOR_POLICY_CLASS: dict[str, dict[str, str]] = {
    # Policy-responsive: "退烧药能压下去"
    "vix":       {"class": "policy_responsive", "label": "VIX恐慌指数",
                  "why": "央行注入流动性→市场恐慌消退→VIX快速回落"},
    "spx":       {"class": "policy_responsive", "label": "标普500",
                  "why": "降息/QE→资金涌入股市→指数反弹"},
    "kospi":     {"class": "policy_responsive", "label": "韩国KOSPI",
                  "why": "全球央行宽松→风险偏好回升→新兴市场反弹"},
    "hsi":       {"class": "policy_responsive", "label": "恒生指数",
                  "why": "中国央行降准降息→港股跟随回暖"},
    "eem":       {"class": "policy_responsive", "label": "新兴市场ETF",
                  "why": "美联储暂停加息→美元走弱→资金回流新兴市场"},
    # Structural: "病根还在，退烧药压不住"
    "hyg":       {"class": "structural", "label": "高收益债ETF",
                  "why": "企业信用状况需要真实盈利改善，央行注入流动性不能直接修复企业偿债能力"},
    "lqd":       {"class": "structural", "label": "投资级债ETF",
                  "why": "企业债利差反映的是市场对企业违约的真实定价"},
    "kre":       {"class": "structural", "label": "区域银行ETF",
                  "why": "银行坏账需要漫长的核销周期，不是降息就能解决"},
    "vnq":       {"class": "structural", "label": "房地产ETF",
                  "why": "房价调整是慢变量，政策只能延缓不能逆转"},
    "dxy":       {"class": "structural", "label": "美元指数",
                  "why": "美元强弱由全球资本流动决定，单一央行难以控制"},
    "krw_usd":   {"class": "structural", "label": "韩元汇率",
                  "why": "韩元取决于出口竞争力和外资流向，非政策能直接管控"},
    "oil_wti":   {"class": "structural", "label": "原油价格",
                  "why": "油价由供需基本面决定，非央行工具能调节"},
    "copper":    {"class": "structural", "label": "铜价",
                  "why": "铜是实体经济的体温计，反映真实工业需求"},
    # Leading: "预告6-18个月后的事"
    "ust_10y":   {"class": "leading", "label": "10年期美债收益率",
                  "why": "长端利率包含市场对未来通胀和增长的预期"},
    "gold":      {"class": "leading", "label": "黄金",
                  "why": "黄金持续走高=市场在为未来的不确定性买保险"},
    "btc":       {"class": "leading", "label": "比特币",
                  "why": "加密货币是风险偏好的极端指标，领先于传统市场反应"},
    "sox":       {"class": "leading", "label": "半导体指数",
                  "why": "芯片是经济周期最敏感的前端，订单变化领先GDP 2-3个季度"},
}


def _abs_score(node_id: str, value: float) -> float | None:
    """Score 0-1 based on where value sits between normal and crisis thresholds."""
    bench = ABS_BENCHMARKS.get(node_id)
    if bench is None:
        return None
    direction, normal, crisis = bench
    if direction == "high":
        rng = crisis - normal
        return max(0.0, min(1.0, (value - normal) / rng)) if rng > 0 else 0.0
    else:
        rng = normal - crisis
        return max(0.0, min(1.0, (normal - value) / rng)) if rng > 0 else 0.0


SUB_INDEX_CONFIG: dict[str, dict[str, Any]] = {
    "SI_RATES": {
        "name": "利率与央行",
        "nodes": ["fed_funds", "ust_10y", "ust_2y"],
        "weight": 0.14,
    },
    "SI_FX": {
        "name": "全球汇率",
        "nodes": ["dxy", "krw_usd", "eurusd", "cny_usd", "jpy_usd"],
        "weight": 0.14,
    },
    "SI_US_EQUITY": {
        "name": "美国股市",
        "nodes": ["spx", "sox"],
        "weight": 0.10,
    },
    "SI_ASIA_EQUITY": {
        "name": "亚洲股市",
        "nodes": ["kospi", "hsi", "nikkei"],
        "weight": 0.10,
    },
    "SI_EUROPE": {
        "name": "欧洲市场",
        "nodes": ["stoxx50", "italy_etf"],
        "weight": 0.08,
    },
    "SI_CREDIT": {
        "name": "信用与违约",
        "nodes": ["hyg", "lqd", "kr_cds_5y", "orcl_cds", "emb"],
        "weight": 0.14,
    },
    "SI_BANKING": {
        "name": "银行与房产",
        "nodes": ["kre", "vnq"],
        "weight": 0.08,
    },
    "SI_COMMODITY": {
        "name": "商品与贸易",
        "nodes": ["oil_wti", "copper", "gold", "natgas", "wheat", "dram_spot", "nand_spot", "bdry"],
        "weight": 0.10,
    },
    "SI_SENTIMENT": {
        "name": "情绪与风险偏好",
        "nodes": ["vix", "us_recession_prob", "btc", "consumer_stress", "eem"],
        "weight": 0.12,
    },
    "SI_TRADE_SPILLOVER": {
        "name": "贸易依赖传导",
        "nodes": [],
        "weight": 0.0,
    },
}

RISK_CHAINS: list[dict[str, Any]] = [
    {
        "id": "fed_cascade",
        "name": "央行加息冲击波",
        "path": ["fed_funds", "ust_10y", "dxy", "krw_usd"],
        "description": "加息通过利率差→强美元→冲击新兴市场货币",
    },
    {
        "id": "dollar_squeeze",
        "name": "强美元挤压",
        "path": ["ust_10y", "dxy", "krw_usd", "kospi"],
        "description": "美债收益率上升→美元走强→韩元贬值→外资撤离韩股",
    },
    {
        "id": "credit_contagion",
        "name": "信用危机传染",
        "path": ["lqd", "hyg", "kr_cds_5y", "kospi"],
        "description": "投资级债→垃圾债→主权信用恶化→股市暴跌",
    },
    {
        "id": "housing_bank_doom",
        "name": "房地产银行危机",
        "path": ["vnq", "kre", "vix"],
        "description": "房价下跌→银行坏账→系统性恐慌",
    },
    {
        "id": "consumer_recession",
        "name": "消费崩塌衰退",
        "path": ["consumer_stress", "us_recession_prob", "vix", "krw_usd"],
        "description": "消费者勒紧裤腰带→衰退→恐慌→资金外逃",
    },
    {
        "id": "ai_semi_cycle",
        "name": "AI芯片周期",
        "path": ["ai_capex", "dram_spot", "kospi", "sox"],
        "description": "AI投资→芯片涨价→韩国股市→半导体板块",
    },
    {
        "id": "safe_haven_flight",
        "name": "避险资金逃亡",
        "path": ["gold", "dxy", "krw_usd"],
        "description": "黄金飙升→美元波动→新兴市场货币承压",
    },
    {
        "id": "europe_contagion",
        "name": "欧债危机传染",
        "path": ["italy_etf", "eurusd", "dxy", "eem"],
        "description": "意大利风险→欧元走弱→美元走强→新兴市场承压",
    },
    {
        "id": "china_shockwave",
        "name": "中国冲击波",
        "path": ["cny_usd", "hsi", "kospi"],
        "description": "人民币贬值→港股暴跌→韩国出口受创",
    },
    {
        "id": "yen_carry_unwind",
        "name": "日元套利平仓",
        "path": ["jpy_usd", "nikkei", "vix"],
        "description": "日元急升→套利交易平仓→全球波动率飙升",
    },
    {
        "id": "crypto_contagion",
        "name": "加密货币传染",
        "path": ["btc", "vix", "eem"],
        "description": "比特币崩盘→风险偏好崩塌→新兴市场抛售",
    },
    {
        "id": "food_energy_shock",
        "name": "粮食能源冲击",
        "path": ["wheat", "natgas", "stoxx50"],
        "description": "粮食/能源价格飙升→欧洲成本危机",
    },
]


class GFCRIEngine:
    """Computes the Global Financial Crisis Risk Index (0-100)."""

    Z_WEIGHT = 0.4
    ABS_WEIGHT = 0.6

    def __init__(self, graph: "MacroRiskCausalGraph") -> None:
        self.graph = graph
        self.trade_engine = TradeDependencyEngine()

    def compute(self) -> dict[str, Any]:
        sub_indices = {}
        for si_id, config in SUB_INDEX_CONFIG.items():
            if config["nodes"]:
                sub_indices[si_id] = self._compute_sub_index(si_id, config)

        chain_results = [self._evaluate_chain(c) for c in RISK_CHAINS]
        active_count = sum(1 for c in chain_results if c["stress"] > 40)
        coherence = 1.0 + 0.05 * max(0, active_count - 1)

        node_contributions = self._compute_node_contributions()
        divergence = self._detect_divergence(node_contributions)
        trade_spillover = self.trade_engine.compute(node_contributions)
        trade_boost = self._compute_trade_spillover_boost(trade_spillover)
        sub_indices["SI_TRADE_SPILLOVER"] = self._trade_sub_index(trade_spillover)

        gfcri_base = sum(
            sub_indices[si_id]["score"] * config["weight"]
            for si_id, config in SUB_INDEX_CONFIG.items()
            if si_id in sub_indices
        )

        # Undercurrent boost: hidden risks that z-score misses must lift the score
        undercurrent = self._compute_undercurrent(node_contributions, divergence, active_count)

        gfcri = min(100.0, max(0.0, gfcri_base * coherence + undercurrent + trade_boost))
        alert_level = self._alert_level(gfcri)

        result = {
            "gfcri": round(gfcri, 2),
            "alert_level": alert_level,
            "sub_indices": sub_indices,
            "chains": chain_results,
            "coherence_multiplier": round(coherence, 2),
            "active_chain_count": active_count,
            "node_contributions": node_contributions,
            "divergence": divergence,
            "undercurrent_boost": round(undercurrent, 2),
            "trade_spillover": trade_spillover,
            "trade_spillover_boost": round(trade_boost, 2),
        }

        logger.info(
            f"GFCRI computed: {gfcri:.1f}/100 ({alert_level}), "
            f"active_chains={active_count}, divergence={divergence['status']}, "
            f"trade={trade_spillover['score']:.1f}/+{trade_boost:.1f}, "
            f"undercurrent=+{undercurrent:.1f}"
        )
        return result

    @staticmethod
    def _compute_trade_spillover_boost(trade_spillover: dict[str, Any]) -> float:
        """Additive GFCRI boost from cross-economy trade spillover.

        The static-v1 trade layer is deliberately capped. It should lift risk
        when external exposure is visible, but it must not dominate direct
        market stress before the trade matrix is validated with official data.
        """
        score = float(trade_spillover.get("score", 0.0))
        if score <= 15:
            return 0.0
        return min(8.0, (score - 15.0) * 0.25)

    def _trade_sub_index(self, trade_spillover: dict[str, Any]) -> dict[str, Any]:
        top_link = trade_spillover.get("top_links", [{}])[0] if trade_spillover.get("top_links") else {}
        affected_scores = trade_spillover.get("affected_node_scores", {})
        return {
            "score": round(float(trade_spillover.get("score", 0.0)), 2),
            "name": "贸易依赖传导",
            "mean_stress": round(float(trade_spillover.get("score", 0.0)) / 100.0, 4),
            "mean_abs_stress": 0.0,
            "transmission": round(float(trade_spillover.get("score", 0.0)) / 100.0, 4),
            "node_scores": affected_scores,
            "top_driver": top_link.get("affected_nodes", ["-"])[0] if top_link else "-",
            "trade_spillover_boost": round(self._compute_trade_spillover_boost(trade_spillover), 2),
            "trade_spillover": trade_spillover,
        }

    def _compute_sub_index(
        self, si_id: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        nodes = config["nodes"]

        z_scores = {}
        abs_scores = {}
        for nid in nodes:
            node = self.graph.nodes.get(nid)
            if node:
                z_scores[nid] = node.anomaly_score
                if node.current_value is not None:
                    a = _abs_score(nid, node.current_value)
                    if a is not None:
                        abs_scores[nid] = a

        mean_z = (
            sum(z_scores.values()) / len(z_scores)
            if z_scores
            else 0.0
        )
        mean_abs = (
            sum(abs_scores.values()) / len(abs_scores)
            if abs_scores
            else 0.0
        )

        transmission = self._compute_transmission_amp(set(nodes))

        raw_stress = self.Z_WEIGHT * mean_z + self.ABS_WEIGHT * mean_abs
        score = 100.0 * (0.6 * raw_stress + 0.4 * transmission)
        score = min(100.0, score)

        top_node = max(z_scores, key=z_scores.get) if z_scores else None

        return {
            "score": round(score, 2),
            "name": config["name"],
            "mean_stress": round(mean_z, 4),
            "mean_abs_stress": round(mean_abs, 4),
            "transmission": round(transmission, 4),
            "node_scores": {k: round(v, 4) for k, v in z_scores.items()},
            "top_driver": top_node,
        }

    def _compute_transmission_amp(self, group_nodes: set[str]) -> float:
        inbound_sum = 0.0
        count = 0
        for edge in self.graph.edges.values():
            if edge.is_deprecated:
                continue
            if edge.target_node in group_nodes and edge.source_node not in group_nodes:
                src_node = self.graph.nodes.get(edge.source_node)
                if src_node:
                    inbound_sum += src_node.anomaly_score * abs(edge.causal_strength)
                    count += 1
        return min(1.0, inbound_sum / max(count, 1))

    def _evaluate_chain(self, chain_config: dict[str, Any]) -> dict[str, Any]:
        path = chain_config["path"]
        node_scores = []
        path_strength = 1.0
        edge_details = []

        for i, nid in enumerate(path):
            node = self.graph.nodes.get(nid)
            score = node.anomaly_score if node else 0.0
            node_scores.append(score)

            if i < len(path) - 1:
                next_nid = path[i + 1]
                edge = self._find_edge(nid, next_nid)
                if edge:
                    path_strength *= edge.causal_strength
                    edge_details.append(
                        f"{nid}→{next_nid}({edge.causal_strength:+.3f})"
                    )

        chain_stress = 100.0 * sum(node_scores) / len(node_scores) if node_scores else 0.0

        return {
            "id": chain_config["id"],
            "name": chain_config["name"],
            "path": path,
            "description": chain_config["description"],
            "stress": round(chain_stress, 2),
            "path_strength": round(path_strength, 4),
            "edge_details": edge_details,
            "active": chain_stress > 40,
            "node_scores": {
                path[i]: round(s, 4) for i, s in enumerate(node_scores)
            },
        }

    def _compute_node_contributions(self) -> dict[str, dict[str, Any]]:
        contributions = {}
        for nid, node in self.graph.nodes.items():
            zscore = node.value_zscore or 0.0
            abs_s = None
            if node.current_value is not None:
                abs_s = _abs_score(nid, node.current_value)
            contributions[nid] = {
                "display_name": node.display_name,
                "current_value": node.current_value,
                "zscore": round(zscore, 4),
                "anomaly_score": round(node.anomaly_score, 4),
                "abs_score": round(abs_s, 4) if abs_s is not None else None,
                "is_anomalous": node.is_anomalous,
                "direction": "above" if zscore > 0 else "below",
            }
        return contributions

    def _detect_divergence(self, contribs: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Detect surface-calm / deep-stress divergence.

        Returns a dict with:
          status: "none" | "mild" | "significant" | "critical"
          surface_avg: mean abs_score of headline indicators
          deep_avg: mean abs_score of structural indicators
          gap: deep_avg - surface_avg
          details: list of specific divergence findings
        """
        surface_scores = []
        deep_scores = []
        for nid, info in contribs.items():
            a = info.get("abs_score")
            if a is None:
                continue
            if nid in SURFACE_INDICATORS:
                surface_scores.append((nid, a))
            if nid in DEEP_INDICATORS:
                deep_scores.append((nid, a))

        surface_avg = sum(s for _, s in surface_scores) / len(surface_scores) if surface_scores else 0
        deep_avg = sum(s for _, s in deep_scores) / len(deep_scores) if deep_scores else 0
        gap = deep_avg - surface_avg

        details = []

        # Pattern 1: deep stress significantly exceeds surface stress
        if gap > 0.15 and deep_avg > 0.3:
            stressed_deep = sorted(
                [(nid, s) for nid, s in deep_scores if s > 0.3],
                key=lambda x: -x[1],
            )
            calm_surface = sorted(
                [(nid, s) for nid, s in surface_scores if s < 0.25],
                key=lambda x: x[1],
            )
            if stressed_deep and calm_surface:
                deep_names = [contribs[nid]["display_name"] for nid, _ in stressed_deep[:3]]
                calm_names = [contribs[nid]["display_name"] for nid, _ in calm_surface[:3]]
                details.append({
                    "type": "surface_calm_deep_stress",
                    "title": "表面平静，底层恶化",
                    "detail": (
                        f"表面指标（{', '.join(calm_names)}）看起来正常，"
                        f"但结构性指标（{', '.join(deep_names)}）处于高压状态。"
                        f"这种背离在2008年4-8月出现过——市场表面反弹，"
                        f"但信用利差和银行间信任从未恢复正常。"
                    ),
                    "stressed_indicators": [nid for nid, _ in stressed_deep],
                    "calm_indicators": [nid for nid, _ in calm_surface],
                })

        # Pattern 2: z-score says normal but absolute level says warning
        zscore_calm_abs_stressed = []
        for nid, info in contribs.items():
            z = abs(info.get("zscore", 0))
            a = info.get("abs_score")
            if a is not None and z < 1.5 and a > 0.4:
                zscore_calm_abs_stressed.append((nid, info["display_name"], z, a))

        if zscore_calm_abs_stressed:
            details.append({
                "type": "zscore_desensitized",
                "title": "市场已「习惯」异常水平",
                "detail": (
                    f"以下指标的绝对水平处于危险区间，但因为持续高位，"
                    f"变化速度指标已经钝化——市场已经「习惯了」这种异常，"
                    f"但风险并未消失：" +
                    "；".join(
                        f"{name}（绝对压力{a*100:.0f}%，变化速度仅{z:.1f}倍）"
                        for _, name, z, a in zscore_calm_abs_stressed[:4]
                    )
                ),
                "desensitized_indicators": [nid for nid, _, _, _ in zscore_calm_abs_stressed],
            })

        # Pattern 3: policy-responsive indicators calmed but structural didn't
        policy_resp = []
        structural = []
        leading = []
        for nid, info in contribs.items():
            a = info.get("abs_score")
            if a is None or nid not in INDICATOR_POLICY_CLASS:
                continue
            cls = INDICATOR_POLICY_CLASS[nid]["class"]
            entry = (nid, INDICATOR_POLICY_CLASS[nid]["label"], a, INDICATOR_POLICY_CLASS[nid]["why"])
            if cls == "policy_responsive":
                policy_resp.append(entry)
            elif cls == "structural":
                structural.append(entry)
            elif cls == "leading":
                leading.append(entry)

        pr_avg = sum(a for _, _, a, _ in policy_resp) / len(policy_resp) if policy_resp else 0
        st_avg = sum(a for _, _, a, _ in structural) / len(structural) if structural else 0
        ld_avg = sum(a for _, _, a, _ in leading) / len(leading) if leading else 0

        healed_items = [(nid, label, a, why) for nid, label, a, why in policy_resp if a < 0.25]
        unhealed_items = [(nid, label, a, why) for nid, label, a, why in structural if a > 0.3]
        warning_items = [(nid, label, a, why) for nid, label, a, why in leading if a > 0.35]

        if healed_items and unhealed_items and (st_avg - pr_avg) > 0.1:
            details.append({
                "type": "policy_mask",
                "title": "政策退烧 vs 病根未除",
                "policy_responsive_avg": round(pr_avg * 100),
                "structural_avg": round(st_avg * 100),
                "leading_avg": round(ld_avg * 100),
                "healed": [{"id": nid, "label": label, "score": round(a * 100), "why": why}
                           for nid, label, a, why in healed_items],
                "unhealed": [{"id": nid, "label": label, "score": round(a * 100), "why": why}
                             for nid, label, a, why in sorted(unhealed_items, key=lambda x: -x[2])],
                "leading_warnings": [{"id": nid, "label": label, "score": round(a * 100), "why": why}
                                     for nid, label, a, why in sorted(warning_items, key=lambda x: -x[2])],
                "detail": (
                    f"政策敏感型指标平均压力 {pr_avg*100:.0f}%（已缓解），"
                    f"但结构性指标平均压力 {st_avg*100:.0f}%（未改善）。"
                    f"{'领先指标平均压力 ' + str(round(ld_avg*100)) + '%，预示未来仍有风险。' if warning_items else ''}"
                ),
            })

        # Pattern 4: speculative / AI-cycle overextension.
        speculative_candidates = []
        for nid in ["ai_capex", "sox", "spx", "kospi", "nikkei"]:
            info = contribs.get(nid)
            if not info:
                continue
            z = float(info.get("zscore", 0) or 0)
            anomaly = float(info.get("anomaly_score", 0) or 0)
            if z > 1.25 and anomaly >= 0.30:
                speculative_candidates.append({
                    "id": nid,
                    "label": info.get("display_name", nid),
                    "zscore": round(z, 2),
                    "anomaly": round(anomaly * 100),
                })

        if speculative_candidates:
            max_z = max(x["zscore"] for x in speculative_candidates)
            details.append({
                "type": "speculative_overextension",
                "title": "泡沫/拥挤交易压力",
                "severity_score": round(min(100, max_z / 3.0 * 100)),
                "indicators": speculative_candidates,
                "detail": (
                    "AI、半导体或股指处于高位异常区间。价格上涨本身不是危机，"
                    "但当上涨由集中叙事和拥挤交易驱动时，市场表面平静会低估回撤风险。"
                ),
            })

        # Pattern 5: yen depreciation pressure.
        jpy = contribs.get("jpy_usd")
        if jpy:
            jpy_z = float(jpy.get("zscore", 0) or 0)
            jpy_abs = float(jpy.get("abs_score") or 0)
            jpy_value = jpy.get("current_value")
            if jpy_z > 1.25 or jpy_abs > 0.30:
                if isinstance(jpy_value, (int, float)):
                    detail = (
                        f"USD/JPY 当前约 {jpy_value:.1f}，绝对压力 {jpy_abs*100:.0f}%。"
                        "日元持续走弱可能暂时支撑日本股市，但也增加干预、输入型通胀和套利交易反转风险。"
                    )
                else:
                    detail = "日元持续走弱增加干预、输入型通胀和套利交易反转风险。"
                details.append({
                    "type": "yen_depreciation_pressure",
                    "title": "日元贬值与套利交易脆弱性",
                    "zscore": round(jpy_z, 2),
                    "abs_score": round(jpy_abs * 100),
                    "current_value": jpy_value,
                    "detail": detail,
                })

        # Pattern 6: Korea equity high with FX/export-channel fragility.
        kospi = contribs.get("kospi")
        krw = contribs.get("krw_usd")
        if kospi and krw:
            kospi_z = float(kospi.get("zscore", 0) or 0)
            kospi_anom = float(kospi.get("anomaly_score", 0) or 0)
            krw_z = float(krw.get("zscore", 0) or 0)
            krw_abs = float(krw.get("abs_score") or 0)
            if kospi_z > 1.0 and kospi_anom >= 0.25 and (krw_z > 1.0 or krw_abs > 0.25):
                details.append({
                    "type": "korea_equity_fx_divergence",
                    "title": "韩国股市高位与汇率压力并存",
                    "kospi_zscore": round(kospi_z, 2),
                    "krw_zscore": round(krw_z, 2),
                    "krw_abs_score": round(krw_abs * 100),
                    "detail": (
                        "KOSPI 处于高位异常区间，同时韩元或外部融资通道承压。"
                        "这类组合常见于半导体周期过热、外资流入拥挤和出口敏感市场的脆弱阶段。"
                    ),
                })

        if gap > 0.25 and deep_avg > 0.4:
            status = "critical"
        elif gap > 0.15 and deep_avg > 0.3:
            status = "significant"
        elif gap > 0.08 or zscore_calm_abs_stressed:
            status = "mild"
        else:
            status = "none"

        hidden_detail_types = {d.get("type") for d in details}
        hidden_pressure_types = {
            "speculative_overextension",
            "yen_depreciation_pressure",
            "korea_equity_fx_divergence",
        }
        if status == "none" and hidden_detail_types.intersection(hidden_pressure_types):
            status = "mild"
        if status == "mild" and hidden_detail_types.intersection({
            "speculative_overextension",
            "korea_equity_fx_divergence",
        }) and len(hidden_detail_types.intersection(hidden_pressure_types)) >= 2:
            status = "significant"

        return {
            "status": status,
            "surface_avg": round(surface_avg, 4),
            "deep_avg": round(deep_avg, 4),
            "gap": round(gap, 4),
            "details": details,
        }

    def _compute_undercurrent(
        self,
        contribs: dict[str, dict[str, Any]],
        divergence: dict[str, Any],
        active_chain_count: int,
    ) -> float:
        """Compute undercurrent boost — hidden risks that z-score misses.

        These are additive points on top of the base GFCRI, reflecting:
        1. Anomalous node density — many indicators off at once = systemic
        2. Absolute-level extremes — indicators near crisis thresholds
        3. Divergence — surface calm but deep stress = deceptive safety
        4. Chain saturation — many transmission chains active simultaneously
        """
        boost = 0.0

        # 1. Anomalous node density: each anomalous node above 3 adds pressure
        anomalous_count = sum(1 for info in contribs.values() if info.get("is_anomalous"))
        total_nodes = max(len(contribs), 1)
        anomaly_ratio = anomalous_count / total_nodes
        if anomalous_count > 3:
            boost += min(8, (anomalous_count - 3) * 1.5)

        # 2. Absolute-level extremes: indicators at >80% of crisis threshold
        extreme_count = 0
        near_crisis = []
        for nid, info in contribs.items():
            a = info.get("abs_score")
            if a is not None and a >= 0.8:
                extreme_count += 1
                near_crisis.append(nid)
            elif a is not None and a >= 0.5:
                boost += 0.5
        if extreme_count > 0:
            boost += extreme_count * 3

        # 3. Divergence: surface-calm / deep-stress gap
        div_status = divergence.get("status", "none")
        div_gap = divergence.get("gap", 0)
        if div_status == "critical":
            boost += 12
        elif div_status == "significant":
            boost += 8
        elif div_status == "mild":
            boost += max(3, div_gap * 20)

        # 4. Chain saturation: when 5+ chains fire together, risk is non-linear
        if active_chain_count >= 6:
            boost += 5
        elif active_chain_count >= 4:
            boost += 3

        # 5. Policy mask penalty: structural stress masked by policy calm
        for d in divergence.get("details", []):
            if d.get("type") == "policy_mask":
                st_avg = d.get("structural_avg", 0)
                pr_avg = d.get("policy_responsive_avg", 0)
                if st_avg > 20 and pr_avg < 10:
                    boost += min(5, (st_avg - pr_avg) / 5)
            elif d.get("type") == "speculative_overextension":
                boost += min(6, max(2, float(d.get("severity_score", 0) or 0) / 18))
            elif d.get("type") == "yen_depreciation_pressure":
                boost += min(4, max(1.5, float(d.get("abs_score", 0) or 0) / 18))
            elif d.get("type") == "korea_equity_fx_divergence":
                boost += 3

        return min(25.0, boost)

    def _find_edge(self, source: str, target: str):
        for edge in self.graph.edges.values():
            if edge.source_node == source and edge.target_node == target:
                return edge
        return None

    @staticmethod
    def _alert_level(gfcri: float) -> str:
        if gfcri >= 75:
            return "red"
        if gfcri >= 50:
            return "orange"
        if gfcri >= 25:
            return "yellow"
        return "green"
