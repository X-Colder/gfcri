from typing import Any, Literal

from pydantic import BaseModel, Field


InstitutionalRole = Literal["admin", "analyst", "viewer"]


class WorkspaceProfileRequest(BaseModel):
    name: str = Field(default="Default Risk Workspace", min_length=2, max_length=255)
    profile: dict[str, Any] = Field(default_factory=dict)


class MemberRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    role: InstitutionalRole = "viewer"


class InvitationRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    role: InstitutionalRole = "viewer"


class InvitationAcceptRequest(BaseModel):
    token: str = Field(min_length=20, max_length=255)


class ApiKeyRequest(BaseModel):
    label: str = Field(min_length=2, max_length=120)
    scopes: list[str] = Field(
        default_factory=lambda: ["analysis:read", "analysis:run", "data:read"],
        min_length=1,
        max_length=20,
    )
    expires_in_days: int | None = Field(default=90, ge=1, le=3650)
