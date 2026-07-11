import logging
from sqlalchemy.orm import Session
from app.services.predictive_engine.predictive_models import PredictiveDashboardSummary, ExtractionPrediction
from app.services.predictive_engine.forecast_engine import ForecastEngine
from app.services.predictive_engine.anomaly_detector import AnomalyDetector
from app.services.predictive_engine.duplicate_predictor import DuplicatePredictor
from app.services.predictive_engine.payment_predictor import PaymentPredictor
from app.services.predictive_engine.fleet_predictor import FleetPredictor
from app.services.predictive_engine.recommendation_engine import RecommendationEngine
from app.services.predictive_engine.confidence_predictor import ConfidencePredictor

logger = logging.getLogger("predictive_orchestrator")

class PredictiveOrchestrator:
    @staticmethod
    def get_dashboard_summary(db: Session) -> PredictiveDashboardSummary:
        """
        Assembles all forecasting, payment risks, anomalies, and templates
        into a consolidated summary dictionary model.
        """
        # 1. Run Revenue Forecasts
        forecast = ForecastEngine.calculate_revenue_forecast(db)

        # 2. Collect Anomalies & Duplicates
        anomalies = AnomalyDetector.detect_anomalies(db)
        duplicates = DuplicatePredictor.scan_duplicates(db)
        combined_anomalies = anomalies + duplicates

        # 3. Predict Late Payments
        payments = PaymentPredictor.predict_payments(db)

        # 4. Fleet Utilization
        utilization = FleetPredictor.get_fleet_utilization(db)

        # 5. Smart Recommendations
        recs = RecommendationEngine.get_smart_recommendations(db)

        # 6. Extraction Health Preds
        health = ConfidencePredictor.predict_extraction_confidence(db)

        return PredictiveDashboardSummary(
            revenue_forecast=forecast,
            payment_risks=payments,
            anomalies=combined_anomalies,
            extraction_health=health,
            recommendations=recs,
            fleet_utilization=utilization,
            learning_growth_percent=14.2,
            active_anomalies_count=len(combined_anomalies)
        )
