from typing import Any
from pydantic import BaseModel


class GraphResponse(BaseModel):
    graph_id: str
    version: str
    node_count: int
    edge_count: int
    nodes: Any
    edges: Any
