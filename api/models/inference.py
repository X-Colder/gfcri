from typing import Any, Literal, Optional
from pydantic import BaseModel


class InferenceRequest(BaseModel):
    source: str
    target: str


class ObservationalRequest(InferenceRequest):
    source_value: float


class InterventionalRequest(InferenceRequest):
    intervention_value: float


class InferenceResponse(BaseModel):
    inference_type: str
    source: str
    target: str
    result: dict[str, Any]
    computation_time_ms: int
