"""Market data cache freshness and coverage checks."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from src.data.collector import FRED_NODE_OVERLAYS, YFINANCE_TICKER_MAP, _all_yfinance_tickers
from src.storage.database import ensure_market_data_daily_table, get_connection


CRITICAL_MARKET_NODES = {
    "vix",
    "spx",
    "dxy",
    "hyg",
    "lqd",
    "kospi",
    "ust_10y",
    "ust_2y",
    "cny_usd",
    "jpy_usd",
}


def market_data_freshness(max_stale_days: int | None = None) -> dict:
    tickers = _all_yfinance_tickers()
    max_stale = max_stale_days or int(os.getenv("MARKET_DATA_MAX_STALE_DAYS", "7"))
    today = datetime.utcnow().date()
    stale_cutoff = today - timedelta(days=max_stale)

    rows = _load_ticker_status(tickers)
    by_ticker = {row["ticker"]: row for row in rows}
    expected_tickers = set(tickers)
    missing = sorted(ticker for ticker in tickers if ticker not in by_ticker)
    stale = [
        ticker
        for ticker, row in by_ticker.items()
        if ticker in expected_tickers
        and row.get("max_trade_date")
        and row["max_trade_date"] < stale_cutoff
    ]
    critical_tickers = _critical_yfinance_tickers()
    critical_missing = [ticker for ticker in critical_tickers if ticker in missing]
    critical_stale = [ticker for ticker in critical_tickers if ticker in stale]

    latest_trade_date = max(
        (row["max_trade_date"] for row in rows if row.get("max_trade_date")),
        default=None,
    )
    earliest_trade_date = min(
        (row["min_trade_date"] for row in rows if row.get("min_trade_date")),
        default=None,
    )
    latest_collected_at = max(
        (row["last_collected_at"] for row in rows if row.get("last_collected_at")),
        default=None,
    )
    cached_tickers = len(expected_tickers & set(by_ticker))
    coverage_pct = round(100 * cached_tickers / max(len(tickers), 1), 1)

    if critical_missing or critical_stale:
        status = "blocked"
    elif missing or stale:
        status = "degraded"
    else:
        status = "ok"

    return {
        "status": status,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "expected_ticker_count": len(tickers),
        "cached_ticker_count": cached_tickers,
        "coverage_pct": coverage_pct,
        "earliest_trade_date": str(earliest_trade_date) if earliest_trade_date else None,
        "latest_trade_date": str(latest_trade_date) if latest_trade_date else None,
        "latest_collected_at": latest_collected_at.isoformat() if latest_collected_at else None,
        "max_stale_days": max_stale,
        "missing_tickers": missing,
        "stale_tickers": sorted(stale),
        "critical_tickers": critical_tickers,
        "critical_missing_tickers": critical_missing,
        "critical_stale_tickers": critical_stale,
        "ticker_status": rows,
        "policy": (
            "Official GFCRI updates require critical market tickers to be present "
            "and fresh. Missing or stale critical tickers block index publication."
        ),
    }


def _critical_yfinance_tickers() -> list[str]:
    fred_enabled = bool(os.getenv("FRED_API_KEY"))
    return sorted(
        ticker
        for node, ticker in YFINANCE_TICKER_MAP.items()
        if node in CRITICAL_MARKET_NODES
        and not (fred_enabled and node in FRED_NODE_OVERLAYS)
    )


def _load_ticker_status(tickers: list[str]) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ensure_market_data_daily_table(cur)
            cur.execute(
                """
                SELECT
                    ticker,
                    COUNT(*)::int AS row_count,
                    MIN(trade_date) AS min_trade_date,
                    MAX(trade_date) AS max_trade_date,
                    MAX(collected_at) AS last_collected_at
                FROM market_data_daily
                WHERE ticker = ANY(%s)
                GROUP BY ticker
                ORDER BY ticker
                """,
                (tickers,),
            )
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
            conn.commit()
            return rows
    finally:
        conn.close()
