from __future__ import annotations

import hashlib
from html import escape
from typing import Any


DEFAULT_PREFERENCES = {
    "daily_brief": False,
    "risk_alerts": False,
    "weekly_digest": False,
    "institutional_data_quality": False,
    "product_updates": False,
    "frequency": "daily",
    "risk_alert_level": "orange",
    "language": "en",
    "timezone": "UTC",
}


def normalize_preferences(payload: dict[str, Any]) -> dict[str, Any]:
    result = dict(DEFAULT_PREFERENCES)
    for key in (
        "daily_brief",
        "risk_alerts",
        "weekly_digest",
        "institutional_data_quality",
        "product_updates",
    ):
        if key in payload:
            result[key] = bool(payload[key])

    if payload.get("frequency") in {"daily", "weekly"}:
        result["frequency"] = payload["frequency"]
    if payload.get("risk_alert_level") in {"yellow", "orange", "red"}:
        result["risk_alert_level"] = payload["risk_alert_level"]
    result["language"] = "zh" if str(payload.get("language") or "").lower().startswith("zh") else "en"
    timezone = str(payload.get("timezone") or "UTC").strip()
    result["timezone"] = timezone[:64] if timezone else "UTC"
    return result


def build_idempotency_key(subscription_id: int, kind: str, date_key: str) -> str:
    raw = f"{subscription_id}:{kind}:{date_key}".encode()
    return hashlib.sha256(raw).hexdigest()


def render_subscription_email(
    *,
    kind: str,
    language: str,
    gfcri_value: float,
    alert_level: str,
    unsubscribe_url: str,
) -> tuple[str, str, str]:
    value = f"{float(gfcri_value):.1f}"
    if language == "zh":
        subject = f"GFCRI 风险简报：{value} / {alert_level}"
        text = (
            f"GFCRI 当前风险分数为 {value}，风险等级为 {alert_level}。\n\n"
            "本邮件仅用于信息和风险监测，不构成投资建议。\n"
            f"取消订阅：{unsubscribe_url}"
        )
        html = (
            f"<h2>GFCRI 风险简报</h2><p>当前风险分数：<strong>{escape(value)}</strong></p>"
            f"<p>风险等级：{escape(alert_level)}</p>"
            "<p>本邮件仅用于信息和风险监测，不构成投资建议。</p>"
            f'<p><a href="{escape(unsubscribe_url)}">取消订阅</a></p>'
        )
    else:
        subject = f"GFCRI Risk Brief: {value} / {alert_level}"
        text = (
            f"GFCRI risk score is {value}, with an alert level of {alert_level}.\n\n"
            "This email is for informational risk monitoring only, not investment advice.\n"
            f"Unsubscribe: {unsubscribe_url}"
        )
        html = (
            f"<h2>GFCRI Risk Brief</h2><p>Risk score: <strong>{escape(value)}</strong></p>"
            f"<p>Alert level: {escape(alert_level)}</p>"
            "<p>This email is for informational risk monitoring only, not investment advice.</p>"
            f'<p><a href="{escape(unsubscribe_url)}">Unsubscribe</a></p>'
        )
    return subject, text, html
