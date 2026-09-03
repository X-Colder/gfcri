from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from psycopg2.extras import Json, RealDictCursor

from api.models.institutional_workspace import (
    ApiKeyRequest,
    InvitationAcceptRequest,
    InvitationRequest,
    MemberRequest,
    WorkspaceProfileRequest,
)
from api.routers.auth import get_current_user, require_institutional_user
from api.security import institutional_context, require_permission
from src.security.api_keys import hash_api_key, new_api_key
from src.security.audit import build_audit_event
from src.security.invitations import (
    hash_invitation_token,
    invitation_expiry,
    new_invitation_token,
)
from src.storage.database import get_connection
from src.storage.institutional_schema import ensure_institutional_schema

router = APIRouter(prefix="/v1/institutional", tags=["institutional-workspace"])

ALLOWED_API_KEY_SCOPES = {
    "data:read",
    "analysis:read",
    "analysis:run",
}


def _context(user: dict) -> dict:
    return institutional_context(user)


def _audit(
    cur,
    *,
    context: dict,
    user: dict,
    action: str,
    target_type: str,
    target_id: str | None,
    outcome: str,
    metadata: dict | None = None,
) -> None:
    event = build_audit_event(
        organization_id=context.get("organization_id"),
        actor_user_id=user.get("user_id"),
        actor_type=user.get("auth_method", "native"),
        action=action,
        target_type=target_type,
        target_id=target_id,
        outcome=outcome,
        request_id=user.get("request_id"),
        metadata=metadata,
    )
    cur.execute(
        """
        INSERT INTO institutional_audit_events
            (organization_id, actor_user_id, actor_type, action, target_type,
             target_id, outcome, request_id, metadata, occurred_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            event["organization_id"],
            event["actor_user_id"],
            event["actor_type"],
            event["action"],
            event["target_type"],
            event["target_id"],
            event["outcome"],
            event["request_id"],
            Json(event["metadata"]),
            event["occurred_at"],
        ),
    )


@router.get("/workspace")
def get_workspace(user=Depends(require_institutional_user)):
    context = _context(user)
    require_permission(context, "organization:read")
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
                SELECT u.id AS user_id, u.email, u.display_name, u.status AS user_status,
                       m.role, m.status, m.created_at
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
                INSERT INTO institutional_workspaces
                    (organization_id, workspace_key, name, profile)
                VALUES (%s, 'default', %s, %s)
                ON CONFLICT (organization_id, workspace_key)
                DO UPDATE SET name = EXCLUDED.name, profile = EXCLUDED.profile
                RETURNING workspace_key, name, profile, created_at
                """,
                (context["organization_id"], req.name, Json(req.profile)),
            )
            workspace = dict(cur.fetchone())
            _audit(
                cur,
                context=context,
                user=user,
                action="workspace.profile.update",
                target_type="workspace",
                target_id="default",
                outcome="success",
            )
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
            cur.execute(
                "SELECT id, email, display_name FROM users WHERE lower(email) = lower(%s)",
                (req.email,),
            )
            member = cur.fetchone()
            if not member:
                raise HTTPException(
                    status_code=404,
                    detail="User must register before being added",
                )
            cur.execute(
                """
                INSERT INTO institutional_memberships
                    (organization_id, user_id, role, status)
                VALUES (%s, %s, %s, 'active')
                ON CONFLICT (organization_id, user_id)
                DO UPDATE SET role = EXCLUDED.role, status = 'active'
                RETURNING organization_id, user_id, role, status
                """,
                (context["organization_id"], member["id"], req.role),
            )
            row = dict(cur.fetchone())
            _audit(
                cur,
                context=context,
                user=user,
                action="member.upsert",
                target_type="membership",
                target_id=str(member["id"]),
                outcome="success",
                metadata={"role": req.role},
            )
            conn.commit()
            return {
                **row,
                "email": member["email"],
                "display_name": member["display_name"],
            }
    finally:
        conn.close()


