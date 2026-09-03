from __future__ import annotations

import json
import os
import secrets
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from psycopg2.extras import Json, RealDictCursor

from api.models.oidc import OIDCProviderRequest
from api.routers.auth import (
    _ensure_auth_schema,
    _issue_session,
    _user_payload,
    get_current_user,
    require_institutional_user,
)
from api.security import institutional_context, require_permission
from src.security.audit import build_audit_event
from src.security.oidc import (
    OIDCConfig,
    build_authorization_url,
    new_oidc_transaction,
    normalize_issuer,
    validate_oidc_claims,
)
from src.security.passwords import hash_password
from src.storage.database import get_connection
from src.storage.institutional_schema import ensure_institutional_schema

router = APIRouter(tags=["oidc"])


def _json_request(url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "OIDC_PROVIDER_UNAVAILABLE", "message": str(exc)},
        ) from exc


def _discovery(issuer: str) -> dict:
    base = normalize_issuer(issuer)
    return _json_request(f"{base}/.well-known/openid-configuration")


def _verify_id_token(
    token: str,
    *,
    jwks_uri: str,
    issuer: str,
    client_id: str,
) -> dict:
    try:
        from authlib.jose import JsonWebKey, jwt
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="OIDC verification dependency is not installed",
        ) from exc

    jwks = _json_request(jwks_uri)
    try:
        key_set = JsonWebKey.import_key_set(jwks)
        claims = jwt.decode(token, key_set)
        claims.validate()
        return dict(claims)
    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail={"code": "OIDC_ID_TOKEN_INVALID", "message": str(exc)},
        ) from exc


