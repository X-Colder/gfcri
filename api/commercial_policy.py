from collections.abc import Mapping
from typing import Any


def is_institutional_account(user: Mapping[str, Any] | None) -> bool:
    return bool(user and str(user.get("account_type") or "").lower() == "institutional")


def _required_text(payload: Mapping[str, Any], key: str, minimum: int, maximum: int) -> str:
    value = str(payload.get(key) or "").strip()
    if len(value) < minimum or len(value) > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum} characters")
    return value


def validate_institutional_lead(payload: Mapping[str, Any]) -> dict[str, str]:
    company_name = _required_text(payload, "company_name", 2, 160)
    work_email = _required_text(payload, "work_email", 5, 255).lower()
    if "@" not in work_email or work_email.startswith("@") or work_email.endswith("@"):
        raise ValueError("work_email must be a valid work email")

    normalized = {
        "company_name": company_name,
        "work_email": work_email,
        "full_name": str(payload.get("full_name") or "").strip()[:120],
        "role": str(payload.get("role") or "").strip()[:120],
        "team_size": str(payload.get("team_size") or "").strip()[:40],
        "use_case": _required_text(payload, "use_case", 10, 2000),
        "deployment": str(payload.get("deployment") or "").strip()[:80],
        "message": str(payload.get("message") or "").strip()[:2000],
        "language": "zh" if str(payload.get("language") or "").lower() == "zh" else "en",
    }
    return normalized


def public_billing_catalog(personal_checkout_configured: bool) -> dict[str, Any]:
    return {
        "personal": {
            "monthly": {
                "name": "Pro Monthly",
                "price": "$19",
                "period": "/ month",
                "checkout_configured": bool(personal_checkout_configured),
            },
            "annual": {
                "name": "Pro Annual",
                "price": "$149",
                "period": "/ year",
                "savings": "35% vs monthly",
                "checkout_configured": bool(personal_checkout_configured),
            },
        },
        "institutional": {
            "pilot": {
                "name": "Institutional Pilot",
                "price": "From $3,000",
                "period": "/ 30 days",
                "cta": "Request a Pilot",
            },
            "team": {
                "name": "Institutional Team",
                "price": "From $1,500",
                "period": "/ month, billed annually",
                "cta": "Contact Sales",
            },
            "enterprise": {
                "name": "Enterprise Private",
                "price": "From $30,000",
                "period": "/ year + setup",
                "cta": "Contact Sales",
            },
        },
    }
