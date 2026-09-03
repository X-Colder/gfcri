"""API key creation and scope helpers."""

from __future__ import annotations

import hashlib
import secrets


DEFAULT_API_KEY_SCOPES = frozenset({"analysis:read", "analysis:run", "data:read"})


def new_api_key() -> str:
    return f"gfcri_{secrets.token_urlsafe(32)}"


def hash_api_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def has_api_key_scope(scopes: list[str] | tuple[str, ...] | set[str], required: str) -> bool:
    return required in set(scopes)
