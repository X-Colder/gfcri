"""Invitation token helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone


INVITATION_TTL_SECONDS = 60 * 60 * 72


def new_invitation_token() -> str:
    return f"gfcri_inv_{secrets.token_urlsafe(32)}"


def hash_invitation_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def invitation_expiry(
    created_at: datetime | None = None,
    ttl_seconds: int = INVITATION_TTL_SECONDS,
) -> datetime:
    created = created_at or datetime.now(timezone.utc)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return created + timedelta(seconds=ttl_seconds)
