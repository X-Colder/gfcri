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


class InstitutionalThemeSummary(BaseModel):
    theme: str
    count: int
    sources: list[str] = Field(default_factory=list)
    affected_nodes: list[str] = Field(default_factory=list)
    affected_chains: list[str] = Field(default_factory=list)


class InstitutionalRadarError(BaseModel):
    source: str
    error: str


class InstitutionalRadarResponse(BaseModel):
    generated_at: str
    source_count: int
    item_count: int
    sources: list[InstitutionalRadarSource]
    items: list[InstitutionalRadarItem]
    theme_summary: list[InstitutionalThemeSummary]
    errors: list[InstitutionalRadarError] = Field(default_factory=list)
    methodology: str
