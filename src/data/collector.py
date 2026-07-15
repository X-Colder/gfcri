"""
Market data collector module.

Data sources:
  - yfinance: 38 market indicators (direct tickers, ETF proxies, computed ratios)
  - FRED API: US economic fundamentals and financial stress indicators
"""

from __future__ import annotations

import os
import time
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import yfinance as yf
from loguru import logger

from src.models.stress import stress_score_from_zscore
from src.storage.database import get_market_data_daily, save_market_data_batch

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
        "tickers": ["MU", "005930.KS", "000660.KS"],
        "description": "DRAM producer equity basket proxy",
        "source_label": "yfinance MU/005930.KS/000660.KS basket (DRAM proxy)",
    },
    "nand_spot": {
        "tickers": ["WDC", "STX", "MU", "005930.KS"],
        "description": "NAND/storage producer equity basket proxy",
        "source_label": "yfinance WDC/STX/MU/005930.KS basket (NAND/storage proxy)",
    },
    "orcl_cds": {
        "tickers": ["ORCL", "MSFT", "AMZN", "GOOGL", "META"],
        "description": "AI/cloud equity basket inverse as credit-stress proxy (basket down = credit stress up)",
        "source_label": "yfinance ORCL/MSFT/AMZN/GOOGL/META basket (proxy, inverted)",
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
        "tickers": ["CLOU", "SMH", "MSFT", "AMZN", "GOOGL", "META", "NVDA"],
        "description": "AI/cloud capex cycle basket proxy",
        "source_label": "yfinance CLOU/SMH/MSFT/AMZN/GOOGL/META/NVDA basket (proxy)",
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
    for ticker in p.get("tickers", [p.get("ticker")]):
        if ticker:
            _ALL_PROXY_TICKERS.add(ticker)

# Data source labels for all nodes
DATA_SOURCE_LABELS: dict[str, str] = {}
for nid, ticker in YFINANCE_TICKER_MAP.items():
    DATA_SOURCE_LABELS[nid] = f"yfinance {ticker}"
for nid, info in PROXY_TICKER_MAP.items():
    DATA_SOURCE_LABELS[nid] = info["source_label"]
DATA_SOURCE_LABELS["consumer_stress"] = "yfinance XLY/XLP (computed ratio)"


def _proxy_tickers(proxy_info: dict) -> list[str]:
    return [t for t in proxy_info.get("tickers", [proxy_info.get("ticker")]) if t]


def _proxy_series(close: pd.DataFrame, proxy_info: dict, node_id: str) -> pd.Series:
    tickers = _proxy_tickers(proxy_info)
    if not tickers:
        return pd.Series(dtype=float, name=node_id)

    series_list = []
    for ticker in tickers:
        try:
            s = close[ticker].dropna()
        except KeyError:
            logger.warning(f"Proxy ticker {ticker} missing for {node_id}")
            continue
        if s.empty:
            continue
        if len(tickers) > 1:
            first = float(s.iloc[0])
            if first == 0:
                continue
            s = s / first * 100.0
        series_list.append(s.rename(ticker))

    if not series_list:
        return pd.Series(dtype=float, name=node_id)

    if len(series_list) == 1:
        result = series_list[0].rename(node_id)
    else:
        result = pd.concat(series_list, axis=1).mean(axis=1).dropna().rename(node_id)

    if proxy_info.get("invert"):
        result = -result
    return result

# ---------------------------------------------------------------------------
# FRED indicators — real economic data replacing yfinance proxies
# ---------------------------------------------------------------------------
FRED_INDICATORS: dict[str, dict] = {
    "fred_effr": {"series": "EFFR", "name": "联邦基金利率", "frequency": "daily"},
    "fred_sofr": {"series": "SOFR", "name": "担保隔夜融资利率", "frequency": "daily"},
    "fred_dgs10": {"series": "DGS10", "name": "10年期美国国债收益率", "frequency": "daily"},
    "fred_dgs2": {"series": "DGS2", "name": "2年期美国国债收益率", "frequency": "daily"},
    "fred_t10y2y": {"series": "T10Y2Y", "name": "10Y-2Y利差", "frequency": "daily"},
    "fred_recession_prob": {"series": "RECPROUSM156N", "name": "美国衰退概率", "frequency": "monthly"},
    "fred_kr_current_account": {"series": "KORB6BLTT02STSAQ", "name": "韩国经常账户余额/GDP", "frequency": "quarterly"},
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
    "fred_euro_hy_spread": {"series": "BAMLHE00EHYIOAS", "name": "欧元区高收益债利差", "frequency": "daily"},
    "fred_all_loan_delinquency": {"series": "DRALACBS", "name": "美国商业银行全贷款逾期率", "frequency": "quarterly"},
    "fred_baa10y_spread": {"series": "BAA10Y", "name": "Baa企业债-10年美债利差", "frequency": "daily"},
    "fred_walcl": {"series": "WALCL", "name": "美联储资产负债表", "frequency": "weekly"},
}

for nid, info in FRED_INDICATORS.items():
    DATA_SOURCE_LABELS[nid] = f"FRED {info['series']}"
DATA_SOURCE_LABELS["sofr_effr_spread"] = "FRED SOFR - EFFR (computed bps)"

FRED_NODE_OVERLAYS: dict[str, str] = {
    "fed_funds": "fred_effr",
    "ust_10y": "fred_dgs10",
    "ust_2y": "fred_dgs2",
    "us_recession_prob": "fred_recession_prob",
    "global_liqd": "fred_walcl",
    "kr_ca": "fred_kr_current_account",
}

TUSHARE_YFINANCE_FALLBACKS: dict[str, dict[str, str]] = {
    "^GSPC": {"api": "index_global", "ts_code": "SPX", "field": "close"},
    "^HSI": {"api": "index_global", "ts_code": "HSI", "field": "close"},
    "^N225": {"api": "index_global", "ts_code": "N225", "field": "close"},
    "^KS11": {"api": "index_global", "ts_code": "KS11", "field": "close"},
    "CNY=X": {"api": "fx_daily", "ts_code": "USDCNH.FXCM", "field": "bid_close"},
    "JPY=X": {"api": "fx_daily", "ts_code": "USDJPY.FXCM", "field": "bid_close"},
    "EURUSD=X": {"api": "fx_daily", "ts_code": "EURUSD.FXCM", "field": "bid_close"},
}


def _all_yfinance_tickers() -> list[str]:
    return sorted(
        set(YFINANCE_TICKER_MAP.values())
        | _ALL_PROXY_TICKERS
        | set(_CONSUMER_TICKERS.values())
    )


def _period_start_date(period: str) -> date:
    """Translate yfinance-style periods to a conservative calendar start date."""
    today = datetime.utcnow().date()
    try:
        value = int(period[:-1])
        unit = period[-1].lower()
    except Exception:
        return today - timedelta(days=365 * 5)

    if unit == "d":
        # Calendar days, plus weekend/holiday slack.
        return today - timedelta(days=max(value * 2, value + 5))
    if unit == "mo":
        return today - timedelta(days=value * 31 + 7)
    if unit == "y":
        return today - timedelta(days=value * 366 + 14)
    return today - timedelta(days=365 * 5)


def _chunked(values: list[str], size: int) -> list[list[str]]:
    return [values[i : i + size] for i in range(0, len(values), size)]


def _extract_yfinance_field(raw: pd.DataFrame, field: str, tickers: list[str]) -> pd.DataFrame:
    """Return a ticker-column DataFrame for a yfinance field."""
    if raw is None or raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        if field in raw.columns.get_level_values(0):
            data = raw[field]
        elif field in raw.columns.get_level_values(-1):
            data = raw.xs(field, level=-1, axis=1)
        else:
            return pd.DataFrame()
        if isinstance(data, pd.Series):
            data = data.to_frame(name=tickers[0] if tickers else field)
        return data
    if field not in raw.columns:
        return pd.DataFrame()
    name = tickers[0] if len(tickers) == 1 else field
    return raw[[field]].rename(columns={field: name})


def _market_rows_from_yfinance(raw: pd.DataFrame, tickers: list[str]) -> list[tuple]:
    close = _extract_yfinance_field(raw, "Close", tickers)
    if close.empty:
        return []
    volume = _extract_yfinance_field(raw, "Volume", tickers)
    rows = []
    for ticker in close.columns:
        series = close[ticker].dropna()
        if series.empty:
            continue
        vol_series = volume[ticker] if not volume.empty and ticker in volume.columns else None
        for ts, close_value in series.items():
            if pd.isna(close_value):
                continue
            trade_date = pd.Timestamp(ts).date()
            vol_value = None
            if vol_series is not None and ts in vol_series.index and not pd.isna(vol_series.loc[ts]):
                try:
                    vol_value = int(vol_series.loc[ts])
                except Exception:
                    vol_value = None
            rows.append((str(ticker), trade_date, float(close_value), vol_value))
    return rows


def _close_frame_from_market_rows(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame()
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["close_price"] = df["close_price"].astype(float)
    return (
        df.pivot_table(
            index="trade_date",
            columns="ticker",
            values="close_price",
            aggfunc="last",
        )
        .sort_index()
    )


class MarketDataCollector:
    """Collects market data from yfinance + FRED API."""

    def __init__(self) -> None:
        self.fred_api_key = os.getenv("FRED_API_KEY", "")
        self._yf_close_cache: dict[str, pd.DataFrame] = {}
        self._historical_cache: dict[str, pd.DataFrame] = {}

    def _download_yfinance_to_cache(self, tickers: list[str], period: str) -> int:
        if not tickers:
            return 0
        batch_size = max(1, int(os.getenv("YFINANCE_BATCH_SIZE", "8")))
        sleep_seconds = float(os.getenv("YFINANCE_SLEEP_SECONDS", "3"))
        saved = 0

        for idx, batch in enumerate(_chunked(sorted(tickers), batch_size), start=1):
            try:
                raw = yf.download(
                    " ".join(batch),
                    period=period,
                    interval="1d",
                    auto_adjust=True,
                    progress=False,
                    threads=False,
                )
                rows = _market_rows_from_yfinance(raw, batch)
                if rows:
                    save_market_data_batch(rows)
                    saved += len(rows)
                    logger.info(
                        f"yfinance cache fill: batch {idx}, tickers={len(batch)}, rows={len(rows)}"
                    )
                else:
                    logger.warning(
                        f"yfinance cache fill returned no rows: batch {idx}, tickers={batch}"
                    )
            except Exception as exc:
                logger.warning(f"yfinance cache fill failed for batch {idx} {batch}: {exc}")
            if idx * batch_size < len(tickers) and sleep_seconds > 0:
                time.sleep(sleep_seconds)
        return saved

    def _download_tushare_to_cache(self, tickers: list[str], start: date) -> int:
        token = os.getenv("TUSHARE_TOKEN") or os.getenv("TS_TOKEN")
        if not token:
            return 0

        import requests

        saved = 0
        end = datetime.utcnow().strftime("%Y%m%d")
        start_str = start.strftime("%Y%m%d")
        for yf_ticker in sorted(tickers):
            mapping = TUSHARE_YFINANCE_FALLBACKS.get(yf_ticker)
            if not mapping:
                continue
            field = mapping["field"]
            fields = f"ts_code,trade_date,{field}"
            try:
                resp = requests.post(
                    "http://api.tushare.pro",
                    json={
                        "api_name": mapping["api"],
                        "token": token,
                        "params": {
                            "ts_code": mapping["ts_code"],
                            "start_date": start_str,
                            "end_date": end,
                        },
                        "fields": fields,
                    },
                    timeout=20,
                )
                data = resp.json()
                if data.get("code") != 0:
                    logger.warning(
                        f"Tushare fallback failed for {yf_ticker}: "
                        f"code={data.get('code')} msg={data.get('msg')}"
                    )
                    continue
                payload = data.get("data") or {}
                result_fields = payload.get("fields") or []
                items = payload.get("items") or []
                if field not in result_fields or "trade_date" not in result_fields:
                    continue
                date_idx = result_fields.index("trade_date")
                value_idx = result_fields.index(field)
                rows = []
                for item in items:
                    value = item[value_idx]
                    if value is None:
                        continue
                    try:
                        trade_date = datetime.strptime(str(item[date_idx]), "%Y%m%d").date()
                        rows.append((yf_ticker, trade_date, float(value), None))
                    except Exception:
                        continue
                if rows:
                    save_market_data_batch(rows)
                    saved += len(rows)
                    logger.info(
                        f"Tushare fallback cache fill: {yf_ticker} "
                        f"({mapping['ts_code']}), rows={len(rows)}"
                    )
            except Exception as exc:
                logger.warning(f"Tushare fallback exception for {yf_ticker}: {exc}")
        return saved

    def _load_yfinance_close_data(self, period: str, require_full_history: bool) -> pd.DataFrame:
        """Read daily market closes from DB, filling missing cache ranges if needed."""
        cache_key = f"{period}:{int(require_full_history)}"
        if cache_key in self._yf_close_cache:
            return self._yf_close_cache[cache_key].copy()

        tickers = _all_yfinance_tickers()
        start = _period_start_date(period)
        rows = get_market_data_daily(tickers, start)
        close = _close_frame_from_market_rows(rows)

        today = datetime.utcnow().date()
        fresh_cutoff = today - timedelta(days=int(os.getenv("MARKET_DATA_MAX_STALE_DAYS", "7")))
        history_slack = start + timedelta(days=14)
        missing = []

        for ticker in tickers:
            if ticker not in close.columns:
                missing.append(ticker)
                continue
            series = close[ticker].dropna()
            if series.empty:
                missing.append(ticker)
                continue
            latest = pd.Timestamp(series.index.max()).date()
            earliest = pd.Timestamp(series.index.min()).date()
            if latest < fresh_cutoff:
                missing.append(ticker)
                continue
            if require_full_history and earliest > history_slack:
                missing.append(ticker)

        if missing:
            tushare_saved = self._download_tushare_to_cache(missing, start)
            if tushare_saved:
                rows = get_market_data_daily(tickers, start)
                close = _close_frame_from_market_rows(rows)
                remaining = []
                for ticker in missing:
                    if ticker not in close.columns or close[ticker].dropna().empty:
                        remaining.append(ticker)
                missing = remaining

        if missing and os.getenv("YFINANCE_DISABLE_ONLINE", "").lower() not in ("1", "true", "yes"):
            logger.info(
                f"Market data cache miss: {len(missing)}/{len(tickers)} tickers "
                f"(period={period}, require_full_history={require_full_history})"
            )
            self._download_yfinance_to_cache(missing, period)
            rows = get_market_data_daily(tickers, start)
            close = _close_frame_from_market_rows(rows)
        elif missing:
            logger.warning(
                f"Market data cache incomplete and online yfinance disabled: "
                f"{len(missing)}/{len(tickers)} missing"
            )

        logger.info(
            f"Market data cache loaded: {0 if close.empty else len(close)} rows x "
            f"{0 if close.empty else len(close.columns)} tickers (period={period})"
        )
        self._yf_close_cache[cache_key] = close.copy()
        return close

    def refresh_market_data_cache(self, period: str | None = None) -> dict:
        """Fill the raw daily market-data cache without computing GFCRI."""
        refresh_period = period or os.getenv("MARKET_DATA_REFRESH_PERIOD", "2y")
        close = self._load_yfinance_close_data(
            period=refresh_period,
            require_full_history=True,
        )
        if close.empty:
            return {
                "period": refresh_period,
                "rows": 0,
                "tickers": 0,
                "start_date": None,
                "end_date": None,
            }
        return {
            "period": refresh_period,
            "rows": int(len(close)),
            "tickers": int(len(close.columns)),
            "start_date": str(pd.Timestamp(close.index.min()).date()),
            "end_date": str(pd.Timestamp(close.index.max()).date()),
        }

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

        close = self._load_yfinance_close_data(period="5d", require_full_history=False)

        for node_id, ticker in YFINANCE_TICKER_MAP.items():
            try:
                series = close[ticker].dropna()
                if not series.empty:
                    result[node_id] = float(series.iloc[-1])
            except KeyError:
                logger.warning(f"Ticker {ticker} missing for {node_id}")

        for node_id, proxy_info in PROXY_TICKER_MAP.items():
            series = _proxy_series(close, proxy_info, node_id)
            if not series.empty:
                result[node_id] = float(series.iloc[-1])

        try:
            xly = close["XLY"].dropna()
            xlp = close["XLP"].dropna()
            if not xly.empty and not xlp.empty:
                result["consumer_stress"] = float(xly.iloc[-1] / xlp.iloc[-1])
        except KeyError:
            logger.warning("Consumer stress tickers (XLY/XLP) missing")

        logger.info(f"fetch_current_data: collected {len(result)} node values (all real)")

        # Overlay FRED data — replaces proxies with real values where available
        fred_data = self._fetch_fred_latest()
        if "fred_sofr" in fred_data and "fred_effr" in fred_data:
            result["sofr_effr_spread"] = (fred_data["fred_sofr"] - fred_data["fred_effr"]) * 100.0
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
        if period in self._historical_cache:
            return self._historical_cache[period].copy()

        frames: dict[str, pd.Series] = {}

        close = self._load_yfinance_close_data(period=period, require_full_history=True)

        for node_id, ticker in YFINANCE_TICKER_MAP.items():
            try:
                series = close[ticker].dropna().rename(node_id)
                if not series.empty:
                    frames[node_id] = series
                else:
                    logger.warning(f"Historical data missing for {node_id} ({ticker})")
            except KeyError:
                logger.warning(f"Historical data missing for {node_id} ({ticker})")

        for node_id, proxy_info in PROXY_TICKER_MAP.items():
            series = _proxy_series(close, proxy_info, node_id)
            if not series.empty:
                frames[node_id] = series
            else:
                logger.warning(f"Historical proxy data missing for {node_id}")

        if "XLY" in close.columns and "XLP" in close.columns:
            ratio = (close["XLY"] / close["XLP"]).dropna().rename("consumer_stress")
            if not ratio.empty:
                frames["consumer_stress"] = ratio

        all_indices = set()
        for s in frames.values():
            all_indices.update(s.index)

        # Merge FRED historical data
        fred_hist = self._fetch_fred_history()
        self._fred_history = fred_hist
        for series in fred_hist.values():
            all_indices.update(pd.to_datetime(series.index))

        if not all_indices:
            logger.error("No historical market or FRED data fetched")
            return pd.DataFrame()

        date_index = pd.DatetimeIndex(sorted(all_indices))

        df = pd.DataFrame(index=date_index)
        for node_id, series in frames.items():
            df[node_id] = series.reindex(date_index)

        for key, series in fred_hist.items():
            series.index = pd.to_datetime(series.index)
            daily = series.reindex(df.index, method="ffill")
            df[key] = daily

        for node_id, fred_key in FRED_NODE_OVERLAYS.items():
            if fred_key in df.columns:
                df[node_id] = df[fred_key]
        if "fred_sofr" in df.columns and "fred_effr" in df.columns:
            df["sofr_effr_spread"] = (df["fred_sofr"] - df["fred_effr"]) * 100.0

        df = df.ffill().dropna(how="all")

        logger.info(
            f"fetch_historical_data: {len(df)} rows x {len(df.columns)} columns "
            f"(period={period}, incl. FRED)"
        )
        self._historical_cache[period] = df.copy()
        return df

    def update_node_values(self, graph: "MacroRiskCausalGraph") -> None:
        current = self.fetch_current_data()
        historical = self.fetch_historical_data(period="2y")

        updated_count = 0
        for node_id, node in graph.nodes.items():
            value = current.get(node_id)
            proxy = PROXY_TICKER_MAP.get(node_id)
            if proxy and len(_proxy_tickers(proxy)) > 1 and node_id in historical.columns:
                hist_col = historical[node_id].dropna()
                if not hist_col.empty:
                    value = float(hist_col.iloc[-1])
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
                        node.anomaly_score = stress_score_from_zscore(node_id, node.value_zscore)
                    else:
                        node.value_zscore = 0.0
                        node.anomaly_score = 0.0
            elif node.historical_mean is not None and node.historical_std:
                std = node.historical_std
                if std > 0:
                    node.value_zscore = (value - node.historical_mean) / std
                    node.is_anomalous = abs(node.value_zscore) > 2.0
                    node.anomaly_score = stress_score_from_zscore(node_id, node.value_zscore)

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
