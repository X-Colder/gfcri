from typing import Optional
from pydantic import BaseModel


class SocialContentResponse(BaseModel):
    date: str
    content: str
    content_type: str


class AlertItem(BaseModel):
    level: str
    title: str
    detail: str
    affected_nodes: list[str]
    chain_id: Optional[str] = None


class AlertsResponse(BaseModel):
    alerts: list[AlertItem]
