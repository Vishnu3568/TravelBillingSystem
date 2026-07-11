from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import RoleChecker
from app.services.learning_engine.learning_service import LearningService

router = APIRouter(prefix="/api/learning", tags=["learning"])

owner_guard = RoleChecker(["OWNER"])

@router.get("/analytics")
def get_learning_analytics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    """
    Returns summarized learning statistics for corrections, accuracy, and layout patterns.
    """
    return LearningService.get_analytics(db)

@router.get("/export")
def export_knowledge_store(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    """
    Exports the Knowledge Store records as structured JSON or CSV file.
    """
    exported_data = LearningService.export_knowledge(db, format)
    
    media_type = "application/json" if format == "json" else "text/csv"
    filename = f"knowledge_store_export.{format}"
    
    return Response(
        content=exported_data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
