import logging
from sqlalchemy.orm import Session
from app.config import settings
from app.models.bill import Bill
from app.models.learning import CorrectionHistory
from app.services.knowledge_graph.graph_orchestrator import GraphOrchestrator
from app.services.knowledge_graph.graph_statistics import GraphStatistics
from app.services.knowledge_graph.graph_visualizer import GraphVisualizer
from app.services.knowledge_graph.graph_export import GraphExport
from app.services.knowledge_graph.graph_queries import GraphQueries
from app.services.knowledge_graph.graph_search import GraphSearch

logger = logging.getLogger("graph_service")

class GraphService:
    @staticmethod
    def register_bill_save(db: Session, bill: Bill) -> None:
        """
        Registers a bill save to update the graph incrementally.
        """
        if not getattr(settings, "USE_ENTERPRISE_GRAPH", False):
            return
        GraphOrchestrator.handle_bill_save(db, bill)

    @staticmethod
    def register_correction_save(db: Session, correction: CorrectionHistory) -> None:
        """
        Registers a correction save to update the graph incrementally.
        """
        if not getattr(settings, "USE_ENTERPRISE_GRAPH", False):
            return
        GraphOrchestrator.handle_correction_save(db, correction)

    @staticmethod
    def register_validation_save(db: Session, bill_id: int, report: dict) -> None:
        """
        Registers a validation save in the graph.
        """
        if not getattr(settings, "USE_ENTERPRISE_GRAPH", False):
            return
        GraphOrchestrator.handle_validation_save(db, bill_id, report)

    @staticmethod
    def register_conversation_save(db: Session, session_id: str, history: list, bill_id: int = None) -> None:
        """
        Registers a conversation session save in the graph.
        """
        if not getattr(settings, "USE_ENTERPRISE_GRAPH", False):
            return
        GraphOrchestrator.handle_conversation_save(db, session_id, history, bill_id)

    @staticmethod
    def query_copilot_context(db: Session, bill_id: int) -> str:
        """
        Queries connected subgraph details for prompt building reasoning context.
        """
        if not getattr(settings, "USE_ENTERPRISE_GRAPH", False):
            return ""
        return GraphOrchestrator.get_copilot_graph_context(db, bill_id)

    @staticmethod
    def get_analytics(db: Session) -> dict:
        """
        Calculates relationship density, depth, and connected components.
        """
        try:
            stats = GraphStatistics.get_statistics(db)
            return stats.model_dump(mode="json")
        except Exception as e:
            logger.error(f"Error gathering graph stats: {e}")
            return {}

    @staticmethod
    def get_visualization(db: Session) -> dict:
        """
        Formats cytoscape-compatible JSON lists.
        """
        return GraphVisualizer.generate_visualization_data(db)

    @staticmethod
    def export_graph(db: Session, format_type: str = "json") -> str:
        """
        Exports graph as JSON, CSV, GraphML, or Neo4j Cypher script.
        """
        try:
            fmt = format_type.strip().lower()
            if fmt == "csv":
                return GraphExport.export_as_csv(db)
            elif fmt == "graphml":
                return GraphExport.export_as_graphml(db)
            elif fmt == "cypher":
                return GraphExport.export_as_cypher(db)
            return GraphExport.export_as_json(db)
        except Exception as e:
            logger.error(f"Error exporting graph: {e}")
            return "{}"

    @staticmethod
    def search(db: Session, query: str) -> list:
        """
        Runs connection searches in the graph.
        """
        try:
            return GraphSearch.search_graph(db, query)
        except Exception as e:
            logger.error(f"Error running graph search: {e}")
            return []
