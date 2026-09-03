"""Provider-neutral OIDC helpers.

The network exchange and signature verification are kept at the API boundary.
These helpers own the protocol invariants that can be tested without a
provider or network.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlencode


@dataclass(frozen=True)
class OIDCConfig:
    issuer: str
    client_id: str
    authorization_endpoint: str
    token_endpoint: str
    redirect_uri: str
    scopes: tuple[str, ...] = ("openid", "email", "profile")
    allowed_domains: tuple[str, ...] = ()


def normalize_issuer(issuer: str) -> str:
    return issuer.strip().rstrip("/")


def new_oidc_transaction() -> dict[str, str]:
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    return {
        "state": state,
        "state_hash": hashlib.sha256(state.encode("utf-8")).hexdigest(),
        "nonce": nonce,
        "code_verifier": verifier,
        "code_challenge": challenge,
    }


def build_authorization_url(
    config: OIDCConfig,
    *,
    state: str,
    nonce: str,
    code_challenge: str,
) -> str:
    query = urlencode(
        {
            "client_id": config.client_id,
            "response_type": "code",
            "redirect_uri": config.redirect_uri,
            "scope": " ".join(config.scopes),
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    separator = "&" if "?" in config.authorization_endpoint else "?"
    return f"{config.authorization_endpoint}{separator}{query}"


def validate_oidc_claims(
    claims: Mapping[str, Any],
    *,
    issuer: str,
    client_id: str,
    nonce: str,
    allowed_domains: tuple[str, ...] = (),
) -> dict[str, Any]:
    normalized_issuer = normalize_issuer(issuer)
    if normalize_issuer(str(claims.get("iss") or "")) != normalized_issuer:
        raise ValueError("OIDC issuer mismatch")
    if claims.get("nonce") != nonce:
        raise ValueError("OIDC nonce mismatch")
    audience = claims.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    if client_id not in audiences:
        raise ValueError("OIDC audience mismatch")

    subject = str(claims.get("sub") or "").strip()
    email = str(claims.get("email") or "").strip().lower()
    if not subject or not email:
        raise ValueError("OIDC subject and email are required")
    if claims.get("email_verified") not in (True, "true", "1", 1):
        raise ValueError("OIDC email must be verified")

    domains = {domain.lower().lstrip("@") for domain in allowed_domains if domain}
    if domains and email.rsplit("@", 1)[-1] not in domains:
        raise ValueError("OIDC email domain is not allowed")

    return {
        "subject": subject,
        "email": email,
        "display_name": str(
            claims.get("name") or claims.get("preferred_username") or email
        )[:100],
        "claims": dict(claims),
    }
