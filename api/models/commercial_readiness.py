from typing import Any

from pydantic import BaseModel, Field


class CommercialReadinessResponse(BaseModel):
    data_quality: dict[str, Any] = Field(default_factory=dict)
    causal_validation: dict[str, Any] = Field(default_factory=dict)
    institutional_report: dict[str, Any] = Field(default_factory=dict)
    subscription_packaging: dict[str, Any] = Field(default_factory=dict)
    private_deployment: dict[str, Any] = Field(default_factory=dict)
    readiness_score: dict[str, Any] = Field(default_factory=dict)
