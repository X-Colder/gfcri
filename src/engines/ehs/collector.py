"""
Economy Health Score (EHS) - Data collector.

Fetches indicator data from FRED API and yfinance.
Optimized for batch yfinance download (single request for all tickers).
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import numpy as np
import yfinance as yf
from loguru import logger

from src.engines.ehs.config import ECONOMIES, Indicator

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


class EHSDataCollector:
    def __init__(self, fred_api_key: Optional[str] = None):
        self.fred_api_key = fred_api_key or ""
        self._yf_cache: Optional[dict] = None
        self._oecd_cache: Optional[dict] = None

    def _prefetch_all_yfinance(self):
        all_tickers = set()
        for econ in ECONOMIES.values():
            for ind in econ.indicators:
                if ind.source == "yfinance":
                    all_tickers.add(ind.series_id)

        tickers_list = sorted(all_tickers)
        logger.info(f"EHS: batch downloading {len(tickers_list)} yfinance tickers...")
        try:
            data = yf.download(
                tickers_list, period="3y", progress=False, auto_adjust=True, group_by="ticker"
            )
            if data.empty:
                logger.warning("EHS: yfinance batch download returned empty")
                self._yf_cache = pd.DataFrame()
                return

            result = {}
            for ticker in tickers_list:
                try:
                    if len(tickers_list) == 1:
                        close = data["Close"]
                    else:
                        close = data[ticker]["Close"]
                    if isinstance(close, pd.DataFrame):
                        close = close.iloc[:, 0]
                    close = close.dropna()
                    if not close.empty:
                        close.index = close.index.tz_localize(None)
                        result[ticker] = close.resample("ME").last().dropna()
                except Exception:
                    pass

            self._yf_cache = result
            logger.info(f"EHS: batch download complete, {len(result)}/{len(tickers_list)} tickers OK")
        except Exception as e:
            logger.error(f"EHS: batch yfinance failed: {e}")
            self._yf_cache = {}

    def fetch_fred_series(self, series_id: str) -> pd.Series:
        if not self.fred_api_key:
            return pd.Series(dtype=float)

        import requests
        params = {
            "series_id": series_id,
            "api_key": self.fred_api_key,
            "file_type": "json",
            "observation_start": "2020-01-01",
            "sort_order": "desc",
            "limit": 120,
        }
        try:
            resp = requests.get(FRED_BASE, params=params, timeout=10)
            data = resp.json()
            obs = data.get("observations", [])
            if not obs:
                return pd.Series(dtype=float)

            records = [
                (row["date"], float(row["value"]))
                for row in obs
                if row["value"] != "."
            ]
            if not records:
                return pd.Series(dtype=float)

            df = pd.DataFrame(records, columns=["date", "value"])
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
            return df["value"]
        except Exception as e:
            logger.warning(f"FRED {series_id} fetch failed: {e}")
            return pd.Series(dtype=float)

    def fetch_indicator(self, indicator: Indicator) -> pd.Series:
        if indicator.source == "fred":
            raw = self.fetch_fred_series(indicator.series_id)
        else:
            if self._yf_cache is None:
                self._prefetch_all_yfinance()
            raw = self._yf_cache.get(indicator.series_id, pd.Series(dtype=float))

        if raw is None or (isinstance(raw, pd.Series) and raw.empty):
            return pd.Series(dtype=float)

        return self._transform(raw, indicator.transform)

    def _transform(self, series: pd.Series, method: str) -> pd.Series:
        if method == "yoy":
            return series.pct_change(12) * 100
        elif method == "mom":
            return series.pct_change(1) * 100
        elif method == "diff":
            return series.diff(1)
        elif method == "level":
            return series
        return series

    def _fetch_oecd_data(self, economy_code: str) -> dict[str, float]:
        if self._oecd_cache is None:
            try:
                from src.data.oecd_macro import fetch_oecd_rates
                self._oecd_cache = fetch_oecd_rates()
            except Exception as e:
                logger.warning(f"OECD fetch failed: {e}")
                self._oecd_cache = {}
        return self._oecd_cache.get(economy_code, {})

    def fetch_all_for_economy(self, economy_code: str) -> dict[str, pd.Series]:
        economy = ECONOMIES.get(economy_code)
        if not economy:
            return {}

        if self._yf_cache is None:
            self._prefetch_all_yfinance()

        results = {}
        for ind in economy.indicators:
            series = self.fetch_indicator(ind)
            if not series.empty:
                results[ind.code] = series

        # Supplement with OECD real data (as single-point latest values)
        oecd = self._fetch_oecd_data(economy_code)
        for key, val in oecd.items():
            if val is not None:
                ts = pd.Timestamp.now()
                results[f"_oecd_{key}"] = pd.Series([val], index=[ts])

        logger.info(
            f"EHS data collected for {economy_code}: "
            f"{len(results)}/{len(economy.indicators)} indicators"
            f" (+{len(oecd)} OECD)"
        )
        return results
