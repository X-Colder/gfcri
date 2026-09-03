from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any


BASE_ENTITLEMENTS = ("basic_data", "basic_history")
PERSONAL_ENTITLEMENTS = BASE_ENTITLEMENTS + (
    "deep_analysis",
    "reports",
    "risk_alerts",
    "report_export",
)
INSTITUTIONAL_ENTITLEMENTS = PERSONAL_ENTITLEMENTS + (
    "institutional_data",
    "institutional_analysis",
    "workspace",
    "team_collaboration",
    "analysis_api",
    "audit_log",
)


def _subscription_active(membership: Mapping[str, Any]) -> bool:
    status = str(membership.get("subscription_status") or "active").lower()
    if status not in {"active", "trialing"}:
        return False
    period_end = membership.get("subscription_current_period_end")
    if not period_end:
        return True
    try:
        if isinstance(period_end, str):
            period_end = datetime.fromisoformat(period_end.replace("Z", "+00:00"))
        if period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=timezone.utc)
        return period_end > datetime.now(timezone.utc)
    except (TypeError, ValueError):
        return False


def _institutional_access(user: Mapping[str, Any] | None) -> bool:
    if not user:
        return False
    memberships = user.get("institutional_memberships")
    if memberships:
        return any(_subscription_active(item) for item in memberships)
    return bool(
        str(user.get("account_type") or "").lower() == "institutional"
        or user.get("institutional_access")
        or user.get("has_institutional_membership")
    )


def build_entitlements(user: Mapping[str, Any] | None) -> dict[str, Any]:
    if _institutional_access(user):
        return {
            "access_level": "institutional",
            "institutional_access": True,
            "entitlements": list(INSTITUTIONAL_ENTITLEMENTS),
        }

    if user and (
        str(user.get("plan") or "").lower() == "pro"
        or str(user.get("plan") or "").lower() == "trial"
    ):
        return {
            "access_level": "personal",
            "institutional_access": False,
            "entitlements": list(PERSONAL_ENTITLEMENTS),
        }

    return {
        "access_level": "free" if user else "anonymous",
        "institutional_access": False,
        "entitlements": list(BASE_ENTITLEMENTS),
    }


def has_entitlement(user: Mapping[str, Any] | None, key: str) -> bool:
    return key in set(build_entitlements(user)["entitlements"])
