from __future__ import annotations

import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.config import settings
from app.models.bill import Bill
from app.models.learning import CorrectionHistory

# Import Predictive Engine modules
from app.services.predictive_engine.predictive_models import PredictiveDashboardSummary
from app.services.predictive_engine.forecast_engine import ForecastEngine
from app.services.predictive_engine.anomaly_detector import AnomalyDetector
from app.services.predictive_engine.duplicate_predictor import DuplicatePredictor
from app.services.predictive_engine.payment_predictor import PaymentPredictor
from app.services.predictive_engine.fleet_predictor import FleetPredictor
from app.services.predictive_engine.recommendation_engine import RecommendationEngine
from app.services.predictive_engine.predictive_orchestrator import PredictiveOrchestrator
from app.services.predictive_engine.predictive_service import PredictiveService

# Setup DB session fixture
@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_revenue_forecasting(db_session):
    # Seed historical bills
    bill = Bill(
        bill_number="BILL-F1",
        company_name="Portescap",
        grand_total=10000.0,
        vehicle_name="Sedan"
    )
    db_session.add(bill)
    db_session.commit()

    forecast = ForecastEngine.calculate_revenue_forecast(db_session)
    assert forecast.daily > 0.0
    assert forecast.monthly > 0.0

def test_anomaly_detection(db_session):
    # Seed bill with impossible travel speed (e.g. 500 km in 2 hours -> 250 km/h)
    bill_impossible = Bill(
        bill_number="BILL-A1",
        company_name="Portescap",
        grand_total=5000.0,
        total_kms=500.0,
        total_hours=2.0
    )
    db_session.add(bill_impossible)
    db_session.commit()

    anoms = AnomalyDetector.detect_anomalies(db_session)
    assert len(anoms) > 0
    # Confirm it flagged the impossible speed
    types = [a.type for a in anoms]
    assert "IMPOSSIBLE_DURATION" in types

def test_duplicate_prediction(db_session):
    # Seed duplicate bills sharing the same duty slip number
    bill1 = Bill(bill_number="BILL-DUP1", duty_slip_no="DS-DUP", company_name="Portescap", grand_total=5000.0)
    bill2 = Bill(bill_number="BILL-DUP2", duty_slip_no="DS-DUP", company_name="Portescap", grand_total=5000.0)
    db_session.add_all([bill1, bill2])
    db_session.commit()

    dups = DuplicatePredictor.scan_duplicates(db_session)
    assert len(dups) >= 2
    assert dups[0].type == "DUPLICATE_INVOICE"

def test_payment_prediction(db_session):
    bill = Bill(bill_number="BILL-P1", company_name="Portescap", grand_total=120000.0)
    db_session.add(bill)
    db_session.commit()

    payments = PaymentPredictor.predict_payments(db_session)
    assert len(payments) == 1
    assert payments[0].company_name == "Portescap"
    # Should flag high risk due to bill size > 100k
    assert payments[0].risk_level == "HIGH"

def test_fleet_prediction(db_session):
    bill = Bill(bill_number="BILL-F1", company_name="Portescap", vehicle_name="TS09EX1111")
    db_session.add(bill)
    db_session.commit()

    util = FleetPredictor.get_fleet_utilization(db_session)
    assert util >= 0.0

def test_recommendation_engine(db_session):
    recs = RecommendationEngine.get_smart_recommendations(db_session, "Portescap")
    assert recs.preferred_company_template is not None
    assert recs.suggested_pricing_per_km == 18.0

def test_dashboard_summary_orchestrator(db_session):
    summary = PredictiveOrchestrator.get_dashboard_summary(db_session)
    assert summary.fleet_utilization is not None
    assert summary.active_anomalies_count == 0

def test_feature_flags_and_facade(db_session):
    settings.USE_PREDICTIVE_ENGINE = False
    
    summary_disabled = PredictiveService.get_predictive_summary(db_session)
    assert summary_disabled.extraction_health is None
    
    settings.USE_PREDICTIVE_ENGINE = True
    summary_enabled = PredictiveService.get_predictive_summary(db_session)
    assert summary_enabled.extraction_health is not None
