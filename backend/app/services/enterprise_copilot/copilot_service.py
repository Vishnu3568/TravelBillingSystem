import logging
from sqlalchemy.orm import Session
from app.config import settings
from app.services.enterprise_copilot.copilot_models import CopilotChatRequest, CopilotChatResponse
from app.services.enterprise_copilot.copilot_orchestrator import CopilotOrchestrator

logger = logging.getLogger("copilot_service")

class CopilotService:
    @staticmethod
    def ask_copilot(
        db: Session,
        request: CopilotChatRequest,
        user_role: str,
        username: str
    ) -> CopilotChatResponse:
        """
        Public facade: routes request to the Enterprise AI Copilot if USE_ENTERPRISE_COPILOT is ON,
        otherwise falls back to the legacy chat assistant logic.
        """
        # Feature Flag toggle
        if getattr(settings, "USE_ENTERPRISE_COPILOT", False):
            logger.info("USE_ENTERPRISE_COPILOT is enabled. Directing to Python Copilot Engine...")
            return CopilotOrchestrator.process_chat(db, request, user_role, username)
        
        # Fallback to Legacy chat assistant
        logger.info("USE_ENTERPRISE_COPILOT is disabled. Delegating to legacy chat assistant...")
        from app.services.analytics import AnalyticsService
        
        legacy_res = AnalyticsService.ask_assistant(
            db=db,
            query=request.query,
            bill_id=request.billId,
            username=username
        )
        
        # Map legacy response keys to CopilotChatResponse format
        return CopilotChatResponse(
            answer=legacy_res.get("answer", "No reply from legacy assistant."),
            confidence=legacy_res.get("confidence", 0.90),
            references=legacy_res.get("references", []),
            action=None
        )
