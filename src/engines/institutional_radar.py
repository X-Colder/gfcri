"""Institutional intelligence radar.

Fetches public institutional feeds and maps each item to GFCRI risk themes,
nodes, and transmission chains. The radar is deliberately metadata-first:
it stores titles, links, short summaries, source quality and model impact,
not copyrighted full text.
"""

from __future__ import annotations

import email.utils
import hashlib
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests
from loguru import logger


@dataclass(frozen=True)
class RadarSource:
    id: str
    name: str
    tier: str
    url: str
    source_type: str = "rss"


SOURCES: tuple[RadarSource, ...] = (
    RadarSource("bis_all", "BIS", "A", "https://www.bis.org/doclist/rss_all_categories.rss"),
    RadarSource("bis_research", "BIS Research", "A", "https://www.bis.org/doclist/bis_fsi_publs.rss"),
    RadarSource("fed_press", "Federal Reserve", "A", "https://www.federalreserve.gov/feeds/press_all.xml"),
    RadarSource("ecb_press", "European Central Bank", "A", "https://www.ecb.europa.eu/rss/press.xml"),
    RadarSource("ecb_publications", "ECB Publications", "A", "https://www.ecb.europa.eu/rss/pub.html"),
    RadarSource("imf_news", "IMF", "A", "https://www.imf.org/en/news/rss"),
)


THEME_RULES: list[dict[str, Any]] = [
    {
        "theme": "AI Capex / Tech Bubble",
        "keywords": ("artificial intelligence", " ai ", "data centre", "data center", "cloud", "semiconductor", "private credit", "technology investment"),
        "nodes": ("ai_capex", "orcl_cds", "sox", "dram_spot", "nand_spot"),
        "chains": ("ai_semi_cycle",),
        "risk_direction": "pressure_up",
    },
    {
        "theme": "Dollar Liquidity",
        "keywords": ("dollar", "liquidity", "swap line", "funding", "repo", "sofr", "balance sheet"),
        "nodes": ("dxy", "global_liqd", "fred_sofr", "sofr_effr_spread", "ust_10y"),
        "chains": ("fed_cascade", "dollar_squeeze"),
        "risk_direction": "pressure_up",
    },
    {
        "theme": "Global Credit",
        "keywords": ("credit", "default", "downgrade", "spread", "corporate bond", "high yield", "bankruptcy"),
        "nodes": ("fred_hy_spread", "fred_bbb_spread", "fred_baa10y_spread", "hyg", "lqd"),
        "chains": ("credit_contagion",),
        "risk_direction": "pressure_up",
    },
    {
        "theme": "Bank Funding",
        "keywords": ("bank", "banking", "supervision", "capital", "liquidity coverage", "repo", "deposit", "funding"),
        "nodes": ("kre", "fred_sofr", "sofr_effr_spread", "fred_all_loan_delinquency"),
        "chains": ("housing_bank_doom",),
        "risk_direction": "pressure_up",
    },
    {
        "theme": "Europe Sovereign / Credit",
        "keywords": ("euro area", "eurozone", "ecb", "sovereign", "italy", "spread", "euro high yield"),
        "nodes": ("fred_euro_hy_spread", "italy_etf", "eurusd", "stoxx50"),
        "chains": ("europe_contagion",),
        "risk_direction": "pressure_up",
    },
    {
        "theme": "China Credit",
        "keywords": ("china", "renminbi", "yuan", "property", "social financing", "credit impulse", "lpr"),
        "nodes": ("cn_social_finance_yoy", "cn_m1_yoy", "cn_lpr_1y", "cny_usd", "hsi"),
        "chains": ("china_shockwave",),
        "risk_direction": "pressure_up",
    },
    {
        "theme": "Commodity / Energy Shock",
        "keywords": ("oil", "energy", "gas", "commodity", "food", "wheat", "inflation"),
        "nodes": ("oil_wti", "natgas", "wheat", "copper", "gold"),
        "chains": ("food_energy_shock", "safe_haven_flight"),
        "risk_direction": "pressure_up",
    },
    {
        "theme": "Japan Carry / Yen",
        "keywords": ("japan", "yen", "boj", "carry trade", "jgb"),
        "nodes": ("jpy_usd", "nikkei", "vix"),
        "chains": ("yen_carry_unwind",),
        "risk_direction": "pressure_up",
    },
    {
        "theme": "EM Debt / FX",
        "keywords": ("emerging market", "em debt", "sovereign debt", "capital flow", "fx pressure"),
        "nodes": ("emb", "eem", "dxy"),
        "chains": ("dollar_squeeze", "crypto_contagion"),
        "risk_direction": "pressure_up",
    },
]


