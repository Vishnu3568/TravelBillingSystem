import logging
from sqlalchemy.orm import Session
from app.models.bill import Bill
from app.models.learning import CorrectionHistory
from app.services.knowledge_graph.graph_builder import GraphBuilder
from app.services.knowledge_graph.graph_queries import GraphQueries

logger = logging.getLogger("graph_orchestrator")

class GraphOrchestrator:
    @staticmethod
    def handle_bill_save(db: Session, bill: Bill) -> None:
        """
        Invoked incrementally whenever a bill is created or updated in the ERP.
        Adds node and triggers relations linking (OWNS, USES, DRIVEN_BY).
        """
        try:
            GraphBuilder.add_bill_node(db, bill)
            logger.info(f"Knowledge Graph updated incrementally for bill: {bill.bill_number}")
        except Exception as e:
            logger.error(f"Failed to update knowledge graph on bill save: {e}")

    @staticmethod
    def handle_correction_save(db: Session, correction: CorrectionHistory) -> None:
        """
        Invoked incrementally when a manual correction is recorded.
        Adds node and connects Reviewer -> Correction -> Bill.
        """
        try:
            GraphBuilder.add_correction_node(db, correction)
            logger.info(f"Knowledge Graph updated incrementally for correction: {correction.id}")
        except Exception as e:
            logger.error(f"Failed to update knowledge graph on correction save: {e}")

    @staticmethod
    def handle_validation_save(db: Session, bill_id: int, report: dict) -> None:
        """
        Invoked incrementally when validation reports are completed.
        """
        try:
            GraphBuilder.add_validation_node(db, bill_id, report)
            logger.info(f"Knowledge Graph updated for validation report on bill ID: {bill_id}")
        except Exception as e:
            logger.error(f"Failed to update validation report node in graph: {e}")

    @staticmethod
    def handle_conversation_save(db: Session, session_id: str, history: list, bill_id: int = None) -> None:
        """
        Invoked incrementally when conversations are updated.
        """
        try:
            GraphBuilder.add_conversation_node(db, session_id, history, bill_id)
        except Exception as e:
            logger.error(f"Failed to update conversation node in graph: {e}")

    @staticmethod
    def get_copilot_graph_context(db: Session, bill_id: int) -> str:
        """
        Queries connected subgraph entities for the target bill up to depth 2,
        returning a formatted text block detailing relations for AI reasoning.
        """
        if not bill_id:
            return ""
            
        try:
            node_id = f"bill:{bill_id}"
            subgraph = GraphQueries.get_subgraph(db, node_id, depth=2)
            if not subgraph.nodes:
                return ""
                
            lines = ["### Connected Enterprise Knowledge Graph Context:"]
            # Summarize nodes
            lines.append("Entity Nodes:")
            for n in subgraph.nodes:
                name_val = n.properties.get("name") or n.properties.get("bill_number") or n.properties.get("registration_number") or n.id
                lines.append(f"  * Node '{n.id}' (Type: {n.entity_type}, Name: {name_val})")
                
            # Summarize relations
            if subgraph.edges:
                lines.append("Relationships:")
                for e in subgraph.edges:
                    lines.append(f"  * {e.source_node_id} - {e.relationship_type} -> {e.target_node_id}")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error querying copilot graph context: {e}")
            return ""
