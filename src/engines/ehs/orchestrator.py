"""
Economy Health Score (EHS) - Main orchestrator.

Runs the full pipeline: collect → score → persist for all economies.
Reads from DB cache when available, falls back to live fetch.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger

from src.engines.ehs.config import ECONOMIES
from src.engines.ehs.collector import EHSDataCollector
from src.engines.ehs.scoring import EHSScoringEngine, EconomyScore


class EHSOrchestrator:
    def __init__(self, fred_api_key: str = ""):
        self.collector = EHSDataCollector(fred_api_key=fred_api_key)
        self.engine = EHSScoringEngine()

    def run_single(self, economy_code: str) -> Optional[EconomyScore]:
        data = self.collector.fetch_all_for_economy(economy_code)
        if not data:
            logger.warning(f"EHS: no data for {economy_code}")
            return None

        score = self.engine.compute_score(economy_code, data)
        if score:
            self._persist_score(score)
            self._persist_indicators(economy_code, data, score)
        return score

    def run_all(self) -> list[EconomyScore]:
        results = []
        for code in ECONOMIES:
            score = self.run_single(code)
            if score:
                results.append(score)
                logger.info(
                    f"EHS {code}: {score.ehs_score:.1f} ({score.cycle_phase})"
                )
        results.sort(key=lambda s: s.ehs_score, reverse=True)
        return results

    def _persist_score(self, score: EconomyScore):
        try:
            from src.engines.ehs.storage import save_ehs_score, get_ehs_score_history

            history = get_ehs_score_history(score.economy_code, limit=2)
            change_1m = None
            if history:
                prev = history[0]
                change_1m = score.ehs_score - float(prev["ehs_score"])

            save_ehs_score(
                economy_code=score.economy_code,
                score_date=score.score_date,
                ehs_score=score.ehs_score,
                growth_score=score.growth_score,
                labor_score=score.labor_score,
                price_score=score.price_score,
                external_score=score.external_score,
                financial_score=score.financial_score,
                cycle_phase=score.cycle_phase,
                score_change_1m=change_1m,
                indicator_details=score.indicator_details,
            )
            score.score_change_1m = change_1m
        except Exception as e:
            logger.warning(f"EHS persist score failed (non-fatal): {e}")

    def _persist_indicators(self, economy_code: str, data: dict[str, pd.Series], score: EconomyScore):
        try:
            from src.engines.ehs.storage import save_indicator_data_batch

            economy = ECONOMIES[economy_code]
            rows = []
            for ind in economy.indicators:
                series = data.get(ind.code)
                if series is None or series.empty:
                    continue

                details = score.indicator_details.get(ind.code, {}) if score.indicator_details else {}
                z = details.get("score", 50.0)
                z_score = (z - 50) / 10.0

                last_date = series.index[-1]
                ref_date = last_date.strftime("%Y-%m-%d") if hasattr(last_date, "strftime") else str(last_date)[:10]
                raw_val = float(series.iloc[-1]) if not np.isnan(series.iloc[-1]) else None

                rows.append((
                    economy_code,
                    ind.code,
                    ref_date,
                    raw_val,
                    raw_val,
                    round(z_score, 4),
                    ind.source,
                ))

            if rows:
                save_indicator_data_batch(rows)
        except Exception as e:
            logger.warning(f"EHS persist indicators failed (non-fatal): {e}")
