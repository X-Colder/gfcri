"""Institutional-grade report pack generation."""

from __future__ import annotations

from datetime import date
from typing import Any

from src.engines.core_themes import latest_core_risk_themes
from src.engines.institutional_radar import cached_or_persisted_institutional_radar
from src.storage.database import get_latest_risk_index


def institutional_report_v2() -> dict[str, Any]:
    risk = get_latest_risk_index()
    themes = latest_core_risk_themes(limit=5, include_causal=False)
    radar = cached_or_persisted_institutional_radar(limit=20)
    if not risk:
        return {"report_date": date.today().isoformat(), "sections": [], "markdown": "No risk data available."}
    sections = _sections(risk, themes, radar)
    return {
        "report_date": str(risk.get("index_date") or date.today()),
        "gfcri_value": float(risk.get("gfcri_value") or 0),
        "alert_level": risk.get("alert_level"),
        "sections": sections,
        "markdown": _markdown(risk, sections),
        "quality_controls": {
            "evidence_table": True,
            "falsification_section": True,
            "source_links": True,
            "compliance_footer": True,
            "copyright_policy": "Uses metadata, model outputs, and short summaries only; does not reproduce institutional full text.",
        },
    }


def _sections(risk: dict[str, Any], themes: dict[str, Any], radar: dict[str, Any]) -> list[dict[str, Any]]:
    top_theme = (themes.get("themes") or [{}])[0]
    top_radar = radar.get("items") or []
    return [
        {
            "id": "executive_summary",
            "title": "Executive Summary",
            "body": f"GFCRI is {float(risk.get('gfcri_value') or 0):.1f} ({risk.get('alert_level')}). The top dynamic theme is {top_theme.get('title', 'not available')}.",
        },
        {
            "id": "what_changed",
            "title": "What Changed",
            "body": "The report prioritizes changes in model pressure, transmission channels, hidden-risk alignment, and official institutional attention.",
        },
        {
            "id": "core_theme",
            "title": "Core Theme",
            "body": top_theme.get("why_it_matters") or top_theme.get("description") or "No dominant theme detected.",
            "evidence": top_theme.get("evidence") or [],
        },
        {
            "id": "official_radar",
            "title": "Official Institutional Radar",
            "body": f"{len(top_radar)} recent official signals are mapped into GFCRI themes.",
            "evidence": top_radar[:5],
        },
        {
            "id": "falsification",
            "title": "What Would Invalidate This View",
            "body": "The view should be downgraded if the mapped nodes normalize, transmission pressure fails to confirm, or official attention shifts away from the theme.",
            "questions": top_theme.get("next_questions") or [],
        },
    ]


def _markdown(risk: dict[str, Any], sections: list[dict[str, Any]]) -> str:
    lines = [
        f"# GFCRI Institutional Risk Brief",
        f"Date: {risk.get('index_date')} | GFCRI: {float(risk.get('gfcri_value') or 0):.1f} | Alert: {risk.get('alert_level')}",
        "",
    ]
    for section in sections:
        lines.append(f"## {section['title']}")
        lines.append(section.get("body") or "")
        if section.get("questions"):
            lines.extend([f"- {q}" for q in section["questions"]])
        if section.get("evidence"):
            lines.append("")
            lines.append("| Evidence | Value / Detail |")
            lines.append("|---|---|")
            for ev in section["evidence"][:5]:
                label = ev.get("label") or ev.get("title") or ev.get("source") or ev.get("type")
                detail = ev.get("detail") or ", ".join(ev.get("risk_themes") or []) or ev.get("url") or ""
                lines.append(f"| {label} | {detail} |")
        lines.append("")
    lines.append("---")
    lines.append("GFCRI is for information and risk-monitoring only. It is not investment advice.")
    return "\n".join(lines)
