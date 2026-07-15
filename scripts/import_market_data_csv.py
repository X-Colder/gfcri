#!/usr/bin/env python3
"""Import GFCRI market-data CSV rows into market_data_daily."""

from __future__ import annotations

import argparse
import csv
import gzip
from datetime import datetime

from src.storage.database import save_market_data_batch


def _iter_rows(path: str):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            volume = row.get("volume") or None
            yield (
                row["ticker"],
                datetime.strptime(row["trade_date"], "%Y-%m-%d").date(),
                float(row["close_price"]),
                int(volume) if volume else None,
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--batch-size", type=int, default=5000)
    args = parser.parse_args()

    total = 0
    batch = []
    for item in _iter_rows(args.path):
        batch.append(item)
        if len(batch) >= args.batch_size:
            save_market_data_batch(batch)
            total += len(batch)
            batch = []
    if batch:
        save_market_data_batch(batch)
        total += len(batch)

    print(f"imported_rows={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
