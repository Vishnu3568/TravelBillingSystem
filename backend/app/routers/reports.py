from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.report import ReportSummaryResponse, TopEntityResponse
from app.services.reports import ReportService
from app.utils.security import RoleChecker

router = APIRouter(prefix="/api/reports", tags=["reports"])

# Only OWNER/MANAGER can view reports
report_guard = RoleChecker(["OWNER", "MANAGER"])

@router.get("/summary", response_model=ReportSummaryResponse)
def get_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(report_guard)
):
    return ReportService.get_summary(db)

@router.get("/top-companies", response_model=List[TopEntityResponse])
def get_top_companies(
    db: Session = Depends(get_db),
    current_user: dict = Depends(report_guard)
):
    return ReportService.get_top_companies(db)

@router.get("/top-vehicles", response_model=List[TopEntityResponse])
def get_top_vehicles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(report_guard)
):
    return ReportService.get_top_vehicles(db)
