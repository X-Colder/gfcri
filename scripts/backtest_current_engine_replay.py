"""Replay the current GFCRI engine across historical crisis windows.

This is stricter than the legacy multi-crisis script because it calls the
current production engines:

- GFCRIEngine
- TradeDependencyEngine through GFCRIEngine
- CrisisRegimeAssessmentEngine

Historical coverage is uneven. The script reports node coverage for each
window and uses some old credit-spread series only as anomaly proxies, not as
price-level substitutes, to avoid mixing incompatible units.
"""

from __future__ import annotations

import argparse
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.backtest_multi_crisis import CRISES, compute_gfcri as compute_legacy_gfcri, fetch_crisis_data
from src.engines.crisis_taxonomy import CrisisRegimeAssessmentEngine
from src.engines.risk_index import GFCRIEngine, SUB_INDEX_CONFIG
from src.models.graph import build_initial_causal_graph


NATIVE_NODE_SERIES = {
    "vix": "vix",
    "spx": "spx",
    "hsi": "hsi",
    "nikkei": "nikkei",
    "kospi": "kospi",
    "gold": "gold",
    "oil_wti": "oil_wti",
    "eem": "eem",
    "hyg": "hyg",
    "ust_10y": "ust_10y",
    "dxy": "dxy",
}


# These historical series are unit-incompatible with ETF price nodes. They are
# useful as anomaly proxies but should not feed absolute-level benchmarks.
ANOMALY_PROXY_SERIES = {
    "baa_spread": ("hyg", "lqd"),
    "baa_aaa_spread": ("hyg", "lqd"),
    "ted_spread": ("hyg", "lqd"),
    "t10y2y": ("ust_2y",),
}


@dataclass
class ReplayRow:
    date: str
    raw_gfcri: float
    adjusted_gfcri: float
    legacy_gfcri: float | None
    damage_level: str
    pressure_level: str
    top_match: str
    top_match_similarity: float
    top_factor: str
    coverage: int
    trade_boost: float
    active_chains: int


def coverage_adjusted_gfcri(gfcri_result: dict[str, Any], covered_nodes: set[str]) -> float:
    """Reweight available sub-index families for historical replay only."""
    sub = gfcri_result.get("sub_indices") or {}
    available_weight = 0.0
    weighted_base = 0.0
    for si_id, config in SUB_INDEX_CONFIG.items():
        nodes = set(config.get("nodes") or [])
        weight = float(config.get("weight") or 0)
        if not nodes or not nodes.intersection(covered_nodes):
            continue
        available_weight += weight
        weighted_base += float((sub.get(si_id) or {}).get("score") or 0) * weight

    if available_weight <= 0:
        return float(gfcri_result.get("gfcri") or 0)

    adjusted_base = weighted_base / available_weight
    coherence = float(gfcri_result.get("coherence_multiplier") or 1.0)
    undercurrent = float(gfcri_result.get("undercurrent_boost") or 0.0)
    trade_boost = float(gfcri_result.get("trade_spillover_boost") or 0.0)
    return min(100.0, max(0.0, adjusted_base * coherence + undercurrent + trade_boost))


def zscore_at(series: pd.Series, date: pd.Timestamp, lookback: int = 12) -> tuple[float, float, float] | None:
    hist = series[series.index <= date].dropna()
    if len(hist) < lookback + 1:
        return None
    current = float(hist.iloc[-1])
    lb = hist.iloc[-(lookback + 1):-1]
    mean = float(lb.mean())
    std = float(lb.std())
    if std <= 0:
        return current, mean, 0.0
    return current, mean, (current - mean) / std


def apply_native_series(graph, data: dict[str, pd.Series], date: pd.Timestamp) -> set[str]:
    covered: set[str] = set()
    for node_id, series_id in NATIVE_NODE_SERIES.items():
        node = graph.nodes.get(node_id)
        series = data.get(series_id)
        if node is None or series is None:
            continue
        z = zscore_at(series, date)
        if z is None:
            continue
        current, mean, value_z = z
        hist = series[series.index <= date].dropna()
        node.current_value = current
        node.historical_mean = mean
        node.historical_std = float(hist.iloc[-13:-1].std()) if len(hist) >= 13 else None
        node.value_zscore = value_z
        node.anomaly_score = min(1.0, abs(value_z) / 4.0)
        node.is_anomalous = abs(value_z) > 2.0
        covered.add(node_id)
    return covered