@router.post("/member-invitations", status_code=201)
def create_member_invitation(
    req: InvitationRequest,
    user=Depends(require_institutional_user),
):
    context = _context(user)
    require_permission(context, "members:write")
    token = new_invitation_token()
    expires_at = invitation_expiry()
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                INSERT INTO institutional_invitations
                    (organization_id, email, role, token_hash, invited_by_user_id, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, email, role, expires_at, created_at
                """,
                (
                    context["organization_id"],
                    req.email.strip().lower(),
                    req.role,
                    hash_invitation_token(token),
                    user["user_id"],
                    expires_at,
                ),
            )
            invitation = dict(cur.fetchone())
            _audit(
                cur,
                context=context,
                user=user,
                action="member.invite",
                target_type="invitation",
                target_id=str(invitation["id"]),
                outcome="created",
                metadata={"email": invitation["email"], "role": req.role},
            )
            conn.commit()
            return {
                **invitation,
                "token": token,
                "delivery": "operator_must_deliver_securely",
            }
    finally:
        conn.close()


@router.post("/member-invitations/accept")
def accept_member_invitation(
    req: InvitationAcceptRequest,
    user=Depends(get_current_user),
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                SELECT id, organization_id, email, role
                FROM institutional_invitations
                WHERE token_hash = %s
                  AND accepted_at IS NULL
                  AND revoked_at IS NULL
                  AND expires_at > NOW()
                """,
                (hash_invitation_token(req.token),),
            )
            invitation = cur.fetchone()
            if not invitation:
                raise HTTPException(
                    status_code=400,
                    detail="Invitation is invalid, expired, or already used",
                )
            if str(invitation["email"]).lower() != str(user["email"]).lower():
                raise HTTPException(
                    status_code=403,
                    detail="Invitation email does not match the authenticated account",
                )
            cur.execute(
                """
                INSERT INTO institutional_memberships
                    (organization_id, user_id, role, status)
                VALUES (%s, %s, %s, 'active')
                ON CONFLICT (organization_id, user_id)
                DO UPDATE SET role = EXCLUDED.role, status = 'active'
                """,
                (invitation["organization_id"], user["user_id"], invitation["role"]),
            )
            cur.execute(
                """
                UPDATE institutional_invitations
                SET accepted_at = NOW()
                WHERE id = %s
                """,
                (invitation["id"],),
            )
            _audit(
                cur,
                context={
                    "organization_id": invitation["organization_id"]
                },
                user=user,
                action="member.invite.accept",
                target_type="invitation",
                target_id=str(invitation["id"]),
                outcome="success",
                metadata={"role": invitation["role"]},
            )
            conn.commit()
            return {
                "status": "accepted",
                "organization_id": invitation["organization_id"],
                "role": invitation["role"],
            }
    finally:
        conn.close()


@router.post("/members/{member_user_id}/suspend")
def suspend_member(
    member_user_id: int,
    user=Depends(require_institutional_user),
):
    context = _context(user)
    require_permission(context, "members:write")
    if member_user_id == int(user["user_id"]):
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                UPDATE institutional_memberships
                SET status = 'suspended'
                WHERE organization_id = %s AND user_id = %s
                  AND role <> 'owner' AND status = 'active'
                """,
                (context["organization_id"], member_user_id),
            )
            if cur.rowcount != 1:
                raise HTTPException(status_code=404, detail="Active member not found")
            _audit(
                cur,
                context=context,
                user=user,
                action="member.suspend",
                target_type="membership",
                target_id=str(member_user_id),
                outcome="success",
            )
            conn.commit()
            return {"status": "suspended", "user_id": member_user_id}
    finally:
        conn.close()


@router.post("/api-keys", status_code=201)
def create_api_key(req: ApiKeyRequest, user=Depends(require_institutional_user)):
    context = _context(user)
    require_permission(context, "keys:write")
    invalid_scopes = sorted(set(req.scopes) - ALLOWED_API_KEY_SCOPES)
    if invalid_scopes:
        raise HTTPException(
            status_code=422,
            detail={"code": "UNSUPPORTED_API_KEY_SCOPE", "scopes": invalid_scopes},
        )
    token = new_api_key()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(days=req.expires_in_days)
        if req.expires_in_days
        else None
    )
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                INSERT INTO institutional_api_keys
                    (organization_id, label, key_prefix, token_hash, scopes, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, label, key_prefix, scopes, expires_at, created_at
                """,
                (
                    context["organization_id"],
                    req.label,
                    token[:14],
                    hash_api_key(token),
                    Json(req.scopes),
                    expires_at,
                ),
            )
            key = dict(cur.fetchone())
            _audit(
                cur,
                context=context,
                user=user,
                action="api_key.create",
                target_type="api_key",
                target_id=str(key["id"]),
                outcome="success",
                metadata={"scopes": req.scopes},
            )
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
                SET revoked_at = NOW(), revoked_by_user_id = %s
                WHERE id = %s AND organization_id = %s AND revoked_at IS NULL
                """,
                (user["user_id"], key_id, context["organization_id"]),
            )
            if cur.rowcount != 1:
                raise HTTPException(status_code=404, detail="API key not found")
            _audit(
                cur,
                context=context,
                user=user,
                action="api_key.revoke",
                target_type="api_key",
                target_id=str(key_id),
                outcome="success",
            )
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
            _audit(
                cur,
                context=context,
                user=user,
                action="raw_data.export",
                target_type="observations",
                target_id=context["tenant_id"],
                outcome="success",
            )
            conn.commit()
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": "attachment; filename=gfcri_observations.csv"
                },
            )
    finally:
        conn.close()
