from fastapi import APIRouter, Query, HTTPException

from src.storage.database import (
    get_latest_risk_index,
    get_latest_risk_index_quality_event,
    get_risk_index_history,
)
from api.models.risk_index import RiskIndexResponse

router = APIRouter(prefix="/risk-index", tags=["risk-index"])


def _trade_spillover(data: dict):
    if data.get("trade_spillover"):
        return data.get("trade_spillover")
    sub = data.get("sub_index_details") or {}
    trade = sub.get("SI_TRADE_SPILLOVER") or {}
    return trade.get("trade_spillover")


def _trade_spillover_boost(data: dict):
    if data.get("trade_spillover_boost") is not None:
        return float(data["trade_spillover_boost"])
    sub = data.get("sub_index_details") or {}
    trade = sub.get("SI_TRADE_SPILLOVER") or {}
    if trade.get("trade_spillover_boost") is not None:
        return float(trade["trade_spillover_boost"])
    return None


@router.get("/latest", response_model=RiskIndexResponse)
def latest_risk_index():
    data = get_latest_risk_index()
    if not data:
        raise HTTPException(status_code=404, detail="No risk index data available")
    quality = get_latest_risk_index_quality_event()
    if quality and (
        quality.get("status") == "ok"
        or quality.get("run_date") <= data.get("index_date")
    ):
        quality = None
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
        divergence=data.get("divergence"),
        undercurrent_boost=float(data["undercurrent_boost"]) if data.get("undercurrent_boost") is not None else None,
        trade_spillover=_trade_spillover(data),
        trade_spillover_boost=_trade_spillover_boost(data),
        data_quality_status=quality.get("status") if quality else None,
        data_quality_message=quality.get("message") if quality else None,
        data_quality_details=quality.get("details") if quality else None,
        latest_blocked_run_date=quality.get("run_date") if quality else None,
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
            divergence=r.get("divergence"),
            undercurrent_boost=float(r["undercurrent_boost"]) if r.get("undercurrent_boost") is not None else None,
            trade_spillover=_trade_spillover(r),
            trade_spillover_boost=_trade_spillover_boost(r),
        )
        for r in rows
    ]
