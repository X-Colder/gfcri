from datetime import date
from typing import Any, Optional
from pydantic import BaseModel


class ReportResponse(BaseModel):
    report_date: date
    gfcri_value: Optional[float] = None
    alert_level: Optional[str] = None
    report_markdown: str
    report_metadata: Optional[dict[str, Any]] = None
    llm_narrative: Optional[str] = None
    generation_time_ms: Optional[int] = None


class InstitutionalReportV2Response(BaseModel):
    report_date: str
    gfcri_value: Optional[float] = None
    alert_level: Optional[str] = None
    sections: list[dict[str, Any]]
    markdown: str
    quality_controls: dict[str, Any]
