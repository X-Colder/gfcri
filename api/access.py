from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException

from api.routers.auth import get_current_user
from src.security.entitlements import has_entitlement


def check_entitlement(user: dict | None, entitlement: str) -> dict:
    if not user:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "AUTH_REQUIRED",
                "message": "Not authenticated",
            },
        )
    if not has_entitlement(user, entitlement):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "ENTITLEMENT_REQUIRED",
                "entitlement": entitlement,
                "message": "This capability requires an active subscription.",
            },
        )
    return user


def require_entitlement(entitlement: str) -> Callable:
    def dependency(user=Depends(get_current_user)):
        return check_entitlement(user, entitlement)

    return dependency


require_deep_analysis = require_entitlement("deep_analysis")
require_institutional_data = require_entitlement("institutional_data")
