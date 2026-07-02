"""
Macro-risk causal graph — main graph structure.

Wraps a ``networkx.DiGraph`` with domain-typed node/edge registries and
exposes causal-inference helpers (path finding, d-separation, parent/child
queries).  The graph is fully serialisable to a plain dictionary so it can be
persisted to PostgreSQL or transmitted over the wire without extra libraries.

Usage
-----
>>> from src.models.graph import build_initial_causal_graph
>>> g = build_initial_causal_graph()
>>> g.get_causal_parents("kospi")
['krw_usd', 'kr_cds_5y', 'dram_spot']
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import networkx as nx

from src.models.edges import CausalEdge, INITIAL_EDGES
from src.models.nodes import CausalNode, CORE_NODES


# ---------------------------------------------------------------------------
# Graph dataclass
# ---------------------------------------------------------------------------


@dataclass
class MacroRiskCausalGraph:
    """Container for the macro-risk causal graph.

    Parameters
    ----------
    graph_id:
        Unique identifier for this graph instance (UUID string).
    version:
        Semantic version string (e.g. ``"1.0.0"``).
    created_at:
        UTC timestamp of graph construction.
    description:
        Human-readable description of this graph variant.
    nodes:
        Mapping of ``node_id → CausalNode``; this is the authoritative
        node registry used throughout the system.
    edges:
        Mapping of ``edge_id → CausalEdge``; authoritative edge registry.

    Notes
    -----
    The underlying ``networkx.DiGraph`` (``_digraph``) is kept in sync with
    *nodes* and *edges* via :meth:`add_node` / :meth:`add_edge`.  Do **not**
    mutate ``_digraph`` directly; always go through the public methods.
    """

    graph_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    description: str = "Macro-risk causal graph"
    nodes: dict[str, CausalNode] = field(default_factory=dict)
    edges: dict[str, CausalEdge] = field(default_factory=dict)

    # Internal networkx representation — excluded from public interface.
    _digraph: nx.DiGraph = field(default_factory=nx.DiGraph, repr=False, compare=False)

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_node(self, node: CausalNode) -> None:
        """Register a node in the graph.

        Idempotent: re-adding a node with the same ``node_id`` updates the
        registry entry and refreshes the networkx attribute dict.

        Parameters
        ----------
        node:
            The :class:`~src.models.nodes.CausalNode` to add.
        """
        self.nodes[node.node_id] = node
        self._digraph.add_node(
            node.node_id,
            node_type=node.node_type.value,
            asset_class=node.asset_class.value,
            display_name=node.display_name,
        )

    def add_edge(self, edge: CausalEdge) -> None:
        """Register a directed causal edge in the graph.

        Both *source_node* and *target_node* must already exist in
        :attr:`nodes`; if not, a :class:`ValueError` is raised so that
        dangling edges are detected early.

        Parameters
        ----------
        edge:
            The :class:`~src.models.edges.CausalEdge` to add.

        Raises
        ------
        ValueError
            If either endpoint is not registered in :attr:`nodes`.
        """
        if edge.source_node not in self.nodes:
            raise ValueError(
                f"Source node '{edge.source_node}' not found in graph "
                f"(edge '{edge.edge_id}')."
            )
        if edge.target_node not in self.nodes:
            raise ValueError(
                f"Target node '{edge.target_node}' not found in graph "
                f"(edge '{edge.edge_id}')."
            )
        self.edges[edge.edge_id] = edge
        self._digraph.add_edge(
            edge.source_node,
            edge.target_node,
            edge_id=edge.edge_id,
            causal_strength=edge.causal_strength,
            mechanism=edge.mechanism.value,
        )

    # ------------------------------------------------------------------
    # Causal-inference queries
    # ------------------------------------------------------------------

    def get_causal_parents(self, node_id: str) -> list[str]:
        """Return direct causal parents of *node_id* (active edges only).

        Parameters
        ----------
        node_id:
            Target node whose parents are requested.

        Returns
        -------
        list[str]
            Sorted list of ``node_id`` strings for each parent.

        Raises
        ------
        KeyError
            If *node_id* is not in the graph.
        """
        if node_id not in self._digraph:
            raise KeyError(f"Node '{node_id}' not found in graph.")

        parent_ids: list[str] = []
        for parent, _, edge_data in self._digraph.in_edges(node_id, data=True):
            eid = edge_data.get("edge_id", "")
            edge = self.edges.get(eid)
            if edge is None or edge.is_active:
                parent_ids.append(parent)

        return sorted(parent_ids)

    def get_causal_children(self, node_id: str) -> list[str]:
        """Return direct causal children of *node_id* (active edges only).

        Parameters
        ----------
        node_id:
            Source node whose children are requested.

        Returns
        -------
        list[str]
            Sorted list of ``node_id`` strings for each child.

        Raises
        ------
        KeyError
            If *node_id* is not in the graph.
        """
        if node_id not in self._digraph:
            raise KeyError(f"Node '{node_id}' not found in graph.")

        child_ids: list[str] = []
        for _, child, edge_data in self._digraph.out_edges(node_id, data=True):
            eid = edge_data.get("edge_id", "")
            edge = self.edges.get(eid)
            if edge is None or edge.is_active:
                child_ids.append(child)

        return sorted(child_ids)

    def find_all_causal_paths(
        self,
        source_node: str,
        target_node: str,
        max_depth: int = 6,
    ) -> list[list[str]]:
        """Find all simple directed paths from *source_node* to *target_node*.

        Uses ``networkx.all_simple_paths`` on the underlying DiGraph which
        already encodes only active edges (deprecated edges are excluded at
        :meth:`add_edge` time — already present edges are never removed here;
        filtering happens in the query layer).

        Parameters
        ----------
        source_node:
            Starting node of the causal path.
        target_node:
            Ending node of the causal path.
        max_depth:
            Maximum path length in hops (default 6).  Prevents combinatorial
            explosion on dense graphs.

        Returns
        -------
        list[list[str]]
            Each element is an ordered list of ``node_id`` strings from source
            to target.  Empty list if no path exists.
        """
        if source_node not in self._digraph:
            raise KeyError(f"Source node '{source_node}' not found in graph.")
        if target_node not in self._digraph:
            raise KeyError(f"Target node '{target_node}' not found in graph.")

        try:
            paths = list(
                nx.all_simple_paths(
                    self._digraph,
                    source=source_node,
                    target=target_node,
                    cutoff=max_depth,
                )
            )
        except nx.NetworkXNoPath:
            paths = []

        return paths

    def are_d_separated(
        self,
        node_x: str,
        node_y: str,
        conditioning_set: Optional[set[str]] = None,
    ) -> bool:
        """Test whether *node_x* and *node_y* are d-separated given *conditioning_set*.

        Uses ``networkx.d_separated`` which implements the Bayes-Ball /
        reachability algorithm on a DAG.

        Parameters
        ----------
        node_x:
            First node.
        node_y:
            Second node.
        conditioning_set:
            Set of nodes being conditioned on (observed).  Pass ``None`` or
            an empty set to test marginal independence.

        Returns
        -------
        bool
            ``True`` if *node_x* and *node_y* are d-separated given
            *conditioning_set* (i.e. conditionally independent in every
            Markov-compatible distribution).

        Raises
        ------
        nx.NetworkXError
            If the underlying graph is not a DAG (cycle detected).
        """
        conditioning_set = conditioning_set or set()

        if not nx.is_directed_acyclic_graph(self._digraph):
            raise nx.NetworkXError(
                "d-separation is only defined for DAGs; the current graph contains a cycle."
            )

        return nx.d_separated(self._digraph, {node_x}, {node_y}, conditioning_set)

    # ------------------------------------------------------------------
    # Graph-level metadata helpers
    # ------------------------------------------------------------------

    @property
    def node_count(self) -> int:
        """Total number of registered nodes."""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Total number of registered edges (including deprecated)."""
        return len(self.edges)

    @property
    def active_edge_count(self) -> int:
        """Number of non-deprecated edges."""
        return sum(1 for e in self.edges.values() if e.is_active)

    def is_dag(self) -> bool:
        """Return ``True`` if the underlying digraph is acyclic."""
        return nx.is_directed_acyclic_graph(self._digraph)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise the full graph to a JSON-compatible dictionary.

        Returns
        -------
        dict
            Contains ``graph_id``, ``version``, ``created_at`` (ISO string),
            ``description``, ``nodes`` (list of node dicts), ``edges``
            (list of edge dicts), and basic stats.
        """
        return {
            "graph_id": self.graph_id,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "stats": {
                "node_count": self.node_count,
                "edge_count": self.edge_count,
                "active_edge_count": self.active_edge_count,
                "is_dag": self.is_dag(),
            },
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges.values()],
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_initial_causal_graph(
    description: str = "Initial macro-risk causal graph v1",
) -> MacroRiskCausalGraph:
    """Construct the canonical macro-risk causal graph from built-in registries.

    Uses :data:`~src.models.nodes.CORE_NODES` and
    :data:`~src.models.edges.INITIAL_EDGES` to populate the graph.

    Parameters
    ----------
    description:
        Optional description override for the graph instance.

    Returns
    -------
    MacroRiskCausalGraph
        A fully populated graph instance ready for analysis.

    Examples
    --------
    >>> g = build_initial_causal_graph()
    >>> g.is_dag()
    True
    >>> "fed_funds" in g.nodes
    True
    >>> len(g.edges) >= 15
    True
    """
    graph = MacroRiskCausalGraph(description=description)

    # Register all canonical nodes first.
    for node in CORE_NODES.values():
        graph.add_node(node)

    # Register all canonical edges; skip edges whose endpoints are missing
    # (defensive: prevents hard failures if a future node is removed from
    # CORE_NODES but its edges are not yet cleaned up).
    skipped: list[str] = []
    for edge in INITIAL_EDGES:
        try:
            graph.add_edge(edge)
        except ValueError as exc:
            skipped.append(str(exc))

    if skipped:
        import warnings

        for msg in skipped:
            warnings.warn(f"[build_initial_causal_graph] Skipped edge: {msg}", stacklevel=2)

    return graph
