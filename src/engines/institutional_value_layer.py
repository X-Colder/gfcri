"""Institution-facing derived risk evidence.

This module turns the core GFCRI result and optional tenant observations into
an institution-readable evidence contract. It deliberately keeps raw
observation values inside the calculation boundary. The customer-facing
result contains normalized risk evidence, quality, provenance class, and
workflow guidance instead.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from src.data.institutional.contracts import MODEL_VERSION
from src.data.institutional.value_tiers import (
    VALUE_LAYER_VERSION,
    apply_visibility_policy,
    normalize_product_tier,
    product_tier_policy,
)
from src.models.data_dictionary import NODE_DATA_DICTIONARY


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return round(max(low, min(high, float(value))), 2)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _risk_level(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 55:
        return "elevated"
    return "contained"


def _direct_overlay(
    observations: list[Mapping[str, Any]],
) -> tuple[float | None, list[dict[str, Any]]]:
    direct = [
        observation
        for observation in observations
        if observation.get("metric_id") in {"risk.pressure_score", "risk.score"}
    ]
    if not direct:
        return None, []

    values = [_clamp(_number(item.get("value"))) for item in direct]
    overlay = _clamp(sum(values) / len(values))
    drivers = [
        {
            "metric_id": item.get("metric_id"),
            "pressure_score": value,
            "quality_status": item.get("quality_status", "verified"),
            "source_tier": item.get("source_tier", "unverified"),
            "as_of": item.get("as_of"),
            "evidence_type": "tenant_derived_pressure_overlay",
        }
        for item, value in zip(direct, values)
    ]
    return overlay, drivers


def _domain_details(core_risk: Mapping[str, Any]) -> list[dict[str, Any]]:
    sub_indices = core_risk.get("sub_index_details") or {}
    rows: list[dict[str, Any]] = []
    for domain_id, raw in sub_indices.items():
        if not isinstance(raw, Mapping) or "score" not in raw:
            continue
        node_scores = raw.get("node_scores") or {}
        rows.append(
            {
                "domain_id": domain_id,
                "name": raw.get("name") or domain_id,
                "score": _clamp(_number(raw.get("score"))),
                "mean_stress": round(_number(raw.get("mean_stress")), 4),
                "mean_absolute_stress": round(
                    _number(raw.get("mean_abs_stress")), 4
                ),
                "transmission": round(_number(raw.get("transmission")), 4),
                "top_driver": raw.get("top_driver"),
                "evidence_count": len(node_scores) if isinstance(node_scores, Mapping) else 0,
            }
        )

    if not rows:
        scalar_domains = (
            ("SI_RATES", "Rates"),
            ("SI_FX", "FX"),
            ("SI_EQUITY", "Equities"),
            ("SI_CREDIT", "Credit"),
            ("SI_SENTIMENT", "Sentiment"),
        )
        for domain_id, name in scalar_domains:
            key = domain_id.lower().replace("si_", "si_")
            if key in core_risk:
                rows.append(
                    {
                        "domain_id": domain_id,
                        "name": name,
                        "score": _clamp(_number(core_risk.get(key))),
                        "mean_stress": None,
                        "mean_absolute_stress": None,
                        "transmission": None,
                        "top_driver": None,
                        "evidence_count": 0,
                    }
                )

    total = sum(_number(row["score"]) for row in rows) or 1.0
    for row in rows:
        row["contribution_share"] = round(_number(row["score"]) / total, 4)
    rows.sort(key=lambda row: row["score"], reverse=True)
    return rows


def _contributor_interpretation(
    anomaly_score: float,
    absolute_score: float | None,
) -> str:
    if absolute_score is None:
        return "Directional anomaly is the available evidence."
    if absolute_score > anomaly_score + 0.1:
        return "Absolute stress is stronger than recent deviation."
    if anomaly_score > absolute_score + 0.1:
        return "Recent deterioration is stronger than absolute stress."
    return "Directional and absolute stress are broadly aligned."


def _contributors(core_risk: Mapping[str, Any]) -> list[dict[str, Any]]:
    node_contributions = core_risk.get("node_contributions") or {}
    if not isinstance(node_contributions, Mapping):
        return []

    rows: list[dict[str, Any]] = []
    for node_id, raw in node_contributions.items():
        if not isinstance(raw, Mapping):
            continue
        anomaly = max(0.0, min(1.0, _number(raw.get("anomaly_score"))))
        absolute = raw.get("abs_score")
        absolute_score = (
            max(0.0, min(1.0, _number(absolute)))
            if absolute is not None
            else None
        )
        stress_score = (
            0.4 * anomaly + 0.6 * absolute_score
            if absolute_score is not None
            else anomaly
        )
        dictionary = NODE_DATA_DICTIONARY.get(node_id, {})
        rows.append(
            {
                "metric_id": node_id,
                "display_name": raw.get("display_name")
                or dictionary.get("display_name")
                or node_id,
                "stress_score": round(stress_score * 100, 2),
                "anomaly_score": round(anomaly, 4),
                "absolute_stress_score": (
                    round(absolute_score, 4) if absolute_score is not None else None
                ),
                "direction": raw.get("stress_direction")
                or ("above" if _number(raw.get("zscore")) > 0 else "below"),
                "source_tier": dictionary.get("source_tier", "unverified"),
                "evidence_type": (
                    "directional_anomaly+absolute_stress"
                    if absolute_score is not None
                    else "directional_anomaly"
                ),
                "interpretation": _contributor_interpretation(
                    anomaly, absolute_score
                ),
            }
        )

    rows.sort(key=lambda row: row["stress_score"], reverse=True)
    total = sum(_number(row["stress_score"]) for row in rows) or 1.0
    for row in rows:
        row["contribution_share"] = round(
            _number(row["stress_score"]) / total, 4
        )
    return rows


def _transmission_paths(core_risk: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_paths = core_risk.get("chain_details")
    if not raw_paths:
        raw_paths = core_risk.get("chains")
    if isinstance(raw_paths, Mapping):
        raw_paths = list(raw_paths.values())
    if not isinstance(raw_paths, list):
        return []

    paths: list[dict[str, Any]] = []
    for raw in raw_paths:
        if not isinstance(raw, Mapping):
            continue
        stress = _clamp(_number(raw.get("stress")))
        paths.append(
            {
                "path_id": raw.get("id"),
                "name": raw.get("name") or raw.get("id"),
                "stress": stress,
                "active": bool(raw.get("active", stress > 40)),
                "path_strength": round(_number(raw.get("path_strength")), 4),
                "path": list(raw.get("path") or []),
                "node_scores": dict(raw.get("node_scores") or {}),
                "interpretation": (
                    "Active monitored transmission channel."
                    if bool(raw.get("active", stress > 40))
                    else "Observed channel remains below the active threshold."
                ),
            }
        )
    paths.sort(key=lambda row: row["stress"], reverse=True)
    return paths


def _hidden_risk(core_risk: Mapping[str, Any]) -> dict[str, Any]:
    divergence = core_risk.get("divergence") or {}
    status = str(divergence.get("status") or "none")
    gap = round(_number(divergence.get("gap")), 4)
    undercurrent = round(_number(core_risk.get("undercurrent_boost")), 2)
    active_chains = int(_number(core_risk.get("active_chain_count")))
    details = list(divergence.get("details") or [])
    patterns = [
        detail.get("type")
        for detail in details
        if isinstance(detail, Mapping) and detail.get("type")
    ]

    if status == "none" and not patterns and undercurrent <= 0:
        summary = "No material surface/deep divergence is currently recorded."
    elif status in {"significant", "critical"}:
        summary = (
            "Deep or structural pressure is materially higher than surface "
            "conditions and requires confirmation monitoring."
        )
    else:
        summary = (
            "Some undercurrent pressure is present; the next review should "
            "test whether it normalizes or broadens across channels."
        )

    return {
        "status": status,
        "summary": summary,
        "surface_deep_gap": gap,
        "undercurrent_points": undercurrent,
        "active_chain_count": active_chains,
        "patterns": patterns,
        "details": details,
    }


def _quality_output(
    data_quality: Mapping[str, Any],
    contributors: list[Mapping[str, Any]],
) -> dict[str, Any]:
    status = str(data_quality.get("status") or "degraded")
    coverage = max(0.0, min(1.0, _number(data_quality.get("coverage"))))
    source_tiers = Counter(
        str(row.get("source_tier") or "unverified")
        for row in contributors
    )
    quality_weights = {
        "A": 1.0,
        "B": 0.8,
        "C": 0.55,
        "D": 0.3,
        "official": 1.0,
        "licensed": 1.0,
        "internal_verified": 0.95,
        "proxy": 0.65,
        "unverified": 0.3,
    }
    weighted_source_score = 0.0
    total = sum(source_tiers.values()) or 1
    for tier, count in source_tiers.items():
        weighted_source_score += quality_weights.get(tier, 0.3) * count / total

    return {
        **dict(data_quality),
        "status": status,
        "coverage": round(coverage, 4),
        "source_tier_mix": dict(source_tiers),
        "source_quality_score": round(weighted_source_score, 4),
        "freshness_detail": {
            "stale_count": int(_number(data_quality.get("stale_count"))),
            "degraded_count": int(_number(data_quality.get("degraded_count"))),
        },
    }


def _confidence(
    data_quality: Mapping[str, Any],
    contributors: list[Mapping[str, Any]],
    domains: list[Mapping[str, Any]],
) -> dict[str, Any]:
    status = str(data_quality.get("status") or "degraded")
    status_score = {
        "verified": 1.0,
        "degraded": 0.6,
        "empty": 0.25,
    }.get(status, 0.4)
    coverage = max(0.0, min(1.0, _number(data_quality.get("coverage"))))
    evidence_score = min(1.0, len(contributors) / 8.0) if contributors else 0.25
    domain_score = min(1.0, len(domains) / 6.0) if domains else 0.25
    score = 100 * (
        0.45 * status_score
        + 0.25 * coverage
        + 0.15 * evidence_score
        + 0.15 * domain_score
    )
    return {
        "score": round(score, 2),
        "label": (
            "high" if score >= 75 else "moderate" if score >= 50 else "low"
        ),
        "basis": [
            "data quality status",
            "observation coverage",
            "derived contributor evidence",
            "risk-domain coverage",
        ],
    }


def _watch_next(
    quality: Mapping[str, Any],
    hidden: Mapping[str, Any],
    contributors: list[Mapping[str, Any]],
    paths: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    watch: list[dict[str, Any]] = []
    if quality.get("status") != "verified":
        watch.append(
            {
                "priority": "high",
                "trigger": "data_quality",
                "question": "Can critical inputs be refreshed and verified?",
                "reason": "Do not interpret a degraded or held reading as unchanged risk.",
            }
        )
    if hidden.get("status") not in {"none", ""}:
        watch.append(
            {
                "priority": "high",
                "trigger": "hidden_risk_confirmation",
                "question": "Do deep indicators normalize or does surface stress catch up?",
                "reason": hidden.get("summary"),
            }
        )
    if contributors:
        top = contributors[0]
        watch.append(
            {
                "priority": "medium",
                "trigger": "top_contributor",
                "question": f"Does {top.get('display_name')} confirm or reverse?",
                "reason": top.get("interpretation"),
            }
        )
    active_paths = [path for path in paths if path.get("active")]
    if active_paths:
        path = active_paths[0]
        watch.append(
            {
                "priority": "medium",
                "trigger": "transmission_confirmation",
                "question": f"Does the {path.get('name')} channel broaden?",
                "reason": path.get("interpretation"),
            }
        )
    return watch[:5]


def analyze_institutional_risk_evidence(
    *,
    target: Mapping[str, str],
    core_score: float,
    observations: list[Mapping[str, Any]],
    data_quality: Mapping[str, Any],
    core_risk: Mapping[str, Any] | None = None,
    product_tier: str = "research",
    parameters: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the derived institutional value layer.

    The function is deterministic and accepts the persisted GFCRI result as a
    mapping so it can be tested without a database or network dependency.
    """

    normalized_tier = normalize_product_tier(product_tier)
    policy = product_tier_policy(normalized_tier)
    core = dict(core_risk or {})
    overlay, direct_drivers = _direct_overlay(observations)
    base_score = _clamp(core_score)
    risk_score = _clamp(
        base_score if overlay is None else base_score * 0.7 + overlay * 0.3
    )

    domains = _domain_details(core)
    contributors = _contributors(core)
    paths = _transmission_paths(core)
    hidden = _hidden_risk(core)
    quality_input = dict(data_quality)
    if overlay is None or str(quality_input.get("status") or "") == "empty":
        quality_input["status"] = "degraded"
    quality = _quality_output(quality_input, contributors)
    confidence = _confidence(quality, contributors, domains)

    derived = {
        "target": {
            "entity_type": target["entity_type"],
            "entity_id": target["entity_id"],
        },
        "risk_score": risk_score,
        "risk_level": _risk_level(risk_score),
        "dimensions": {
            "gfcri_core": base_score,
            "target_overlay": overlay,
            "risk_domains": domains,
        },
        "drivers": direct_drivers,
        "contributors": contributors,
        "transmission_paths": paths,
        "hidden_risk": hidden,
        "watch_next": _watch_next(quality, hidden, contributors, paths),
        "confidence": confidence,
        "data_quality": quality,
        "algorithm": {
            "name": "GFCRI institutional derived risk evidence",
            "version": VALUE_LAYER_VERSION,
            "layers": [
                "directional anomaly",
                "absolute stress",
                "risk-domain contribution",
                "transmission channel",
                "hidden-risk divergence",
                "data-quality governance",
                "workflow watch-next",
            ],
        },
        "formula_receipt": {
            "score_blend": (
                "70% core GFCRI + 30% tenant-derived pressure overlay "
                "when a verified overlay is available"
            ),
            "node_evidence": (
                "0.4 directional anomaly + 0.6 absolute stress when both "
                "components are available"
            ),
            "institutional_value": (
                "derived evidence and workflow guidance; raw observations "
                "remain internal inputs"
            ),
        },
        "model_version": MODEL_VERSION,
        "value_layer_version": VALUE_LAYER_VERSION,
        "generated_at": None,
        "parameters": dict(parameters or {}),
    }
    return apply_visibility_policy(derived, policy["id"])
