import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.config import settings
from app.schemas.ai import AiBillResponse
from app.services.learning_engine.learning_orchestrator import LearningOrchestrator
from app.services.learning_engine.knowledge_store import KnowledgeStore
from app.services.learning_engine.learning_statistics import LearningStatistics
from app.services.learning_engine.knowledge_export import KnowledgeExport
from app.services.learning_engine.feedback_processor import FeedbackProcessor

logger = logging.getLogger("learning_service")

class LearningService:
    @staticmethod
    def process_bill_save(db: Session, bill: AiBillResponse, username: str) -> None:
        """
        Processes and learns from a saved bill if USE_ENTERPRISE_LEARNING is active.
        """
        # Backward Compatibility: Check Feature Flag
        if not getattr(settings, "USE_ENTERPRISE_LEARNING", False):
            logger.info("USE_ENTERPRISE_LEARNING is disabled. Skipping learning processor.")
            return
            
        try:
            LearningOrchestrator.process_save(db, bill, username)
        except Exception as e:
            logger.error(f"Error executing learning orchestrator: {e}")

    @staticmethod
    def get_learned_context(db: Session, company_name: str, vehicle_type: str = None) -> str:
        """
        Retrieves the learned context block to append to the LLM prompt.
        Only returns if USE_ENTERPRISE_LEARNING is enabled.
        """
        if not getattr(settings, "USE_ENTERPRISE_LEARNING", False):
            return ""
            
        try:
            return KnowledgeStore.retrieve_learned_context(db, company_name, vehicle_type)
        except Exception as e:
            logger.error(f"Error retrieving learned context: {e}")
            return ""

    @staticmethod
    def get_analytics(db: Session) -> Dict[str, Any]:
        """
        Retrieves statistics regarding corrections, reviewer actions, and accuracy.
        """
        try:
            stats = LearningStatistics.get_statistics(db)
            return stats.model_dump(mode="json")
        except Exception as e:
            logger.error(f"Error gathering learning statistics: {e}")
            return {}

    @staticmethod
    def export_knowledge(db: Session, format_type: str = "json") -> str:
        """
        Exports the knowledge store in either 'json' or 'csv' format.
        """
        try:
            if format_type.strip().lower() == "csv":
                return KnowledgeExport.export_as_csv(db)
            return KnowledgeExport.export_as_json(db)
        except Exception as e:
            logger.error(f"Error exporting knowledge store: {e}")
            return "{}"

    @staticmethod
    def log_reviewer_action(db: Session, username: str, action_type: str) -> None:
        """
        Helper to track interactive operations (Approve, Reject, Undo, Restore) in ReviewerStatistics.
        """
        if not getattr(settings, "USE_ENTERPRISE_LEARNING", False):
            return
            
        try:
            FeedbackProcessor.process_reviewer_action(db, username, action_type)
        except Exception as e:
            logger.error(f"Error logging reviewer action: {e}")
