import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor

from src.security.passwords import hash_password, verify_password
from src.security.sessions import (
    hash_session_token,
    new_session_token,
    session_expiry,
)
from src.security.entitlements import build_entitlements
from src.storage.database import get_connection
from src.storage.institutional_schema import ensure_institutional_schema

router = APIRouter(prefix="/auth", tags=["auth"])

LEGACY_JWT_SECRET = os.environ.get("JWT_SECRET")
MAX_LOGIN_FAILURES = 5
LOCKOUT_MINUTES = 15


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str = ""
    lang: str = "zh"
    account_type: str = "personal"


class LoginRequest(BaseModel):
    email: str
    password: str


def _iso(dt) -> str | None:
    if not dt:
        return None
    if isinstance(dt, str):
        return dt
    if getattr(dt, "tzinfo", None) is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _trial_active(user: dict) -> bool:
    expires = user.get("trial_expires_at")
    if not expires:
        return False
    try:
        expires_dt = (
            datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if isinstance(expires, str)
            else expires
        )
    except ValueError:
        return False
    if expires_dt.tzinfo is None:
        expires_dt = expires_dt.replace(tzinfo=timezone.utc)
    return expires_dt > datetime.now(timezone.utc)


def _effective_plan(user: dict) -> str:
    if user.get("plan") == "pro":
        return "pro"
    if _trial_active(user):
        return "trial"
    return "free"


def _account_type(user: dict) -> str:
    account_type = str(user.get("account_type") or "personal").lower()
    return "institutional" if account_type == "institutional" else "personal"


def _requested_account_type(value: str) -> str:
    if str(value or "").lower() == "institutional" and os.getenv(
        "ALLOW_INSTITUTIONAL_SELF_REGISTER", ""
    ).lower() in ("1", "true", "yes"):
        return "institutional"
    return "personal"


def _user_payload(user: dict) -> dict:
    entitlements = build_entitlements(user)
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user.get("display_name") or "",
        "account_type": _account_type(user),
        "plan": _effective_plan(user),
        "status": user.get("status", "active"),
        "email_verified": bool(user.get("email_verified_at")),
        "trial_started_at": _iso(user.get("trial_started_at")),
        "trial_expires_at": _iso(user.get("trial_expires_at")),
        "institutional_access": entitlements["institutional_access"],
        "institutional_memberships": user.get("institutional_memberships", []),
        "access_level": entitlements["access_level"],
        "entitlements": entitlements["entitlements"],
    }


def _ensure_auth_schema(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                display_name VARCHAR(100),
                account_type VARCHAR(20) NOT NULL DEFAULT 'personal',
                plan VARCHAR(20) NOT NULL DEFAULT 'free',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                email_verified_at TIMESTAMPTZ,
                failed_login_count INTEGER NOT NULL DEFAULT 0,
                locked_until TIMESTAMPTZ,
                password_changed_at TIMESTAMPTZ,
                last_login_at TIMESTAMPTZ,
                trial_started_at TIMESTAMPTZ,
                trial_expires_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS account_type VARCHAR(20) NOT NULL DEFAULT 'personal'"
        )
        cur.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR(20) NOT NULL DEFAULT 'free'"
        )
        cur.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active'"
        )
        cur.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ"
        )
        cur.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_count INTEGER NOT NULL DEFAULT 0"
        )
        cur.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ"
        )
        cur.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ"
        )
        cur.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ"
        )
        cur.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMPTZ"
        )
        cur.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMPTZ"
        )
        cur.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_sessions (
                token_hash VARCHAR(128) PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMPTZ NOT NULL,
                last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                revoked_at TIMESTAMPTZ,
                ip_address VARCHAR(128),
                user_agent TEXT
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id, expires_at DESC)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_active ON auth_sessions(expires_at, revoked_at)"
        )
    conn.commit()


