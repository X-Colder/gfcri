#!/usr/bin/env python3
"""Export yfinance daily close/volume rows for GFCRI tickers to CSV.

This script is intended for running on a host whose Yahoo/yfinance egress is
currently healthy. It does not write to the database.
"""

from __future__ import annotations

import argparse
import gzip
import csv
from pathlib import Path

import pandas as pd
import yfinance as yf

from src.data.collector import (
    PROXY_TICKER_MAP,
    YFINANCE_TICKER_MAP,
    _CONSUMER_TICKERS,
)


def _all_tickers() -> list[str]:
    tickers = set(YFINANCE_TICKER_MAP.values()) | set(_CONSUMER_TICKERS.values())
    for proxy in PROXY_TICKER_MAP.values():
        for ticker in proxy.get("tickers", [proxy.get("ticker")]):
            if ticker:
                tickers.add(ticker)
    return sorted(tickers)


def _extract_field(raw: pd.DataFrame, field: str, tickers: list[str]) -> pd.DataFrame:
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


def _chunks(values: list[str], size: int):
    for idx in range(0, len(values), size):
        yield values[idx : idx + size]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", default="2y")
    parser.add_argument("--output", required=True)
    parser.add_argument("--batch-size", type=int, default=45)
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    tickers = _all_tickers()
    rows = []
    ok = set()
    missing = set(tickers)

    for batch in _chunks(tickers, max(1, args.batch_size)):
        raw = yf.download(
            " ".join(batch),
            period=args.period,
            interval="1d",
            progress=False,
            auto_adjust=True,
            threads=False,
        )
        close = _extract_field(raw, "Close", batch)
        volume = _extract_field(raw, "Volume", batch)
        for ticker in close.columns:
            series = close[ticker].dropna()
            if series.empty:
                continue
            ok.add(str(ticker))
            missing.discard(str(ticker))
            vol_series = volume[ticker] if not volume.empty and ticker in volume.columns else None
            for ts, close_value in series.items():
                if pd.isna(close_value):
                    continue
                vol_value = ""
                if vol_series is not None and ts in vol_series.index and not pd.isna(vol_series.loc[ts]):
                    try:
                        vol_value = str(int(vol_series.loc[ts]))
                    except Exception:
                        vol_value = ""
                rows.append(
                    [
                        str(ticker),
                        pd.Timestamp(ts).date().isoformat(),
                        f"{float(close_value):.10f}",
                        vol_value,
                    ]
                )

    with gzip.open(output, "wt", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ticker", "trade_date", "close_price", "volume"])
        writer.writerows(rows)

    print(f"tickers_total={len(tickers)}")
    print(f"tickers_ok={len(ok)}")
    print(f"rows={len(rows)}")
    print(f"missing={','.join(sorted(missing))}")
    print(f"output={output}")
    return 0 if len(ok) == len(tickers) else 2


if __name__ == "__main__":
    raise SystemExit(main())
