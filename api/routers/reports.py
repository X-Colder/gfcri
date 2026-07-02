from fastapi import APIRouter, HTTPException

from src.storage.database import get_latest_report
from api.models.report import ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/latest", response_model=ReportResponse)
def latest_report():
    data = get_latest_report()
    if not data:
        raise HTTPException(status_code=404, detail="No report data available")
    return ReportResponse(
        report_date=data["report_date"],
        gfcri_value=float(data["gfcri_value"]) if data.get("gfcri_value") else None,
        alert_level=data.get("alert_level"),
        report_markdown=data["report_markdown"],
        report_metadata=data.get("report_metadata"),
        llm_narrative=data.get("llm_narrative"),
        generation_time_ms=data.get("generation_time_ms"),
    )