def _issue_session(cur, user_id: int, ip_address: str | None = None, user_agent: str | None = None):
    token = new_session_token()
    created_at = datetime.now(timezone.utc)
    expires_at = session_expiry(created_at)
    cur.execute(
        """
        INSERT INTO auth_sessions
            (token_hash, user_id, created_at, expires_at, last_seen_at, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            hash_session_token(token),
            user_id,
            created_at,
            expires_at,
            created_at,
            ip_address,
            (user_agent or "")[:1000],
        ),
    )
    return token, expires_at
def _create_token(
    user_id: int,
    email: str,
    plan: str,
    trial_expires_at: str | None = None,
    account_type: str = "personal",
) -> str:
    """Issue a session token for legacy billing-status callers."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _ensure_auth_schema(conn)
            token, _ = _issue_session(cur, user_id)
            conn.commit()
            return token
    finally:
        conn.close()




def _legacy_password_matches(password: str, encoded: str) -> bool:
    if not LEGACY_JWT_SECRET or not encoded:
        return False
    legacy = hashlib.sha256(
        (password + LEGACY_JWT_SECRET).encode("utf-8")
    ).hexdigest()
    return hmac.compare_digest(legacy, encoded)


def _resolve_session(token: str) -> dict | None:
    if not token.startswith("gfcri_sess_"):
        return None
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_auth_schema(conn)
            ensure_institutional_schema(conn)
            cur.execute(
                """
                SELECT s.token_hash, s.expires_at, u.*,
                       EXISTS (
                           SELECT 1
                           FROM institutional_memberships im
                           WHERE im.user_id = u.id AND im.status = 'active'
                       ) AS has_institutional_membership
                FROM auth_sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = %s
                  AND s.revoked_at IS NULL
                  AND s.expires_at > NOW()
                  AND u.status = 'active'
                """,
                (hash_session_token(token),),
            )
            row = cur.fetchone()
            if not row:
                return None
            cur.execute(
                """
                SELECT o.id, o.org_key, o.name, m.role,
                       o.subscription_status, o.subscription_plan,
                       o.subscription_current_period_end
                FROM institutional_memberships m
                JOIN institutional_organizations o ON o.id = m.organization_id
                WHERE m.user_id = %s AND m.status = 'active'
                ORDER BY o.id
                """,
                (row["id"],),
            )
            memberships = [
                {
                    "organization_id": int(item["id"]),
                    "org_key": item["org_key"],
                    "name": item["name"],
                    "role": item["role"],
                    "subscription_status": item["subscription_status"] or "active",
                    "subscription_plan": item["subscription_plan"] or "team",
                    "subscription_current_period_end": item["subscription_current_period_end"].isoformat() if item["subscription_current_period_end"] else None,
                }
                for item in cur.fetchall()
            ]
            cur.execute(
                "UPDATE auth_sessions SET last_seen_at = NOW() WHERE token_hash = %s",
                (hash_session_token(token),),
            )
            conn.commit()
            user = dict(row)
            user["user_id"] = user["id"]
            user["auth_method"] = "native"
            user["session_token_hash"] = hash_session_token(token)
            user["institutional_memberships"] = memberships
            user["has_institutional_membership"] = bool(memberships)
            return user
    finally:
        conn.close()


def get_current_user(authorization: str = Header(default="")) -> dict | None:
    if not authorization.startswith("Bearer "):
        return None
    return _resolve_session(authorization[7:])


def get_current_user_or_api_key(
    authorization: str = Header(default=""),
    x_api_key: str = Header(default="", alias="X-API-Key"),
    x_organization_id: str = Header(default="", alias="X-Organization-ID"),
) -> dict | None:
    requested_organization_id = None
    if x_organization_id:
        try:
            requested_organization_id = int(x_organization_id)
        except ValueError:
            return None

    user = get_current_user(authorization)
    if user:
        if requested_organization_id is not None:
            user["organization_id"] = requested_organization_id
        return user
    if not x_api_key:
        return None

    token_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_auth_schema(conn)
            ensure_institutional_schema(conn)
            cur.execute(
                """
                SELECT k.id AS api_key_id, o.id AS organization_id,
                       o.owner_user_id, u.email, u.display_name,
                       u.account_type, u.status, k.scopes, k.expires_at,
                       o.subscription_status, o.subscription_plan,
                       o.subscription_current_period_end
                FROM institutional_api_keys k
                JOIN institutional_organizations o ON o.id = k.organization_id
                JOIN users u ON u.id = o.owner_user_id
                WHERE k.token_hash = %s
                  AND k.revoked_at IS NULL
                  AND (k.expires_at IS NULL OR k.expires_at > NOW())
                  AND u.status = 'active'
                """,
                (token_hash,),
            )
            row = cur.fetchone()
            if not row:
                return None
            cur.execute(
                "UPDATE institutional_api_keys SET last_used_at = NOW() WHERE id = %s",
                (row["api_key_id"],),
            )
            conn.commit()
            if (
                requested_organization_id is not None
                and requested_organization_id != int(row["organization_id"])
            ):
                return None
            return {
                "user_id": row["owner_user_id"],
                "email": row["email"],
                "display_name": row["display_name"],
                "account_type": "institutional",
                "status": row["status"],
                "organization_id": row["organization_id"],
                "role": "api",
                "auth_method": "api_key",
                "api_key_id": row["api_key_id"],
                "institutional_memberships": [{
                    "organization_id": row["organization_id"],
                    "subscription_status": row["subscription_status"] or "active",
                    "subscription_plan": row["subscription_plan"] or "team",
                    "subscription_current_period_end": row["subscription_current_period_end"].isoformat() if row["subscription_current_period_end"] else None,
                }],
                "api_key_scopes": list(row.get("scopes") or []),
            }
    finally:
        conn.close()


def require_institutional_user(user=Depends(get_current_user_or_api_key)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if user.get("status", "active") != "active":
        raise HTTPException(status_code=403, detail="Account is not active")
    if not build_entitlements(user)["institutional_access"]:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "INSTITUTIONAL_SUBSCRIPTION_REQUIRED",
                "message": "An active institutional subscription is required.",
            },
        )
    return user


