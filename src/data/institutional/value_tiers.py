"""Institutional value-layer access policies.

The institution pays for derived evidence, workflow depth, and delivery
governance. Raw observations remain an internal input and are never exposed
through the value-layer analysis contract.
"""

from __future__ import annotations

from typing import Any


VALUE_LAYER_VERSION = "gfcri-institutional-value-v1"
PRODUCT_TIERS = ("research", "team", "private")

_TIER_POLICIES: dict[str, dict[str, Any]] = {
    "research": {
        "name": "Research",
        "max_contributors": 5,
        "max_transmission_paths": 3,
        "include_path_nodes": False,
        "include_source_tiers": False,
        "include_formula_receipt": False,
        "include_quality_breakdown": False,
        "include_custom_overlay": False,
        "include_full_hidden_details": False,
    },
    "team": {
        "name": "Team",
        "max_contributors": 10,
        "max_transmission_paths": 8,
        "include_path_nodes": True,
        "include_source_tiers": True,
        "include_formula_receipt": True,
        "include_quality_breakdown": True,
        "include_custom_overlay": True,
        "include_full_hidden_details": True,
    },
    "private": {
        "name": "Private",
        "max_contributors": 25,
        "max_transmission_paths": 20,
        "include_path_nodes": True,
        "include_source_tiers": True,
        "include_formula_receipt": True,
        "include_quality_breakdown": True,
        "include_custom_overlay": True,
        "include_full_hidden_details": True,
    },
}


def normalize_product_tier(value: str | None) -> str:
    tier = str(value or "research").strip().lower()
    if tier not in PRODUCT_TIERS:
        raise ValueError(f"unsupported product_tier: {tier}")
    return tier


def product_tier_policy(value: str | None) -> dict[str, Any]:
    tier = normalize_product_tier(value)
    return {"id": tier, **_TIER_POLICIES[tier]}


def value_layer_manifest() -> dict[str, Any]:
    return {
        "version": VALUE_LAYER_VERSION,
        "tiers": [
            {
                "id": tier,
                "name": policy["name"],
                "raw_observations_exposed": False,
                "derived_evidence": True,
                "max_contributors": policy["max_contributors"],
                "max_transmission_paths": policy["max_transmission_paths"],
                "includes": [
                    key.removeprefix("include_").replace("_", " ")
                    for key, enabled in policy.items()
                    if key.startswith("include_") and enabled
                ],
            }
            for tier, policy in _TIER_POLICIES.items()
        ],
        "commercial_principle": (
            "Pricing changes coverage, evidence depth, workflow customization, "
            "and delivery governance; it does not create a different risk truth."
        ),
    }


def apply_visibility_policy(
    evidence: dict[str, Any],
    product_tier: str | None,
) -> dict[str, Any]:
    """Redact the derived evidence contract according to the paid tier.

    This function intentionally never adds raw observation values. The
    analysis engine may use raw values internally, but the customer-facing
    result only contains normalized scores, contributions, quality and
    workflow guidance.
    """

    policy = product_tier_policy(product_tier)
    output = dict(evidence)
    output["product_tier"] = policy["id"]
    output["value_layer_version"] = VALUE_LAYER_VERSION
    output["delivery"] = {
        "raw_observations_exposed": False,
        "derived_evidence_exposed": True,
        "private_deployment": policy["id"] == "private",
        "custom_overlay": policy["include_custom_overlay"],
    }

    output["contributors"] = list(output.get("contributors") or [])[
        : policy["max_contributors"]
    ]
    output["transmission_paths"] = list(
        output.get("transmission_paths") or []
    )[: policy["max_transmission_paths"]]

    if not policy["include_path_nodes"]:
        for path in output["transmission_paths"]:
            path.pop("path", None)
            path.pop("node_scores", None)

    if not policy["include_source_tiers"]:
        for contributor in output["contributors"]:
            contributor.pop("source_tier", None)

    if not policy["include_quality_breakdown"]:
        quality = dict(output.get("data_quality") or {})
        for key in ("source_tier_mix", "source_quality_score", "freshness_detail"):
            quality.pop(key, None)
        output["data_quality"] = quality

    hidden = dict(output.get("hidden_risk") or {})
    if not policy["include_full_hidden_details"]:
        hidden.pop("details", None)
        hidden.pop("patterns", None)
    output["hidden_risk"] = hidden

    if not policy["include_formula_receipt"]:
        output.pop("formula_receipt", None)

    return output
