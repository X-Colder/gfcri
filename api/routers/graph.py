from fastapi import APIRouter

from api.dependencies import get_graph
from api.models.graph import GraphResponse

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=GraphResponse)
def get_full_graph():
    graph = get_graph()
    data = graph.to_dict()
    return GraphResponse(
        graph_id=data["graph_id"],
        version=data["version"],
        node_count=graph.node_count,
        edge_count=graph.edge_count,
        nodes=data["nodes"],
        edges=data["edges"],
    )


@router.get("/nodes")
def get_nodes():
    graph = get_graph()
    return {
        nid: n.to_dict() for nid, n in graph.nodes.items()
    }


@router.get("/edges")
def get_edges():
    graph = get_graph()
    return {
        eid: e.to_dict() for eid, e in graph.edges.items()
    }
