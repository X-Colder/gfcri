"""
Economy Health Score (EHS) - Scoring engine.

Computes Z-Score based health scores for each economy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger

from src.engines.ehs.config import ECONOMIES, DIMENSION_WEIGHTS, Economy, Indicator


@dataclass
class EconomyScore:
    economy_code: str
    economy_name: str
    score_date: str
    ehs_score: float
    growth_score: float
    labor_score: float
    price_score: float
    external_score: float
    financial_score: float
    cycle_phase: str
    score_change_1m: Optional[float] = None
    score_change_3m: Optional[float] = None
    indicator_details: dict = None

    def to_dict(self) -> dict:
        return {
            "economy_code": self.economy_code,
            "economy_name": self.economy_name,
            "score_date": self.score_date,
            "ehs_score": self.ehs_score,
            "growth_score": self.growth_score,
            "labor_score": self.labor_score,
            "price_score": self.price_score,
            "external_score": self.external_score,
            "financial_score": self.financial_score,
            "cycle_phase": self.cycle_phase,
            "score_change_1m": self.score_change_1m,
            "score_change_3m": self.score_change_3m,
            "indicator_details": self.indicator_details,
        }


class EHSScoringEngine:
    def __init__(self, lookback_months: int = 36):
        self.lookback = lookback_months

    def compute_score(
        self,
        economy_code: str,
        indicator_data: dict[str, pd.Series],
    ) -> Optional[EconomyScore]:
        economy = ECONOMIES.get(economy_code)
        if not economy:
            return None

        dimension_scores: dict[str, list[float]] = {
            "growth": [], "labor": [], "price": [], "external": [], "financial": [],
        }
        indicator_details = {}

        for ind in economy.indicators:
            series = indicator_data.get(ind.code)
            if series is None or series.empty or len(series) < 6:
                continue

            latest = series.iloc[-1]
            if np.isnan(latest):
                continue

            if ind.dimension == "price":
                score = self._price_score(latest, economy.target_inflation)
            else:
                score = self._zscore_to_score(series, ind.direction)

            if score is not None:
                dimension_scores[ind.dimension].append(score * ind.weight)
                indicator_details[ind.code] = {
                    "name": ind.name_zh,
                    "value": float(latest),
                    "score": float(score),
                    "dimension": ind.dimension,
                }

        dim_final = {}
        for dim, weights_list in dimension_scores.items():
            if weights_list:
                total_w = sum(
                    ind.weight for ind in economy.indicators
                    if ind.dimension == dim and ind.code in indicator_data
                )
                dim_final[dim] = sum(weights_list) / total_w if total_w > 0 else 50.0
            else:
                dim_final[dim] = 50.0

        ehs = sum(
            DIMENSION_WEIGHTS.get(dim, 0) * dim_final.get(dim, 50)
            for dim in DIMENSION_WEIGHTS
        )

        cycle = self._determine_cycle(
            ehs, dim_final.get("growth", 50), dim_final.get("price", 50)
        )

        today = pd.Timestamp.now().strftime("%Y-%m-%d")

        return EconomyScore(
            economy_code=economy_code,
            economy_name=economy.name_zh,
            score_date=today,
            ehs_score=round(ehs, 1),
            growth_score=round(dim_final.get("growth", 50), 1),
            labor_score=round(dim_final.get("labor", 50), 1),
            price_score=round(dim_final.get("price", 50), 1),
            external_score=round(dim_final.get("external", 50), 1),
            financial_score=round(dim_final.get("financial", 50), 1),
            cycle_phase=cycle,
            indicator_details=indicator_details,
        )

    def _zscore_to_score(self, series: pd.Series, direction: int) -> Optional[float]:
        if len(series) < 6:
            return None
        latest = series.iloc[-1]
        lookback = series.iloc[-self.lookback:] if len(series) >= self.lookback else series
        mean = lookback.mean()
        std = lookback.std()
        if std == 0 or np.isnan(std):
            return 50.0

        z = (latest - mean) / std
        z = z * direction
        score = 50 + 10 * np.clip(z, -5, 5)
        return float(np.clip(score, 0, 100))

    def _price_score(self, cpi_value: float, target: float) -> float:
        deviation = abs(cpi_value - target)
        score = 100 - 15 * deviation
        return float(np.clip(score, 0, 100))

    def _determine_cycle(
        self, ehs: float, growth_score: float, price_score: float
    ) -> str:
        if ehs >= 60:
            if price_score < 40:
                return "overheating"
            return "expansion"
        elif ehs >= 40:
            if growth_score < 45:
                return "slowdown"
            return "expansion"
        else:
            return "recession"


CYCLE_LABELS = {
    "expansion": "扩张",
    "overheating": "过热",
    "slowdown": "放缓",
    "recession": "衰退",
}
