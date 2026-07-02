from fastapi import APIRouter

from src.storage.database import get_latest_risk_index, get_risk_index_history, get_latest_daily_state
from src.engines.risk_monitor import RiskMonitor
from api.dependencies import get_graph
from api.models.social import AlertItem, AlertsResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/latest", response_model=AlertsResponse)
def latest_alerts():
    graph = get_graph()
    latest_risk = get_latest_risk_index()
    latest_state = get_latest_daily_state()

    if not latest_risk or not latest_state:
        return AlertsResponse(alerts=[])

    history = get_risk_index_history(limit=2)
    prev_gfcri = history[1] if len(history) > 1 else None
    prev_zscores = None
    if prev_gfcri and prev_gfcri.get("node_contributions"):
        prev_zscores = {
            nid: info.get("zscore", 0)
            for nid, info in prev_gfcri["node_contributions"].items()
        }

    gfcri_result = {
        "gfcri": float(latest_risk["gfcri_value"]),
        "alert_level": latest_risk["alert_level"],
        "sub_indices": latest_risk.get("sub_index_details", {}),
        "chains": list((latest_risk.get("chain_details") or {}).values()) if isinstance(latest_risk.get("chain_details"), dict) else (latest_risk.get("chain_details") or []),
        "node_contributions": latest_risk.get("node_contributions", {}),
    }

    monitor = RiskMonitor(
        graph=graph,
        gfcri_result=gfcri_result,
        prev_gfcri={
            "gfcri": float(prev_gfcri["gfcri_value"]),
            "alert_level": prev_gfcri["alert_level"],
        } if prev_gfcri else None,
        prev_node_zscores=prev_zscores,
    )

    alerts = monitor.run_all_checks()
    return AlertsResponse(
        alerts=[
            AlertItem(
                level=a.level,
                title=a.title,
                detail=a.detail,
                affected_nodes=a.affected_nodes,
                chain_id=a.chain_id,
            )
            for a in alerts
        ]
    )
