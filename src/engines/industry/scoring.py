"""
Industry Research Module - Scoring Engine (Layer 1).

Tracks industry health/momentum using ETF and commodity prices.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
from loguru import logger

from src.engines.industry import INDUSTRIES, Industry, IndustryTicker


@dataclass
class IndustryScore:
    code: str
    name_zh: str
    name_en: str
    category: str
    score: float  # 0-100 momentum score
    trend: str  # up/down/flat
    change_1m: float  # % change last month
    change_3m: float  # % change last 3 months
    volatility: float  # annualized vol
    key_economies: list[str]
    ticker_details: list[dict]

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name_zh": self.name_zh,
            "name_en": self.name_en,
            "category": self.category,
            "score": self.score,
            "trend": self.trend,
            "change_1m": self.change_1m,
            "change_3m": self.change_3m,
            "volatility": self.volatility,
            "key_economies": self.key_economies,
            "ticker_details": self.ticker_details,
        }


class IndustryScoringEngine:

    def score_all(self) -> list[IndustryScore]:
        all_tickers = set()
        for ind in INDUSTRIES.values():
            for t in ind.tickers:
                all_tickers.add(t.ticker)

        ticker_list = sorted(all_tickers)
        logger.info(f"Industry: batch downloading {len(ticker_list)} tickers...")

        try:
            raw = yf.download(ticker_list, period="6mo", progress=False, auto_adjust=True)
        except Exception as e:
            logger.error(f"Industry batch download failed: {e}")
            return []

        prices: dict[str, pd.Series] = {}
        if raw.empty:
            logger.warning("Industry: yfinance returned empty DataFrame")
            return []

        for ticker in ticker_list:
            try:
                if len(ticker_list) == 1:
                    close = raw["Close"]
                else:
                    if isinstance(raw.columns, pd.MultiIndex):
                        if ("Close", ticker) in raw.columns:
                            close = raw[("Close", ticker)]
                        elif ticker in raw.columns.get_level_values(0):
                            close = raw[ticker]["Close"]
                        else:
                            continue
                    else:
                        continue
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
                close = close.dropna()
                if len(close) >= 20:
                    prices[ticker] = close
            except Exception:
                pass

        logger.info(f"Industry: {len(prices)}/{len(ticker_list)} tickers downloaded")

        results = []
        for code, ind in INDUSTRIES.items():
            score = self._score_industry(ind, prices)
            if score:
                results.append(score)

        results.sort(key=lambda s: s.score, reverse=True)
        return results

    def _score_industry(self, ind: Industry, prices: dict[str, pd.Series]) -> Optional[IndustryScore]:
        ticker_details = []
        scores = []

        for t in ind.tickers:
            series = prices.get(t.ticker)
            if series is None or len(series) < 20:
                continue

            latest = series.iloc[-1]
            m1 = series.iloc[-22] if len(series) >= 22 else series.iloc[0]
            m3 = series.iloc[-66] if len(series) >= 66 else series.iloc[0]

            chg_1m = (latest / m1 - 1) * 100 if m1 != 0 else 0
            chg_3m = (latest / m3 - 1) * 100 if m3 != 0 else 0

            returns = series.pct_change().dropna()
            vol = returns.std() * np.sqrt(252) * 100 if len(returns) > 5 else 0

            momentum = self._momentum_score(series)
            scores.append(momentum)

            ticker_details.append({
                "ticker": t.ticker,
                "name": t.name_zh,
                "role": t.role,
                "price": round(float(latest), 2),
                "change_1m": round(chg_1m, 2),
                "change_3m": round(chg_3m, 2),
                "volatility": round(vol, 1),
                "momentum": round(momentum, 1),
            })

        if not scores:
            return None

        avg_score = np.mean(scores)
        avg_chg_1m = np.mean([d["change_1m"] for d in ticker_details])
        avg_chg_3m = np.mean([d["change_3m"] for d in ticker_details])
        avg_vol = np.mean([d["volatility"] for d in ticker_details])

        if avg_chg_1m > 2:
            trend = "up"
        elif avg_chg_1m < -2:
            trend = "down"
        else:
            trend = "flat"

        return IndustryScore(
            code=ind.code,
            name_zh=ind.name_zh,
            name_en=ind.name_en,
            category=ind.category,
            score=round(float(avg_score), 1),
            trend=trend,
            change_1m=round(float(avg_chg_1m), 2),
            change_3m=round(float(avg_chg_3m), 2),
            volatility=round(float(avg_vol), 1),
            key_economies=ind.key_economies,
            ticker_details=ticker_details,
        )

    def _momentum_score(self, series: pd.Series) -> float:
        if len(series) < 20:
            return 50.0

        sma20 = series.rolling(20).mean().iloc[-1]
        sma60 = series.rolling(60).mean().iloc[-1] if len(series) >= 60 else series.mean()
        latest = series.iloc[-1]

        above_sma20 = 1 if latest > sma20 else -1
        above_sma60 = 1 if latest > sma60 else -1
        trend_slope = (series.iloc[-1] / series.iloc[-20] - 1) * 100

        raw = 50 + above_sma20 * 10 + above_sma60 * 10 + np.clip(trend_slope * 2, -20, 20)
        return float(np.clip(raw, 0, 100))
