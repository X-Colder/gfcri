"""Refresh Institutional Radar and dynamic core themes.

This script is safe to run from cron or manually inside the API/app container.
It persists public institutional metadata and governed causal candidates.
"""

from src.engines.institutional_radar import latest_institutional_radar
from src.engines.core_themes import latest_core_risk_themes
from src.models.graph import build_initial_causal_graph


def main() -> None:
    radar = latest_institutional_radar(limit=80, force_refresh=True)
    themes = latest_core_risk_themes(limit=6, include_causal=True, graph=build_initial_causal_graph())
    print(
        {
            "radar_items": radar.get("item_count", 0),
            "radar_errors": len(radar.get("errors") or []),
            "core_themes": len(themes.get("themes") or []),
            "causal_candidates": (themes.get("causal") or {}).get("candidate_count", 0),
        }
    )


if __name__ == "__main__":
    main()