def apply_proxy_anomalies(graph, data: dict[str, pd.Series], date: pd.Timestamp, covered: set[str]) -> None:
    for series_id, node_ids in ANOMALY_PROXY_SERIES.items():
        series = data.get(series_id)
        if series is None:
            continue
        z = zscore_at(series, date)
        if z is None:
            continue
        _, _, value_z = z
        anomaly = min(1.0, abs(value_z) / 4.0)
        for node_id in node_ids:
            node = graph.nodes.get(node_id)
            if node is None:
                continue
            if anomaly > node.anomaly_score:
                # Keep current_value untouched to avoid absolute benchmark misuse.
                node.value_zscore = value_z
                node.anomaly_score = anomaly
                node.is_anomalous = abs(value_z) > 2.0
                covered.add(node_id)


def replay_month(data: dict[str, pd.Series], date: pd.Timestamp) -> dict[str, Any] | None:
    graph = build_initial_causal_graph()
    covered = apply_native_series(graph, data, date)
    apply_proxy_anomalies(graph, data, date, covered)
    if len(covered) < 4:
        return None

    gfcri = GFCRIEngine(graph).compute()
    adjusted_gfcri = coverage_adjusted_gfcri(gfcri, covered)
    risk_like = {
        "gfcri_value": adjusted_gfcri,
        "coherence_multiplier": gfcri.get("coherence_multiplier"),
        "undercurrent_boost": gfcri.get("undercurrent_boost"),
        "sub_index_details": gfcri.get("sub_indices"),
        "node_contributions": gfcri.get("node_contributions"),
        "trade_spillover": gfcri.get("trade_spillover"),
    }
    regime = CrisisRegimeAssessmentEngine().assess(risk_like, [])
    legacy = compute_legacy_gfcri(data, date)
    return {
        "gfcri": gfcri,
        "adjusted_gfcri": adjusted_gfcri,
        "regime": regime,
        "legacy": legacy,
        "coverage": len(covered),
    }


def first_at_or_above(rows: list[ReplayRow], threshold: float) -> str | None:
    hit = next((r for r in rows if r.adjusted_gfcri >= threshold), None)
    return hit.date if hit else None


def months_before(peak_event: str, month: str | None) -> str:
    if not month:
        return "-"
    diff = (pd.Timestamp(peak_event + "-01") - pd.Timestamp(month + "-01")).days // 30
    if diff > 0:
        return f"{diff}m before"
    if diff == 0:
        return "same month"
    return f"{abs(diff)}m after"


