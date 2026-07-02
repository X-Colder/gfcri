import hashlib
import hmac
import json
import time
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["auth"])

JWT_SECRET = os.environ.get("JWT_SECRET", "gfcri_secret_key_change_in_production")


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str = ""
    lang: str = "zh"


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
    if isinstance(expires, str):
        try:
            expires_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        except ValueError:
            return False
    else:
        expires_dt = expires
    if expires_dt.tzinfo is None:
        expires_dt = expires_dt.replace(tzinfo=timezone.utc)
    return expires_dt > datetime.now(timezone.utc)


def _effective_plan(user: dict) -> str:
    if user.get("plan") == "pro":
        return "pro"
    if _trial_active(user):
        return "trial"
    return "free"


def _user_payload(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user.get("display_name") or "",
        "plan": _effective_plan(user),
        "trial_started_at": _iso(user.get("trial_started_at")),
        "trial_expires_at": _iso(user.get("trial_expires_at")),
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
                plan VARCHAR(20) NOT NULL DEFAULT 'free',
                trial_started_at TIMESTAMPTZ,
                trial_expires_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR(20) NOT NULL DEFAULT 'free'")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMPTZ")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMPTZ")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    conn.commit()


def _hash_password(password: str) -> str:
    return hashlib.sha256((password + JWT_SECRET).encode()).hexdigest()


def _create_token(user_id: int, email: str, plan: str, trial_expires_at: str | None = None) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "plan": plan,
        "trial_expires_at": trial_expires_at,
        "exp": int(time.time()) + 86400 * 30,  # 30 days
    }
    data = json.dumps(payload, separators=(",", ":"))
    sig = hmac.new(JWT_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
    import base64
    token = base64.urlsafe_b64encode(data.encode()).decode() + "." + sig
    return token


def _verify_token(token: str) -> dict | None:
    try:
        import base64
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return None
        data = base64.urlsafe_b64decode(parts[0]).decode()
        sig = hmac.new(JWT_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
        if sig != parts[1]:
            return None
        payload = json.loads(data)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def get_current_user(authorization: str = Header(default="")) -> dict | None:
    if not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    return _verify_token(token)


@router.post("/register")
def register(req: RegisterRequest):
    from src.storage.database import get_connection
    from psycopg2.extras import RealDictCursor

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_auth_schema(conn)
            cur.execute("SELECT id FROM users WHERE email = %s", (req.email,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Email already registered")

            pw_hash = _hash_password(req.password)
            name = req.display_name or req.email.split("@")[0]
            cur.execute(
                "INSERT INTO users (email, password_hash, display_name) VALUES (%s, %s, %s) RETURNING id",
                (req.email, pw_hash, name),
            )
            user_id = cur.fetchone()["id"]
            conn.commit()

            user = {"id": user_id, "email": req.email, "display_name": name, "plan": "free"}
            token = _create_token(user_id, req.email, "free")
            return {"token": token, "user": _user_payload(user)}
    finally:
        conn.close()


@router.post("/login")
def login(req: LoginRequest):
    from src.storage.database import get_connection
    from psycopg2.extras import RealDictCursor

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_auth_schema(conn)
            cur.execute("SELECT * FROM users WHERE email = %s", (req.email,))
            row = cur.fetchone()
            user = dict(row) if row else None
            if not user or user["password_hash"] != _hash_password(req.password):
                raise HTTPException(status_code=401, detail="Invalid email or password")

            payload = _user_payload(user)
            token = _create_token(user["id"], user["email"], payload["plan"], payload.get("trial_expires_at"))
            return {"token": token, "user": payload}
    finally:
        conn.close()


@router.get("/me")
def get_me(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user_id": user["user_id"], "email": user["email"], "plan": user["plan"], "trial_expires_at": user.get("trial_expires_at")}


@router.post("/trial/start")
def start_trial(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from src.storage.database import get_connection
    from psycopg2.extras import RealDictCursor

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_auth_schema(conn)
            cur.execute("SELECT * FROM users WHERE id = %s", (user["user_id"],))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")

            current = dict(row)
            if current.get("plan") == "pro":
                payload = _user_payload(current)
                token = _create_token(current["id"], current["email"], payload["plan"], payload.get("trial_expires_at"))
                return {"token": token, "user": payload}

            if current.get("trial_started_at"):
                if _trial_active(current):
                    payload = _user_payload(current)
                    token = _create_token(current["id"], current["email"], payload["plan"], payload.get("trial_expires_at"))
                    return {"token": token, "user": payload}
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
                (user["user_id"],),
            )
            updated = dict(cur.fetchone())
            conn.commit()

            payload = _user_payload(updated)
            token = _create_token(updated["id"], updated["email"], payload["plan"], payload.get("trial_expires_at"))
            return {"token": token, "user": payload}
    finally:
        conn.close()
