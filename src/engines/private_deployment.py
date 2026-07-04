"""Private deployment readiness package for institutional delivery."""

from __future__ import annotations


def private_deployment_readiness() -> dict:
    return {
        "deployment_modes": [
            {"id": "single_node", "name": "Single-node Docker Compose", "fit": "Pilot / internal demo", "status": "ready"},
            {"id": "private_lan", "name": "Private LAN deployment", "fit": "Broker research or advisor desk", "status": "ready_with_env_config"},
            {"id": "white_label", "name": "White-label frontend", "fit": "Client-facing broker app", "status": "design_ready"},
            {"id": "managed_api", "name": "Managed API integration", "fit": "Institutional internal systems", "status": "api_ready"},
        ],
        "capabilities": [
            "Dockerized API/frontend/app/postgres stack",
            "Private `.env` configuration",
            "Institutional radar and report refresh script",
            "Model/data coverage audit",
            "Causal candidate registry and promotion gate",
            "Rollback via source backup archive",
        ],
        "gaps_to_close": [
            "Formal multi-tenant RBAC beyond current user/trial model",
            "SAML/SSO integration for enterprise identity",
            "Per-client private data connector sandbox",
            "Operational dashboards for job health and data freshness",
            "Signed PDF report export and report approval workflow",
        ],
        "pilot_acceptance": [
            "Deploys inside client network without external write dependency except configured public data sources.",
            "Daily refresh completes and records source health.",
            "Dashboard, Institutional Radar, Methodology audit, and report API return successfully.",
            "Rollback package and version hash are recorded for every upgrade.",
        ],
    }
