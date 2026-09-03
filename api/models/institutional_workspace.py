from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkspaceProfileRequest(BaseModel):
    name: str = Field(default="Default Risk Workspace", min_length=2, max_length=255)
    profile: dict[str, Any] = Field(default_factory=dict)


class MemberRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    role: Literal["admin", "analyst", "viewer"] = "viewer"


class ApiKeyRequest(BaseModel):
    label: str = Field(min_length=2, max_length=120)
