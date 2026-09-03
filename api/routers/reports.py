from fastapi import APIRouter, Depends, HTTPException

from api.access import require_deep_analysis, require_institutional_data
from api.models.report import InstitutionalReportV2Response, ReportResponse
from src.engines.institutional_report_v2 import institutional_report_v2
from src.storage.database import get_latest_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/latest", response_model=ReportResponse)
def latest_report(user=Depends(require_deep_analysis)):
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


@router.get("/institutional-v2/latest", response_model=InstitutionalReportV2Response)
def latest_institutional_report_v2(user=Depends(require_institutional_data)):
    return institutional_report_v2()
