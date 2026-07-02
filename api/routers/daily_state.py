from fastapi import APIRouter, Query, HTTPException

from src.storage.database import get_latest_daily_state, get_daily_states
from api.models.daily_state import DailyStateResponse

router = APIRouter(prefix="/daily-state", tags=["daily-state"])


@router.get("/latest", response_model=DailyStateResponse)
def latest_daily_state():
    data = get_latest_daily_state()
    if not data:
        raise HTTPException(status_code=404, detail="No daily state data available")
    return DailyStateResponse(
        state_date=data["state_date"],
        graph_version=data["graph_version"],
        current_regime=data["current_regime"],
        node_values=data["node_values"] or {},
        node_zscores=data["node_zscores"] or {},
        anomalous_nodes=data["anomalous_nodes"] or [],
        active_paths=data.get("active_paths"),
        inference_summary=data.get("inference_summary"),
        alert_level=data["alert_level"],
        alert_details=data.get("alert_details"),
    )


@router.get("/history", response_model=list[DailyStateResponse])
def daily_state_history(limit: int = Query(default=30, ge=1, le=365)):
    rows = get_daily_states(limit=limit)
    return [
        DailyStateResponse(
            state_date=r["state_date"],
            graph_version=r["graph_version"],
            current_regime=r["current_regime"],
            node_values=r["node_values"] or {},
            node_zscores=r["node_zscores"] or {},
            anomalous_nodes=r["anomalous_nodes"] or [],
            active_paths=r.get("active_paths"),
            inference_summary=r.get("inference_summary"),
            alert_level=r["alert_level"],
            alert_details=r.get("alert_details"),
        )
        for r in rows
    ]
