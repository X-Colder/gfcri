"""Explicit institutional role permissions."""

from __future__ import annotations


ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "owner": frozenset(
        {
            "organization:read",
            "organization:write",
            "members:read",
            "members:write",
            "identity:write",
            "data:read",
            "data:write",
            "analysis:read",
            "analysis:run",
            "reports:read",
            "reports:export",
            "keys:write",
            "raw-data:export",
        }
    ),
    "admin": frozenset(
        {
            "organization:read",
            "organization:write",
            "members:read",
            "members:write",
            "identity:write",
            "data:read",
            "data:write",
            "analysis:read",
            "analysis:run",
            "reports:read",
            "reports:export",
            "keys:write",
            "raw-data:export",
        }
    ),
    "analyst": frozenset(
        {
            "organization:read",
            "members:read",
            "data:read",
            "data:write",
            "analysis:read",
            "analysis:run",
            "reports:read",
        }
    ),
    "viewer": frozenset(
        {
            "organization:read",
            "members:read",
            "data:read",
            "analysis:read",
            "reports:read",
        }
    ),
    "api": frozenset({"data:read", "analysis:read", "analysis:run"}),
}


def has_permission(role: str | None, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(str(role or "").lower(), frozenset())
