from __future__ import annotations

from typing import Any

from src.storage.institutional_schema import ensure_institutional_schema


def select_organization_id(
    membership_ids: list[int],
    requested_id: int | None,
) -> int:
    normalized = [int(value) for value in membership_ids]
    if requested_id is not None:
        requested = int(requested_id)
        if requested not in normalized:
            raise ValueError("Requested organization is not an active membership")
        return requested
    if len(normalized) == 1:
        return normalized[0]
    if not normalized:
        raise ValueError("No active institutional organization membership")
    raise ValueError("Organization context is required for multiple memberships")


def ensure_tenant_context(conn, user: dict[str, Any]) -> dict[str, Any]:
    ensure_institutional_schema(conn)
    user_id = int(user["user_id"])
    requested_id = user.get("organization_id")
    display_name = str(user.get("display_name") or "").strip()
    email = str(user.get("email") or "").strip()
    default_name = display_name or (
        email.split("@", 1)[0] if "@" in email else f"Organization {user_id}"
    )
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT o.id, o.org_key, o.name, m.role
            FROM institutional_memberships m
            JOIN institutional_organizations o ON o.id = m.organization_id
            WHERE m.user_id = %s AND m.status = 'active'
            ORDER BY o.id
            """,
            (user_id,),
        )
        memberships = cur.fetchall()
        membership_ids = [int(row[0]) for row in memberships]
        try:
            organization_id = select_organization_id(membership_ids, requested_id)
        except ValueError:
            if membership_ids or requested_id is not None:
                raise
            cur.execute(
                """
                INSERT INTO institutional_organizations (org_key, name, owner_user_id)
                VALUES (%s, %s, %s)
                RETURNING id, org_key, name
                """,
                (f"user-{user_id}", default_name, user_id),
            )
            organization_id, org_key, organization_name = cur.fetchone()
            cur.execute(
                """
                INSERT INTO institutional_memberships
                    (organization_id, user_id, role, status)
                VALUES (%s, %s, 'owner', 'active')
                """,
                (organization_id, user_id),
            )
            cur.execute(
                """
                INSERT INTO institutional_workspaces
                    (organization_id, workspace_key, name, profile)
                VALUES (%s, 'default', %s, '{}'::jsonb)
                ON CONFLICT (organization_id, workspace_key) DO NOTHING
                """,
                (organization_id, f"{organization_name} Risk Workspace"),
            )
            conn.commit()
            return {
                "tenant_id": f"org:{organization_id}",
                "organization_id": organization_id,
                "org_key": org_key,
                "organization_name": organization_name,
                "role": "owner",
            }

        selected = next(row for row in memberships if int(row[0]) == organization_id)
        return {
            "tenant_id": f"org:{selected[0]}",
            "organization_id": selected[0],
            "org_key": selected[1],
            "organization_name": selected[2],
            "role": selected[3],
        }


def is_admin(role: str | None) -> bool:
    return str(role or "").lower() in {"owner", "admin"}
