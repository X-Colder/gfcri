from typing import Any

from pydantic import BaseModel, Field


class CoreThemeEvidence(BaseModel):
    type: str
    label: str | None = None
    value: float | None = None
    detail: str | None = None
    node_id: str | None = None
    chain_id: str | None = None
    sub_index_id: str | None = None
    source: str | None = None
    url: str | None = None


class CoreRiskTheme(BaseModel):
    theme_id: str
    title: str
    description: str
    priority_score: float
    status: str
    model_pressure: float
    transmission_pressure: float
    institutional_attention: float
    hidden_risk_alignment: float
    watch_metrics: list[str] = Field(default_factory=list)
    affected_nodes: list[str] = Field(default_factory=list)
    affected_chains: list[str] = Field(default_factory=list)
    evidence: list[CoreThemeEvidence] = Field(default_factory=list)
    why_it_matters: str
    next_questions: list[str] = Field(default_factory=list)


class CoreThemesResponse(BaseModel):
    generated_at: str
    index_date: str | None = None
    gfcri_value: float | None = None
    alert_level: str | None = None
    themes: list[CoreRiskTheme]
    methodology: str
    radar_context: dict[str, Any] = Field(default_factory=dict)
    causal: dict[str, Any] = Field(default_factory=dict)
