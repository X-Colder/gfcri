from __future__ import annotations

import csv
import hashlib
import io
import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from psycopg2.extras import Json, RealDictCursor

from api.models.institutional_workspace import ApiKeyRequest, MemberRequest, WorkspaceProfileRequest
from api.routers.auth import require_institutional_user
from api.security import institutional_context, require_permission
from src.storage.database import get_connection
from src.storage.institutional_schema import ensure_institutional_schema

router = APIRouter(prefix="/v1/institutional", tags=["institutional-workspace"])


def _context(user: dict) -> dict:
    return institutional_context(user)


@router.get("/workspace")
def get_workspace(user=Depends(require_institutional_user)):
    context = _context(user)
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                SELECT workspace_key, name, profile, created_at
                FROM institutional_workspaces
                WHERE organization_id = %s
                ORDER BY id
                LIMIT 1
                """,
                (context["organization_id"],),
            )
            workspace = dict(cur.fetchone() or {})
            cur.execute(
                """
                SELECT u.email, u.display_name, m.role, m.status, m.created_at
                FROM institutional_memberships m
                JOIN users u ON u.id = m.user_id
                WHERE m.organization_id = %s
                ORDER BY m.created_at
                """,
                (context["organization_id"],),
            )
            members = [dict(row) for row in cur.fetchall()]
            return {
                "organization": context,
                "workspace": workspace,
                "members": members,
            }
    finally:
        conn.close()


@router.put("/workspace/profile")
def update_workspace_profile(
    req: WorkspaceProfileRequest,
    user=Depends(require_institutional_user),
):
    context = _context(user)
    require_permission(context, "organization:write")
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                INSERT INTO institutional_workspaces (organization_id, workspace_key, name, profile)
                VALUES (%s, 'default', %s, %s)
                ON CONFLICT (organization_id, workspace_key)
                DO UPDATE SET name = EXCLUDED.name, profile = EXCLUDED.profile
                RETURNING workspace_key, name, profile, created_at
                """,
                (context["organization_id"], req.name, Json(req.profile)),
            )
            workspace = dict(cur.fetchone())
            conn.commit()
            return workspace
    finally:
        conn.close()


@router.get("/members")
def list_members(user=Depends(require_institutional_user)):
    return get_workspace(user)["members"]


@router.post("/members", status_code=201)
def add_member(req: MemberRequest, user=Depends(require_institutional_user)):
    context = _context(user)
    require_permission(context, "members:write")
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_institutional_schema(conn)
            cur.execute("SELECT id, email, display_name FROM users WHERE lower(email) = lower(%s)", (req.email,))
            member = cur.fetchone()
            if not member:
                raise HTTPException(status_code=404, detail="User must register before being added")
            cur.execute(
                """
                INSERT INTO institutional_memberships (organization_id, user_id, role, status)
                VALUES (%s, %s, %s, 'active')
                ON CONFLICT (organization_id, user_id)
                DO UPDATE SET role = EXCLUDED.role, status = 'active'
                RETURNING organization_id, user_id, role, status
                """,
                (context["organization_id"], member["id"], req.role),
            )
            row = dict(cur.fetchone())
            conn.commit()
            return {**row, "email": member["email"], "display_name": member["display_name"]}
    finally:
        conn.close()


@router.post("/api-keys", status_code=201)
def create_api_key(req: ApiKeyRequest, user=Depends(require_institutional_user)):
    context = _context(user)
    require_permission(context, "keys:write")
    token = f"gfcri_{secrets.token_urlsafe(32)}"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    prefix = token[:14]
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                INSERT INTO institutional_api_keys (organization_id, label, key_prefix, token_hash)
                VALUES (%s, %s, %s, %s)
                RETURNING id, label, key_prefix, created_at
                """,
                (context["organization_id"], req.label, prefix, token_hash),
            )
            key = dict(cur.fetchone())
            conn.commit()
            return {**key, "token": token}
    finally:
        conn.close()


@router.post("/api-keys/{key_id}/revoke")
def revoke_api_key(key_id: int, user=Depends(require_institutional_user)):
    context = _context(user)
    require_permission(context, "keys:write")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                UPDATE institutional_api_keys
                SET revoked_at = NOW()
                WHERE id = %s AND organization_id = %s AND revoked_at IS NULL
                """,
                (key_id, context["organization_id"]),
            )
            if cur.rowcount != 1:
                raise HTTPException(status_code=404, detail="API key not found")
            conn.commit()
            return {"status": "revoked", "id": key_id}
    finally:
        conn.close()


@router.get("/observations.csv")
def export_observations(user=Depends(require_institutional_user)):
    context = _context(user)
    require_permission(context, "raw-data:export")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                SELECT entity_type, entity_id, metric_id, value, unit, as_of,
                       frequency, source_id, source_tier, quality_status, snapshot_id
                FROM institutional_observations
                WHERE tenant_id = %s
                ORDER BY as_of DESC, entity_type, entity_id, metric_id
                """,
                (context["tenant_id"],),
            )
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                [
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
                    "snapshot_id",
                ]
            )
            writer.writerows(cur.fetchall())
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=gfcri_observations.csv"},
            )
    finally:
        conn.close()
