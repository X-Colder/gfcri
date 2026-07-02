from datetime import date
from typing import Any, Optional
from pydantic import BaseModel


class RiskIndexResponse(BaseModel):
    index_date: date
    gfcri_value: float
    alert_level: str
    si_rates: float
    si_fx: float
    si_equity: float
    si_credit: float
    si_sentiment: float
    sub_index_details: Optional[dict[str, Any]] = None
    active_chains: Any = None
    chain_details: Any = None
    coherence_multiplier: Optional[float] = None
    node_contributions: Optional[dict[str, Any]] = None
