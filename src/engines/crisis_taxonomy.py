"""Crisis taxonomy and regime assessment.

This layer gives GFCRI an explicit reference frame: crisis levels, historical
archetypes, factor contribution, and current-regime matching.
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
    level_id: str
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


CRISIS_LEVELS: tuple[CrisisLevel, ...] = (
    CrisisLevel(
        "normal",
        0,
        "Normal Monitoring",
        "正常监测",
        0,
        25,
        "Broad risk assets remain within normal drawdown ranges.",
        "No broad evidence of economic damage.",
        "Routine macro-financial monitoring.",
    ),
    CrisisLevel(
        "market_stress",
        1,
        "Market Stress",
        "市场压力",
        25,
        40,
        "Equity drawdown around 10%-15%, volatility rising, credit spreads mildly wider.",
        "Economic damage is usually limited, but funding and confidence start to tighten.",
        "A tradable stress episode rather than a full macro crisis.",
    ),
    CrisisLevel(
        "regional_crisis",
        2,
        "Regional / Transmission Crisis",
        "区域或传导危机",
        40,
        55,
        "Regional equity/FX/credit stress, often 20%-30% equity drawdowns in affected markets.",
        "Trade, capital-flow, and currency pressure can spill into partner economies.",
        "Stress is no longer isolated; transmission channels matter.",
    ),
    CrisisLevel(
        "macro_recession",
        3,
        "Macro Recession Crisis",
        "宏观衰退危机",
        55,
        75,
        "Broad risk-asset drawdowns, sustained credit stress, and recession pricing.",
        "GDP, jobs, consumption, or corporate earnings show material damage.",
        "Market stress is becoming real-economy damage.",
    ),
    CrisisLevel(
        "systemic_financial",
        4,
        "Systemic Financial Crisis",
        "系统性金融危机",
        75,
        100,
        "Multi-asset liquidation, bank/funding stress, and policy rescue conditions.",
        "Credit creation, employment, output, and confidence can be impaired together.",
        "The financial system itself becomes a source of macro damage.",
    ),
)


HISTORICAL_ARCHETYPES: tuple[CrisisArchetype, ...] = (
    CrisisArchetype(
        "asia_1997",
        "1997 Asian Financial Crisis",
        "1997 亚洲金融危机",
        "regional_crisis",
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
        "systemic_financial",
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
        "regional_crisis",
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
        "regional_crisis",
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
        "systemic_financial",
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
        "macro_recession",
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
        level = self._level_for_score(gfcri)
        matches = self._historical_matches(factors)

        return {
            "score": round(gfcri, 2),
            "level": self._level_to_dict(level),
            "level_progress": self._level_progress(gfcri, level),
            "interpretation": self._interpretation(level, matches),
            "factors": contributions,
            "matches": matches,
            "levels": [self._level_to_dict(l) for l in CRISIS_LEVELS],
            "methodology": {
                "factor_weights": FACTOR_WEIGHTS,
                "matching": "weighted Euclidean distance converted into 0-100 similarity",
                "note": "Crisis level is a reference frame, not a prediction of exact crisis timing.",
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
                "level_id": archetype.level_id,
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

    @staticmethod
    def _level_for_score(score: float) -> CrisisLevel:
        for level in CRISIS_LEVELS:
            if level.range_min <= score < level.range_max:
                return level
        return CRISIS_LEVELS[-1]

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
    def _interpretation(level: CrisisLevel, matches: list[dict[str, Any]]) -> str:
        if not matches:
            return level.description
        top = matches[0]
        return (
            f"Current conditions sit in {level.label}. The closest historical "
            f"reference is {top['name']} with {top['similarity']:.0f}% profile similarity."
        )
