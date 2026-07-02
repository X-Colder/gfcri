from fastapi import APIRouter, Query, HTTPException

from src.storage.database import get_latest_risk_index, get_risk_index_history
from api.models.risk_index import RiskIndexResponse

router = APIRouter(prefix="/risk-index", tags=["risk-index"])


@router.get("/latest", response_model=RiskIndexResponse)
def latest_risk_index():
    data = get_latest_risk_index()
    if not data:
        raise HTTPException(status_code=404, detail="No risk index data available")
    return RiskIndexResponse(
        index_date=data["index_date"],
        gfcri_value=float(data["gfcri_value"]),
        alert_level=data["alert_level"],
        si_rates=float(data["si_rates"]),
        si_fx=float(data["si_fx"]),
        si_equity=float(data["si_equity"]),
        si_credit=float(data["si_credit"]),
        si_sentiment=float(data["si_sentiment"]),
        sub_index_details=data.get("sub_index_details"),
        active_chains=data.get("active_chains"),
        chain_details=data.get("chain_details"),
        coherence_multiplier=float(data["coherence_multiplier"]) if data.get("coherence_multiplier") else None,
        node_contributions=data.get("node_contributions"),
    )


@router.get("/history", response_model=list[RiskIndexResponse])
def risk_index_history(limit: int = Query(default=30, ge=1, le=365)):
    rows = get_risk_index_history(limit=limit)
    return [
        RiskIndexResponse(
            index_date=r["index_date"],
            gfcri_value=float(r["gfcri_value"]),
            alert_level=r["alert_level"],
            si_rates=float(r["si_rates"]),
            si_fx=float(r["si_fx"]),
            si_equity=float(r["si_equity"]),
            si_credit=float(r["si_credit"]),
            si_sentiment=float(r["si_sentiment"]),
            sub_index_details=r.get("sub_index_details"),
            active_chains=r.get("active_chains"),
            chain_details=r.get("chain_details"),
            coherence_multiplier=float(r["coherence_multiplier"]) if r.get("coherence_multiplier") else None,
            node_contributions=r.get("node_contributions"),
        )
        for r in rows
    ]
