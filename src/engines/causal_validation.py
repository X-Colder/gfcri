"""Causal validation scoring for candidate graph expansions."""

from __future__ import annotations

from typing import Any

from src.engines.causal_promotion import CausalPromotionGate
from src.storage.database import get_causal_candidates, get_risk_index_history


def causal_validation_report(limit: int = 50) -> dict[str, Any]:
    candidates = get_causal_candidates(limit=limit)
    history = get_risk_index_history(limit=120)
    gate = CausalPromotionGate()
    rows = []
    for candidate in candidates:
        validation = _validate_candidate(candidate, history, gate)
        rows.append(validation)
    rows.sort(key=lambda x: x["validation_score"], reverse=True)
    return {
        "candidate_count": len(rows),
        "validated_count": sum(1 for r in rows if r["stage"] in {"validated", "promotion_ready"}),
        "promotion_ready_count": sum(1 for r in rows if r["stage"] == "promotion_ready"),
        "methodology": (
            "Causal Validation v1 scores each candidate using data coverage, graph support, repeat observation, "
            "falsifiability, temporal plausibility, and promotion-gate eligibility. It does not mutate the core graph."
        ),
        "candidates": rows,
    }


def _validate_candidate(candidate: dict[str, Any], history: list[dict[str, Any]], gate: CausalPromotionGate) -> dict[str, Any]:
    scores = candidate.get("scores") or {}
    promotion = gate.evaluate(candidate)
    cause = candidate.get("cause_node")
    effect = candidate.get("effect_node")
    temporal = _temporal_plausibility(cause, effect, history)
    repeat = min(1.0, int(candidate.get("seen_count") or 0) / 3)
    falsifiability = 1.0 if candidate.get("falsification") else 0.0
    data_coverage = float(scores.get("data_coverage") or 0)
    graph_support = float(scores.get("graph_support") or 0)
    confidence = float(candidate.get("overall_confidence") or 0)
    validation_score = (
        0.20 * data_coverage
        + 0.18 * graph_support
        + 0.18 * confidence
        + 0.16 * repeat
        + 0.16 * falsifiability
        + 0.12 * temporal["score"]
    )
    stage = "watchlist"
    if promotion.get("eligible"):
        stage = "promotion_ready"
    elif validation_score >= 0.72:
        stage = "validated"
    elif validation_score >= 0.50:
        stage = "candidate_graph"
    elif validation_score < 0.35:
        stage = "weak"
    return {
        "candidate_id": candidate.get("candidate_id") or candidate.get("id"),
        "title": candidate.get("title"),
        "cause_node": cause,
        "effect_node": effect,
        "stage": stage,
        "validation_score": round(validation_score, 3),
        "temporal_plausibility": temporal,
        "promotion_gate": promotion,
        "checks": {
            "data_coverage": data_coverage,
            "graph_support": graph_support,
            "confidence": confidence,
            "repeat_observation": repeat,
            "falsifiability": falsifiability,
        },
        "review_action": _review_action(stage),
    }


def _temporal_plausibility(cause: str | None, effect: str | None, history: list[dict[str, Any]]) -> dict[str, Any]:
    if not cause or not effect or len(history) < 3:
        return {"score": 0.35, "detail": "Insufficient history or missing cause/effect node mapping."}
    rows = list(reversed(history))
    cause_series = []
    effect_series = []
    for row in rows:
        contrib = row.get("node_contributions") or {}
        c = contrib.get(cause) or {}
        e = contrib.get(effect) or {}
        cause_series.append(max(float(c.get("anomaly_score") or 0), float(c.get("abs_score") or 0)))
        effect_series.append(max(float(e.get("anomaly_score") or 0), float(e.get("abs_score") or 0)))
    lead_hits = 0
    comparable = 0
    for i in range(1, len(cause_series)):
        if cause_series[i - 1] >= 0.35 or effect_series[i] >= 0.35:
            comparable += 1
            if cause_series[i - 1] >= 0.35 and effect_series[i] >= 0.25:
                lead_hits += 1
    score = lead_hits / comparable if comparable else 0.35
    return {
        "score": round(score, 3),
        "detail": f"{lead_hits}/{comparable} recent windows show cause pressure preceding or coinciding with effect pressure.",
    }


def _review_action(stage: str) -> str:
    if stage == "promotion_ready":
        return "Prepare reviewed core-edge PR; do not auto-merge."
    if stage == "validated":
        return "Keep in candidate graph and monitor out-of-sample behavior."
    if stage == "candidate_graph":
        return "Collect more observations and refine falsification tests."
    if stage == "weak":
        return "Reject or keep only as low-priority watchlist hypothesis."
    return "Continue watchlist monitoring."
