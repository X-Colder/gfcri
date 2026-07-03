"""
Stress Test Engine - Scenario-based risk propagation.

Given a shock to one or more nodes, propagates the impact through the
causal graph and estimates the resulting GFCRI under stress.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd
from loguru import logger

from src.models.graph import MacroRiskCausalGraph
from src.models.stress import stress_score_from_zscore
from src.engines.risk_index import GFCRIEngine


@dataclass
class ShockScenario:
    name: str
    description: str
    shocks: dict[str, float]  # node_id -> shocked z-score


@dataclass
class PropagationStep:
    node_id: str
    node_name: str
    baseline_zscore: float
    shocked_zscore: float
    delta: float
    caused_by: str
    caused_by_name: str
    edge_strength: float
    confidence: float
    baseline_price: float
    stressed_price: float
    unit: str
    explanation: str


@dataclass
class StressTestResult:
    scenario: ShockScenario
    baseline_gfcri: float
    stressed_gfcri: float
    gfcri_delta: float
    baseline_alert: str
    stressed_alert: str
    propagation_chain: list[PropagationStep]
    activated_chains: list[str]
    shock_details: list[dict] = field(default_factory=list)
    most_vulnerable_nodes: list[dict] = field(default_factory=list)
    edge_validations: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "scenario_name": self.scenario.name,
            "scenario_description": self.scenario.description,
            "shocks": self.scenario.shocks,
            "shock_details": self.shock_details,
            "baseline_gfcri": self.baseline_gfcri,
            "stressed_gfcri": self.stressed_gfcri,
            "gfcri_delta": self.gfcri_delta,
            "baseline_alert": self.baseline_alert,
            "stressed_alert": self.stressed_alert,
            "propagation_chain": [
                {
                    "node": s.node_id, "name": s.node_name,
                    "baseline_z": round(s.baseline_zscore, 2),
                    "stressed_z": round(s.shocked_zscore, 2),
                    "delta": round(s.delta, 2),
                    "caused_by": s.caused_by,
                    "caused_by_name": s.caused_by_name,
                    "edge_strength": round(s.edge_strength, 3),
                    "confidence": round(s.confidence, 2),
                    "baseline_price": round(s.baseline_price, 2),
                    "stressed_price": round(s.stressed_price, 2),
                    "unit": s.unit,
                    "explanation": s.explanation,
                }
                for s in self.propagation_chain
            ],
            "activated_chains": self.activated_chains,
            "most_vulnerable_nodes": self.most_vulnerable_nodes,
            "edge_validations": self.edge_validations,
        }


# Predefined extreme scenarios
PREDEFINED_SCENARIOS = [
    ShockScenario(
        name="美元危机",
        description="美元指数突然跳升至110（+3σ），模拟强美元冲击全球市场",
        shocks={"dxy": 3.0},
    ),
    ShockScenario(
        name="美联储紧急加息",
        description="联邦基金利率突升200bp（+4σ），模拟紧急加息冲击",
        shocks={"fed_funds": 4.0, "ust_2y": 3.5, "ust_10y": 2.5},
    ),
    ShockScenario(
        name="中国硬着陆",
        description="人民币急贬+恒生暴跌（各+4σ），模拟中国经济崩盘",
        shocks={"cny_usd": 4.0, "hsi": -4.0},
    ),
    ShockScenario(
        name="全球流动性枯竭",
        description="VIX飙升+信用利差急扩（模拟2008年9月/2020年3月）",
        shocks={"vix": 4.0, "hyg": -3.0, "lqd": -2.5},
    ),
    ShockScenario(
        name="半导体断供",
        description="半导体指数暴跌+DRAM价格崩盘",
        shocks={"sox": -4.0, "dram_spot": -3.0, "nand_spot": -3.0},
    ),
    ShockScenario(
        name="油价冲击",
        description="原油价格飙升至$120+（供给侧危机）",
        shocks={"oil_wti": 3.5, "natgas": 3.0},
    ),
    ShockScenario(
        name="多重危机共振（2008式）",
        description="美元飙升+信用冻结+中国减速+油价冲击同时发生，模拟多因素共振的系统性危机",
        shocks={
            "dxy": 3.0, "vix": 4.0, "hyg": -3.0,
            "cny_usd": 3.0, "hsi": -3.0,
            "oil_wti": 2.5, "fed_funds": 2.0, "ust_10y": 2.0,
        },
    ),
]


class StressTestEngine:

    def __init__(
        self,
        graph: MacroRiskCausalGraph,
        historical_data: Optional[pd.DataFrame] = None,
    ):
        self.graph = graph
        self.hist = historical_data

    def run_scenario(self, scenario: ShockScenario) -> StressTestResult:
        # 1. Validate edges involved in the propagation
        edge_validations = self._validate_edges()

        # 2. Record baseline state
        baseline_zscores = {}
        for nid, node in self.graph.nodes.items():
            baseline_zscores[nid] = node.value_zscore or 0.0

        baseline_engine = GFCRIEngine(self.graph)
        baseline_result = baseline_engine.compute()
        baseline_gfcri = baseline_result["gfcri"]
        baseline_alert = baseline_result["alert_level"]

        # 3. Propagate shocks through the graph (BFS)
        shocked_zscores = dict(baseline_zscores)
        propagation_chain = []

        # Apply initial shocks
        shock_details = []
        for nid, shock_z in scenario.shocks.items():
            if nid in shocked_zscores:
                shocked_zscores[nid] = shock_z
                node = self.graph.nodes.get(nid)
                from src.i18n import cn_name
                name = cn_name(nid)
                base_val = node.current_value if node and node.current_value else 0
                mean = node.historical_mean if node and node.historical_mean else base_val
                std = node.historical_std if node and node.historical_std else 1
                stressed_val = mean + shock_z * std if std > 0 else base_val
                unit = node.unit if node else ""
                shock_details.append({
                    "node": nid, "name": name,
                    "baseline_price": round(base_val, 2),
                    "stressed_price": round(stressed_val, 2),
                    "unit": unit,
                    "shock_z": shock_z,
                })

        # BFS propagation (max 5 hops)
        visited = set(scenario.shocks.keys())
        frontier = list(scenario.shocks.keys())

        for depth in range(5):
            next_frontier = []
            for src_nid in frontier:
                for edge in self.graph.edges.values():
                    if edge.is_deprecated or edge.source_node != src_nid:
                        continue
                    tgt = edge.target_node
                    if tgt in scenario.shocks:
                        continue

                    src_z = shocked_zscores.get(src_nid, 0)
                    baseline_src_z = baseline_zscores.get(src_nid, 0)
                    delta_src = src_z - baseline_src_z

                    transmitted_delta = delta_src * edge.causal_strength
                    new_z = baseline_zscores.get(tgt, 0) + transmitted_delta

                    if abs(transmitted_delta) > 0.1:
                        # Find validation confidence
                        conf = 0.5
                        for ev in edge_validations:
                            if ev["edge_id"] == edge.edge_id:
                                conf = ev["confidence"]
                                break

                        from src.i18n import cn_name
                        tgt_node = self.graph.nodes.get(tgt)
                        src_node = self.graph.nodes.get(src_nid)

                        base_price = tgt_node.current_value if tgt_node and tgt_node.current_value else 0
                        mean = tgt_node.historical_mean if tgt_node and tgt_node.historical_mean else base_price
                        std = tgt_node.historical_std if tgt_node and tgt_node.historical_std else 1
                        stressed_price = mean + new_z * std if std > 0 else base_price
                        unit = tgt_node.unit if tgt_node else ""

                        src_name = cn_name(src_nid)
                        tgt_name = cn_name(tgt)
                        direction = "上升" if transmitted_delta > 0 else "下降"
                        mechanism = edge.mechanism_description if hasattr(edge, 'mechanism_description') else ""
                        explanation = f"{src_name}异动导致{tgt_name}{direction}：传导强度{edge.causal_strength:+.2f}，预计从{base_price:.1f}变为{stressed_price:.1f}{unit}"

                        propagation_chain.append(PropagationStep(
                            node_id=tgt,
                            node_name=tgt_name,
                            baseline_zscore=baseline_zscores.get(tgt, 0),
                            shocked_zscore=new_z,
                            delta=transmitted_delta,
                            caused_by=src_nid,
                            caused_by_name=src_name,
                            edge_strength=edge.causal_strength,
                            confidence=conf,
                            baseline_price=base_price,
                            stressed_price=stressed_price,
                            unit=unit,
                            explanation=explanation,
                        ))

                        if abs(new_z) > abs(shocked_zscores.get(tgt, baseline_zscores.get(tgt, 0))):
                            shocked_zscores[tgt] = new_z

                        if tgt not in visited:
                            next_frontier.append(tgt)
                            visited.add(tgt)

            frontier = next_frontier
            if not frontier:
                break

        # 4. Compute stressed GFCRI
        for nid, z in shocked_zscores.items():
            node = self.graph.nodes.get(nid)
            if node:
                node.value_zscore = z
                node.is_anomalous = abs(z) > 2.0
                node.anomaly_score = stress_score_from_zscore(nid, z)

        stressed_engine = GFCRIEngine(self.graph)
        stressed_result = stressed_engine.compute()
        stressed_gfcri = stressed_result["gfcri"]
        stressed_alert = stressed_result["alert_level"]

        # Restore original state
        for nid, z in baseline_zscores.items():
            node = self.graph.nodes.get(nid)
            if node:
                node.value_zscore = z
                node.is_anomalous = abs(z) > 2.0
                node.anomaly_score = stress_score_from_zscore(nid, z)

        # 5. Find most vulnerable nodes
        vuln = []
        for step in propagation_chain:
            vuln.append({
                "node": step.node_id,
                "name": step.node_name,
                "impact": abs(step.delta),
                "stressed_z": step.shocked_zscore,
            })
        vuln.sort(key=lambda x: x["impact"], reverse=True)

        # 6. Identify activated chains
        activated = [
            c["name"] for c in stressed_result.get("chains", [])
            if c.get("active") and not any(
                bc.get("active") and bc["id"] == c["id"]
                for bc in baseline_result.get("chains", [])
            )
        ]

        return StressTestResult(
            scenario=scenario,
            baseline_gfcri=baseline_gfcri,
            stressed_gfcri=stressed_gfcri,
            gfcri_delta=stressed_gfcri - baseline_gfcri,
            baseline_alert=baseline_alert,
            stressed_alert=stressed_alert,
            propagation_chain=propagation_chain,
            activated_chains=activated,
            shock_details=shock_details,
            most_vulnerable_nodes=vuln[:10],
            edge_validations=edge_validations,
        )

    def run_all_scenarios(self) -> list[StressTestResult]:
        results = []
        for scenario in PREDEFINED_SCENARIOS:
            result = self.run_scenario(scenario)
            logger.info(
                f"Stress test '{scenario.name}': "
                f"GFCRI {result.baseline_gfcri:.1f} → {result.stressed_gfcri:.1f} "
                f"(+{result.gfcri_delta:.1f})"
            )
            results.append(result)
        return results

    def _validate_edges(self) -> list[dict]:
        validations = []
        if self.hist is None or self.hist.empty:
            for edge in self.graph.edges.values():
                if not edge.is_deprecated:
                    validations.append({
                        "edge_id": edge.edge_id,
                        "source": edge.source_node,
                        "target": edge.target_node,
                        "strength": edge.causal_strength,
                        "confidence": edge.strength_confidence,
                        "validated": False,
                        "method": "prior_only",
                    })
            return validations

        for edge in self.graph.edges.values():
            if edge.is_deprecated:
                continue

            src, tgt = edge.source_node, edge.target_node
            if src not in self.hist.columns or tgt not in self.hist.columns:
                validations.append({
                    "edge_id": edge.edge_id, "source": src, "target": tgt,
                    "strength": edge.causal_strength,
                    "confidence": edge.strength_confidence * 0.5,
                    "validated": False, "method": "no_data",
                })
                continue

            try:
                from sklearn.linear_model import LinearRegression

                x = self.hist[src].dropna()
                y = self.hist[tgt].dropna()
                common = x.index.intersection(y.index)
                if len(common) < 30:
                    validations.append({
                        "edge_id": edge.edge_id, "source": src, "target": tgt,
                        "strength": edge.causal_strength,
                        "confidence": edge.strength_confidence * 0.5,
                        "validated": False, "method": "insufficient_data",
                    })
                    continue

                lag = edge.peak_lag_days or 1
                x_lagged = x.reindex(common).shift(lag).dropna()
                y_aligned = y.reindex(x_lagged.index)
                both = pd.concat([x_lagged, y_aligned], axis=1).dropna()

                if len(both) < 20:
                    continue

                X = both.iloc[:, 0].values.reshape(-1, 1)
                Y = both.iloc[:, 1].values

                reg = LinearRegression().fit(X, Y)
                r2 = reg.score(X, Y)

                # Compute empirical correlation
                corr = both.iloc[:, 0].corr(both.iloc[:, 1])
                sign_match = (np.sign(corr) == np.sign(edge.causal_strength))

                confidence = min(1.0, edge.strength_confidence * (0.5 + 0.5 * r2))
                if not sign_match:
                    confidence *= 0.3

                validations.append({
                    "edge_id": edge.edge_id, "source": src, "target": tgt,
                    "strength": edge.causal_strength,
                    "empirical_r2": round(r2, 3),
                    "empirical_corr": round(corr, 3),
                    "sign_match": bool(sign_match),
                    "confidence": round(confidence, 3),
                    "validated": True,
                    "method": "lagged_regression",
                })
            except Exception:
                validations.append({
                    "edge_id": edge.edge_id, "source": src, "target": tgt,
                    "strength": edge.causal_strength,
                    "confidence": edge.strength_confidence,
                    "validated": False, "method": "error",
                })

        return validations
