from typing import Literal

from pydantic import BaseModel, Field


class OIDCProviderRequest(BaseModel):
    issuer: str = Field(min_length=8, max_length=500)
    client_id: str = Field(min_length=2, max_length=255)
    client_secret_env: str = Field(min_length=2, max_length=160)
    redirect_uri: str = Field(min_length=8, max_length=500)
    scopes: list[str] = Field(
        default_factory=lambda: ["openid", "email", "profile"],
        min_length=2,
        max_length=12,
    )
    allowed_domains: list[str] = Field(default_factory=list, max_length=50)
    default_role: Literal["admin", "analyst", "viewer"] = "viewer"
    enabled: bool = True
