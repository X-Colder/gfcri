from typing import Any

from pydantic import BaseModel, Field


class AnalysisRunRequest(BaseModel):
    entity_type: str = Field(min_length=2, max_length=40)
    entity_id: str = Field(min_length=1, max_length=160)
    snapshot_id: str | None = Field(default=None, max_length=160)
    product_tier: str = Field(default="research", min_length=1, max_length=30)
    parameters: dict[str, Any] = Field(default_factory=dict)
