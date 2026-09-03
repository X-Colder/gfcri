"""Structured audit event construction."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_audit_event(
    *,
    organization_id: int | None,
    actor_user_id: int | None,
    actor_type: str,
    action: str,
    target_type: str,
    target_id: str | None,
    outcome: str,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not action or not target_type:
        raise ValueError("action and target_type are required")
    return {
        "organization_id": organization_id,
        "actor_user_id": actor_user_id,
        "actor_type": actor_type,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "outcome": outcome,
        "request_id": request_id,
        "metadata": dict(metadata or {}),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }
