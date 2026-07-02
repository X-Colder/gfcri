"""
Industry Research Module - Supply Chain Network (Layer 2).

Builds and queries the industry supply chain graph.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.engines.industry import INDUSTRIES


@dataclass
class SupplyChainLink:
    source: str
    target: str
    source_name: str
    target_name: str
    relationship: str  # upstream/downstream


@dataclass
class ImpactPath:
    path: list[str]
    path_names: list[str]
    depth: int


class SupplyChainNetwork:

    def __init__(self):
        self._build_graph()

    def _build_graph(self):
        self.edges: list[SupplyChainLink] = []
        for code, ind in INDUSTRIES.items():
            for up_code in ind.upstream:
                if up_code in INDUSTRIES:
                    self.edges.append(SupplyChainLink(
                        source=up_code,
                        target=code,
                        source_name=INDUSTRIES[up_code].name_zh,
                        target_name=ind.name_zh,
                        relationship="supplies",
                    ))

    def get_upstream(self, industry_code: str) -> list[dict]:
        ind = INDUSTRIES.get(industry_code)
        if not ind:
            return []
        return [
            {"code": up, "name_zh": INDUSTRIES[up].name_zh, "category": INDUSTRIES[up].category}
            for up in ind.upstream if up in INDUSTRIES
        ]

    def get_downstream(self, industry_code: str) -> list[dict]:
        ind = INDUSTRIES.get(industry_code)
        if not ind:
            return []
        return [
            {"code": dn, "name_zh": INDUSTRIES[dn].name_zh, "category": INDUSTRIES[dn].category}
            for dn in ind.downstream if dn in INDUSTRIES
        ]

    def trace_impact(self, industry_code: str, direction: str = "downstream", max_depth: int = 4) -> list[ImpactPath]:
        paths = []
        self._dfs(industry_code, direction, [industry_code], max_depth, paths)
        return paths

    def _dfs(self, current: str, direction: str, path: list[str], max_depth: int, results: list[ImpactPath]):
        if len(path) > max_depth:
            return
        ind = INDUSTRIES.get(current)
        if not ind:
            return

        neighbors = ind.downstream if direction == "downstream" else ind.upstream
        for nb in neighbors:
            if nb in path:
                continue
            new_path = path + [nb]
            results.append(ImpactPath(
                path=new_path,
                path_names=[INDUSTRIES[c].name_zh for c in new_path],
                depth=len(new_path) - 1,
            ))
            self._dfs(nb, direction, new_path, max_depth, results)

    def get_full_graph(self) -> dict:
        nodes = []
        for code, ind in INDUSTRIES.items():
            nodes.append({
                "code": code,
                "name_zh": ind.name_zh,
                "category": ind.category,
                "key_economies": ind.key_economies,
                "upstream_count": len(ind.upstream),
                "downstream_count": len(ind.downstream),
            })

        edges = [
            {"source": e.source, "target": e.target, "source_name": e.source_name, "target_name": e.target_name}
            for e in self.edges
        ]

        return {"nodes": nodes, "edges": edges}
