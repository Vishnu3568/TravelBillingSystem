from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.dashboard import OwnerDashboardResponse
from app.services.dashboard import DashboardService
from app.utils.security import RoleChecker

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

owner_guard = RoleChecker(["OWNER"])

@router.get("/owner", response_model=OwnerDashboardResponse)
def get_owner_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    return DashboardService.get_owner_dashboard(db)
