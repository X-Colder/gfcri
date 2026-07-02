"""Damage-based crisis taxonomy and forward-pressure assessment.

This layer deliberately separates three concepts:

1. Realized damage: what has already been damaged in markets/economy/credit.
2. Forward pressure: GFCRI-style stress that may lead to future damage.
3. Hidden risk: structural stress that may not yet be visible in realized damage.

The crisis level is anchored to realized damage. GFCRI is not used to define
whether a crisis has already happened.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any


@dataclass(frozen=True)
class CrisisLevel:
    id: str
    level: int
    label: str
    label_zh: str
    range_min: float
    range_max: float
    market_reference: str
    economy_reference: str
    description: str


@dataclass(frozen=True)
class CrisisArchetype:
    id: str
    name: str
    name_zh: str
    damage_level_id: str
    pressure_phase: str
    peak_period: str
    description: str
    factors: dict[str, float]


FACTOR_WEIGHTS: dict[str, float] = {
    "capital_markets": 0.20,
    "credit_banking": 0.18,
    "fx_dollar": 0.15,
    "economic_health": 0.15,
    "trade_spillover": 0.12,
    "commodities": 0.08,
    "policy_buffer": 0.05,
    "signal_coherence": 0.07,
}


FACTOR_LABELS: dict[str, dict[str, str]] = {
    "capital_markets": {"en": "Capital Markets", "zh": "资本市场"},
    "credit_banking": {"en": "Credit & Banking", "zh": "信用与银行"},
    "fx_dollar": {"en": "FX / Dollar Pressure", "zh": "汇率与美元压力"},
    "economic_health": {"en": "Economic Health", "zh": "经济健康"},
    "trade_spillover": {"en": "Trade Spillover", "zh": "贸易传导"},
    "commodities": {"en": "Commodities & Energy", "zh": "商品与能源"},
    "policy_buffer": {"en": "Policy Buffer", "zh": "政策缓冲"},
    "signal_coherence": {"en": "Signal Coherence", "zh": "信号一致性"},
}


DAMAGE_COMPONENT_WEIGHTS: dict[str, float] = {
    "market_damage": 0.20,
    "economic_activity_damage": 0.20,
    "labor_consumer_damage": 0.15,
    "credit_banking_damage": 0.20,
    "external_fx_damage": 0.15,
    "trade_damage": 0.10,
}


DAMAGE_COMPONENT_LABELS: dict[str, dict[str, str]] = {
    "market_damage": {"en": "Market Damage", "zh": "市场损害"},
    "economic_activity_damage": {"en": "Economic Activity Damage", "zh": "经济活动损害"},
    "labor_consumer_damage": {"en": "Labor / Consumer Damage", "zh": "就业与消费损害"},
    "credit_banking_damage": {"en": "Credit / Banking Damage", "zh": "信用与银行损害"},
    "external_fx_damage": {"en": "External / FX Damage", "zh": "外部与汇率损害"},
    "trade_damage": {"en": "Trade Damage", "zh": "贸易损害"},
}


DAMAGE_LEVELS: tuple[CrisisLevel, ...] = (
    CrisisLevel(
        "no_material_damage",
        0,
        "No Material Damage",
        "无显著损害",
        0,
        15,
        "No broad drawdown or funding damage is visible.",
        "No broad evidence of GDP, labor-market, consumption, or credit damage.",
        "Pressure may exist, but realized damage is still limited.",
    ),
    CrisisLevel(
        "market_correction",
        1,
        "Market Correction",
        "市场调整",
        15,
        30,
        "Typical equity drawdown around 10%-15%; volatility rises but forced liquidation is limited.",
        "Economic activity is not yet materially damaged.",
        "Damage is mostly mark-to-market rather than macroeconomic.",
    ),
    CrisisLevel(
        "regional_market_damage",
        2,
        "Regional / Market Damage",
        "区域或市场损害",
        30,
        50,
        "Affected markets may draw down 20%-30%; FX, rates, or credit stress becomes visible regionally.",
        "Damage is material for some economies or sectors, but not yet a broad global recession.",
        "Transmission has caused damage, but system-wide macro damage is not yet dominant.",
    ),
    CrisisLevel(
        "macro_recession_damage",
        3,
        "Macro Recession Damage",
        "宏观衰退损害",
        50,
        70,
        "Broad drawdowns and sustained credit stress are visible.",
        "GDP, jobs, consumption, corporate earnings, or industrial activity show real deterioration.",
        "The crisis has moved from market pricing into the real economy.",
    ),
    CrisisLevel(
        "systemic_financial_damage",
        4,
        "Systemic Financial Damage",
        "系统性金融损害",
        70,
        90,
        "Multi-asset liquidation, bank/funding stress, and emergency policy support are visible.",
        "Credit creation, employment, output, and confidence can be impaired together.",
        "The financial system itself becomes a source of macroeconomic damage.",
    ),
    CrisisLevel(
        "depression_structural_damage",
        5,
        "Depression / Structural Damage",
        "萧条或结构性损害",
        90,
        100,
        "Market losses are deep and persistent across multiple asset classes.",
        "GDP, employment, credit creation, banks, or sovereign balance sheets suffer long-duration damage.",
        "Damage is structural rather than cyclical.",
    ),
)


FORWARD_PRESSURE_LEVELS: tuple[CrisisLevel, ...] = (
    CrisisLevel("normal_pressure", 0, "Normal Pressure", "正常压力", 0, 25, "Risk pressure is normal.", "No near-term damage signal.", "Routine monitoring."),
    CrisisLevel("elevated_pressure", 1, "Elevated Pressure", "压力升高", 25, 40, "Market pressure is rising.", "Damage is not yet broad.", "Watch for confirmation."),
    CrisisLevel("high_transmission_pressure", 2, "High / Transmission Pressure", "高压或传导压力", 40, 55, "Multiple channels are warming.", "Damage can emerge if pressure persists.", "This is pre-damage or early transmission risk."),
    CrisisLevel("severe_pre_crisis_pressure", 3, "Severe Pre-Crisis Pressure", "严重危机前压力", 55, 75, "Stress resembles prior pre-crisis windows.", "Real economy damage risk is material.", "Pressure is high enough to require defensive attention."),
    CrisisLevel("crisis_level_pressure", 4, "Crisis-Level Pressure", "危机级压力", 75, 100, "Pressure is comparable to major crisis windows.", "Damage is likely already visible or imminent.", "This is crisis-grade pressure, not necessarily final damage classification."),
)


HISTORICAL_ARCHETYPES: tuple[CrisisArchetype, ...] = (
    CrisisArchetype(
        "asia_1997",
        "1997 Asian Financial Crisis",
        "1997 亚洲金融危机",
        "regional_market_damage",
        "damage_realization",
        "1997-10 to 1998-01",
        "FX pressure, external funding stress, regional equity contagion, and trade exposure.",
        {
            "capital_markets": 65,
            "credit_banking": 52,
            "fx_dollar": 88,
            "economic_health": 58,
            "trade_spillover": 72,
            "commodities": 35,
            "policy_buffer": 62,
            "signal_coherence": 76,
        },
    ),
    CrisisArchetype(
        "gfc_2008",
        "2008 Global Financial Crisis",
        "2008 全球金融危机",
        "systemic_financial_damage",
        "damage_realization",
        "2008-09 to 2009-03",
        "Credit, banking, housing, liquidity, and equity stress became mutually reinforcing.",
        {
            "capital_markets": 92,
            "credit_banking": 96,
            "fx_dollar": 72,
            "economic_health": 84,
            "trade_spillover": 58,
            "commodities": 55,
            "policy_buffer": 82,
            "signal_coherence": 94,
        },
    ),
    CrisisArchetype(
        "euro_2011",
        "2011 Eurozone Sovereign Crisis",
        "2011 欧债危机",
        "regional_market_damage",
        "damage_realization",
        "2011-08 to 2011-11",
        "Sovereign-credit, euro, banking, and regional equity stress fed into global risk appetite.",
        {
            "capital_markets": 68,
            "credit_banking": 78,
            "fx_dollar": 64,
            "economic_health": 52,
            "trade_spillover": 48,
            "commodities": 32,
            "policy_buffer": 70,
            "signal_coherence": 74,
        },
    ),
    CrisisArchetype(
        "china_2015",
        "2015 China Shock",
        "2015 中国冲击",
        "regional_market_damage",
        "damage_realization",
        "2015-08 to 2016-01",
        "China equity, RMB, commodity, and regional trade exposure drove global repricing.",
        {
            "capital_markets": 72,
            "credit_banking": 45,
            "fx_dollar": 74,
            "economic_health": 55,
            "trade_spillover": 82,
            "commodities": 68,
            "policy_buffer": 54,
            "signal_coherence": 70,
        },
    ),
    CrisisArchetype(
        "covid_2020",
        "2020 COVID Liquidity Shock",
        "2020 新冠流动性冲击",
        "macro_recession_damage",
        "rapid_damage_realization",
        "2020-02 to 2020-03",
        "Global equity liquidation, volatility shock, supply-chain disruption, and emergency policy response.",
        {
            "capital_markets": 95,
            "credit_banking": 74,
            "fx_dollar": 70,
            "economic_health": 88,
            "trade_spillover": 86,
            "commodities": 78,
            "policy_buffer": 90,
            "signal_coherence": 96,
        },
    ),
    CrisisArchetype(
        "rate_2022",
        "2022 Rate-Hike Shock",
        "2022 加息冲击",
        "market_correction",
        "pre_damage_pressure",
        "2022-06 to 2022-10",
        "Rates, dollar strength, equity valuation compression, and global liquidity stress dominated.",
        {
            "capital_markets": 76,
            "credit_banking": 54,
            "fx_dollar": 90,
            "economic_health": 46,
            "trade_spillover": 58,
            "commodities": 60,
            "policy_buffer": 45,
            "signal_coherence": 78,
        },
    ),
)


class CrisisRegimeAssessmentEngine:
    def assess(
        self,
        risk_index: dict[str, Any],
        ehs_scores: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        gfcri = float(risk_index.get("gfcri_value") or risk_index.get("gfcri") or 0)
        factors = self._factor_scores(risk_index, ehs_scores or [])
        contributions = self._factor_contributions(factors)
        damage_components = self._damage_components(factors, ehs_scores or [], risk_index)
        damage_score = self._realized_damage_score(damage_components)
        damage_level = self._level_for_score(damage_score, DAMAGE_LEVELS)
        pressure_level = self._level_for_score(gfcri, FORWARD_PRESSURE_LEVELS)
        hidden = self._hidden_risk_assessment(risk_index)
        matches = self._historical_matches(factors)

        return {
            "score": round(gfcri, 2),
            "realized_damage": {
                "score": round(damage_score, 2),
                "level": self._level_to_dict(damage_level),
                "level_progress": self._level_progress(damage_score, damage_level),
                "evidence": self._damage_evidence(damage_components),
                "components": damage_components,
            },
            "forward_pressure": {
                "score": round(gfcri, 2),
                "level": self._level_to_dict(pressure_level),
                "level_progress": self._level_progress(gfcri, pressure_level),
            },
            "hidden_risk": hidden,
            # Backward-compatible aliases for existing consumers.
            "level": self._level_to_dict(damage_level),
            "level_progress": self._level_progress(damage_score, damage_level),
            "interpretation": self._interpretation(damage_level, pressure_level, hidden, matches),
            "factors": contributions,
            "matches": matches,
            "levels": [self._level_to_dict(l) for l in DAMAGE_LEVELS],
            "damage_levels": [self._level_to_dict(l) for l in DAMAGE_LEVELS],
            "pressure_levels": [self._level_to_dict(l) for l in FORWARD_PRESSURE_LEVELS],
            "methodology": {
                "factor_weights": FACTOR_WEIGHTS,
                "damage_component_weights": DAMAGE_COMPONENT_WEIGHTS,
                "damage_level_basis": "realized damage evidence, not GFCRI score",
                "forward_pressure_basis": "GFCRI score and risk transmission pressure",
                "matching": "weighted Euclidean distance converted into 0-100 similarity",
                "note": "Damage level describes realized damage; forward pressure describes risk that may or may not become damage.",
            },
        }

    def _factor_scores(self, risk_index: dict[str, Any], ehs_scores: list[dict[str, Any]]) -> dict[str, float]:
        sub = risk_index.get("sub_index_details") or {}
        trade = risk_index.get("trade_spillover") or (sub.get("SI_TRADE_SPILLOVER") or {}).get("trade_spillover") or {}
        coherence = float(risk_index.get("coherence_multiplier") or 1.0)
        node_contrib = risk_index.get("node_contributions") or {}

        capital = self._avg_sub(sub, ["SI_US_EQUITY", "SI_ASIA_EQUITY", "SI_EUROPE", "SI_SENTIMENT"])
        credit = self._avg_sub(sub, ["SI_CREDIT", "SI_BANKING"])
        fx = self._sub_score(sub, "SI_FX")
        commodities = self._sub_score(sub, "SI_COMMODITY")
        trade_score = float(trade.get("score") or (sub.get("SI_TRADE_SPILLOVER") or {}).get("score") or 0)
        econ = self._economic_health_stress(ehs_scores, node_contrib)

        return {
            "capital_markets": capital,
            "credit_banking": credit,
            "fx_dollar": fx,
            "economic_health": econ,
            "trade_spillover": trade_score,
            "commodities": commodities,
            "policy_buffer": self._policy_stress(risk_index, sub),
            "signal_coherence": max(0.0, min(100.0, (coherence - 1.0) / 0.35 * 100.0)),
        }

    def _factor_contributions(self, factors: dict[str, float]) -> list[dict[str, Any]]:
        weighted = {
            factor: max(0.0, min(100.0, value)) * FACTOR_WEIGHTS[factor]
            for factor, value in factors.items()
        }
        total = sum(weighted.values()) or 1.0
        rows = []
        for factor, points in sorted(weighted.items(), key=lambda x: x[1], reverse=True):
            labels = FACTOR_LABELS[factor]
            rows.append({
                "id": factor,
                "name": labels["en"],
                "name_zh": labels["zh"],
                "score": round(factors[factor], 2),
                "weight": FACTOR_WEIGHTS[factor],
                "points": round(points, 2),
                "share": round(points / total * 100, 2),
            })
        return rows

    def _historical_matches(self, factors: dict[str, float]) -> list[dict[str, Any]]:
        matches = []
        for archetype in HISTORICAL_ARCHETYPES:
            distance = 0.0
            max_distance = 0.0
            for factor, weight in FACTOR_WEIGHTS.items():
                distance += weight * (factors[factor] - archetype.factors[factor]) ** 2
                max_distance += weight * 100 ** 2
            similarity = max(0.0, 100.0 * (1.0 - sqrt(distance) / sqrt(max_distance)))
            matches.append({
                "id": archetype.id,
                "name": archetype.name,
                "name_zh": archetype.name_zh,
                "damage_level_id": archetype.damage_level_id,
                "level_id": archetype.damage_level_id,
                "pressure_phase": archetype.pressure_phase,
                "peak_period": archetype.peak_period,
                "description": archetype.description,
                "similarity": round(similarity, 2),
                "factor_profile": archetype.factors,
            })
        return sorted(matches, key=lambda x: x["similarity"], reverse=True)[:4]

    @staticmethod
    def _avg_sub(sub: dict[str, Any], ids: list[str]) -> float:
        vals = [float((sub.get(i) or {}).get("score") or 0) for i in ids if i in sub]
        return sum(vals) / len(vals) if vals else 0.0

    @staticmethod
    def _sub_score(sub: dict[str, Any], key: str) -> float:
        return float((sub.get(key) or {}).get("score") or 0)

    @staticmethod
    def _economic_health_stress(ehs_scores: list[dict[str, Any]], node_contrib: dict[str, Any]) -> float:
        if ehs_scores:
            vals = [float(r.get("ehs_score") or 50) for r in ehs_scores if r.get("ehs_score") is not None]
            if vals:
                return max(0.0, min(100.0, 100.0 - (sum(vals) / len(vals))))

        consumer = node_contrib.get("consumer_stress") or {}
        recession = node_contrib.get("us_recession_prob") or {}
        consumer_stress = max(float(consumer.get("anomaly_score") or 0), float(consumer.get("abs_score") or 0)) * 100
        recession_stress = max(float(recession.get("anomaly_score") or 0), float(recession.get("abs_score") or 0)) * 100
        return max(consumer_stress, recession_stress)

    @staticmethod
    def _policy_stress(risk_index: dict[str, Any], sub: dict[str, Any]) -> float:
        # Policy-buffer stress is intentionally conservative until explicit
        # policy-space data is wired in. Rates/credit stress proxy constrained
        # policy room and funding pressure.
        rates = float((sub.get("SI_RATES") or {}).get("score") or 0)
        credit = float((sub.get("SI_CREDIT") or {}).get("score") or 0)
        hidden = float(risk_index.get("undercurrent_boost") or 0) * 4
        return max(0.0, min(100.0, 0.45 * rates + 0.35 * credit + 0.20 * hidden))

    def _damage_components(
        self,
        factors: dict[str, float],
        ehs_scores: list[dict[str, Any]],
        risk_index: dict[str, Any],
    ) -> dict[str, float]:
        ehs_damage = self._ehs_damage_components(ehs_scores)
        node_contrib = risk_index.get("node_contributions") or {}
        consumer = node_contrib.get("consumer_stress") or {}
        recession = node_contrib.get("us_recession_prob") or {}
        consumer_damage = max(
            float(consumer.get("anomaly_score") or 0),
            float(consumer.get("abs_score") or 0),
            float(recession.get("anomaly_score") or 0),
            float(recession.get("abs_score") or 0),
        ) * 100

        return {
            "market_damage": max(0.0, min(100.0, (factors["capital_markets"] - 30.0) * 1.15)),
            "economic_activity_damage": max(
                ehs_damage.get("growth", 0.0),
                max(0.0, (factors["economic_health"] - 45.0) * 0.85),
            ),
            "labor_consumer_damage": max(
                ehs_damage.get("labor", 0.0),
                consumer_damage,
            ),
            "credit_banking_damage": max(
                ehs_damage.get("financial", 0.0),
                max(0.0, (factors["credit_banking"] - 30.0) * 1.05),
            ),
            "external_fx_damage": max(
                ehs_damage.get("external", 0.0),
                max(0.0, (factors["fx_dollar"] - 45.0) * 0.90),
            ),
            "trade_damage": max(0.0, min(100.0, (factors["trade_spillover"] - 50.0) * 0.70)),
        }

    @staticmethod
    def _ehs_damage_components(ehs_scores: list[dict[str, Any]]) -> dict[str, float]:
        if not ehs_scores:
            return {}

        def avg_damage(field: str, neutral: float = 50.0) -> float:
            vals = [float(r.get(field) or neutral) for r in ehs_scores if r.get(field) is not None]
            if not vals:
                return 0.0
            avg_score = sum(vals) / len(vals)
            # EHS dimensions are health scores. Damage only starts once a
            # dimension is below neutral; the multiplier maps weak health into
            # a 0-100 damage-evidence scale.
            return max(0.0, min(100.0, (neutral - avg_score) * 2.0))

        return {
            "growth": avg_damage("growth_score"),
            "labor": avg_damage("labor_score"),
            "external": avg_damage("external_score"),
            "financial": avg_damage("financial_score"),
        }

    @staticmethod
    def _realized_damage_score(components: dict[str, float]) -> float:
        weighted = sum(
            max(0.0, min(100.0, components.get(k, 0.0))) * w
            for k, w in DAMAGE_COMPONENT_WEIGHTS.items()
        )
        return max(0.0, min(100.0, weighted))

    @staticmethod
    def _damage_evidence(components: dict[str, float]) -> list[dict[str, Any]]:
        rows = []
        total = sum(
            max(0.0, min(100.0, components.get(k, 0.0))) * w
            for k, w in DAMAGE_COMPONENT_WEIGHTS.items()
        ) or 1.0
        for component, score in sorted(components.items(), key=lambda x: x[1], reverse=True):
            labels = DAMAGE_COMPONENT_LABELS[component]
            points = max(0.0, min(100.0, score)) * DAMAGE_COMPONENT_WEIGHTS[component]
            rows.append({
                "id": component,
                "name": labels["en"],
                "name_zh": labels["zh"],
                "score": round(score, 2),
                "weight": DAMAGE_COMPONENT_WEIGHTS[component],
                "points": round(points, 2),
                "share": round(points / total * 100, 2),
            })
        return rows

    @staticmethod
    def _hidden_risk_assessment(risk_index: dict[str, Any]) -> dict[str, Any]:
        divergence = risk_index.get("divergence") or {}
        status = str(divergence.get("status") or "none")
        undercurrent = float(risk_index.get("undercurrent_boost") or 0.0)
        trade_boost = float(risk_index.get("trade_spillover_boost") or 0.0)
        status_score = {"none": 0.0, "mild": 25.0, "significant": 55.0, "critical": 80.0}.get(status, 0.0)
        score = max(status_score, min(100.0, undercurrent * 4.0 + trade_boost * 6.0))
        if score >= 75:
            label, label_zh = "Critical Hidden Risk", "严重隐藏风险"
        elif score >= 50:
            label, label_zh = "Significant Hidden Risk", "显著隐藏风险"
        elif score >= 25:
            label, label_zh = "Mild Hidden Risk", "轻度隐藏风险"
        else:
            label, label_zh = "Low Hidden Risk", "低隐藏风险"
        return {
            "score": round(score, 2),
            "label": label,
            "label_zh": label_zh,
            "divergence_status": status,
            "undercurrent_boost": round(undercurrent, 2),
            "trade_spillover_boost": round(trade_boost, 2),
        }

    @staticmethod
    def _level_for_score(score: float, levels: tuple[CrisisLevel, ...]) -> CrisisLevel:
        for level in levels:
            if level.range_min <= score < level.range_max:
                return level
        return levels[-1]

    @staticmethod
    def _level_progress(score: float, level: CrisisLevel) -> float:
        span = max(level.range_max - level.range_min, 1.0)
        return round(max(0.0, min(1.0, (score - level.range_min) / span)) * 100, 2)

    @staticmethod
    def _level_to_dict(level: CrisisLevel) -> dict[str, Any]:
        return {
            "id": level.id,
            "level": level.level,
            "label": level.label,
            "label_zh": level.label_zh,
            "range_min": level.range_min,
            "range_max": level.range_max,
            "market_reference": level.market_reference,
            "economy_reference": level.economy_reference,
            "description": level.description,
        }

    @staticmethod
    def _interpretation(
        damage_level: CrisisLevel,
        pressure_level: CrisisLevel,
        hidden: dict[str, Any],
        matches: list[dict[str, Any]],
    ) -> str:
        if not matches:
            return damage_level.description
        top = matches[0]
        return (
            f"Realized damage is currently {damage_level.label}, while forward pressure is "
            f"{pressure_level.label}. Hidden risk is {hidden['label']}. The closest historical "
            f"pressure profile is {top['name']} with {top['similarity']:.0f}% similarity."
        )
