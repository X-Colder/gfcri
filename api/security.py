from __future__ import annotations

from fastapi import HTTPException

from src.security.authorization import has_permission
from src.storage.database import get_connection
from src.storage.institutional_schema import ensure_institutional_schema
from src.storage.institutional_tenancy import ensure_tenant_context


def institutional_context(user: dict) -> dict:
    conn = get_connection()
    try:
        ensure_institutional_schema(conn)
        try:
            context = ensure_tenant_context(conn, user)
            if user.get("auth_method") == "api_key":
                context["role"] = "api"
                context["api_key_scopes"] = list(user.get("api_key_scopes") or [])
            return context
        except ValueError as exc:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "ORGANIZATION_CONTEXT_REQUIRED",
                    "message": str(exc),
                    "header": "X-Organization-ID",
                },
            ) from exc
    finally:
        conn.close()


def require_permission(context: dict, permission: str) -> None:
    role = context.get("role")
    allowed = (
        permission in set(context.get("api_key_scopes") or [])
        if role == "api"
        else has_permission(role, permission)
    )
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "INSTITUTIONAL_PERMISSION_REQUIRED",
                "permission": permission,
                "role": role,
            },
        )
