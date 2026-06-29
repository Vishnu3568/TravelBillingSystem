from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.database import get_db
from app.schemas.ai import AiInsightResponse, AiAssistantResponse, AiSuggestionResponse, CurrentBill
from app.services.analytics import AnalyticsService
from app.utils.security import get_current_user, RoleChecker

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

auth_guard = get_current_user
manager_guard = RoleChecker(["OWNER", "MANAGER"])
operator_guard = RoleChecker(["OWNER", "MANAGER", "OPERATOR"])

@router.get("/ai-insights", response_model=AiInsightResponse)
def get_ai_insights(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    return AnalyticsService.get_ai_insights(db)

@router.post("/assistant", response_model=AiAssistantResponse)
def ask_assistant(
    query: str = Query(...),
    billId: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(manager_guard)
):
    return AnalyticsService.ask_assistant(
        db, 
        query, 
        billId, 
        current_user.get("sub")
    )

@router.post("/suggestions", response_model=AiSuggestionResponse)
def get_suggestions(
    current_bill: CurrentBill,
    db: Session = Depends(get_db),
    current_user: dict = Depends(operator_guard)
):
    return AnalyticsService.generate_suggestions(db, current_bill.model_dump())