def _audit(cur, *, organization_id: int, user: dict, action: str, target_id: str, metadata: dict):
    event = build_audit_event(
        organization_id=organization_id,
        actor_user_id=user.get("user_id"),
        actor_type=user.get("auth_method", "native"),
        action=action,
        target_type="identity",
        target_id=target_id,
        outcome="success",
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


@router.post("/api/v1/institutional/identity-provider")
def configure_oidc_provider(
    req: OIDCProviderRequest,
    user=Depends(require_institutional_user),
):
    context = institutional_context(user)
    require_permission(context, "identity:write")
    issuer = normalize_issuer(req.issuer)
    if not issuer.startswith("https://"):
        raise HTTPException(status_code=422, detail="OIDC issuer must use HTTPS")
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_auth_schema(conn)
            ensure_institutional_schema(conn)
            cur.execute(
                """
                INSERT INTO institutional_identity_providers
                    (organization_id, protocol, issuer, client_id, client_secret_env,
                     redirect_uri, scopes, allowed_domains, default_role, enabled)
                VALUES (%s, 'oidc', %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (organization_id)
                DO UPDATE SET
                    issuer = EXCLUDED.issuer,
                    client_id = EXCLUDED.client_id,
                    client_secret_env = EXCLUDED.client_secret_env,
                    redirect_uri = EXCLUDED.redirect_uri,
                    scopes = EXCLUDED.scopes,
                    allowed_domains = EXCLUDED.allowed_domains,
                    default_role = EXCLUDED.default_role,
                    enabled = EXCLUDED.enabled,
                    updated_at = NOW()
                RETURNING id, organization_id, protocol, issuer, client_id,
                          redirect_uri, scopes, allowed_domains, default_role,
                          enabled, updated_at
                """,
                (
                    context["organization_id"],
                    issuer,
                    req.client_id,
                    req.client_secret_env,
                    req.redirect_uri,
                    Json(req.scopes),
                    Json([domain.lower().lstrip("@") for domain in req.allowed_domains]),
                    req.default_role,
                    req.enabled,
                ),
            )
            provider = dict(cur.fetchone())
            _audit(
                cur,
                organization_id=context["organization_id"],
                user=user,
                action="identity_provider.configure",
                target_id=str(provider["id"]),
                metadata={"protocol": "oidc", "enabled": req.enabled},
            )
            conn.commit()
            return provider
    finally:
        conn.close()


@router.get("/api/auth/oidc/{org_key}/start")
def start_oidc_login(org_key: str):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_auth_schema(conn)
            ensure_institutional_schema(conn)
            cur.execute(
                """
                SELECT p.*, o.id AS organization_id, o.org_key
                FROM institutional_identity_providers p
                JOIN institutional_organizations o ON o.id = p.organization_id
                WHERE o.org_key = %s AND p.enabled = TRUE AND p.protocol = 'oidc'
                """,
                (org_key,),
            )
            provider = cur.fetchone()
            if not provider:
                raise HTTPException(status_code=404, detail="OIDC provider not configured")
            discovery = _discovery(provider["issuer"])
            transaction = new_oidc_transaction()
            redirect_uri = provider["redirect_uri"]
            cur.execute(
                """
                INSERT INTO auth_transactions
                    (state_hash, organization_id, provider_id, nonce, code_verifier,
                     redirect_uri, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    transaction["state_hash"],
                    provider["organization_id"],
                    provider["id"],
                    transaction["nonce"],
                    transaction["code_verifier"],
                    redirect_uri,
                    datetime.now(timezone.utc) + timedelta(minutes=10),
                ),
            )
            conn.commit()
            config = OIDCConfig(
                issuer=provider["issuer"],
                client_id=provider["client_id"],
                authorization_endpoint=discovery["authorization_endpoint"],
                token_endpoint=discovery["token_endpoint"],
                redirect_uri=redirect_uri,
                scopes=tuple(provider["scopes"] or ["openid", "email", "profile"]),
                allowed_domains=tuple(provider["allowed_domains"] or []),
            )
            return RedirectResponse(
                build_authorization_url(
                    config,
                    state=transaction["state"],
                    nonce=transaction["nonce"],
                    code_challenge=transaction["code_challenge"],
                )
            )
    finally:
        conn.close()


@router.get("/api/auth/oidc/{org_key}/callback")
def oidc_callback(
    org_key: str,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
):
    if error:
        raise HTTPException(status_code=401, detail={"code": "OIDC_LOGIN_DENIED", "error": error})
    if not code or not state:
        raise HTTPException(status_code=400, detail="OIDC code and state are required")

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_auth_schema(conn)
            ensure_institutional_schema(conn)
            state_hash = __import__("hashlib").sha256(state.encode("utf-8")).hexdigest()
            cur.execute(
                """
                SELECT t.*, p.*, o.org_key
                FROM auth_transactions t
                JOIN institutional_identity_providers p ON p.id = t.provider_id
                JOIN institutional_organizations o ON o.id = t.organization_id
                WHERE t.state_hash = %s
                  AND t.expires_at > NOW()
                  AND o.org_key = %s
                  AND p.enabled = TRUE
                """,
                (state_hash, org_key),
            )
            transaction = cur.fetchone()
            if not transaction:
                raise HTTPException(status_code=400, detail="OIDC state is invalid or expired")

            discovery = _discovery(transaction["issuer"])
            secret = os.getenv(transaction["client_secret_env"])
            if not secret:
                raise HTTPException(
                    status_code=503,
                    detail="OIDC client secret environment variable is not configured",
                )
            token_payload = _json_request(
                discovery["token_endpoint"],
                {
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": transaction["client_id"],
                    "client_secret": secret,
                    "redirect_uri": transaction["redirect_uri"],
                    "code_verifier": transaction["code_verifier"],
                },
            )
            id_token = token_payload.get("id_token")
            if not id_token:
                raise HTTPException(status_code=401, detail="OIDC provider did not return an id_token")
            claims = _verify_id_token(
                id_token,
                jwks_uri=discovery["jwks_uri"],
                issuer=transaction["issuer"],
                client_id=transaction["client_id"],
            )
            identity = validate_oidc_claims(
                claims,
                issuer=transaction["issuer"],
                client_id=transaction["client_id"],
                nonce=transaction["nonce"],
                allowed_domains=tuple(transaction["allowed_domains"] or []),
            )

            cur.execute(
                """
                SELECT user_id
                FROM external_identities
                WHERE issuer = %s AND subject = %s
                """,
                (normalize_issuer(transaction["issuer"]), identity["subject"]),
            )
            linked = cur.fetchone()
            if linked:
                user_id = linked["user_id"]
                cur.execute("SELECT status FROM users WHERE id = %s", (user_id,))
                linked_user = cur.fetchone()
                if not linked_user or linked_user["status"] != "active":
                    raise HTTPException(status_code=403, detail="Linked account is not active")
                cur.execute(
                    """
                    UPDATE institutional_memberships
                    SET status = 'active'
                    WHERE organization_id = %s AND user_id = %s
                    """,
                    (transaction["organization_id"], user_id),
                )
                cur.execute(
                    """
                    UPDATE external_identities
                    SET last_login_at = NOW(), email = %s
                    WHERE issuer = %s AND subject = %s
                    """,
                    (
                        identity["email"],
                        normalize_issuer(transaction["issuer"]),
                        identity["subject"],
                    ),
                )
            else:
                cur.execute(
                    "SELECT * FROM users WHERE lower(email) = %s",
                    (identity["email"],),
                )
                existing = dict(cur.fetchone() or {})
                if existing and existing.get("status") != "active":
                    raise HTTPException(status_code=403, detail="Linked account is not active")
                if existing:
                    user_id = existing["id"]
                    cur.execute(
                        """
                        UPDATE users
                        SET email_verified_at = COALESCE(email_verified_at, NOW())
                        WHERE id = %s
                        """,
                        (user_id,),
                    )
                else:
                    random_password = hash_password(secrets.token_urlsafe(48))
                    cur.execute(
                        """
                        INSERT INTO users
                            (email, password_hash, display_name, account_type,
                             status, email_verified_at, password_changed_at)
                        VALUES (%s, %s, %s, 'institutional', 'active', NOW(), NOW())
                        RETURNING id
                        """,
                        (
                            identity["email"],
                            random_password,
                            identity["display_name"],
                        ),
                    )
                    user_id = cur.fetchone()["id"]

                cur.execute(
                    """
                    INSERT INTO institutional_memberships
                        (organization_id, user_id, role, status)
                    VALUES (%s, %s, %s, 'active')
                    ON CONFLICT (organization_id, user_id)
                    DO UPDATE SET status = 'active'
                    """,
                    (
                        transaction["organization_id"],
                        user_id,
                        transaction["default_role"],
                    ),
                )
                cur.execute(
                    """
                    INSERT INTO external_identities
                        (organization_id, user_id, issuer, subject, email, claims)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (issuer, subject)
                    DO UPDATE SET last_login_at = NOW(), email = EXCLUDED.email,
                                  claims = EXCLUDED.claims
                    """,
                    (
                        transaction["organization_id"],
                        user_id,
                        normalize_issuer(transaction["issuer"]),
                        identity["subject"],
                        identity["email"],
                        Json(
                            {
                                "iss": claims.get("iss"),
                                "sub": claims.get("sub"),
                                "aud": claims.get("aud"),
                                "email": claims.get("email"),
                                "name": claims.get("name"),
                            }
                        ),
                    ),
                )

            cur.execute(
                "SELECT * FROM users WHERE id = %s",
                (user_id,),
            )
            user = dict(cur.fetchone())
            token, expires_at = _issue_session(cur, user_id)
            cur.execute(
                "DELETE FROM auth_transactions WHERE state_hash = %s",
                (state_hash,),
            )
            _audit(
                cur,
                organization_id=transaction["organization_id"],
                user={
                    "user_id": user_id,
                    "auth_method": "oidc",
                },
                action="identity.login",
                target_id=identity["subject"],
                metadata={"issuer": normalize_issuer(transaction["issuer"])},
            )
            conn.commit()
            return {
                "token": token,
                "expires_at": expires_at.isoformat(),
                "user": _user_payload(user),
                "organization_id": transaction["organization_id"],
                "auth_method": "oidc",
            }
    finally:
        conn.close()
