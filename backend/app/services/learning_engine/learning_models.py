from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CorrectionRecord(BaseModel):
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    field_type: str
    table_number: Optional[int] = None
    row_index: Optional[int] = None
    column_index: Optional[int] = None
    company_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    bill_number: Optional[str] = None
    reviewer: Optional[str] = None
    reason: Optional[str] = None
    ai_confidence: Optional[float] = None
    validation_status: Optional[str] = None

class CompanyLayoutProfile(BaseModel):
    company_name: str
    layout_name: Optional[str] = "Layout A"
    header_positions: Dict[str, Any] = Field(default_factory=dict)
    field_locations: Dict[str, Any] = Field(default_factory=dict)
    preferred_labels: List[str] = Field(default_factory=list)
    frequently_corrected_fields: Dict[str, int] = Field(default_factory=dict)
    average_confidence: float = 1.0
    extraction_success_rate: float = 1.0

class VehicleLayoutProfile(BaseModel):
    vehicle_type: str
    layout_name: Optional[str] = "Layout A"
    recurring_structures: Dict[str, Any] = Field(default_factory=dict)

class LearningStatisticsSummary(BaseModel):
    total_corrections: int = 0
    learning_accuracy: float = 1.0
    most_corrected_fields: Dict[str, int] = Field(default_factory=dict)
    top_companies: List[Dict[str, Any]] = Field(default_factory=list)
    top_vehicles: List[Dict[str, Any]] = Field(default_factory=list)
    reviewer_activity: Dict[str, int] = Field(default_factory=dict)
    confidence_trends: Dict[str, float] = Field(default_factory=dict)
    pattern_growth: int = 0
    knowledge_base_size: int = 0
