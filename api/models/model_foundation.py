from typing import Any

from pydantic import BaseModel


class NodeDataDictionaryEntry(BaseModel):
    node_id: str
    display_name: str
    economic_meaning: str
    asset_class: str
    geography: str
    declared_data_source: str
    update_frequency: str
    unit: str
    source_tier: str
    raw_formula: str
    stress_direction: str
    absolute_threshold: str
    known_limitations: str
    upgrade_plan: str


class SubIndexNodeReceipt(BaseModel):
    node_id: str
    display_name: str
    current_value: float | None = None
    zscore: float | None = None
    anomaly_score: float | None = None
    abs_score: float | None = None
    source_tier: str
    data_source: str
    raw_formula: str
    known_limitations: str


class SubIndexReceipt(BaseModel):
    sub_index_id: str
    name: str
    score: float
    formula: str
    mean_stress: float
    mean_abs_stress: float
    transmission: float
    top_driver: str | None = None
    node_count: int
    source_tier_summary: dict[str, int]
    nodes: list[SubIndexNodeReceipt]
    limitations: list[str]
    formula_type: str | None = None
    dimension_details: dict[str, Any] | None = None
    dimension_weights: dict[str, float] | None = None
    config: dict[str, Any] | None = None


class ModelFoundationResponse(BaseModel):
    index_date: str
    sub_index_receipts: dict[str, SubIndexReceipt]
    data_dictionary: dict[str, NodeDataDictionaryEntry]
    coverage_summary: dict[str, Any] | None = None
    upgrade_priorities: list[dict[str, Any]] | None = None
