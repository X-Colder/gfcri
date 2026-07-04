from pydantic import BaseModel, Field


class InstitutionalRadarSource(BaseModel):
    id: str
    name: str
    tier: str
    url: str
    source_type: str = "rss"


class InstitutionalRadarItem(BaseModel):
    id: str
    source: str
    source_id: str
    source_tier: str
    title: str
    summary: str = ""
    url: str
    published_at: str | None = None
    risk_themes: list[str] = Field(default_factory=list)
    affected_nodes: list[str] = Field(default_factory=list)
    affected_chains: list[str] = Field(default_factory=list)
    risk_direction: str
    confidence: float
    importance_score: float = 0
    importance_reasons: list[str] = Field(default_factory=list)


class InstitutionalThemeSummary(BaseModel):
    theme: str
    count: int
    sources: list[str] = Field(default_factory=list)
    affected_nodes: list[str] = Field(default_factory=list)
    affected_chains: list[str] = Field(default_factory=list)


class InstitutionalRadarError(BaseModel):
    source: str
    error: str


class InstitutionalRadarSourceHealth(BaseModel):
    source_id: str
    source_name: str
    source_tier: str
    url: str
    status: str
    last_error: str | None = None
    item_count: int = 0
    latency_ms: int = 0


class InstitutionalRadarResponse(BaseModel):
    generated_at: str
    source_count: int
    item_count: int
    sources: list[InstitutionalRadarSource]
    items: list[InstitutionalRadarItem]
    theme_summary: list[InstitutionalThemeSummary]
    errors: list[InstitutionalRadarError] = Field(default_factory=list)
    source_health: list[InstitutionalRadarSourceHealth] = Field(default_factory=list)
    source_latency_ms: dict[str, int] = Field(default_factory=dict)
    methodology: str
