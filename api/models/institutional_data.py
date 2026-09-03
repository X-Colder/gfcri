from typing import Any

from pydantic import BaseModel, Field


class EntityRequest(BaseModel):
    entity_type: str = Field(min_length=2, max_length=40)
    entity_id: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataSourceRequest(BaseModel):
    source_id: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=255)
    source_tier: str = Field(min_length=2, max_length=40)
    license_status: str = Field(default="review_required", max_length=40)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ObservationRequest(BaseModel):
    entity_type: str
    entity_id: str
    metric_id: str
    value: float
    unit: str
    as_of: str
    frequency: str
    source_id: str
    source_tier: str = ""
    quality_status: str = "verified"


class ObservationBatchRequest(BaseModel):
    snapshot_id: str | None = Field(default=None, max_length=160)
    observations: list[ObservationRequest] = Field(min_length=1, max_length=5000)
