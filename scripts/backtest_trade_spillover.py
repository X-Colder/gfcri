"""Backtest the trade-dependency GFCRI extension against historical crises.

The script reuses the existing multi-crisis historical downloader and compares:

  old GFCRI = current historical backtest score
  new GFCRI = old GFCRI + capped static-v1 trade spillover boost

This is an evaluation harness for the trade dependency layer, not a claim that
the static matrix is final. The next data upgrade should replace static-v1 with
UN Comtrade, OECD TiVA, or IMF DOTS weights.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.backtest_multi_crisis import CRISES, fetch_crisis_data, compute_gfcri
from src.engines.trade_dependency import TradeDependencyEngine, TRADE_DATA_VERSION


TRADE_BOOST_THRESHOLD = 15.0
TRADE_BOOST_SLOPE = 0.25
TRADE_BOOST_CAP = 8.0

HIGH_IS_DANGER = {"vix", "baa_spread", "baa_aaa_spread", "ted_spread", "ust_10y", "dxy", "oil_wti", "unrate", "gold"}
LOW_IS_DANGER = {"spx", "hsi", "nikkei", "kospi", "eem", "hyg", "t10y2y", "emb"}

TRADE_NODE_MAP = {
    "baa_spread": ("hyg", "lqd"),
    "baa_aaa_spread": ("hyg", "lqd"),
    "ted_spread": ("hyg", "lqd"),
    "t10y2y": ("ust_10y",),
}


@dataclass
class CrisisComparison:
    crisis: str
    peak_event: str
    old_peak_event_score: float | None
    new_peak_event_score: float | None
    old_first_warning: str | None
    new_first_warning: str | None
    old_first_orange: str | None
    new_first_orange: str | None
    old_window_peak: float
    new_window_peak: float
    avg_trade_score: float
    max_trade_score: float
    avg_trade_boost: float
    max_trade_boost: float


def trade_spillover_boost(trade_score: float) -> float:
    if trade_score <= TRADE_BOOST_THRESHOLD:
        return 0.0
    return min(TRADE_BOOST_CAP, (trade_score - TRADE_BOOST_THRESHOLD) * TRADE_BOOST_SLOPE)


def indicator_stress(data: dict[str, pd.Series], date: pd.Timestamp, lookback: int = 12) -> dict[str, float]:
    stress: dict[str, float] = {}
    for nid, series in data.items():
        hist = series[series.index <= date].dropna()
        if len(hist) < lookback + 1:
            continue
        current = hist.iloc[-1]
        lb = hist.iloc[-(lookback + 1):-1]
        std = lb.std()

        z_stress = 0.0
        if std > 0:
            z = (current - lb.mean()) / std
            z_stress = min(1.0, abs(float(z)) / 4.0)

        pct_stress = 0.0
        all_hist = series[series.index <= date].dropna()
        if len(all_hist) >= 24:
            if nid in HIGH_IS_DANGER:
                pct = float((all_hist < current).mean())
            elif nid in LOW_IS_DANGER:
                pct = float((all_hist > current).mean())
            else:
                pct = 0.5
            pct_stress = max(0.0, min(1.0, (pct - 0.5) / 0.5)) if pct > 0.5 else 0.0

        value = max(z_stress, pct_stress)
        if value <= 0:
            continue
        for mapped in TRADE_NODE_MAP.get(nid, (nid,)):
            stress[mapped] = max(stress.get(mapped, 0.0), value)
    return stress


def alert(score: float) -> str:
    if score >= 75:
        return "RED"
    if score >= 50:
        return "ORANGE"
    if score >= 25:
        return "YELLOW"
    return "GREEN"


def first_at_or_above(results: list[dict[str, Any]], threshold: float) -> str | None:
    hit = next((r for r in results if r["new_gfcri"] >= threshold), None)
    return hit["date"] if hit else None


def first_old_at_or_above(results: list[dict[str, Any]], threshold: float) -> str | None:
    hit = next((r for r in results if r["old_gfcri"] >= threshold), None)
    return hit["date"] if hit else None


def months_before(peak_event: str, month: str | None) -> str:
    if not month:
        return "-"
    diff = (pd.Timestamp(peak_event + "-01") - pd.Timestamp(month + "-01")).days // 30
    if diff > 0:
        return f"{diff}m before"
    if diff == 0:
        return "same month"
    return f"{abs(diff)}m after"


def compare_crisis(crisis: dict[str, Any], verbose: bool = False) -> CrisisComparison | None:
    data = fetch_crisis_data(crisis)
    if not data:
        print(f"{crisis['name']}: no data")
        return None

    engine = TradeDependencyEngine()
    results: list[dict[str, Any]] = []

    for date in pd.date_range(pd.Timestamp(crisis["backtest_start"]), pd.Timestamp(crisis["backtest_end"]), freq="M"):
        old = compute_gfcri(data, date)
        if not old:
            continue
        stress = indicator_stress(data, date)
        trade = engine.compute_from_node_stress(stress)
        boost = trade_spillover_boost(float(trade["score"]))
        new_score = min(100.0, float(old["gfcri"]) + boost)
        results.append({
            "date": date.strftime("%Y-%m"),
            "old_gfcri": float(old["gfcri"]),
            "new_gfcri": new_score,
            "trade_score": float(trade["score"]),
            "trade_boost": boost,
            "old_alert": old["alert"],
            "new_alert": alert(new_score),
            "top_trade_link": trade["top_links"][0] if trade.get("top_links") else None,
        })

    if not results:
        print(f"{crisis['name']}: insufficient data")
        return None

    if verbose:
        print(f"\n{'=' * 96}")
        print(f"{crisis['name']}  [{TRADE_DATA_VERSION}]")
        print(f"{'=' * 96}")
        print(f"{'Date':<9} {'Old':>6} {'New':>6} {'Trade':>7} {'Boost':>7} {'OldAlert':>9} {'NewAlert':>9}  Top spillover")
        print("-" * 96)
        for row in results:
            link = row["top_trade_link"]
            link_desc = ""
            if link:
                link_desc = f"{link['source']}->{link['target']} {link['sector']} {link['spillover']:.1f}"
            print(
                f"{row['date']:<9} {row['old_gfcri']:>6.1f} {row['new_gfcri']:>6.1f} "
                f"{row['trade_score']:>7.1f} {row['trade_boost']:>7.1f} "
                f"{row['old_alert']:>9} {row['new_alert']:>9}  {link_desc}"
            )

    peak_event_row = next((r for r in results if r["date"] == crisis["peak_event"]), None)
    old_peak = max(results, key=lambda r: r["old_gfcri"])
    new_peak = max(results, key=lambda r: r["new_gfcri"])

    return CrisisComparison(
        crisis=crisis["name"],
        peak_event=crisis["peak_event"],
        old_peak_event_score=peak_event_row["old_gfcri"] if peak_event_row else None,
        new_peak_event_score=peak_event_row["new_gfcri"] if peak_event_row else None,
        old_first_warning=first_old_at_or_above(results, 25),
        new_first_warning=first_at_or_above(results, 25),
        old_first_orange=first_old_at_or_above(results, 50),
        new_first_orange=first_at_or_above(results, 50),
        old_window_peak=old_peak["old_gfcri"],
        new_window_peak=new_peak["new_gfcri"],
        avg_trade_score=sum(r["trade_score"] for r in results) / len(results),
        max_trade_score=max(r["trade_score"] for r in results),
        avg_trade_boost=sum(r["trade_boost"] for r in results) / len(results),
        max_trade_boost=max(r["trade_boost"] for r in results),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?", default="all", help="Substring of crisis name, or all")
    parser.add_argument("--verbose", action="store_true", help="Print monthly crisis tables")
    args = parser.parse_args()

    comparisons: list[CrisisComparison] = []
    for crisis in CRISES:
        if args.target != "all" and args.target not in crisis["name"]:
            continue
        comp = compare_crisis(crisis, verbose=args.verbose)
        if comp:
            comparisons.append(comp)

    if not comparisons:
        print("No comparable crisis windows.")
        return

    print(f"\n\n{'=' * 120}")
    print(f"Trade spillover backtest summary [{TRADE_DATA_VERSION}]")
    print(f"{'=' * 120}")
    print(
        f"{'Crisis':<34} {'PeakOld':>8} {'PeakNew':>8} {'ΔPeak':>7} "
        f"{'WarnOld':>12} {'WarnNew':>12} {'OrangeOld':>12} {'OrangeNew':>12} "
        f"{'AvgTrade':>9} {'MaxTrade':>9} {'MaxBoost':>9}"
    )
    print("-" * 120)
    for c in comparisons:
        old_peak_event = c.old_peak_event_score
        new_peak_event = c.new_peak_event_score
        delta = None if old_peak_event is None or new_peak_event is None else new_peak_event - old_peak_event
        print(
            f"{c.crisis[:33]:<34} "
            f"{old_peak_event if old_peak_event is not None else 0:>8.1f} "
            f"{new_peak_event if new_peak_event is not None else 0:>8.1f} "
            f"{delta if delta is not None else 0:>7.1f} "
            f"{months_before(c.peak_event, c.old_first_warning):>12} "
            f"{months_before(c.peak_event, c.new_first_warning):>12} "
            f"{months_before(c.peak_event, c.old_first_orange):>12} "
            f"{months_before(c.peak_event, c.new_first_orange):>12} "
            f"{c.avg_trade_score:>9.1f} {c.max_trade_score:>9.1f} {c.max_trade_boost:>9.1f}"
        )

    valid_deltas = [
        c.new_peak_event_score - c.old_peak_event_score
        for c in comparisons
        if c.new_peak_event_score is not None and c.old_peak_event_score is not None
    ]
    if valid_deltas:
        print("-" * 120)
        print(f"Average peak-event score change: {sum(valid_deltas) / len(valid_deltas):+.2f}")
        print("Interpretation: positive change means the trade layer lifted risk during historical crisis peak months.")


if __name__ == "__main__":
    main()
