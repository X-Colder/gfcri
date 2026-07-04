"""Dynamic core risk theme engine.

Ranks the risk themes that matter now by combining current GFCRI model
evidence, active transmission channels, hidden-risk divergence, and official
institutional radar signals. The engine is deliberately theme-general: AI may
be the top theme today, but credit, dollar liquidity, yen carry, Europe,
China, or commodities can take over when their evidence strengthens.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.engines.causal_expansion import CausalExpansionEngine
from src.engines.institutional_radar import cached_or_persisted_institutional_radar
from src.storage.database import get_latest_risk_index, save_causal_candidates


@dataclass(frozen=True)
class ThemeDefinition:
    id: str
    title: str
    description: str
    nodes: tuple[str, ...]
    chains: tuple[str, ...]
    sub_indices: tuple[str, ...]
    radar_themes: tuple[str, ...]
    watch_metrics: tuple[str, ...]
    institutional_value: str


THEMES: tuple[ThemeDefinition, ...] = (
    ThemeDefinition(
        id="ai_capex_tech_cycle",
        title="AI Capex / Tech Concentration",
        description="Tracks whether AI investment, semiconductor momentum, mega-cap concentration, and related credit proxies are becoming a systemic risk focus.",
        nodes=("ai_capex", "orcl_cds", "sox", "dram_spot", "nand_spot", "spx", "kospi"),
        chains=("ai_semi_cycle",),
        sub_indices=("SI_US_EQUITY", "SI_ASIA_EQUITY", "SI_CREDIT", "SI_COMMODITY"),
        radar_themes=("AI Capex / Tech Bubble",),
        watch_metrics=("AI/Cloud capex basket", "SOX", "DRAM/NAND producer basket", "AI/cloud credit proxy", "SPX breadth"),
        institutional_value="Identifies when a popular growth narrative is masking concentration, credit, or supply-chain fragility.",
    ),
    ThemeDefinition(
        id="dollar_liquidity",
        title="Dollar Liquidity / Funding Squeeze",
        description="Tracks broad dollar strength, US rates, repo funding, and EM FX sensitivity.",
        nodes=("dxy", "ust_10y", "ust_2y", "fred_sofr", "sofr_effr_spread", "global_liqd", "krw_usd", "eem", "emb"),
        chains=("fed_cascade", "dollar_squeeze", "safe_haven_flight"),
        sub_indices=("SI_RATES", "SI_FX", "SI_CREDIT", "SI_SENTIMENT"),
        radar_themes=("Dollar Liquidity", "EM Debt / FX"),
        watch_metrics=("DXY", "US 10Y", "SOFR-EFFR spread", "KRW/USD", "EM bonds"),
        institutional_value="Explains when tightening dollar funding can transmit from rates into FX, credit, and EM assets.",
    ),
    ThemeDefinition(
        id="global_credit",
        title="Global Credit / Default Cycle",
        description="Tracks corporate credit spreads, loan delinquency, bank funding, and downgrade/default pressure.",
        nodes=("fred_hy_spread", "fred_bbb_spread", "fred_ic_spread", "fred_baa10y_spread", "fred_all_loan_delinquency", "hyg", "lqd", "emb", "kre"),
        chains=("credit_contagion", "housing_bank_doom"),
        sub_indices=("SI_CREDIT", "SI_BANKING"),
        radar_themes=("Global Credit", "Bank Funding"),
        watch_metrics=("HY OAS", "BBB OAS", "BAA-10Y spread", "loan delinquency", "regional banks"),
        institutional_value="Turns a broad credit warning into traceable funding, downgrade, and default-cycle evidence.",
    ),
    ThemeDefinition(
        id="japan_yen_carry",
        title="Japan Carry / Yen Reversal",
        description="Tracks yen depreciation pressure, Japan equity sensitivity, volatility, and carry-unwind risk.",
        nodes=("jpy_usd", "nikkei", "vix", "ust_10y", "dxy"),
        chains=("yen_carry_unwind", "safe_haven_flight"),
        sub_indices=("SI_FX", "SI_ASIA_EQUITY", "SI_SENTIMENT"),
        radar_themes=("Japan Carry / Yen",),
        watch_metrics=("USD/JPY", "Nikkei", "VIX", "US-Japan rate differential", "carry positioning"),
        institutional_value="Surfaces risk when yen weakness looks supportive for equities but increases reversal and intervention risk.",
    ),
    ThemeDefinition(
        id="china_asia_spillover",
        title="China / Asia Spillover",
        description="Tracks China credit impulse proxies, CNY pressure, Hong Kong equities, Korea equities, and trade spillover.",
        nodes=("cn_social_finance_yoy", "cn_m1_yoy", "cn_lpr_1y", "cny_usd", "hsi", "kospi", "krw_usd", "kr_ca"),
        chains=("china_shockwave",),
        sub_indices=("SI_FX", "SI_ASIA_EQUITY", "SI_CREDIT", "SI_TRADE_SPILLOVER"),
        radar_themes=("China Credit",),
        watch_metrics=("China social finance", "CNY/USD", "Hang Seng", "KOSPI", "Korea current account"),
        institutional_value="Connects China-specific stress to Asian equity, FX, and trade-dependency transmission.",
    ),
    ThemeDefinition(
        id="europe_sovereign_credit",
        title="Europe Sovereign / Credit Contagion",
        description="Tracks Eurozone credit, Italy stress proxies, EUR/USD, European equities, and sovereign-bank feedback.",
        nodes=("fred_euro_hy_spread", "italy_etf", "eurusd", "stoxx50", "dxy"),
        chains=("europe_contagion",),
        sub_indices=("SI_EUROPE", "SI_FX", "SI_CREDIT"),
        radar_themes=("Europe Sovereign / Credit",),
        watch_metrics=("Euro HY OAS", "Italy risk proxy", "EUR/USD", "Euro Stoxx 50", "DXY"),
        institutional_value="Makes European sovereign, credit, and FX feedback loops visible before they dominate headlines.",
    ),
    ThemeDefinition(
        id="commodity_energy_shock",
        title="Commodity / Energy Shock",
        description="Tracks oil, gas, food, metals, gold, and the inflation-growth squeeze from supply shocks.",
        nodes=("oil_wti", "natgas", "wheat", "copper", "gold", "bdry"),
        chains=("food_energy_shock", "safe_haven_flight"),
        sub_indices=("SI_COMMODITY", "SI_SENTIMENT", "SI_FX"),
        radar_themes=("Commodity / Energy Shock",),
        watch_metrics=("WTI", "natural gas", "wheat", "copper", "gold", "shipping"),
        institutional_value="Separates growth-sensitive commodities from inflationary supply shocks and safe-haven demand.",
    ),
)


def latest_core_risk_themes(limit: int = 6, include_causal: bool = True, graph: Any | None = None) -> dict[str, Any]:
    risk = get_latest_risk_index()
    if not risk:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "index_date": None,
            "themes": [],
            "methodology": _methodology(),
            "causal": {"triggered": False, "candidate_count": 0, "candidates": []},
        }
    radar = cached_or_persisted_institutional_radar(limit=80)
    themes = [_score_theme(theme, risk, radar) for theme in THEMES]
    themes.sort(key=lambda item: item["priority_score"], reverse=True)
    themes = themes[:limit]
    causal = _causal_from_themes(risk, themes, graph) if include_causal and graph is not None else {
        "triggered": False,
        "candidate_count": 0,
        "candidates": [],
        "reason": "Causal expansion not requested for this call.",
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "index_date": str(risk.get("index_date")),
        "gfcri_value": float(risk.get("gfcri_value") or 0),
        "alert_level": risk.get("alert_level"),
        "themes": themes,
        "methodology": _methodology(),
        "radar_context": {
            "item_count": radar.get("item_count", 0),
            "theme_count": len(radar.get("theme_summary") or []),
            "source_health": radar.get("source_health") or [],
        },
        "causal": causal,
    }


def _score_theme(theme: ThemeDefinition, risk: dict[str, Any], radar: dict[str, Any]) -> dict[str, Any]:
    node_evidence = _node_evidence(theme, risk)
    chain_evidence = _chain_evidence(theme, risk)
    sub_index_evidence = _sub_index_evidence(theme, risk)
    radar_evidence = _radar_evidence(theme, radar)
    hidden_evidence = _hidden_evidence(theme, risk)

    model_score = max(node_evidence["score"], sub_index_evidence["score"])
    transmission_score = chain_evidence["score"]
    radar_score = radar_evidence["score"]
    hidden_score = hidden_evidence["score"]
    priority = min(
        100.0,
        0.42 * model_score
        + 0.24 * transmission_score
        + 0.20 * radar_score
        + 0.14 * hidden_score,
    )

    evidence = [
        *node_evidence["items"][:4],
        *chain_evidence["items"][:2],
        *sub_index_evidence["items"][:2],
        *radar_evidence["items"][:3],
        *hidden_evidence["items"][:2],
    ]
    return {
        "theme_id": theme.id,
        "title": theme.title,
        "description": theme.description,
        "priority_score": round(priority, 2),
        "status": _status(priority),
        "model_pressure": round(model_score, 2),
        "transmission_pressure": round(transmission_score, 2),
        "institutional_attention": round(radar_score, 2),
        "hidden_risk_alignment": round(hidden_score, 2),
        "watch_metrics": list(theme.watch_metrics),
        "affected_nodes": list(theme.nodes),
        "affected_chains": list(theme.chains),
        "evidence": evidence[:10],
        "why_it_matters": theme.institutional_value,
        "next_questions": _next_questions(theme, evidence),
    }


def _node_evidence(theme: ThemeDefinition, risk: dict[str, Any]) -> dict[str, Any]:
    contrib = risk.get("node_contributions") or {}
    rows = []
    for node_id in theme.nodes:
        info = contrib.get(node_id)
        if not info:
            continue
        anomaly = float(info.get("anomaly_score") or 0) * 100
        abs_score = 0 if info.get("abs_score") is None else float(info.get("abs_score") or 0) * 100
        pressure = max(anomaly, abs_score)
        if pressure < 15:
            continue
        rows.append({
            "type": "node",
            "label": info.get("display_name") or node_id,
            "node_id": node_id,
            "value": round(pressure, 1),
            "detail": f"Directional pressure {anomaly:.1f}; absolute stress {abs_score:.1f}; z-score {float(info.get('zscore') or 0):.2f}.",
        })
    rows.sort(key=lambda item: item["value"], reverse=True)
    score = sum(item["value"] for item in rows[:5]) / max(len(rows[:5]), 1) if rows else 0.0
    return {"score": score, "items": rows}


def _chain_evidence(theme: ThemeDefinition, risk: dict[str, Any]) -> dict[str, Any]:
    chains = risk.get("chain_details") or {}
    chain_list = chains if isinstance(chains, list) else list(chains.values())
    rows = []
    for chain in chain_list:
        if chain.get("id") not in theme.chains:
            continue
        stress = float(chain.get("stress") or 0)
        rows.append({
            "type": "chain",
            "label": chain.get("name") or chain.get("id"),
            "chain_id": chain.get("id"),
            "value": round(stress, 1),
            "detail": f"Transmission stress {stress:.1f}; active={bool(chain.get('active'))}.",
        })
    rows.sort(key=lambda item: item["value"], reverse=True)
    score = max([row["value"] for row in rows], default=0.0)
    return {"score": score, "items": rows}


def _sub_index_evidence(theme: ThemeDefinition, risk: dict[str, Any]) -> dict[str, Any]:
    details = risk.get("sub_index_details") or {}
    rows = []
    for sub_id in theme.sub_indices:
        info = details.get(sub_id)
        if not info:
            continue
        score = float(info.get("score") or 0)
        rows.append({
            "type": "sub_index",
            "label": info.get("name") or sub_id,
            "sub_index_id": sub_id,
            "value": round(score, 1),
            "detail": f"Sub-index pressure {score:.1f}; top driver {info.get('top_driver') or '-'}; transmission {float(info.get('transmission') or 0):.2f}.",
        })
    rows.sort(key=lambda item: item["value"], reverse=True)
    score = max([row["value"] for row in rows], default=0.0)
    return {"score": score, "items": rows}


def _radar_evidence(theme: ThemeDefinition, radar: dict[str, Any]) -> dict[str, Any]:
    rows = []
    wanted = set(theme.radar_themes)
    node_set = set(theme.nodes)
    chain_set = set(theme.chains)
    for item in radar.get("items") or []:
        item_themes = set(item.get("risk_themes") or [])
        item_nodes = set(item.get("affected_nodes") or [])
        item_chains = set(item.get("affected_chains") or [])
        if not (wanted.intersection(item_themes) or node_set.intersection(item_nodes) or chain_set.intersection(item_chains)):
            continue
        importance = float(item.get("importance_score") or 0)
        rows.append({
            "type": "institutional_radar",
            "label": item.get("title"),
            "source": item.get("source"),
            "url": item.get("url"),
            "value": round(importance, 1),
            "detail": f"{item.get('source')} mapped this signal to {', '.join(item.get('risk_themes') or ['General Macro / Policy'])}.",
        })
    rows.sort(key=lambda item: item["value"], reverse=True)
    if not rows:
        return {"score": 0.0, "items": []}
    score = min(100.0, sum(row["value"] for row in rows[:5]) / max(len(rows[:5]), 1) + min(20, len(rows) * 2))
    return {"score": score, "items": rows[:5]}


def _hidden_evidence(theme: ThemeDefinition, risk: dict[str, Any]) -> dict[str, Any]:
    divergence = risk.get("divergence") or {}
    boost = float(risk.get("undercurrent_boost") or 0)
    details = divergence.get("details") or []
    rows = []
    theme_nodes = set(theme.nodes)
    text = " ".join([theme.id, theme.title, theme.description]).lower()
    for detail in details:
        raw = " ".join(str(v) for v in detail.values()).lower() if isinstance(detail, dict) else str(detail).lower()
        node_hit = any(node in raw for node in theme_nodes)
        keyword_hit = any(token in raw for token in text.split("/") + text.split())
        if node_hit or keyword_hit:
            rows.append({
                "type": "hidden_risk",
                "label": detail.get("title") if isinstance(detail, dict) else "Hidden risk divergence",
                "value": round(min(100.0, 40 + boost * 3), 1),
                "detail": detail.get("detail") if isinstance(detail, dict) else str(detail),
            })
    if not rows and boost > 0:
        return {"score": min(70.0, boost * 4), "items": []}
    score = max([row["value"] for row in rows], default=0.0)
    return {"score": score, "items": rows}


def _causal_from_themes(risk: dict[str, Any], themes: list[dict[str, Any]], graph: Any) -> dict[str, Any]:
    top = themes[0] if themes else None
    if not top or float(top.get("priority_score") or 0) < 45:
        return {"triggered": False, "candidate_count": 0, "candidates": [], "reason": "No high-priority theme trigger."}
    trigger = {
        "type": "theme_priority",
        "theme_id": top.get("theme_id"),
        "theme_title": top.get("title"),
        "theme_priority_score": top.get("priority_score"),
        "gap": float((risk.get("divergence") or {}).get("gap") or 0),
        "reason": f"Top dynamic theme is {top.get('title')} with priority {top.get('priority_score')}.",
    }
    engine = CausalExpansionEngine(graph)
    node_contrib = risk.get("node_contributions") or {}
    candidates = []
    for idx, evidence in enumerate((top.get("evidence") or [])[:3]):
        if evidence.get("type") not in {"institutional_radar", "node", "chain"}:
            continue
        affected_nodes = top.get("affected_nodes") or []
        cause = affected_nodes[0] if affected_nodes else None
        effect = affected_nodes[1] if len(affected_nodes) > 1 else None
        mechanism = {
            "id": f"theme_{top.get('theme_id')}_{idx}",
            "hypothesis": f"{top.get('title')} may be changing the transmission path behind {evidence.get('label')}.",
            "cause_node": cause,
            "effect_node": effect,
            "mechanism": f"Dynamic theme evidence suggests {top.get('description')} Evidence: {evidence.get('detail')}",
            "observable_tests": list(top.get("watch_metrics") or [])[:5],
            "falsification": [
                "Theme priority falls below 35 for two consecutive observations.",
                "Mapped nodes normalize while institutional attention remains high.",
                "Transmission channel pressure fails to confirm the theme.",
            ],
            "confidence": min(0.9, float(top.get("priority_score") or 0) / 100.0),
        }
        candidates.append(engine.score_external_candidate(mechanism, node_contrib, trigger, source="core_theme"))
    if candidates:
        save_causal_candidates(str(risk.get("index_date")), trigger, candidates)
    return {
        "triggered": bool(candidates),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "trigger": trigger,
    }


def _status(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 55:
        return "priority"
    if score >= 35:
        return "watch"
    return "background"


def _next_questions(theme: ThemeDefinition, evidence: list[dict[str, Any]]) -> list[str]:
    questions = [
        f"Are {', '.join(theme.watch_metrics[:3])} confirming the same direction?",
        "Is the pressure still only market pricing, or is it entering credit, employment, trade, or funding damage?",
        "What observable evidence would falsify this theme within the next two weeks?",
    ]
    if any(e.get("type") == "institutional_radar" for e in evidence):
        questions.append("Do new official reports add a mechanism that is missing from the current causal graph?")
    return questions


def _methodology() -> str:
    return (
        "Dynamic Core Risk Themes v1 ranks reusable macro-financial themes using "
        "current GFCRI node pressure, sub-index stress, active transmission channels, "
        "hidden-risk divergence, and official institutional radar attention. It is a "
        "prioritization layer, not an investment recommendation."
    )
