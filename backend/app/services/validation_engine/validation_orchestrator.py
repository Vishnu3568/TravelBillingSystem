from __future__ import annotations

from typing import List, Optional
from sqlalchemy.orm import Session
from app.services.field_labeling.field_models import LabeledDocument
from app.services.validation_engine.validation_models import ValidatedDocument, ValidationIssue
from app.services.validation_engine.coordinate_validator import CoordinateValidator
from app.services.validation_engine.label_validator import LabelValidator
from app.services.validation_engine.confidence_validator import ConfidenceValidator
from app.services.validation_engine.relationship_validator import RelationshipValidator
from app.services.validation_engine.formula_validator import FormulaValidator
from app.services.validation_engine.duplicate_detector import DuplicateDetector
from app.services.validation_engine.validation_report import ValidationReportGenerator

class ValidationOrchestrator:
    @staticmethod
    def run_validation(db: Optional[Session], labeled_doc: LabeledDocument) -> ValidatedDocument:
        """
        Runs the full sequence of validation stages:
        Coordinate → Label → Confidence → Relationship → Formula → Duplicate → Report
        """
        issues: List[ValidationIssue] = []

        # 1. Coordinate Validation
        issues.extend(CoordinateValidator.validate(labeled_doc))

        # 2. Label Validation
        issues.extend(LabelValidator.validate(labeled_doc))

        # 3. Confidence Validation
        issues.extend(ConfidenceValidator.validate(labeled_doc))

        # 4. Relationship Validation
        issues.extend(RelationshipValidator.validate(db, labeled_doc))

        # 5. Formula Validation
        issues.extend(FormulaValidator.validate(labeled_doc))

        # 6. Duplicate Detection
        issues.extend(DuplicateDetector.validate(db, labeled_doc))

        # 7. Generate Validation Report
        return ValidationReportGenerator.generate_report(labeled_doc, issues)
