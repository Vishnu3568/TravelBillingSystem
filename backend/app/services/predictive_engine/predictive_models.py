from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class RevenueForecast(BaseModel):
    daily: float = 0.0
    weekly: float = 0.0
    monthly: float = 0.0
    quarterly: float = 0.0
    yearly: float = 0.0
    seasonality_multiplier: float = 1.0

class PaymentPrediction(BaseModel):
    company_name: str
    late_payment_probability: float = 0.0
    expected_collection_days: int = 30
    risk_level: str = "LOW" # LOW, MEDIUM, HIGH

class AnomalyRecord(BaseModel):
    id: str
    type: str # e.g. "IMPOSSIBLE_DURATION", "DUPLICATE_INVOICE", "UNUSUAL_AMOUNT", "ABNORMAL_CHARGES"
    description: str
    severity: str # e.g. "LOW", "MEDIUM", "HIGH"
    confidence: float = 0.90
    reference_id: Optional[str] = None

class ExtractionPrediction(BaseModel):
    extraction_success_probability: float = 0.95
    manual_review_likelihood: float = 0.05
    expected_validation_score: float = 0.98
    expected_confidence: float = 0.95

class SmartRecommendations(BaseModel):
    preferred_company_template: str
    preferred_vehicle_template: str
    suggested_pricing_per_km: float = 18.0
    likely_fields: List[str] = Field(default_factory=list)

class PredictiveDashboardSummary(BaseModel):
    revenue_forecast: RevenueForecast
    payment_risks: List[PaymentPrediction] = Field(default_factory=list)
    anomalies: List[AnomalyRecord] = Field(default_factory=list)
    extraction_health: Optional[ExtractionPrediction] = None
    recommendations: SmartRecommendations
    fleet_utilization: float = 0.85
    learning_growth_percent: float = 12.5
    active_anomalies_count: int = 0