@router.post("/register")
def register(req: RegisterRequest):
    email = req.email.strip().lower()
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_auth_schema(conn)
            cur.execute("SELECT id FROM users WHERE lower(email) = %s", (email,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Email already registered")
            try:
                password_hash = hash_password(req.password)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            name = req.display_name.strip() or email.split("@")[0]
            account_type = _requested_account_type(req.account_type)
            cur.execute(
                """
                INSERT INTO users
                    (email, password_hash, display_name, account_type,
                     password_changed_at)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING *
                """,
                (email, password_hash, name, account_type),
            )
            user = dict(cur.fetchone())
            token, expires_at = _issue_session(cur, user["id"])
            conn.commit()
            user["id"] = user["id"]
            return {
                "token": token,
                "expires_at": _iso(expires_at),
                "user": _user_payload(user),
            }
    finally:
        conn.close()


@router.post("/login")
def login(req: LoginRequest):
    email = req.email.strip().lower()
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_auth_schema(conn)
            cur.execute("SELECT * FROM users WHERE lower(email) = %s", (email,))
            user = dict(cur.fetchone() or {})
            if not user:
                raise HTTPException(status_code=401, detail="Invalid email or password")

            locked_until = user.get("locked_until")
            if locked_until and locked_until > datetime.now(timezone.utc):
                raise HTTPException(status_code=429, detail="Account temporarily locked")

            stored_hash = str(user.get("password_hash") or "")
            valid = verify_password(req.password, stored_hash)
            if not valid and _legacy_password_matches(req.password, stored_hash):
                valid = True
                cur.execute(
                    """
                    UPDATE users
                    SET password_hash = %s, password_changed_at = NOW()
                    WHERE id = %s
                    """,
                    (hash_password(req.password), user["id"]),
                )

            if not valid:
                next_failures = int(user.get("failed_login_count") or 0) + 1
                lock_until = (
                    datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
                    if next_failures >= MAX_LOGIN_FAILURES
                    else None
                )
                cur.execute(
                    """
                    UPDATE users
                    SET failed_login_count = %s, locked_until = %s
                    WHERE id = %s
                    """,
                    (next_failures, lock_until, user["id"]),
                )
                conn.commit()
                raise HTTPException(status_code=401, detail="Invalid email or password")

            cur.execute(
                """
                UPDATE users
                SET failed_login_count = 0, locked_until = NULL, last_login_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                (user["id"],),
            )
            updated = dict(cur.fetchone())
            token, expires_at = _issue_session(cur, updated["id"])
            conn.commit()
            return {
                "token": token,
                "expires_at": _iso(expires_at),
                "user": _user_payload(updated),
            }
    finally:
        conn.close()


@router.post("/logout")
def logout(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token_hash = user.get("session_token_hash")
    if token_hash:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                _ensure_auth_schema(conn)
                cur.execute(
                    """
                    UPDATE auth_sessions
                    SET revoked_at = NOW()
                    WHERE token_hash = %s AND revoked_at IS NULL
                    """,
                    (token_hash,),
                )
                conn.commit()
        finally:
            conn.close()
    return {"status": "logged_out"}


@router.get("/me")
def get_me(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _user_payload(user)


@router.post("/trial/start")
def start_trial(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if _account_type(user) == "institutional":
        raise HTTPException(
            status_code=400,
            detail="Institutional account does not use personal trial flow",
        )

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_auth_schema(conn)
            cur.execute("SELECT * FROM users WHERE id = %s", (user["user_id"],))
            current = dict(cur.fetchone() or {})
            if not current:
                raise HTTPException(status_code=404, detail="User not found")
            if current.get("plan") == "pro":
                token, expires_at = _issue_session(cur, current["id"])
                conn.commit()
                return {
                    "token": token,
                    "expires_at": _iso(expires_at),
                    "user": _user_payload(current),
                }
            if current.get("trial_started_at"):
                if _trial_active(current):
                    token, expires_at = _issue_session(cur, current["id"])
                    conn.commit()
                    return {
                        "token": token,
                        "expires_at": _iso(expires_at),
                        "user": _user_payload(current),
                    }
                raise HTTPException(status_code=400, detail="Trial already used")

            cur.execute(
                """
                UPDATE users
                SET plan = 'trial',
                    trial_started_at = NOW(),
                    trial_expires_at = NOW() + INTERVAL '7 days'
                WHERE id = %s
                RETURNING *
                """,
                (current["id"],),
            )
            updated = dict(cur.fetchone())
            token, expires_at = _issue_session(cur, updated["id"])
            conn.commit()
            return {
                "token": token,
                "expires_at": _iso(expires_at),
                "user": _user_payload(updated),
            }
    finally:
        conn.close()
