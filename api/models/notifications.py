from pydantic import BaseModel, Field


class NotificationPreferencesRequest(BaseModel):
    daily_brief: bool = False
    risk_alerts: bool = False
    weekly_digest: bool = False
    institutional_data_quality: bool = False
    product_updates: bool = False
    frequency: str = "daily"
    risk_alert_level: str = "orange"
    language: str = "en"
    timezone: str = "UTC"


class EmailSubscribeRequest(NotificationPreferencesRequest):
    email: str = Field(min_length=5, max_length=255)
