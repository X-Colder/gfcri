#!/usr/bin/env python3
"""Backfill daily_risk_index from cached market_data_daily rows.

This script is deliberately offline: it reads only the persisted
market_data_daily cache and never calls yfinance/FRED/Tushare. It is intended
to extend the UI trend history after market data has already been imported.
Existing official daily_risk_index rows are skipped by default.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from loguru import logger

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.collector import (  # noqa: E402
    PROXY_TICKER_MAP,
    YFINANCE_TICKER_MAP,
    _CONSUMER_TICKERS,
    _all_yfinance_tickers,
    _close_frame_from_market_rows,
    _proxy_series,
)
from src.engines.risk_index import GFCRIEngine  # noqa: E402
from src.models.graph import build_initial_causal_graph  # noqa: E402
from src.models.stress import stress_score_from_zscore  # noqa: E402
from src.storage.database import (  # noqa: E402
    get_connection,
    get_market_data_daily,
    save_risk_index,
)


def _existing_index_dates() -> set[str]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT index_date FROM daily_risk_index")
            return {str(row[0]) for row in cur.fetchall()}
    finally:
        conn.close()


def _series_by_node(close: pd.DataFrame) -> dict[str, pd.Series]:
    frames: dict[str, pd.Series] = {}
    for node_id, ticker in YFINANCE_TICKER_MAP.items():
        if ticker in close.columns:
            series = close[ticker].dropna().rename(node_id)
            if not series.empty:
                frames[node_id] = series

    for node_id, proxy_info in PROXY_TICKER_MAP.items():
        series = _proxy_series(close, proxy_info, node_id)
        if not series.empty:
            frames[node_id] = series

    xly = _CONSUMER_TICKERS.get("xly")
    xlp = _CONSUMER_TICKERS.get("xlp")
    if xly in close.columns and xlp in close.columns:
        ratio = (close[xly] / close[xlp]).dropna().rename("consumer_stress")
        if not ratio.empty:
            frames["consumer_stress"] = ratio
    return frames


def _build_node_frame(series_by_node: dict[str, pd.Series]) -> pd.DataFrame:
    if not series_by_node:
        return pd.DataFrame()
    all_index = sorted({idx for series in series_by_node.values() for idx in series.index})
    df = pd.DataFrame(index=pd.DatetimeIndex(all_index))
    for node_id, series in series_by_node.items():
        df[node_id] = series.reindex(df.index)
    return df.ffill().dropna(how="all")


def _anchor_trade_dates(close: pd.DataFrame) -> set[pd.Timestamp]:
    """Return major-market dates to avoid weekend-only crypto/FX rows."""
    anchor_tickers = ["^GSPC", "^VIX", "DX-Y.NYB", "HYG", "LQD", "^HSI", "^KS11"]
    dates: set[pd.Timestamp] = set()
    for ticker in anchor_tickers:
        if ticker not in close.columns:
            continue
        series = close[ticker].dropna()
        dates.update(pd.Timestamp(idx).normalize() for idx in series.index)
    return dates


def _apply_row_to_graph(
    graph,
    node_frame: pd.DataFrame,
    asof: pd.Timestamp,
    lookback: int,
    min_history: int,
) -> int:
    history = node_frame[node_frame.index <= asof]
    updated = 0
    for node_id, node in graph.nodes.items():
        if node_id not in history.columns:
            continue
        series = history[node_id].dropna()
        if len(series) < min_history + 1:
            continue

        current = float(series.iloc[-1])
        baseline = series.iloc[-(lookback + 1):-1] if len(series) > lookback else series.iloc[:-1]
        baseline = baseline.dropna()
        if len(baseline) < min_history:
            continue

        mean = float(baseline.mean())
        std = float(baseline.std())
        zscore = 0.0 if std <= 0 else (current - mean) / std

        node.current_value = current
        node.historical_mean = mean
        node.historical_std = std
        node.value_zscore = zscore
        node.anomaly_score = stress_score_from_zscore(node_id, zscore)
        node.is_anomalous = abs(zscore) > 2.0
        node.last_updated = asof.to_pydatetime()
        updated += 1
    return updated


def _save_result(index_date: str, result: dict) -> None:
    sub = result["sub_indices"]
    save_risk_index(
        index_date=index_date,
        gfcri_value=result["gfcri"],
        alert_level=result["alert_level"],
        si_rates=sub.get("SI_RATES", {}).get("score", 0),
        si_fx=sub.get("SI_FX", {}).get("score", 0),
        si_equity=sub.get("SI_EQUITY", {}).get("score", 0),
        si_credit=sub.get("SI_CREDIT", {}).get("score", 0),
        si_sentiment=sub.get("SI_SENTIMENT", {}).get("score", 0),
        sub_index_details=sub,
        active_chains=[c for c in result["chains"] if c["active"]],
        chain_details=result["chains"],
        coherence_multiplier=result["coherence_multiplier"],
        node_contributions=result.get("node_contributions"),
        divergence=result.get("divergence"),
        undercurrent_boost=result.get("undercurrent_boost", 0),
        trade_spillover=result.get("trade_spillover"),
        trade_spillover_boost=result.get("trade_spillover_boost", 0),
    )


def backfill(days: int, lookback: int, min_history: int, dry_run: bool, overwrite: bool) -> dict:
    end = datetime.utcnow().date()
    output_start = end - timedelta(days=days)
    read_start = output_start - timedelta(days=max(lookback * 2, lookback + min_history + 30))

    rows = get_market_data_daily(_all_yfinance_tickers(), read_start)
    close = _close_frame_from_market_rows(rows)
    if close.empty:
        raise RuntimeError("market_data_daily cache is empty for requested window")

    node_frame = _build_node_frame(_series_by_node(close))
    if node_frame.empty:
        raise RuntimeError("No node series could be built from market_data_daily")

    existing = set() if overwrite else _existing_index_dates()
    anchor_dates = _anchor_trade_dates(close)
    candidates = [
        pd.Timestamp(idx)
        for idx in node_frame.index
        if pd.Timestamp(idx).date() >= output_start
        and pd.Timestamp(idx).date() <= end
        and (not anchor_dates or pd.Timestamp(idx).normalize() in anchor_dates)
    ]

    written = 0
    skipped_existing = 0
    skipped_coverage = 0
    preview: list[dict] = []

    for asof in candidates:
        index_date = asof.date().isoformat()
        if index_date in existing:
            skipped_existing += 1
            continue

        graph = build_initial_causal_graph()
        updated = _apply_row_to_graph(graph, node_frame, asof, lookback, min_history)
        if updated < 8:
            skipped_coverage += 1
            continue

        result = GFCRIEngine(graph).compute()
        row = {
            "index_date": index_date,
            "gfcri": result["gfcri"],
            "alert_level": result["alert_level"],
            "updated_nodes": updated,
        }
        if len(preview) < 5:
            preview.append(row)

        if not dry_run:
            _save_result(index_date, result)
        written += 1

    return {
        "dry_run": dry_run,
        "overwrite": overwrite,
        "read_start": str(read_start),
        "output_start": str(output_start),
        "end": str(end),
        "candidate_dates": len(candidates),
        "written_or_would_write": written,
        "skipped_existing": skipped_existing,
        "skipped_coverage": skipped_coverage,
        "node_columns": len(node_frame.columns),
        "anchor_trade_dates": len(anchor_dates),
        "cache_start": str(pd.Timestamp(close.index.min()).date()),
        "cache_end": str(pd.Timestamp(close.index.max()).date()),
        "preview": preview,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--lookback", type=int, default=252)
    parser.add_argument("--min-history", type=int, default=60)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    summary = backfill(
        days=args.days,
        lookback=args.lookback,
        min_history=args.min_history,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
    )
    for key, value in summary.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
