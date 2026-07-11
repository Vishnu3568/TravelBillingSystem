import logging
from sqlalchemy.orm import Session
from app.config import settings
from app.services.predictive_engine.predictive_models import PredictiveDashboardSummary, RevenueForecast, SmartRecommendations
from app.services.predictive_engine.predictive_orchestrator import PredictiveOrchestrator
from app.services.predictive_engine.forecast_engine import ForecastEngine
from app.services.predictive_engine.anomaly_detector import AnomalyDetector
from app.services.predictive_engine.recommendation_engine import RecommendationEngine

logger = logging.getLogger("predictive_service")

class PredictiveService:
    @staticmethod
    def get_predictive_summary(db: Session) -> PredictiveDashboardSummary:
        """
        Retrieves consolidated predictive metrics if feature flag is active.
        """
        if not getattr(settings, "USE_PREDICTIVE_ENGINE", False):
            logger.info("USE_PREDICTIVE_ENGINE is disabled. Returning mock empty metrics...")
            # Return empty baseline defaults
            return PredictiveDashboardSummary(
                revenue_forecast=RevenueForecast(),
                extraction_health=None,
                recommendations=SmartRecommendations(
                    preferred_company_template="None",
                    preferred_vehicle_template="None"
                )
            )

        return PredictiveOrchestrator.get_dashboard_summary(db)

    @staticmethod
    def get_forecasts(db: Session) -> RevenueForecast:
        """
        Retrieves revenue forecasts.
        """
        if not getattr(settings, "USE_PREDICTIVE_ENGINE", False):
            return RevenueForecast()
        return ForecastEngine.calculate_revenue_forecast(db)

    @staticmethod
    def get_anomalies(db: Session) -> list:
        """
        Retrieves current anomalies.
        """
        if not getattr(settings, "USE_PREDICTIVE_ENGINE", False):
            return []
        return AnomalyDetector.detect_anomalies(db)

    @staticmethod
    def get_recommendations(db: Session, company_name: str = None) -> SmartRecommendations:
        """
        Retrieves recommendations.
        """
        if not getattr(settings, "USE_PREDICTIVE_ENGINE", False):
            return SmartRecommendations(
                preferred_company_template="None",
                preferred_vehicle_template="None"
            )
        return RecommendationEngine.get_smart_recommendations(db, company_name)
