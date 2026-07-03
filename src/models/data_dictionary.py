"""Machine-readable data dictionary for GFCRI nodes.

This file makes model data provenance explicit. It is intentionally lightweight:
the node registry remains the source of truth for canonical node definitions,
while this dictionary records data-source quality, raw formulas, and known
limitations needed for institutional-grade auditability.
"""

from __future__ import annotations

from typing import Any

from src.models.nodes import CORE_NODES


SOURCE_TIERS: dict[str, str] = {
    "A": "Official or primary index/provider data suitable for core scoring.",
    "B": "Liquid market proxy or broad ETF suitable as fallback/core supplement.",
    "C": "Equity/ETF inverse or narrow proxy; temporary fallback only.",
    "D": "Synthetic or narrative proxy; research-only unless validated.",
}


NODE_DATA_OVERRIDES: dict[str, dict[str, Any]] = {
    "fred_hy_spread": {
        "source_tier": "A",
        "raw_formula": "FRED BAMLH0A0HYM2 latest observation; level in percentage points.",
        "stress_direction": "higher_is_worse",
        "absolute_threshold": "normal=3.5, crisis=10.0",
        "known_limitations": "US high-yield credit only; does not cover Europe, China, private credit, or bank funding.",
        "upgrade_plan": "Add CDX HY and global HY spread composites when data access is available.",
    },
    "fred_bbb_spread": {
        "source_tier": "A",
        "raw_formula": "FRED BAMLC0A4CBBB latest observation; BBB option-adjusted spread in percentage points.",
        "stress_direction": "higher_is_worse",
        "absolute_threshold": "normal=1.2, crisis=4.0",
        "known_limitations": "US BBB credit only; misses non-US investment-grade stress.",
        "upgrade_plan": "Add CDX IG, US IG OAS, and Europe IG spread indices.",
    },
    "fred_ic_spread": {
        "source_tier": "A",
        "raw_formula": "FRED BAMLC0A1CAAAEY latest observation; AAA corporate effective yield.",
        "stress_direction": "higher_is_worse",
        "absolute_threshold": "normal=4.0, crisis=7.0",
        "known_limitations": "Effective yield mixes risk-free rates and credit premium; not a pure spread.",
        "upgrade_plan": "Replace or supplement with pure AAA/IG option-adjusted spread series.",
    },
    "hyg": {
        "source_tier": "B",
        "raw_formula": "HYG adjusted close from yfinance.",
        "stress_direction": "lower_is_worse",
        "absolute_threshold": "normal=82, crisis=60",
        "known_limitations": "ETF price mixes credit spread, duration, liquidity, and ETF flow effects.",
        "upgrade_plan": "Keep as liquid market confirmation; reduce weight when direct HY OAS/CDX HY are available.",
    },
    "lqd": {
        "source_tier": "B",
        "raw_formula": "LQD adjusted close from yfinance.",
        "stress_direction": "lower_is_worse",
        "absolute_threshold": "normal=110, crisis=90",
        "known_limitations": "ETF price is duration-sensitive and not a pure credit spread.",
        "upgrade_plan": "Keep as market confirmation; add direct IG OAS/CDX IG data.",
    },
    "emb": {
        "source_tier": "B",
        "raw_formula": "EMB adjusted close from yfinance.",
        "stress_direction": "lower_is_worse",
        "absolute_threshold": "not yet defined",
        "known_limitations": "ETF proxy; does not decompose sovereign spread, duration, and FX effects.",
        "upgrade_plan": "Add EMBI Global spread, sovereign CDS basket, and country-level EM stress.",
    },
    "kr_cds_5y": {
        "source_tier": "C",
        "raw_formula": "-EWY adjusted close from yfinance as temporary inverse proxy.",
        "stress_direction": "higher_is_worse after inversion",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Not actual Korea CDS; equity proxy can move for non-credit reasons.",
        "upgrade_plan": "Replace with actual Korea 5Y sovereign CDS or official sovereign spread proxy.",
    },
    "orcl_cds": {
        "source_tier": "C",
        "raw_formula": "-ORCL adjusted close from yfinance as temporary inverse proxy.",
        "stress_direction": "higher_is_worse after inversion",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Not actual Oracle CDS; single equity proxy is not sufficient for AI/cloud credit risk.",
        "upgrade_plan": "Replace with actual CDS or basket of cloud/AI credit spreads and bond OAS.",
    },
}


def build_node_data_dictionary() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for node_id, node in CORE_NODES.items():
        override = NODE_DATA_OVERRIDES.get(node_id, {})
        result[node_id] = {
            "node_id": node_id,
            "display_name": node.display_name,
            "economic_meaning": node.description,
            "asset_class": node.asset_class.value,
            "geography": node.geography,
            "declared_data_source": node.data_source,
            "update_frequency": node.update_frequency,
            "unit": node.unit,
            "source_tier": override.get("source_tier", "B" if node.data_source == "yfinance" else "D"),
            "raw_formula": override.get("raw_formula", "Direct latest value from declared data source."),
            "stress_direction": override.get("stress_direction", "see model configuration"),
            "absolute_threshold": override.get("absolute_threshold", "not yet defined"),
            "known_limitations": override.get("known_limitations", "Requires formal review."),
            "upgrade_plan": override.get("upgrade_plan", "Document source quality and add replacement plan."),
        }
    return result


NODE_DATA_DICTIONARY = build_node_data_dictionary()

