from sqlalchemy.orm import Session
from typing import Dict, Any, List, Set, Tuple
from app.models.graph import GraphNode, GraphEdge
from app.services.knowledge_graph.graph_models import GraphNodeSchema, GraphEdgeSchema, SubgraphSchema
import json

class GraphQueries:
    @staticmethod
    def get_connected_nodes(db: Session, node_id: str, rel_type: str = None) -> List[GraphNode]:
        """
        Retrieves all adjacent nodes connected to the target node.
        Optional filter by relationship_type.
        """
        query = db.query(GraphEdge).filter(
            (GraphEdge.source_node_id == node_id) | (GraphEdge.target_node_id == node_id)
        )
        if rel_type:
            query = query.filter(GraphEdge.relationship_type == rel_type)
            
        edges = query.all()
        neighbor_ids = set()
        for e in edges:
            if e.source_node_id == node_id:
                neighbor_ids.add(e.target_node_id)
            else:
                neighbor_ids.add(e.source_node_id)
                
        if not neighbor_ids:
            return []
            
        return db.query(GraphNode).filter(GraphNode.id.in_(neighbor_ids)).all()

    @staticmethod
    def get_subgraph(db: Session, start_node_id: str, depth: int = 1) -> SubgraphSchema:
        """
        Runs a Breadth-First Search (BFS) starting from start_node_id up to depth levels.
        Assembles all traversed nodes and edges into a SubgraphSchema.
        """
        visited_nodes: Set[str] = set()
        visited_edges: Set[int] = set()
        
        nodes_queue: List[Tuple[str, int]] = [(start_node_id, 0)]
        
        nodes_out: List[GraphNodeSchema] = []
        edges_out: List[GraphEdgeSchema] = []
        
        while nodes_queue:
            curr_id, curr_depth = nodes_queue.pop(0)
            if curr_id in visited_nodes:
                continue
                
            # Load node
            node = db.query(GraphNode).filter(GraphNode.id == curr_id).first()
            if not node:
                continue
                
            visited_nodes.add(curr_id)
            try:
                props = json.loads(node.properties or "{}")
            except Exception:
                props = {}
                
            nodes_out.append(
                GraphNodeSchema(
                    id=node.id,
                    entity_type=node.entity_type,
                    entity_id=node.entity_id,
                    properties=props
                )
            )
            
            if curr_depth >= depth:
                continue
                
            # Retrieve adjacent edges
            outgoing = db.query(GraphEdge).filter(GraphEdge.source_node_id == curr_id).all()
            incoming = db.query(GraphEdge).filter(GraphEdge.target_node_id == curr_id).all()
            
            for edge in outgoing + incoming:
                if edge.id in visited_edges:
                    continue
                visited_edges.add(edge.id)
                
                try:
                    e_props = json.loads(edge.properties or "{}")
                except Exception:
                    e_props = {}
                    
                edges_out.append(
                    GraphEdgeSchema(
                        source_node_id=edge.source_node_id,
                        target_node_id=edge.target_node_id,
                        relationship_type=edge.relationship_type,
                        properties=e_props
                    )
                )
                
                # Add unvisited endpoints to queue
                next_id = edge.target_node_id if edge.source_node_id == curr_id else edge.source_node_id
                if next_id not in visited_nodes:
                    nodes_queue.append((next_id, curr_depth + 1))
                    
        return SubgraphSchema(nodes=nodes_out, edges=edges_out)
