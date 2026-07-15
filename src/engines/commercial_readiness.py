"""Aggregate commercial-readiness surface for product and institutional pages."""

from __future__ import annotations

from src.engines.causal_validation import causal_validation_report
from src.engines.data_quality import data_quality_assessment
from src.engines.institutional_report_v2 import institutional_report_v2
from src.engines.market_data_freshness import market_data_freshness
from src.engines.private_deployment import private_deployment_readiness
from src.engines.product_packaging import product_packaging


def commercial_readiness() -> dict:
    data = data_quality_assessment()
    causal = causal_validation_report(limit=30)
    report = institutional_report_v2()
    packaging = product_packaging()
    private = private_deployment_readiness()
    freshness = market_data_freshness()
    return {
        "data_quality": data,
        "data_freshness": freshness,
        "causal_validation": causal,
        "institutional_report": report,
        "subscription_packaging": packaging,
        "private_deployment": private,
        "readiness_score": _score(data, freshness, causal, report, private),
    }


def _score(data: dict, freshness: dict, causal: dict, report: dict, private: dict) -> dict:
    score = 0
    score += 20 if data.get("tier_a_b_share", 0) >= 80 else 12
    freshness_status = freshness.get("status")
    if freshness_status == "ok":
        score += 20
    elif freshness_status == "degraded":
        score += 10
    score += 20 if causal.get("candidate_count", 0) > 0 else 8
    score += 20 if report.get("quality_controls", {}).get("evidence_table") else 8
    score += 20 if private.get("deployment_modes") else 8
    stage = "pilot_ready" if score >= 75 else "prototype"
    interpretation = (
        "Ready for paid pilot conversations; continue hardening data depth, RBAC, "
        "and report approval workflow."
    )
    if freshness_status == "blocked":
        stage = "pilot_blocked_data"
        interpretation = (
            "Commercial package is structurally pilot-ready, but this environment "
            "is blocked until critical market data is cached and fresh."
        )
    return {
        "score": min(100, score),
        "stage": stage,
        "interpretation": interpretation,
    }