_CACHE: dict[str, Any] = {"ts": 0.0, "data": None}
_TTL_SECONDS = 900
_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; GFCRI/1.0; +https://gfcri.local) "
        "AppleWebKit/537.36"
    ),
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*;q=0.8",
}


def latest_institutional_radar(limit: int = 30, force_refresh: bool = False) -> dict[str, Any]:
    now = time.time()
    if not force_refresh and _CACHE["data"] and now - float(_CACHE["ts"]) < _TTL_SECONDS:
        return _limited_response(_CACHE["data"], limit)

    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    source_latency_ms: dict[str, int] = {}
    for source in SOURCES:
        started = time.perf_counter()
        try:
            fetched = _fetch_source(source)
            source_latency_ms[source.id] = int((time.perf_counter() - started) * 1000)
            items.extend(fetched)
        except Exception as exc:
            source_latency_ms[source.id] = int((time.perf_counter() - started) * 1000)
            logger.warning(f"Institutional radar fetch failed for {source.id}: {exc}")
            errors.append({"source": source.name, "error": str(exc)})

    items.sort(key=lambda x: x.get("published_at") or "", reverse=True)
    items.sort(key=lambda x: float(x.get("importance_score") or 0), reverse=True)

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_count": len(SOURCES),
        "item_count": len(items),
        "sources": [source.__dict__ for source in SOURCES],
        "items": items,
        "theme_summary": _theme_summary(items),
        "errors": errors,
        "source_health": _source_health_from_fetch(source_latency_ms, errors, items),
        "source_latency_ms": source_latency_ms,
        "methodology": (
            "Institutional Radar v1 fetches public RSS/Atom metadata from official institutional sources "
            "and maps titles/summaries to GFCRI themes, nodes and chains using transparent keyword rules. "
            "It does not ingest copyrighted full text."
        ),
    }
    _CACHE["ts"] = now
    _CACHE["data"] = data
    _persist_snapshot(data)
    return _limited_response(data, limit)


def _limited_response(data: dict[str, Any], limit: int) -> dict[str, Any]:
    items = list(data.get("items") or [])[:limit]
    response = dict(data)
    response["items"] = items
    response["item_count"] = len(items)
    response["theme_summary"] = _theme_summary(items)
    return response


def cached_or_persisted_institutional_radar(limit: int = 50) -> dict[str, Any]:
    """Return radar data without outbound network calls."""
    if _CACHE["data"]:
        return _limited_response(_CACHE["data"], limit)
    try:
        from src.storage.database import get_institutional_radar_items, get_institutional_radar_source_health

        rows = get_institutional_radar_items(limit=limit)
        items = [_item_from_row(row) for row in rows]
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_count": len(SOURCES),
            "item_count": len(items),
            "sources": [source.__dict__ for source in SOURCES],
            "items": items,
            "theme_summary": _theme_summary(items),
            "errors": [],
            "source_health": get_institutional_radar_source_health(),
            "source_latency_ms": {},
            "methodology": "Returned from persisted Institutional Radar metadata without outbound network calls.",
        }
    except Exception as exc:
        logger.warning(f"Institutional radar persisted fallback failed: {exc}")
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_count": len(SOURCES),
            "item_count": 0,
            "sources": [source.__dict__ for source in SOURCES],
            "items": [],
            "theme_summary": [],
            "errors": [{"source": "persisted_radar", "error": str(exc)}],
            "source_health": [],
            "source_latency_ms": {},
            "methodology": "Institutional Radar persisted fallback returned no data.",
        }


