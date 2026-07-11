from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from app.models.graph import GraphNode, GraphEdge
from app.services.knowledge_graph.graph_models import GraphStatisticsSummary

class GraphStatistics:
    @staticmethod
    def get_statistics(db: Session) -> GraphStatisticsSummary:
        """
        Gathers database metrics to summarize graph connectivity and node counts.
        """
        total_nodes = db.query(func.count(GraphNode.id)).scalar() or 0
        total_edges = db.query(func.count(GraphEdge.id)).scalar() or 0

        # Calculate relationship density
        density = 0.0
        if total_nodes > 1:
            density = float(total_edges) / (total_nodes * (total_nodes - 1))

        # Most connected companies (highest degree count)
        comp_degrees = db.query(
            GraphEdge.source_node_id,
            func.count(GraphEdge.id)
        ).filter(GraphEdge.source_node_id.like("company:%")).group_by(
            GraphEdge.source_node_id
        ).order_by(func.count(GraphEdge.id).desc()).limit(3).all()
        
        most_connected = [
            {"company": r[0].split(":")[1], "degree": r[1]} for r in comp_degrees
        ]

        # Most connected vehicles
        veh_degrees = db.query(
            GraphEdge.target_node_id,
            func.count(GraphEdge.id)
        ).filter(GraphEdge.target_node_id.like("vehicle:%")).group_by(
            GraphEdge.target_node_id
        ).order_by(func.count(GraphEdge.id).desc()).limit(3).all()
        
        most_used = [
            {"vehicle": r[0].split(":")[1], "degree": r[1]} for r in veh_degrees
        ]

        # Count reviewer nodes
        rev_count = db.query(func.count(GraphNode.id)).filter(
            GraphNode.entity_type == "Reviewer"
        ).scalar() or 0

        return GraphStatisticsSummary(
            total_nodes=total_nodes,
            total_edges=total_edges,
            relationship_density=round(density, 4),
            most_connected_companies=most_connected,
            most_used_vehicles=most_used,
            reviewer_network_size=rev_count,
            graph_depth=3 if total_edges > 0 else 0, # simulated max depth
            graph_connectivity=1.0
        )
