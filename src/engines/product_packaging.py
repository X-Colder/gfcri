"""Subscription conversion and packaging configuration."""

from __future__ import annotations


def product_packaging() -> dict:
    return {
        "conversion_principle": "Show enough evidence to build trust; reserve full causal chains, institutional radar depth, exports, and watch automation for paid tiers.",
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "target_user": "Macro-curious individual user",
                "promise": "Know the current systemic-risk state quickly.",
                "features": ["Current GFCRI", "Top core theme", "Limited dashboard", "Basic methodology"],
                "conversion_trigger": "Unlock full evidence, hidden-risk scan, and alerts.",
            },
            {
                "id": "pro",
                "name": "Pro",
                "target_user": "Active investor / analyst",
                "promise": "Understand what is driving risk and what to watch next.",
                "features": ["All core themes", "Institutional radar", "Hidden-risk scan", "Full brief", "Watchlist", "Backtest details"],
                "conversion_trigger": "7-day trial with no payment info.",
            },
            {
                "id": "institutional",
                "name": "Institutional",
                "target_user": "Broker, advisor desk, risk team, research desk",
                "promise": "Turn GFCRI into internal risk infrastructure and client communication workflow.",
                "features": ["API", "Private deployment", "White-label reports", "Custom data connectors", "Audit logs", "Team permissions"],
                "conversion_trigger": "Book private deployment / pilot.",
            },
        ],
        "onboarding_flow": [
            "Choose market focus: global, US, China/Asia, Europe, commodities.",
            "Choose risk themes to watch.",
            "Generate first watchlist from current core themes.",
            "Send first institutional-style brief within the trial session.",
        ],
        "paywall_rules": [
            "Free users see the top theme and partial evidence.",
            "Pro users see all evidence, causal candidates, watch metrics, and exports.",
            "Institutional users get API, private data, team workflows, and audit logs.",
        ],
    }
