from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.services.document_intelligence.document_models import DocumentMetadata
from app.services.field_labeling.field_models import LabeledDocument

class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

class Recommendation(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    FAIL = "FAIL"

class ValidationIssue(BaseModel):
    field: str
    severity: Severity
    message: str
    coordinates: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    rule_violated: str
    suggested_correction: Optional[str] = None

class ValidationSummary(BaseModel):
    overall_quality_score: float
    average_confidence: float
    recommendation: Recommendation
    error_count: int
    warning_count: int
    info_count: int

class ValidatedDocument(BaseModel):
    metadata: DocumentMetadata
    labeled_document: LabeledDocument
    validation_summary: ValidationSummary
    issues: List[ValidationIssue] = Field(default_factory=list)

    def to_json(self) -> Dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)
