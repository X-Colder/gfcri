"""
Market data collector module.

Data sources:
  - yfinance: 38 market indicators (direct tickers, ETF proxies, computed ratios)
  - FRED API: US economic fundamentals and financial stress indicators
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import yfinance as yf
from loguru import logger

if TYPE_CHECKING:
    from src.models.graph import MacroRiskCausalGraph

# ---------------------------------------------------------------------------
# Direct yfinance tickers — real-time market data
# ---------------------------------------------------------------------------
YFINANCE_TICKER_MAP: dict[str, str] = {
    "dxy": "DX-Y.NYB",
    "ust_10y": "^TNX",
    "ust_2y": "^IRX",
    "krw_usd": "KRW=X",
    "kospi": "^KS11",
    "vix": "^VIX",
    "sox": "^SOX",
    "oil_wti": "CL=F",
    "hyg": "HYG",
    "kre": "KRE",
    "vnq": "VNQ",
    "copper": "HG=F",
    "gold": "GC=F",
    "eurusd": "EURUSD=X",
    "stoxx50": "^STOXX50E",
    "italy_etf": "EWI",
    "cny_usd": "CNY=X",
    "hsi": "^HSI",
    "jpy_usd": "JPY=X",
    "nikkei": "^N225",
    "eem": "EEM",
    "emb": "EMB",
    "btc": "BTC-USD",
    "spx": "^GSPC",
    "lqd": "LQD",
    "natgas": "NG=F",
    "wheat": "ZW=F",
    "bdry": "BDRY",
}

# ---------------------------------------------------------------------------
# Proxy tickers — real market proxies for nodes without direct data
# ---------------------------------------------------------------------------
PROXY_TICKER_MAP: dict[str, dict] = {
    "fed_funds": {
        "ticker": "^IRX",
        "description": "3-month T-bill yield as fed funds rate proxy",
        "source_label": "yfinance ^IRX (proxy)",
        "fred_id": "EFFR",
    },
    "dram_spot": {
        "ticker": "SMH",
        "description": "VanEck Semiconductor ETF as DRAM demand proxy",
        "source_label": "yfinance SMH (proxy)",
    },
    "nand_spot": {
        "ticker": "SMH",
        "description": "VanEck Semiconductor ETF as NAND demand proxy (shared with DRAM)",
        "source_label": "yfinance SMH (proxy)",
    },
    "orcl_cds": {
        "ticker": "ORCL",
        "description": "Oracle stock price inverse as CDS spread proxy (stock down = CDS up)",
        "source_label": "yfinance ORCL (proxy, inverted)",
        "invert": True,
    },
    "kr_cds_5y": {
        "ticker": "EWY",
        "description": "iShares MSCI South Korea ETF inverse as sovereign CDS proxy",
        "source_label": "yfinance EWY (proxy, inverted)",
        "invert": True,
    },
    "kr_ca": {
        "ticker": "EWY",
        "description": "Korea ETF as current account health proxy",
        "source_label": "yfinance EWY (proxy)",
    },
    "ai_capex": {
        "ticker": "CLOU",
        "description": "Global X Cloud Computing ETF as AI/cloud capex proxy",
        "source_label": "yfinance CLOU (proxy)",
    },
    "global_liqd": {
        "ticker": "TLT",
        "description": "iShares 20+ Year Treasury Bond ETF as global liquidity proxy",
        "source_label": "yfinance TLT (proxy)",
    },
    "us_recession_prob": {
        "ticker": "TLT",
        "description": "Long-bond ETF as recession probability proxy (TLT rises when recession fears rise)",
        "source_label": "yfinance TLT (proxy)",
    },
}

# Consumer stress ratio tickers
_CONSUMER_TICKERS = {"xly": "XLY", "xlp": "XLP"}

# Collect all unique proxy tickers for bulk download
_ALL_PROXY_TICKERS: set[str] = set()
for p in PROXY_TICKER_MAP.values():
    _ALL_PROXY_TICKERS.add(p["ticker"])

# Data source labels for all nodes
DATA_SOURCE_LABELS: dict[str, str] = {}
for nid, ticker in YFINANCE_TICKER_MAP.items():
    DATA_SOURCE_LABELS[nid] = f"yfinance {ticker}"
for nid, info in PROXY_TICKER_MAP.items():
    DATA_SOURCE_LABELS[nid] = info["source_label"]
DATA_SOURCE_LABELS["consumer_stress"] = "yfinance XLY/XLP (computed ratio)"

# ---------------------------------------------------------------------------
# FRED indicators — real economic data replacing yfinance proxies
# ---------------------------------------------------------------------------
FRED_INDICATORS: dict[str, dict] = {
    "fred_effr": {"series": "EFFR", "name": "联邦基金利率", "frequency": "daily"},
    "fred_dgs10": {"series": "DGS10", "name": "10年期美国国债收益率", "frequency": "daily"},
    "fred_dgs2": {"series": "DGS2", "name": "2年期美国国债收益率", "frequency": "daily"},
    "fred_t10y2y": {"series": "T10Y2Y", "name": "10Y-2Y利差", "frequency": "daily"},
    "fred_recession_prob": {"series": "RECPROUSM156N", "name": "美国衰退概率", "frequency": "monthly"},
    "fred_bbb_spread": {"series": "BAMLC0A4CBBB", "name": "BBB信用利差", "frequency": "daily"},
    "fred_hy_spread": {"series": "BAMLH0A0HYM2", "name": "高收益债利差", "frequency": "daily"},
    "fred_mortgage30": {"series": "MORTGAGE30US", "name": "30年房贷利率", "frequency": "weekly"},
    "fred_unrate": {"series": "UNRATE", "name": "失业率", "frequency": "monthly"},
    "fred_payems": {"series": "PAYEMS", "name": "非农就业人数", "frequency": "monthly"},
    "fred_cpi": {"series": "CPIAUCSL", "name": "CPI", "frequency": "monthly"},
    "fred_pce": {"series": "PCEPILFE", "name": "核心PCE", "frequency": "monthly"},
    "fred_indpro": {"series": "INDPRO", "name": "工业生产指数", "frequency": "monthly"},
    "fred_m2": {"series": "M2SL", "name": "M2货币供应", "frequency": "monthly"},
    "fred_umcsent": {"series": "UMCSENT", "name": "消费者信心", "frequency": "monthly"},
    "fred_house": {"series": "CSUSHPINSA", "name": "房价指数", "frequency": "monthly"},
    "fred_ic_spread": {"series": "BAMLC0A1CAAAEY", "name": "投资级利差", "frequency": "daily"},
    "fred_walcl": {"series": "WALCL", "name": "美联储资产负债表", "frequency": "weekly"},
}

for nid, info in FRED_INDICATORS.items():
    DATA_SOURCE_LABELS[nid] = f"FRED {info['series']}"

FRED_NODE_OVERLAYS: dict[str, str] = {
    "fed_funds": "fred_effr",
    "ust_10y": "fred_dgs10",
    "ust_2y": "fred_dgs2",
    "us_recession_prob": "fred_recession_prob",
}


class MarketDataCollector:
    """Collects market data from yfinance + FRED API."""

    def __init__(self) -> None:
        self.fred_api_key = os.getenv("FRED_API_KEY", "")

    def _fetch_fred_latest(self) -> dict[str, float]:
        if not self.fred_api_key:
            return {}
        import requests
        result = {}
        for key, info in FRED_INDICATORS.items():
            try:
                resp = requests.get(
                    "https://api.stlouisfed.org/fred/series/observations",
                    params={
                        "series_id": info["series"],
                        "api_key": self.fred_api_key,
                        "file_type": "json",
                        "sort_order": "desc",
                        "limit": 1,
                    },
                    timeout=10,
                )
                obs = resp.json().get("observations", [])
                if obs and obs[0]["value"] != ".":
                    result[key] = float(obs[0]["value"])
            except Exception as e:
                logger.debug(f"FRED {info['series']} failed: {e}")
        logger.info(f"FRED: fetched {len(result)}/{len(FRED_INDICATORS)} indicators")
        return result

    def _fetch_fred_history(self, period_years: int = 3) -> dict[str, pd.Series]:
        if not self.fred_api_key:
            return {}
        import requests
        from datetime import timedelta
        start = (datetime.utcnow() - timedelta(days=period_years * 365)).strftime("%Y-%m-%d")
        result = {}
        for key, info in FRED_INDICATORS.items():
            try:
                resp = requests.get(
                    "https://api.stlouisfed.org/fred/series/observations",
                    params={
                        "series_id": info["series"],
                        "api_key": self.fred_api_key,
                        "file_type": "json",
                        "observation_start": start,
                    },
                    timeout=15,
                )
                obs = resp.json().get("observations", [])
                records = [(r["date"], float(r["value"])) for r in obs if r["value"] != "."]
                if records:
                    df = pd.DataFrame(records, columns=["date", "value"])
                    df["date"] = pd.to_datetime(df["date"])
                    result[key] = df.set_index("date")["value"].sort_index()
            except Exception as e:
                logger.debug(f"FRED history {info['series']} failed: {e}")
        logger.info(f"FRED history: fetched {len(result)}/{len(FRED_INDICATORS)} series")
        return result

    def fetch_current_data(self) -> dict[str, float]:
        result: dict[str, float] = {}

        all_tickers = set(YFINANCE_TICKER_MAP.values()) | _ALL_PROXY_TICKERS | set(_CONSUMER_TICKERS.values())
        tickers_str = " ".join(all_tickers)

        try:
            raw = yf.download(
                tickers_str, period="5d", interval="1d",
                auto_adjust=True, progress=False, threads=True,
            )
            close = raw["Close"] if "Close" in raw.columns else raw

            for node_id, ticker in YFINANCE_TICKER_MAP.items():
                try:
                    series = close[ticker].dropna()
                    if not series.empty:
                        result[node_id] = float(series.iloc[-1])
                except KeyError:
                    logger.warning(f"Ticker {ticker} missing for {node_id}")

            for node_id, proxy_info in PROXY_TICKER_MAP.items():
                try:
                    ticker = proxy_info["ticker"]
                    series = close[ticker].dropna()
                    if not series.empty:
                        value = float(series.iloc[-1])
                        if proxy_info.get("invert"):
                            value = -value
                        result[node_id] = value
                except KeyError:
                    logger.warning(f"Proxy ticker {proxy_info['ticker']} missing for {node_id}")

            try:
                xly = close["XLY"].dropna()
                xlp = close["XLP"].dropna()
                if not xly.empty and not xlp.empty:
                    result["consumer_stress"] = float(xly.iloc[-1] / xlp.iloc[-1])
            except KeyError:
                logger.warning("Consumer stress tickers (XLY/XLP) missing")

        except Exception as exc:
            logger.error(f"yfinance bulk download failed: {exc}")
            result.update(self._fetch_individual_tickers())

        logger.info(f"fetch_current_data: collected {len(result)} node values (all real)")

        # Overlay FRED data — replaces proxies with real values where available
        fred_data = self._fetch_fred_latest()
        for node_id, fred_key in FRED_NODE_OVERLAYS.items():
            if fred_key in fred_data:
                result[node_id] = fred_data[fred_key]
                DATA_SOURCE_LABELS[node_id] = DATA_SOURCE_LABELS.get(fred_key, f"FRED {fred_key}")

        result.update(fred_data)
        logger.info(f"fetch_current_data (with FRED): {len(result)} total values")

        # Overlay AKShare China macro data
        try:
            from src.data.china_macro import fetch_china_macro
            china_data = fetch_china_macro()
            self._china_current = china_data
            result.update(china_data)
            logger.info(f"fetch_current_data (with AKShare): {len(result)} total values")
        except Exception as e:
            self._china_current = {}
            logger.warning(f"AKShare China data failed (non-fatal): {e}")

        return result

    def fetch_historical_data(self, period: str = "5y") -> pd.DataFrame:
        frames: dict[str, pd.Series] = {}

        all_tickers = set(YFINANCE_TICKER_MAP.values()) | _ALL_PROXY_TICKERS | set(_CONSUMER_TICKERS.values())
        tickers_str = " ".join(all_tickers)

        try:
            raw = yf.download(
                tickers_str, period=period, interval="1d",
                auto_adjust=True, progress=False, threads=True,
            )
            close = raw["Close"] if "Close" in raw.columns else raw

            for node_id, ticker in YFINANCE_TICKER_MAP.items():
                try:
                    series = close[ticker].dropna().rename(node_id)
                    frames[node_id] = series
                except KeyError:
                    logger.warning(f"Historical data missing for {node_id} ({ticker})")

            for node_id, proxy_info in PROXY_TICKER_MAP.items():
                try:
                    ticker = proxy_info["ticker"]
                    series = close[ticker].dropna().rename(node_id)
                    if proxy_info.get("invert"):
                        series = -series
                    frames[node_id] = series
                except KeyError:
                    logger.warning(f"Historical proxy data missing for {node_id}")

            if "XLY" in close.columns and "XLP" in close.columns:
                ratio = (close["XLY"] / close["XLP"]).dropna().rename("consumer_stress")
                frames["consumer_stress"] = ratio

        except Exception as exc:
            logger.error(f"yfinance historical download failed: {exc}")

        if not frames:
            logger.error("No data fetched at all")
            return pd.DataFrame()

        all_indices = set()
        for s in frames.values():
            all_indices.update(s.index)
        date_index = pd.DatetimeIndex(sorted(all_indices))

        df = pd.DataFrame(index=date_index)
        for node_id, series in frames.items():
            df[node_id] = series.reindex(date_index)

        df = df.ffill().dropna(how="all")

        # Merge FRED historical data
        fred_hist = self._fetch_fred_history()
        self._fred_history = fred_hist
        for key, series in fred_hist.items():
            series.index = pd.to_datetime(series.index)
            daily = series.reindex(df.index, method="ffill")
            df[key] = daily

        for node_id, fred_key in FRED_NODE_OVERLAYS.items():
            if fred_key in df.columns:
                df[node_id] = df[fred_key]

        logger.info(
            f"fetch_historical_data: {len(df)} rows x {len(df.columns)} columns "
            f"(period={period}, incl. FRED)"
        )
        return df

    def update_node_values(self, graph: "MacroRiskCausalGraph") -> None:
        current = self.fetch_current_data()
        historical = self.fetch_historical_data(period="1y")

        updated_count = 0
        for node_id, node in graph.nodes.items():
            value = current.get(node_id)
            if value is None:
                logger.debug(f"No current value for node {node_id}, skipping")
                continue

            node.current_value = value
            node.last_updated = datetime.utcnow().isoformat()
            node.data_source = DATA_SOURCE_LABELS.get(node_id, "unknown")

            if node_id in historical.columns:
                col = historical[node_id].dropna()
                if len(col) >= 5:
                    mean = float(col.mean())
                    std = float(col.std())
                    node.historical_mean = mean
                    node.historical_std = std
                    if std > 0:
                        node.value_zscore = (value - mean) / std
                        node.is_anomalous = abs(node.value_zscore) > 2.0
                        node.anomaly_score = min(1.0, abs(node.value_zscore) / 4.0)
                    else:
                        node.value_zscore = 0.0
            elif node.historical_mean is not None and node.historical_std:
                std = node.historical_std
                if std > 0:
                    node.value_zscore = (value - node.historical_mean) / std
                    node.is_anomalous = abs(node.value_zscore) > 2.0

            updated_count += 1

        logger.info(f"update_node_values: updated {updated_count}/{len(graph.nodes)} nodes (all real)")

        # Store FRED indicators as supplementary context (not graph nodes, but available for reports)
        self._fred_current = {k: v for k, v in current.items() if k.startswith("fred_")}

    def _fetch_individual_tickers(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for node_id, ticker in YFINANCE_TICKER_MAP.items():
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="5d")
                if hist.empty:
                    continue
                result[node_id] = float(hist["Close"].dropna().iloc[-1])
            except Exception as exc:
                logger.warning(f"Individual fetch failed for {ticker}: {exc}")
        return result

    @staticmethod
    def get_data_source_registry() -> dict[str, str]:
        return dict(DATA_SOURCE_LABELS)
