from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping
from typing import Any

from src.security.entitlements import has_entitlement


def _base_sub_index_details(details: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    visible: dict[str, dict[str, Any]] = {}
    for key, value in (details or {}).items():
        if not isinstance(value, Mapping):
            continue
        visible[key] = {
            "name": value.get("name"),
            "score": value.get("score"),
            "top_driver": value.get("top_driver"),
        }
    return visible


def visible_risk_index(data: Mapping[str, Any], user: Mapping[str, Any] | None) -> dict[str, Any]:
    result = deepcopy(dict(data))
    if has_entitlement(user, "deep_analysis"):
        return result

    result["sub_index_details"] = _base_sub_index_details(data.get("sub_index_details"))
    result["active_chains"] = []
    result["chain_details"] = []
    result["coherence_multiplier"] = None
    result["node_contributions"] = None
    result["divergence"] = None
    result["undercurrent_boost"] = None

    trade_spillover = data.get("trade_spillover") or {}
    result["trade_spillover"] = {
        "score": trade_spillover.get("score"),
        "top_links": [],
    }
    result["trade_spillover_boost"] = None
    return result
