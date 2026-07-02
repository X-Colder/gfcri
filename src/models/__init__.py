"""
src.models — causal graph data model package.

Public re-exports for convenience:

    from src.models import (
        NodeType, AssetClass, CausalNode, CORE_NODES,
        EdgeMechanism, ActivationCondition, ActivationRule,
        CausalEdge, INITIAL_EDGES,
        MacroRiskCausalGraph, build_initial_causal_graph,
    )
"""

from src.models.nodes import (
    AssetClass,
    CausalNode,
    CORE_NODES,
    NodeType,
)
from src.models.edges import (
    ActivationCondition,
    ActivationRule,
    CausalEdge,
    EdgeMechanism,
    INITIAL_EDGES,
)
from src.models.graph import (
    MacroRiskCausalGraph,
    build_initial_causal_graph,
)

__all__ = [
    # nodes
    "NodeType",
    "AssetClass",
    "CausalNode",
    "CORE_NODES",
    # edges
    "EdgeMechanism",
    "ActivationCondition",
    "ActivationRule",
    "CausalEdge",
    "INITIAL_EDGES",
    # graph
    "MacroRiskCausalGraph",
    "build_initial_causal_graph",
]
