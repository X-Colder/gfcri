"""Data-source depth and reliability assessment for GFCRI."""

from __future__ import annotations

from collections import Counter
from typing import Any

from src.models.data_dictionary import NODE_DATA_DICTIONARY, SOURCE_TIERS


OFFICIAL_UPGRADE_CATALOG: dict[str, dict[str, Any]] = {
    "point_in_time": {
        "name": "Point-in-time / vintage macro data",
        "sources": ["ALFRED", "FRED vintages", "OECD SDMX revisions"],
        "value": "Prevents backtests from accidentally using data revisions that were not known at the historical date.",
        "priority": "P0",
    },
    "global_liquidity": {
        "name": "Global liquidity and cross-border credit",
        "sources": ["BIS Global Liquidity Indicators", "BIS locational banking statistics", "BIS international debt securities"],
        "value": "Improves dollar funding, offshore credit, and cross-border contagion coverage.",
        "priority": "P0",
    },
    "financial_soundness": {
        "name": "Banking system soundness",
        "sources": ["IMF Financial Soundness Indicators", "national regulators", "central bank balance-sheet statistics"],
        "value": "Adds bank capital, NPL, profitability, and liquidity buffers instead of relying only on market proxies.",
        "priority": "P1",
    },
    "trade_dependency": {
        "name": "Dynamic trade and supply-chain exposure",
        "sources": ["UN Comtrade", "OECD TiVA", "WTO", "national customs"],
        "value": "Turns the static trade-spillover matrix into a calibrated exposure model.",
        "priority": "P1",
    },
    "market_microstructure": {
        "name": "Funding and positioning microstructure",
        "sources": ["CFTC positioning", "cross-currency basis", "repo specials", "options skew"],
        "value": "Improves hidden-risk detection when headline prices look calm.",
        "priority": "P2",
    },
}


def data_quality_assessment() -> dict[str, Any]:
    tier_counts = Counter(str(v.get("source_tier") or "D") for v in NODE_DATA_DICTIONARY.values())
    node_count = len(NODE_DATA_DICTIONARY)
    low_tier_nodes = []
    for node_id, entry in NODE_DATA_DICTIONARY.items():
        tier = str(entry.get("source_tier") or "D")
        limitations = str(entry.get("known_limitations") or "")
        formula = str(entry.get("raw_formula") or "")
        if tier in {"C", "D"} or "proxy" in limitations.lower() or "proxy" in formula.lower():
            low_tier_nodes.append({
                "node_id": node_id,
                "display_name": entry.get("display_name") or node_id,
                "source_tier": tier,
                "data_source": entry.get("declared_data_source") or "unknown",
                "limitation": limitations,
                "upgrade_plan": entry.get("upgrade_plan") or "",
            })
    low_tier_nodes.sort(key=lambda x: (x["source_tier"], x["node_id"]), reverse=True)
    return {
        "node_count": node_count,
        "source_tiers": SOURCE_TIERS,
        "source_tier_counts": dict(tier_counts),
        "tier_a_b_share": round(100 * (tier_counts.get("A", 0) + tier_counts.get("B", 0)) / max(node_count, 1), 1),
        "low_tier_or_proxy_nodes": low_tier_nodes[:20],
        "upgrade_catalog": list(OFFICIAL_UPGRADE_CATALOG.values()),
        "point_in_time_readiness": {
            "status": "designed_not_complete",
            "current_gap": "Most current nodes can be scored, but not every historical replay is guaranteed to use vintage-only observations.",
            "target": "Backtests should record data vintage, release timestamp, observation date, and revision policy for every official macro series.",
        },
        "next_implementation_steps": [
            "Add ALFRED vintage fetchers for FRED macro series used in backtests.",
            "Add BIS GLI and cross-border banking connectors for global dollar credit.",
            "Add IMF FSI connectors for banking-system health and country-level buffers.",
            "Attach data confidence score to each node and down-weight low-tier proxies in institutional mode.",
        ],
    }
