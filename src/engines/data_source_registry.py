"""Unified data-source registry for GFCRI.

This registry is an operational inventory: it shows what sources are connected,
where they are used, whether they affect the core GFCRI model, and what the
current readiness state is. It is intentionally separate from scoring logic.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from src.engines.data_quality import OFFICIAL_UPGRADE_CATALOG, data_quality_assessment
from src.engines.market_data_freshness import market_data_freshness
from src.engines.trade_data import trade_source_health, trade_sources
from src.models.data_dictionary import NODE_DATA_DICTIONARY
from src.storage.database import get_institutional_radar_source_health


def _source_status_from_health(items: list[dict[str, Any]], source_id: str, default: str) -> str:
    match = next((item for item in items if item.get("source_id") == source_id), None)
    return str(match.get("status")) if match else default


def _source_health_item(items: list[dict[str, Any]], source_id: str) -> dict[str, Any] | None:
    return next((item for item in items if item.get("source_id") == source_id), None)


def _node_source_summary() -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node_id, entry in NODE_DATA_DICTIONARY.items():
        grouped[str(entry.get("declared_data_source") or "unknown")].append({
            "node_id": node_id,
            "display_name": entry.get("display_name") or node_id,
            "source_tier": entry.get("source_tier") or "D",
            "update_frequency": entry.get("update_frequency") or "unknown",
        })

    result = []
    for source_id, nodes in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        tiers = Counter(str(node["source_tier"]) for node in nodes)
        result.append({
            "source_id": f"model_{source_id}",
            "name": source_id,
            "node_count": len(nodes),
            "tier_counts": dict(tiers),
            "sample_nodes": nodes[:8],
        })
    return result


def data_source_overview() -> dict[str, Any]:
    quality = data_quality_assessment()
    freshness = {}
    freshness_status = "unknown"
    try:
        freshness = market_data_freshness()
        freshness_status = str(freshness.get("status") or "unknown")
    except Exception as exc:
        freshness = {"status": "error", "error": str(exc)}
        freshness_status = "error"

    try:
        radar_health = get_institutional_radar_source_health()
    except Exception:
        radar_health = []

    trade_health = trade_source_health(refresh=False)
    trade_registry = trade_sources()

    model_sources = _node_source_summary()
    source_cards: list[dict[str, Any]] = [
        {
            "source_id": "market_data_daily_cache",
            "name": "Market data daily cache",
            "provider": "GFCRI local Postgres cache",
            "category": "market_cache",
            "tier": "system",
            "status": freshness_status,
            "source_type": "internal_cache",
            "access_mode": "local_db",
            "update_frequency": "daily",
            "official": False,
            "affects_core_gfcri": True,
            "used_by": ["GFCRI core scoring", "EHS", "Dashboard", "Commercial readiness"],
            "domains": ["market closes", "volumes", "freshness gate"],
            "latest_observation": freshness.get("latest_trade_date"),
            "coverage_pct": freshness.get("coverage_pct"),
            "limitations": "Cache quality depends on upstream market connectors and import schedule.",
            "next_step": "Add vendor-grade market data connector for production deployments.",
            "health": freshness,
        },
        {
            "source_id": "model_node_dictionary",
            "name": "GFCRI node data dictionary",
            "provider": "GFCRI model registry",
            "category": "model_registry",
            "tier": "system",
            "status": "active",
            "source_type": "internal_registry",
            "access_mode": "version_control",
            "update_frequency": "on_model_change",
            "official": False,
            "affects_core_gfcri": True,
            "used_by": ["Methodology", "Audit", "Commercial readiness"],
            "domains": ["node provenance", "source tiers", "limitations", "upgrade plans"],
            "latest_observation": None,
            "coverage_pct": quality.get("tier_a_b_share"),
            "limitations": "Documents source quality but does not itself guarantee vendor rights.",
            "next_step": "Attach signed-off data-rights status and production source owner.",
            "health": {
                "node_count": quality.get("node_count"),
                "source_tier_counts": quality.get("source_tier_counts"),
            },
        },
    ]

    for item in trade_registry:
        health = _source_health_item(trade_health, item["source_id"])
        source_cards.append({
            "source_id": item["source_id"],
            "name": item["name"],
            "provider": item["provider"],
            "category": "trade",
            "tier": item["tier"],
            "status": health.get("status") if health else item["status"],
            "source_type": item["source_type"],
            "access_mode": item["access_mode"],
            "update_frequency": item["update_frequency"],
            "official": True,
            "affects_core_gfcri": item["affects_core_gfcri"],
            "used_by": list(item["used_by"]),
            "domains": list(item["domains"]),
            "latest_observation": health.get("latest_period") if health else None,
            "coverage_pct": None,
            "limitations": item["limitations"],
            "next_step": item["next_step"],
            "url": item["url"],
            "health": health or {},
        })

    for item in radar_health:
        source_cards.append({
            "source_id": f"radar_{item.get('source_id')}",
            "name": item.get("source_name"),
            "provider": item.get("source_name"),
            "category": "institutional_radar",
            "tier": item.get("source_tier"),
            "status": item.get("status"),
            "source_type": "public_metadata_feed",
            "access_mode": "rss_or_public_metadata",
            "update_frequency": "on_refresh",
            "official": True,
            "affects_core_gfcri": False,
            "used_by": ["Institutional Radar", "Core themes context"],
            "domains": ["official reports", "macro policy metadata", "risk themes"],
            "latest_observation": item.get("last_success_at"),
            "coverage_pct": None,
            "limitations": "Stores metadata and links, not full copyrighted report text.",
            "next_step": "Add source rights review and richer taxonomy mapping.",
            "url": item.get("url"),
            "health": item,
        })

    status_counts = Counter(str(item.get("status") or "unknown") for item in source_cards)
    category_counts = Counter(str(item.get("category") or "unknown") for item in source_cards)
    core_count = sum(1 for item in source_cards if item.get("affects_core_gfcri"))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.2",
        "summary": {
            "source_count": len(source_cards),
            "core_source_count": core_count,
            "standalone_source_count": len(source_cards) - core_count,
            "status_counts": dict(status_counts),
            "category_counts": dict(category_counts),
            "tier_a_b_share": quality.get("tier_a_b_share"),
        },
        "sources": source_cards,
        "model_node_sources": model_sources,
        "upgrade_catalog": list(OFFICIAL_UPGRADE_CATALOG.values()),
        "governance": {
            "trade_affects_core_gfcri": False,
            "principle": "New data domains can be registered, refreshed and analyzed before they are promoted into core GFCRI scoring.",
            "promotion_gate": "A source must have stable ingestion, freshness checks, data-rights review, methodology notes and backtest evidence before affecting core scoring.",
        },
    }
