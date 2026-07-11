import json
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.models.graph import GraphNode, GraphEdge

class GraphVisualizer:
    @staticmethod
    def generate_visualization_data(db: Session) -> Dict[str, Any]:
        """
        Retrieves all nodes and edges from the database, formatting them as a JSON object
        suitable for force-directed layout widgets (e.g. D3.js, Cytoscape).
        """
        nodes = db.query(GraphNode).all()
        edges = db.query(GraphEdge).all()

        node_list = []
        for n in nodes:
            try:
                props = json.loads(n.properties or "{}")
            except Exception:
                props = {}
            node_list.append({
                "id": n.id,
                "type": n.entity_type,
                "label": props.get("name") or props.get("bill_number") or props.get("registration_number") or n.id,
                "properties": props
            })

        edge_list = []
        for e in edges:
            edge_list.append({
                "source": e.source_node_id,
                "target": e.target_node_id,
                "type": e.relationship_type
            })

        return {
            "nodes": node_list,
            "edges": edge_list
        }
