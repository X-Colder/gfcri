from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from typing import Any, Mapping

MODEL_VERSION = "gfcri-institutional-v1"
ENTITY_TYPES = ("country", "economy", "company", "security", "portfolio")
ACTIVE_ENTITY_TYPES = ("country", "economy")
FREQUENCIES = ("intraday", "daily", "weekly", "monthly", "quarterly", "annual")
SOURCE_TIERS = ("official", "licensed", "internal_verified", "proxy", "unverified")
QUALITY_STATUSES = ("verified", "degraded", "missing", "rejected")

_SOURCE_TIER_ALIASES = {
    "official": "official",
    "fred": "official",
    "government": "official",
    "licensed": "licensed",
    "internal": "internal_verified",
    "internal_verified": "internal_verified",
    "proxy": "proxy",
    "unverified": "unverified",
}


def model_manifest() -> dict[str, Any]:
    return {
        "model_version": MODEL_VERSION,
        "entity_types": list(ENTITY_TYPES),
        "active_entity_types": list(ACTIVE_ENTITY_TYPES),
        "frequencies": list(FREQUENCIES),
        "source_tiers": list(SOURCE_TIERS),
        "quality_statuses": list(QUALITY_STATUSES),
        "observation_fields": [
            "tenant_id",
            "entity_type",
            "entity_id",
            "metric_id",
            "value",
            "unit",
            "as_of",
            "frequency",
            "source_id",
            "source_tier",
            "quality_status",
            "ingested_at",
        ],
    }


def _text(payload: Mapping[str, Any], key: str, minimum: int = 1, maximum: int = 255) -> str:
    value = str(payload.get(key) or "").strip()
    if not minimum <= len(value) <= maximum:
        raise ValueError(f"{key} must contain {minimum}-{maximum} characters")
    return value


def _parse_date(value: Any, key: str) -> str:
    text = _text({key: value}, key, 10, 40)
    try:
        if "T" in text:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return parsed.date().isoformat()
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise ValueError(f"{key} must be an ISO date") from exc


def normalize_observation(payload: Mapping[str, Any]) -> dict[str, Any]:
    tenant_id = _text(payload, "tenant_id", 2, 120)
    entity_type = _text(payload, "entity_type", 2, 40).lower()
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"unsupported entity_type: {entity_type}")

    entity_id = _text(payload, "entity_id", 1, 160)
    metric_id = _text(payload, "metric_id", 2, 160)
    unit = _text(payload, "unit", 1, 60)
    frequency = _text(payload, "frequency", 3, 20).lower()
    if frequency not in FREQUENCIES:
        raise ValueError(f"unsupported frequency: {frequency}")

    try:
        numeric_value = float(payload.get("value"))
    except (TypeError, ValueError) as exc:
        raise ValueError("value must be numeric") from exc
    if not math.isfinite(numeric_value):
        raise ValueError("value must be finite")

    source_id = _text(payload, "source_id", 1, 160)
    source_tier = _SOURCE_TIER_ALIASES.get(
        str(payload.get("source_tier") or payload.get("quality_tier") or payload.get("source_type") or "").lower()
    )
    if not source_tier:
        source_tier = _SOURCE_TIER_ALIASES.get(source_id.lower(), "unverified")
    quality_status = str(payload.get("quality_status") or "verified").strip().lower()
    if quality_status not in QUALITY_STATUSES:
        raise ValueError(f"unsupported quality_status: {quality_status}")

    ingested_at = payload.get("ingested_at")
    if ingested_at:
        ingested_at = datetime.fromisoformat(str(ingested_at).replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    else:
        ingested_at = datetime.now(timezone.utc).isoformat()

    return {
        "tenant_id": tenant_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "metric_id": metric_id,
        "value": numeric_value,
        "unit": unit,
        "as_of": _parse_date(payload.get("as_of"), "as_of"),
        "frequency": frequency,
        "source_id": source_id,
        "source_tier": source_tier,
        "quality_status": quality_status,
        "ingested_at": ingested_at,
    }


def summarize_quality(
    observations: list[Mapping[str, Any]],
    *,
    as_of: str,
    stale_after_days: int = 7,
) -> dict[str, Any]:
    reference_date = date.fromisoformat(as_of)
    stale_cutoff = reference_date - timedelta(days=stale_after_days)
    degraded_count = 0
    stale_count = 0
    for observation in observations:
        if observation.get("quality_status") in {"degraded", "missing", "rejected"}:
            degraded_count += 1
        try:
            observation_date = date.fromisoformat(str(observation.get("as_of")))
            if observation_date < stale_cutoff:
                stale_count += 1
        except ValueError:
            stale_count += 1

    status = "degraded" if degraded_count or stale_count else "verified"
    return {
        "status": status,
        "observation_count": len(observations),
        "degraded_count": degraded_count,
        "stale_count": stale_count,
        "coverage": 0 if not observations else round(
            (len(observations) - degraded_count - stale_count) / len(observations),
            4,
        ),
        "as_of": reference_date.isoformat(),
    }
