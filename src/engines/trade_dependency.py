"""Global trade dependency spillover model.

This module intentionally starts with a transparent static dependency matrix.
It is not a replacement for UN Comtrade / OECD TiVA / IMF DOTS data. The goal is
to make cross-economy trade exposure explicit and reproducible before wiring in
live data feeds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


TRADE_DATA_VERSION = "static-v1"


@dataclass(frozen=True)
class TradeDependencyLink:
    source: str
    target: str
    sector: str
    description: str
    export_dependency: float
    sector_criticality: float
    substitution_difficulty: float
    affected_nodes: tuple[str, ...]

    @property
    def exposure_weight(self) -> float:
        return self.export_dependency * self.sector_criticality * self.substitution_difficulty


ECONOMY_MARKET_NODES: dict[str, tuple[str, ...]] = {
    "US": ("spx", "sox", "vix", "hyg", "lqd", "kre", "vnq", "dxy", "ust_10y", "consumer_stress"),
    "CN": ("cny_usd", "hsi", "copper"),
    "EU": ("eurusd", "stoxx50", "italy_etf", "natgas"),
    "JP": ("jpy_usd", "nikkei"),
    "KR": ("krw_usd", "kospi", "kr_cds_5y", "sox"),
    "GLOBAL_COMMODITY": ("oil_wti", "copper", "gold", "natgas", "wheat", "bdry"),
    "GLOBAL_EM": ("eem", "emb", "dxy"),
}


ECONOMY_NAMES: dict[str, str] = {
    "US": "United States",
    "CN": "China",
    "EU": "Eurozone",
    "JP": "Japan",
    "KR": "South Korea",
    "TW": "Taiwan",
    "DE": "Germany",
    "GB": "United Kingdom",
    "IN": "India",
    "BR": "Brazil",
    "AU": "Australia",
    "CA": "Canada",
    "MX": "Mexico",
    "SG": "Singapore",
    "GLOBAL_COMMODITY": "Global Commodities",
    "GLOBAL_EM": "Emerging Markets",
}


TRADE_DEPENDENCIES: tuple[TradeDependencyLink, ...] = (
    TradeDependencyLink("CN", "KR", "semiconductors", "China demand shock pressures Korea exports and KRW/KOSPI.", 0.28, 0.92, 0.78, ("krw_usd", "kospi", "kr_cds_5y")),
    TradeDependencyLink("CN", "JP", "capital goods", "China industrial slowdown weighs on Japan machinery, autos, and Nikkei.", 0.20, 0.76, 0.62, ("jpy_usd", "nikkei")),
    TradeDependencyLink("CN", "EU", "industrial exports", "China demand weakness hits European industrial exporters and luxury cyclicals.", 0.16, 0.68, 0.55, ("eurusd", "stoxx50")),
    TradeDependencyLink("CN", "AU", "bulk commodities", "China construction/manufacturing stress transmits to Australia through iron ore and bulk commodities.", 0.32, 0.88, 0.72, ("copper", "bdry")),
    TradeDependencyLink("US", "CN", "consumer demand", "US consumption slowdown pressures China export earnings and offshore China equities.", 0.20, 0.80, 0.58, ("cny_usd", "hsi")),
    TradeDependencyLink("US", "KR", "technology demand", "US tech demand shock transmits to Korea semiconductors and export cycle.", 0.18, 0.86, 0.70, ("kospi", "krw_usd", "sox")),
    TradeDependencyLink("US", "MX", "manufacturing chain", "US industrial and consumer stress affects Mexico manufacturing exports and peso risk.", 0.34, 0.74, 0.50, ("eem", "dxy")),
    TradeDependencyLink("EU", "DE", "intra-Europe demand", "Eurozone demand and funding stress feed into German industrial cyclicals.", 0.30, 0.70, 0.45, ("stoxx50", "eurusd")),
    TradeDependencyLink("EU", "GB", "financial/services trade", "Eurozone stress transmits to UK risk sentiment and European funding channels.", 0.18, 0.58, 0.45, ("stoxx50", "eurusd")),
    TradeDependencyLink("JP", "KR", "electronics inputs", "Japan electronics and capital goods stress can transmit into Korea semiconductor supply chains.", 0.12, 0.74, 0.66, ("kospi", "krw_usd")),
    TradeDependencyLink("KR", "CN", "electronics cycle", "Korea semiconductor stress is a leading signal for China electronics exports and offshore China equities.", 0.14, 0.82, 0.64, ("hsi", "cny_usd")),
    TradeDependencyLink("GLOBAL_COMMODITY", "EU", "energy imports", "Energy and food shocks raise Europe input costs and pressure Eurozone equities.", 0.24, 0.90, 0.78, ("stoxx50", "eurusd", "natgas")),
    TradeDependencyLink("GLOBAL_COMMODITY", "IN", "energy imports", "Oil and food shocks pressure import-heavy economies through inflation and FX channels.", 0.26, 0.84, 0.72, ("eem", "dxy", "oil_wti")),
    TradeDependencyLink("GLOBAL_COMMODITY", "BR", "commodity beta", "Commodity shocks affect Brazil through export income, inflation, and EM risk appetite.", 0.22, 0.70, 0.52, ("eem", "emb", "copper")),
    TradeDependencyLink("GLOBAL_EM", "BR", "portfolio flows", "Broad EM funding stress transmits into Brazil through equity and sovereign-credit channels.", 0.18, 0.66, 0.62, ("eem", "emb")),
    TradeDependencyLink("GLOBAL_EM", "IN", "portfolio flows", "Broad EM funding stress transmits into India through equity, FX, and external funding channels.", 0.16, 0.66, 0.58, ("eem", "emb", "dxy")),
)


class TradeDependencyEngine:
    """Scores cross-economy trade spillover pressure from market node stress."""

    def __init__(self, links: tuple[TradeDependencyLink, ...] = TRADE_DEPENDENCIES) -> None:
        self.links = links

    def compute(self, node_contributions: dict[str, dict[str, Any]]) -> dict[str, Any]:
        node_stress = {
            nid: self._stress_from_contribution(info)
            for nid, info in node_contributions.items()
        }
        return self.compute_from_node_stress(node_stress)

    def compute_from_node_stress(self, node_stress: dict[str, float]) -> dict[str, Any]:
        source_pressure = {
            economy: self._economy_pressure(nodes, node_stress)
            for economy, nodes in ECONOMY_MARKET_NODES.items()
        }

        target_exposures: dict[str, float] = {}
        link_results: list[dict[str, Any]] = []
        affected_node_scores: dict[str, float] = {}

        for link in self.links:
            pressure = source_pressure.get(link.source, 0.0)
            stress = min(1.0, pressure * link.exposure_weight)
            if stress <= 0:
                continue

            target_exposures[link.target] = min(1.0, target_exposures.get(link.target, 0.0) + stress)
            for nid in link.affected_nodes:
                affected_node_scores[nid] = max(affected_node_scores.get(nid, 0.0), stress)

            link_results.append({
                "source": link.source,
                "source_name": ECONOMY_NAMES.get(link.source, link.source),
                "target": link.target,
                "target_name": ECONOMY_NAMES.get(link.target, link.target),
                "sector": link.sector,
                "description": link.description,
                "source_pressure": round(pressure * 100, 2),
                "export_dependency": round(link.export_dependency, 4),
                "sector_criticality": round(link.sector_criticality, 4),
                "substitution_difficulty": round(link.substitution_difficulty, 4),
                "spillover": round(stress * 100, 2),
                "affected_nodes": list(link.affected_nodes),
            })

        top_links = sorted(link_results, key=lambda x: x["spillover"], reverse=True)
        top_exposures = sorted(target_exposures.items(), key=lambda x: x[1], reverse=True)

        # Top-heavy aggregation: systemic risk should rise when several important
        # counterparties are simultaneously exposed, without letting a long tail
        # of small links dominate.
        top5 = [score for _, score in top_exposures[:5]]
        if top5:
            score = 100.0 * (0.70 * max(top5) + 0.30 * (sum(top5) / len(top5)))
        else:
            score = 0.0

        return {
            "score": round(min(100.0, score), 2),
            "data_version": TRADE_DATA_VERSION,
            "economy_exposures": [
                {
                    "economy": econ,
                    "economy_name": ECONOMY_NAMES.get(econ, econ),
                    "score": round(val * 100, 2),
                }
                for econ, val in top_exposures
            ],
            "top_links": top_links[:8],
            "affected_node_scores": {k: round(v, 4) for k, v in affected_node_scores.items()},
            "source_pressure": {k: round(v * 100, 2) for k, v in source_pressure.items()},
        }

    @staticmethod
    def _stress_from_contribution(info: dict[str, Any]) -> float:
        anomaly = abs(float(info.get("anomaly_score") or 0.0))
        abs_score = info.get("abs_score")
        absolute = float(abs_score) if abs_score is not None else 0.0
        z_component = min(1.0, abs(float(info.get("zscore") or 0.0)) / 4.0)
        return max(anomaly, absolute, z_component)

    @staticmethod
    def _economy_pressure(nodes: tuple[str, ...], node_stress: dict[str, float]) -> float:
        values = [max(0.0, min(1.0, node_stress.get(nid, 0.0))) for nid in nodes if nid in node_stress]
        if not values:
            return 0.0
        values.sort(reverse=True)
        top = values[:4]
        return min(1.0, 0.65 * max(top) + 0.35 * (sum(top) / len(top)))
