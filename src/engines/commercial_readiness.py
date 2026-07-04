"""Aggregate commercial-readiness surface for product and institutional pages."""

from __future__ import annotations

from src.engines.causal_validation import causal_validation_report
from src.engines.data_quality import data_quality_assessment
from src.engines.institutional_report_v2 import institutional_report_v2
from src.engines.private_deployment import private_deployment_readiness
from src.engines.product_packaging import product_packaging


def commercial_readiness() -> dict:
    data = data_quality_assessment()
    causal = causal_validation_report(limit=30)
    report = institutional_report_v2()
    packaging = product_packaging()
    private = private_deployment_readiness()
    return {
        "data_quality": data,
        "causal_validation": causal,
        "institutional_report": report,
        "subscription_packaging": packaging,
        "private_deployment": private,
        "readiness_score": _score(data, causal, report, private),
    }


def _score(data: dict, causal: dict, report: dict, private: dict) -> dict:
    score = 0
    score += 25 if data.get("tier_a_b_share", 0) >= 80 else 15
    score += 20 if causal.get("candidate_count", 0) > 0 else 8
    score += 20 if report.get("quality_controls", {}).get("evidence_table") else 8
    score += 15
    score += 20 if private.get("deployment_modes") else 8
    return {
        "score": min(100, score),
        "stage": "pilot_ready" if score >= 75 else "prototype",
        "interpretation": "Ready for paid pilot conversations; continue hardening data depth, RBAC, and report approval workflow.",
    }
