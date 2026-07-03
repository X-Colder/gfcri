"""AI-assisted causal graph expansion governance.

The engine does not let an LLM mutate the production graph. It detects an
unexplained state, prepares a strict prompt for AI hypothesis generation, and
builds deterministic candidate mechanisms that are then scored by data coverage,
graph support, structural plausibility, and falsifiability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CandidateTemplate:
    id: str
    title: str
    cause_node: str | None
    effect_node: str | None
    mechanism: str
    trigger_types: tuple[str, ...]
    observable_tests: tuple[str, ...]
    falsification: tuple[str, ...]
    structural_score: float


CANDIDATE_TEMPLATES: tuple[CandidateTemplate, ...] = (
    CandidateTemplate(
        id="ai_earnings_support",
        title="AI earnings narrative suppressing equity damage",
        cause_node="ai_capex",
        effect_node="spx",
        mechanism="AI capex expectations and mega-cap earnings revisions can support index-level equity prices even while concentration risk rises.",
        trigger_types=("speculative_overextension",),
        observable_tests=("AI capex guidance", "SOX relative strength", "SPX equal-weight underperformance", "mega-cap earnings revisions"),
        falsification=("AI capex guidance declines for two quarters", "SOX breaks below its long-term trend", "SPX equal-weight confirms broad participation rather than concentration"),
        structural_score=0.82,
    ),
    CandidateTemplate(
        id="semi_cycle_korea_support",
        title="Semiconductor cycle supporting Korea equities despite FX fragility",
        cause_node="sox",
        effect_node="kospi",
        mechanism="Global semiconductor strength can support Korean equities while KRW pressure signals external fragility.",
        trigger_types=("korea_equity_fx_divergence", "speculative_overextension"),
        observable_tests=("SOX/KOSPI relative strength", "KRW/USD pressure", "Korea semiconductor export momentum", "foreign equity flows"),
        falsification=("KOSPI weakens while SOX remains strong", "Korea export momentum turns negative", "KRW stabilizes without equity support"),
        structural_score=0.78,
    ),
    CandidateTemplate(
        id="weak_yen_exporter_buffer",
        title="Weak yen buffering Japanese equity damage",
        cause_node="jpy_usd",
        effect_node="nikkei",
        mechanism="Yen depreciation supports exporter earnings and can keep Nikkei resilient, while increasing intervention and carry-trade reversal risk.",
        trigger_types=("yen_depreciation_pressure",),
        observable_tests=("USD/JPY level", "Nikkei exporter relative performance", "Japan FX intervention signals", "imported inflation measures"),
        falsification=("Yen weakens but exporters underperform", "Nikkei falls despite yen weakness", "policy intervention reverses USD/JPY without equity stress"),
        structural_score=0.84,
    ),
    CandidateTemplate(
        id="policy_put_suppressing_credit_damage",
        title="Policy easing expectations suppressing credit damage",
        cause_node="fed_funds",
        effect_node="hyg",
        mechanism="Rate-cut or liquidity-support expectations can keep credit damage from materializing even when underlying pressure is elevated.",
        trigger_types=("policy_mask", "zscore_desensitized"),
        observable_tests=("Fed funds path", "BBB/HY spreads", "HYG/LQD relative performance", "rate-cut probabilities"),
        falsification=("Rate-cut expectations rise but credit spreads widen materially", "default rates accelerate despite easing expectations"),
        structural_score=0.76,
    ),
    CandidateTemplate(
        id="passive_flow_concentration_buffer",
        title="Passive and concentration flows delaying visible equity damage",
        cause_node=None,
        effect_node="spx",
        mechanism="Index concentration and passive flows can mask deterioration under the surface until breadth, earnings, or liquidity breaks.",
        trigger_types=("speculative_overextension",),
        observable_tests=("market breadth", "SPX equal-weight versus cap-weight", "top-7 concentration", "options positioning"),
        falsification=("Breadth improves while concentration risk stays high", "equal-weight leadership confirms broad risk appetite"),
        structural_score=0.66,
    ),
)


class CausalExpansionEngine:
    def __init__(self, graph) -> None:
        self.graph = graph

    def assess_current(
        self,
        risk_index: dict[str, Any],
        regime: dict[str, Any],
    ) -> dict[str, Any]:
        trigger = self._trigger_state(risk_index, regime)
        candidates = self._candidate_mechanisms(risk_index, regime, trigger)
        prompt = self._ai_prompt(risk_index, regime, trigger)
        return {
            "trigger": trigger,
            "ai_prompt": prompt,
            "candidate_mechanisms": candidates,
            "governance": {
                "core_rule": "AI may propose mechanisms, but daliyQ validates and governs graph changes.",
                "allowed_statuses": ["rejected", "watchlist", "candidate_graph", "eligible_for_promotion"],
                "promotion_rule": "A mechanism needs strong structural fit, measurable evidence, repeated validation, and human approval before entering the core graph.",
            },
        }

    def _trigger_state(self, risk_index: dict[str, Any], regime: dict[str, Any]) -> dict[str, Any]:
        hidden = regime.get("hidden_risk") or {}
        damage = regime.get("realized_damage") or {}
        pressure = regime.get("forward_pressure") or {}
        hidden_score = float(hidden.get("score") or 0)
        damage_score = float(damage.get("score") or 0)
        pressure_score = float(pressure.get("score") or risk_index.get("gfcri_value") or 0)
        gap = max(0.0, hidden_score - damage_score)
        trigger_type = "hidden_pressure_without_damage" if hidden_score >= 50 and damage_score < 20 else "monitoring"
        return {
            "type": trigger_type,
            "hidden_risk": round(hidden_score, 2),
            "realized_damage": round(damage_score, 2),
            "forward_pressure": round(pressure_score, 2),
            "gap": round(gap, 2),
            "reason": (
                "Hidden risk is elevated while realized damage remains low."
                if trigger_type == "hidden_pressure_without_damage"
                else "No strong hidden-pressure / damage gap trigger."
            ),
        }

    def _candidate_mechanisms(
        self,
        risk_index: dict[str, Any],
        regime: dict[str, Any],
        trigger: dict[str, Any],
    ) -> list[dict[str, Any]]:
        detail_types = {
            d.get("type")
            for d in (risk_index.get("divergence") or {}).get("details", [])
            if d.get("type")
        }
        node_contrib = risk_index.get("node_contributions") or {}
        candidates = []
        for template in CANDIDATE_TEMPLATES:
            if not detail_types.intersection(template.trigger_types):
                continue
            candidates.append(self._score_candidate(template, node_contrib, trigger))
        candidates.sort(key=lambda x: x["overall_confidence"], reverse=True)
        return candidates

    def _score_candidate(
        self,
        template: CandidateTemplate,
        node_contrib: dict[str, Any],
        trigger: dict[str, Any],
    ) -> dict[str, Any]:
        nodes = [n for n in [template.cause_node, template.effect_node] if n]
        known_nodes = [n for n in nodes if n in node_contrib or n in self.graph.nodes]
        data_coverage = len(known_nodes) / max(len(nodes), 1)
        graph_support = self._graph_support(template.cause_node, template.effect_node)
        falsifiability = 1.0 if template.falsification else 0.0
        trigger_strength = min(1.0, float(trigger.get("gap") or 0) / 100.0)
        overall = (
            0.25 * data_coverage
            + 0.25 * graph_support
            + 0.25 * template.structural_score
            + 0.15 * falsifiability
            + 0.10 * trigger_strength
        )
        decision = self._decision(overall, data_coverage, falsifiability)
        return {
            "id": template.id,
            "title": template.title,
            "cause_node": template.cause_node,
            "effect_node": template.effect_node,
            "mechanism": template.mechanism,
            "observable_tests": list(template.observable_tests),
            "falsification": list(template.falsification),
            "scores": {
                "data_coverage": round(data_coverage, 2),
                "graph_support": round(graph_support, 2),
                "structural_score": round(template.structural_score, 2),
                "falsifiability": round(falsifiability, 2),
                "trigger_strength": round(trigger_strength, 2),
            },
            "overall_confidence": round(overall, 2),
            "decision": decision,
            "graph_status": "candidate_graph" if decision == "candidate_graph" else decision,
            "validation_note": self._validation_note(overall, graph_support, data_coverage),
        }

    def score_external_candidate(
        self,
        mechanism: dict[str, Any],
        node_contrib: dict[str, Any],
        trigger: dict[str, Any],
        source: str = "ai",
    ) -> dict[str, Any]:
        cause = mechanism.get("cause_node")
        effect = mechanism.get("effect_node")
        nodes = [n for n in [cause, effect] if n]
        known_nodes = [n for n in nodes if n in node_contrib or n in self.graph.nodes]
        data_coverage = len(known_nodes) / max(len(nodes), 1)
        graph_support = self._graph_support(cause, effect)
        falsification = mechanism.get("falsification") or []
        falsifiability = 1.0 if falsification else 0.0
        structural_score = float(mechanism.get("confidence") or 0.5)
        trigger_strength = min(1.0, float(trigger.get("gap") or 0) / 100.0)
        overall = (
            0.20 * data_coverage
            + 0.20 * graph_support
            + 0.25 * min(max(structural_score, 0), 1)
            + 0.20 * falsifiability
            + 0.15 * trigger_strength
        )
        decision = self._decision(overall, data_coverage, falsifiability)
        cid = mechanism.get("id") or self._candidate_id(source, cause, effect, mechanism.get("hypothesis") or mechanism.get("mechanism"))
        return {
            "id": cid,
            "title": mechanism.get("hypothesis") or mechanism.get("title") or cid,
            "cause_node": cause,
            "effect_node": effect,
            "mechanism": mechanism.get("mechanism") or "",
            "observable_tests": list(mechanism.get("observable_tests") or []),
            "falsification": list(falsification),
            "scores": {
                "data_coverage": round(data_coverage, 2),
                "graph_support": round(graph_support, 2),
                "structural_score": round(min(max(structural_score, 0), 1), 2),
                "falsifiability": round(falsifiability, 2),
                "trigger_strength": round(trigger_strength, 2),
            },
            "overall_confidence": round(overall, 2),
            "decision": decision,
            "graph_status": "candidate_graph" if decision == "candidate_graph" else decision,
            "validation_note": self._validation_note(overall, graph_support, data_coverage),
            "source": source,
        }

    def _graph_support(self, cause: str | None, effect: str | None) -> float:
        if not cause or not effect:
            return 0.25
        if cause not in self.graph.nodes or effect not in self.graph.nodes:
            return 0.0
        direct = any(e.source_node == cause and e.target_node == effect for e in self.graph.edges.values())
        if direct:
            return 1.0
        try:
            paths = self.graph.find_all_causal_paths(cause, effect, max_depth=4)
        except Exception:
            paths = []
        return 0.65 if paths else 0.35

    @staticmethod
    def _candidate_id(source: str, cause: str | None, effect: str | None, text: str | None) -> str:
        import hashlib
        raw = f"{source}:{cause or 'unknown'}:{effect or 'unknown'}:{text or ''}"
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
        return f"{source}_{cause or 'unknown'}_{effect or 'unknown'}_{digest}"

    @staticmethod
    def _decision(overall: float, data_coverage: float, falsifiability: float) -> str:
        if falsifiability < 1 or data_coverage < 0.5 or overall < 0.45:
            return "watchlist" if overall >= 0.35 else "rejected"
        if overall >= 0.80:
            return "eligible_for_promotion"
        if overall >= 0.65:
            return "candidate_graph"
        return "watchlist"

    @staticmethod
    def _validation_note(overall: float, graph_support: float, data_coverage: float) -> str:
        if overall >= 0.80:
            return "Strong candidate, but still requires repeated validation and human approval."
        if graph_support < 0.5:
            return "Candidate is structurally plausible but weakly supported by the current graph."
        if data_coverage < 0.75:
            return "Candidate needs better measurable indicators before promotion."
        return "Candidate is suitable for watchlist or candidate graph validation."

    @staticmethod
    def _ai_prompt(
        risk_index: dict[str, Any],
        regime: dict[str, Any],
        trigger: dict[str, Any],
    ) -> dict[str, Any]:
        divergence_details = (risk_index.get("divergence") or {}).get("details", [])
        top_factors = (regime.get("factors") or [])[:5]
        return {
            "system": (
                "You are a macro-financial causal research assistant. Propose candidate causal mechanisms only. "
                "Do not provide investment advice. Do not assert causality without falsifiable tests. "
                "Use only observable variables or clearly label missing variables."
            ),
            "user_payload": {
                "task": "Explain why hidden pressure is high while realized damage remains low, and propose candidate causal graph expansions.",
                "trigger": trigger,
                "gfcri": risk_index.get("gfcri_value"),
                "alert_level": risk_index.get("alert_level"),
                "hidden_risk_details": divergence_details,
                "top_factor_contributions": top_factors,
                "required_json_schema": {
                    "candidate_mechanisms": [
                        {
                            "hypothesis": "string",
                            "cause_node": "existing node id or proposed observable variable",
                            "effect_node": "existing node id",
                            "mechanism": "string",
                            "observable_tests": ["string"],
                            "falsification": ["string"],
                            "confidence": "0-1",
                            "recommended_status": "watchlist | candidate_graph | reject",
                        }
                    ]
                },
                "constraints": [
                    "No direct mutation of the core graph.",
                    "Every mechanism must include falsification tests.",
                    "Prefer measurable variables and existing node IDs.",
                    "Separate pressure suppression from realized damage.",
                ],
            },
        }
