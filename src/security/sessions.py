"""Opaque server-side session token helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone


SESSION_TTL_SECONDS = 60 * 60 * 12


def new_session_token() -> str:
    return f"gfcri_sess_{secrets.token_urlsafe(32)}"


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_expiry(
    created_at: datetime | None = None,
    ttl_seconds: int = SESSION_TTL_SECONDS,
) -> datetime:
    created = created_at or datetime.now(timezone.utc)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return created + timedelta(seconds=ttl_seconds)
