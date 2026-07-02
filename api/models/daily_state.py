from datetime import date
from typing import Any, Optional
from pydantic import BaseModel


class DailyStateResponse(BaseModel):
    state_date: date
    graph_version: str
    current_regime: str
    node_values: dict[str, Any]
    node_zscores: dict[str, Any]
    anomalous_nodes: list[str]
    active_paths: Optional[dict[str, Any]] = None
    inference_summary: Optional[dict[str, Any]] = None
    alert_level: str
    alert_details: Optional[dict[str, Any]] = None
