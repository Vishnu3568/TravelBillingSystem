from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import get_current_user
from app.services.predictive_engine.predictive_service import PredictiveService
from app.services.predictive_engine.predictive_models import PredictiveDashboardSummary, RevenueForecast, SmartRecommendations

router = APIRouter(prefix="/api/predictive", tags=["predictive"])

auth_guard = get_current_user

@router.get("/dashboard", response_model=PredictiveDashboardSummary)
def get_predictive_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    """
    Exposes consolidated forecasts, payments, and template recommendations.
    """
    return PredictiveService.get_predictive_summary(db)

@router.get("/forecast", response_model=RevenueForecast)
def get_forecasts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    """
    Exposes detailed daily/weekly/monthly revenue forecasts.
    """
    return PredictiveService.get_forecasts(db)

@router.get("/anomalies")
def get_anomalies(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    """
    Exposes active invoice anomalies and duplicate warnings.
    """
    return PredictiveService.get_anomalies(db)

@router.get("/recommendations", response_model=SmartRecommendations)
def get_recommendations(
    company_name: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    """
    Exposes smart company template preferences and km pricing suggestions.
    """
    return PredictiveService.get_recommendations(db, company_name)
