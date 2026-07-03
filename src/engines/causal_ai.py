"""Controlled LLM proposal generation for causal graph expansion."""

from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic
from loguru import logger

from src.config import settings
from src.engines.causal_expansion import CausalExpansionEngine


class CausalAIProposalEngine:
    def __init__(self, graph) -> None:
        self.graph = graph
        self._settings = settings

    @property
    def available(self) -> bool:
        return bool(self._settings.anthropic_api_key)

    def propose(
        self,
        base_assessment: dict[str, Any],
        risk_index: dict[str, Any],
        regime: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.available:
            return {
                "available": False,
                "error": "ANTHROPIC_API_KEY is not configured",
                "candidate_mechanisms": [],
            }

        prompt = base_assessment.get("ai_prompt") or {}
        system = prompt.get("system") or ""
        payload = prompt.get("user_payload") or {}
        content = (
            "Return strict JSON only. Do not include markdown.\n\n"
            + json.dumps(payload, ensure_ascii=False, default=str)
        )

        client = Anthropic(
            api_key=self._settings.anthropic_api_key,
            base_url=self._settings.anthropic_base_url,
        )
        try:
            response = client.messages.create(
                model=self._settings.anthropic_model,
                max_tokens=2500,
                system=system,
                messages=[{"role": "user", "content": content}],
            )
            text = response.content[0].text.strip()
            parsed = self._parse_json(text)
        except Exception as exc:
            logger.warning(f"Causal AI proposal failed: {exc}")
            return {
                "available": True,
                "error": str(exc),
                "candidate_mechanisms": [],
            }

        mechanisms = parsed.get("candidate_mechanisms") or []
        scorer = CausalExpansionEngine(self.graph)
        trigger = base_assessment.get("trigger") or {}
        node_contrib = risk_index.get("node_contributions") or {}
        scored = [
            scorer.score_external_candidate(m, node_contrib, trigger, source="ai")
            for m in mechanisms
            if isinstance(m, dict)
        ]
        scored.sort(key=lambda x: x["overall_confidence"], reverse=True)
        return {
            "available": True,
            "model": self._settings.anthropic_model,
            "raw_count": len(mechanisms),
            "candidate_mechanisms": scored[:8],
        }

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start:end + 1])
            raise
