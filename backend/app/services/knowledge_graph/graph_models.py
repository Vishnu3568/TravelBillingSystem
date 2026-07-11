from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class GraphNodeSchema(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphEdgeSchema(BaseModel):
    source_node_id: str
    target_node_id: str
    relationship_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class SubgraphSchema(BaseModel):
    nodes: List[GraphNodeSchema] = Field(default_factory=list)
    edges: List[GraphEdgeSchema] = Field(default_factory=list)

class GraphSearchQueryResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(default_factory=list)

class GraphStatisticsSummary(BaseModel):
    total_nodes: int = 0
    total_edges: int = 0
    relationship_density: float = 0.0
    most_connected_companies: List[Dict[str, Any]] = Field(default_factory=list)
    most_used_vehicles: List[Dict[str, Any]] = Field(default_factory=list)
    reviewer_network_size: int = 0
    graph_depth: int = 0
    graph_connectivity: float = 1.0
