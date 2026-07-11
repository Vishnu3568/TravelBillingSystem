from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import get_current_user
from app.services.enterprise_copilot.copilot_models import CopilotChatRequest, CopilotChatResponse
from app.services.enterprise_copilot.copilot_service import CopilotService
from app.services.enterprise_copilot.conversation_memory import ConversationMemory

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

auth_guard = get_current_user

@router.post("/chat", response_model=CopilotChatResponse)
def ask_copilot(
    request: CopilotChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    """
    POST chat endpoint for Copilot conversation requests.
    Automatically resolves user identity, role, and passes context.
    """
    user_role = current_user.get("role", "EMPLOYEE")
    username = current_user.get("sub", "System Reviewer")
    
    return CopilotService.ask_copilot(db, request, user_role, username)

@router.delete("/memory/{sessionId}")
def clear_memory(
    sessionId: str,
    current_user: dict = Depends(auth_guard)
):
    """
    Deletes the conversation session cache for a given sessionId.
    """
    ConversationMemory.clear_session(sessionId)
    return {"message": f"Conversation session {sessionId} memory cleared successfully."}
