from fastapi import APIRouter, Depends, Query, HTTPException

from api.models.risk_index import RiskIndexResponse
from api.routers.auth import get_current_user
from src.security.data_visibility import visible_risk_index
from src.storage.database import (
    get_latest_risk_index,
    get_latest_risk_index_quality_event,
    get_risk_index_history,
)

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


def _risk_response(data: dict, user: dict | None, quality: dict | None = None) -> RiskIndexResponse:
    visible = visible_risk_index(data, user)
    return RiskIndexResponse(
        index_date=data["index_date"],
        gfcri_value=float(data["gfcri_value"]),
        alert_level=data["alert_level"],
        si_rates=float(data["si_rates"]),
        si_fx=float(data["si_fx"]),
        si_equity=float(data["si_equity"]),
        si_credit=float(data["si_credit"]),
        si_sentiment=float(data["si_sentiment"]),
        sub_index_details=visible.get("sub_index_details"),
        active_chains=visible.get("active_chains"),
        chain_details=visible.get("chain_details"),
        coherence_multiplier=(
            float(visible["coherence_multiplier"])
            if visible.get("coherence_multiplier") is not None
            else None
        ),
        node_contributions=visible.get("node_contributions"),
        divergence=visible.get("divergence"),
        undercurrent_boost=(
            float(visible["undercurrent_boost"])
            if visible.get("undercurrent_boost") is not None
            else None
        ),
        trade_spillover=visible.get("trade_spillover") or _trade_spillover(visible),
        trade_spillover_boost=_trade_spillover_boost(visible),
        data_quality_status=quality.get("status") if quality else None,
        data_quality_message=quality.get("message") if quality else None,
        data_quality_details=quality.get("details") if quality else None,
        latest_blocked_run_date=quality.get("run_date") if quality else None,
    )


@router.get("/latest", response_model=RiskIndexResponse)
def latest_risk_index(user=Depends(get_current_user)):
    data = get_latest_risk_index()
    if not data:
        raise HTTPException(status_code=404, detail="No risk index data available")
    quality = get_latest_risk_index_quality_event()
    if quality and (
        quality.get("status") == "ok"
        or quality.get("run_date") <= data.get("index_date")
    ):
        quality = None
    return _risk_response(data, user, quality)


@router.get("/history", response_model=list[RiskIndexResponse])
def risk_index_history(
    limit: int = Query(default=30, ge=1, le=365),
    user=Depends(get_current_user),
):
    rows = get_risk_index_history(limit=limit)
    return [_risk_response(row, user) for row in rows]