def replay_crisis(crisis: dict[str, Any], verbose: bool = False) -> dict[str, Any] | None:
    data = fetch_crisis_data(crisis)
    if not data:
        print(f"{crisis['name']}: no data")
        return None

    rows: list[ReplayRow] = []
    for date in pd.date_range(pd.Timestamp(crisis["backtest_start"]), pd.Timestamp(crisis["backtest_end"]), freq="M"):
        result = replay_month(data, date)
        if not result:
            continue
        gfcri = result["gfcri"]
        regime = result["regime"]
        top_match = regime["matches"][0] if regime["matches"] else {}
        top_factor = regime["factors"][0] if regime["factors"] else {}
        rows.append(ReplayRow(
            date=date.strftime("%Y-%m"),
            raw_gfcri=float(gfcri["gfcri"]),
            adjusted_gfcri=float(result["adjusted_gfcri"]),
            legacy_gfcri=float(result["legacy"]["gfcri"]) if result.get("legacy") else None,
            damage_level=regime["realized_damage"]["level"]["id"],
            pressure_level=regime["forward_pressure"]["level"]["id"],
            top_match=top_match.get("name", "-"),
            top_match_similarity=float(top_match.get("similarity", 0)),
            top_factor=top_factor.get("id", "-"),
            coverage=int(result["coverage"]),
            trade_boost=float(gfcri.get("trade_spillover_boost", 0)),
            active_chains=int(gfcri.get("active_chain_count", 0)),
        ))

    if not rows:
        print(f"{crisis['name']}: insufficient replay coverage")
        return None

    if verbose:
        print(f"\n{'=' * 110}")
        print(crisis["name"])
        print(f"{'=' * 110}")
        print(f"{'Date':<9} {'Raw':>6} {'Adj':>6} {'Legacy':>7} {'Damage':>20} {'Pressure':>20} {'Top Factor':>18} {'Match':>24} {'Sim':>5} {'Cov':>4} {'Tr+':>5}")
        print("-" * 110)
        for row in rows:
            legacy = f"{row.legacy_gfcri:.1f}" if row.legacy_gfcri is not None else "-"
            print(
                f"{row.date:<9} {row.raw_gfcri:>6.1f} {row.adjusted_gfcri:>6.1f} {legacy:>7} "
                f"{row.damage_level[:20]:>20} {row.pressure_level[:20]:>20} "
                f"{row.top_factor[:18]:>18} {row.top_match[:24]:>24} "
                f"{row.top_match_similarity:>5.0f} {row.coverage:>4} {row.trade_boost:>5.1f}"
            )

    peak = max(rows, key=lambda r: r.adjusted_gfcri)
    peak_event_row = next((r for r in rows if r.date == crisis["peak_event"]), None)
    first_warning = first_at_or_above(rows, 25)
    first_orange = first_at_or_above(rows, 50)

    return {
        "crisis": crisis["name"],
        "peak_event": crisis["peak_event"],
        "peak_event_gfcri": peak_event_row.adjusted_gfcri if peak_event_row else None,
        "window_peak_gfcri": peak.adjusted_gfcri,
        "window_peak_raw_gfcri": peak.raw_gfcri,
        "window_peak_date": peak.date,
        "window_peak_damage_level": peak.damage_level,
        "window_peak_pressure_level": peak.pressure_level,
        "first_warning": first_warning,
        "first_orange": first_orange,
        "avg_coverage": sum(r.coverage for r in rows) / len(rows),
        "avg_trade_boost": sum(r.trade_boost for r in rows) / len(rows),
        "top_factor_at_peak": peak.top_factor,
        "top_match_at_peak": peak.top_match,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?", default="all", help="Substring of crisis name, or all")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    summaries = []
    for crisis in deepcopy(CRISES):
        if args.target != "all" and args.target not in crisis["name"]:
            continue
        summary = replay_crisis(crisis, verbose=args.verbose)
        if summary:
            summaries.append(summary)

    if not summaries:
        print("No replay summaries.")
        return

    print(f"\n\n{'=' * 132}")
    print("Current GFCRI engine historical replay summary")
    print(f"{'=' * 132}")
    print(
        f"{'Crisis':<34} {'PeakEvent':>9} {'WinPeak':>8} {'PeakDate':>8} "
        f"{'Damage':>20} {'Pressure':>20} {'Warn':>12} {'Orange':>12} {'Cov':>5} {'Tr+':>5} {'TopFactor':>18}"
    )
    print("-" * 132)
    for s in summaries:
        peak_event = s["peak_event_gfcri"]
        peak_event_text = f"{peak_event:.1f}" if peak_event is not None else "-"
        print(
            f"{s['crisis'][:33]:<34} {peak_event_text:>9} {s['window_peak_gfcri']:>8.1f} "
            f"{s['window_peak_date']:>8} {s['window_peak_damage_level'][:20]:>20} "
            f"{s['window_peak_pressure_level'][:20]:>20} "
            f"{months_before(s['peak_event'], s['first_warning']):>12} "
            f"{months_before(s['peak_event'], s['first_orange']):>12} "
            f"{s['avg_coverage']:>5.1f} {s['avg_trade_boost']:>5.1f} "
            f"{s['top_factor_at_peak'][:18]:>18}"
        )

    print("-" * 132)
    print("Note: coverage is the average number of production GFCRI nodes with historical observations/proxies in the window.")


if __name__ == "__main__":
    main()