def _fetch_source(source: RadarSource) -> list[dict[str, Any]]:
    resp = requests.get(source.url, timeout=12, headers=_REQUEST_HEADERS)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    entries = _rss_entries(root) or _atom_entries(root)
    output = []
    for entry in entries[:12]:
        mapped = _map_item(entry["title"], entry.get("summary", ""))
        importance = _importance_score(source, entry, mapped)
        output.append({
            "id": _stable_id(source.id, entry.get("link", ""), entry["title"]),
            "source": source.name,
            "source_id": source.id,
            "source_tier": source.tier,
            "title": entry["title"],
            "summary": entry.get("summary", ""),
            "url": entry.get("link", source.url),
            "published_at": entry.get("published_at"),
            "risk_themes": mapped["themes"],
            "affected_nodes": mapped["nodes"],
            "affected_chains": mapped["chains"],
            "risk_direction": mapped["risk_direction"],
            "confidence": mapped["confidence"],
            "importance_score": importance["score"],
            "importance_reasons": importance["reasons"],
        })
    return output


def _importance_score(source: RadarSource, entry: dict[str, Any], mapped: dict[str, Any]) -> dict[str, Any]:
    score = 35.0 if source.tier == "A" else 24.0
    reasons = [f"Tier {source.tier} official source"]
    theme_count = len([t for t in mapped.get("themes", []) if t != "General Macro / Policy"])
    if theme_count:
        score += min(25.0, 8.0 * theme_count)
        reasons.append(f"{theme_count} mapped GFCRI risk theme(s)")
    node_count = len(mapped.get("nodes") or [])
    chain_count = len(mapped.get("chains") or [])
    if node_count:
        score += min(18.0, 2.5 * node_count)
        reasons.append(f"{node_count} affected model node(s)")
    if chain_count:
        score += min(16.0, 5.0 * chain_count)
        reasons.append(f"{chain_count} affected transmission channel(s)")

    text = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
    report_keywords = ("financial stability", "systemic", "risk", "credit", "liquidity", "bank", "stress", "inflation", "debt")
    hits = [kw for kw in report_keywords if kw in text]
    if hits:
        score += min(18.0, 4.0 * len(hits))
        reasons.append(f"Contains institutional risk keyword(s): {', '.join(hits[:4])}")

    published_at = entry.get("published_at")
    try:
        if published_at:
            dt = datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
            age_days = max(0.0, (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 86400)
            recency_bonus = max(0.0, 12.0 - age_days)
            score += recency_bonus
            if recency_bonus >= 6:
                reasons.append("Fresh institutional signal")
    except Exception:
        pass

    return {"score": round(min(100.0, score), 2), "reasons": reasons[:6]}


def _source_health_from_fetch(
    source_latency_ms: dict[str, int],
    errors: list[dict[str, str]],
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    error_by_name = {e.get("source"): e.get("error") for e in errors}
    item_count_by_source: dict[str, int] = {}
    for item in items:
        sid = item.get("source_id")
        item_count_by_source[sid] = item_count_by_source.get(sid, 0) + 1
    rows = []
    for source in SOURCES:
        err = error_by_name.get(source.name)
        rows.append({
            "source_id": source.id,
            "source_name": source.name,
            "source_tier": source.tier,
            "url": source.url,
            "status": "error" if err else "ok",
            "last_error": err,
            "item_count": item_count_by_source.get(source.id, 0),
            "latency_ms": source_latency_ms.get(source.id, 0),
        })
    return rows


def _persist_snapshot(data: dict[str, Any]) -> None:
    try:
        from src.storage.database import save_institutional_radar_snapshot

        save_institutional_radar_snapshot(data)
    except Exception as exc:
        logger.warning(f"Institutional radar persistence failed: {exc}")


def _item_from_row(row: dict[str, Any]) -> dict[str, Any]:
    published = row.get("published_at")
    return {
        "id": row.get("item_id"),
        "source": row.get("source_name"),
        "source_id": row.get("source_id"),
        "source_tier": row.get("source_tier"),
        "title": row.get("title"),
        "summary": row.get("summary") or "",
        "url": row.get("url"),
        "published_at": published.isoformat() if hasattr(published, "isoformat") else published,
        "risk_themes": row.get("risk_themes") or [],
        "affected_nodes": row.get("affected_nodes") or [],
        "affected_chains": row.get("affected_chains") or [],
        "risk_direction": row.get("risk_direction") or "monitoring",
        "confidence": float(row.get("confidence") or 0),
        "importance_score": float(row.get("importance_score") or 0),
        "importance_reasons": row.get("importance_reasons") or [],
    }


def _rss_entries(root: ET.Element) -> list[dict[str, Any]]:
    entries = []
    for item in root.findall(".//item"):
        title = _text(item, "title")
        if not title:
            continue
        entries.append({
            "title": title,
            "link": _text(item, "link"),
            "summary": _clean(_text(item, "description")),
            "published_at": _parse_date(_text(item, "pubDate") or _text(item, "date")),
        })
    return entries


def _atom_entries(root: ET.Element) -> list[dict[str, Any]]:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entries = []
    for entry in root.findall(".//a:entry", ns):
        title = _text_ns(entry, "a:title", ns)
        if not title:
            continue
        link = ""
        link_el = entry.find("a:link", ns)
        if link_el is not None:
            link = link_el.attrib.get("href", "")
        entries.append({
            "title": title,
            "link": link,
            "summary": _clean(_text_ns(entry, "a:summary", ns) or _text_ns(entry, "a:content", ns)),
            "published_at": _parse_date(_text_ns(entry, "a:published", ns) or _text_ns(entry, "a:updated", ns)),
        })
    return entries


def _map_item(title: str, summary: str) -> dict[str, Any]:
    text = f" {title} {summary} ".lower()
    themes: list[str] = []
    nodes: set[str] = set()
    chains: set[str] = set()
    directions: list[str] = []

    for rule in THEME_RULES:
        if any(keyword in text for keyword in rule["keywords"]):
            themes.append(rule["theme"])
            nodes.update(rule["nodes"])
            chains.update(rule["chains"])
            directions.append(rule["risk_direction"])

    if not themes:
        themes.append("General Macro / Policy")
        directions.append("monitoring")

    return {
        "themes": themes[:4],
        "nodes": sorted(nodes),
        "chains": sorted(chains),
        "risk_direction": "pressure_up" if "pressure_up" in directions else "monitoring",
        "confidence": min(0.95, 0.45 + 0.15 * len(themes)),
    }


def _theme_summary(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, dict[str, Any]] = {}
    for item in items:
        for theme in item.get("risk_themes", []):
            row = counts.setdefault(theme, {"theme": theme, "count": 0, "sources": set(), "nodes": set(), "chains": set()})
            row["count"] += 1
            row["sources"].add(item["source"])
            row["nodes"].update(item.get("affected_nodes") or [])
            row["chains"].update(item.get("affected_chains") or [])
    rows = []
    for row in counts.values():
        rows.append({
            "theme": row["theme"],
            "count": row["count"],
            "sources": sorted(row["sources"]),
            "affected_nodes": sorted(row["nodes"]),
            "affected_chains": sorted(row["chains"]),
        })
    rows.sort(key=lambda x: x["count"], reverse=True)
    return rows[:8]


def _text(parent: ET.Element, tag: str) -> str:
    el = parent.find(tag)
    return _clean(el.text if el is not None else "")


def _text_ns(parent: ET.Element, tag: str, ns: dict[str, str]) -> str:
    el = parent.find(tag, ns)
    return _clean(el.text if el is not None else "")


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_date(raw: str) -> str | None:
    if not raw:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        except Exception:
            return raw


def _stable_id(source_id: str, link: str, title: str) -> str:
    seed = f"{source_id}:{link}:{title}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
