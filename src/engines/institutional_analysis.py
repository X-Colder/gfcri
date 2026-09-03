"""Backward-compatible institutional analysis entry point.

The value-layer implementation lives in
``src.engines.institutional_value_layer``. This module keeps the existing
function name and default behavior stable for current API callers and tests.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.engines.institutional_value_layer import (
    analyze_institutional_risk_evidence,
)


def analyze_target_observations(
    *,
    target: Mapping[str, str],
    core_score: float,
    observations: list[Mapping[str, Any]],
    data_quality: Mapping[str, Any],
    core_risk: Mapping[str, Any] | None = None,
    product_tier: str = "research",
    parameters: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return analyze_institutional_risk_evidence(
        target=target,
        core_score=core_score,
        observations=observations,
        data_quality=data_quality,
        core_risk=core_risk,
        product_tier=product_tier,
        parameters=parameters,
    )
