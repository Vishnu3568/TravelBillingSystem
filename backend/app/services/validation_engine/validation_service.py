from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session
from app.services.field_labeling.field_models import LabeledDocument
from app.services.validation_engine.validation_models import ValidatedDocument
from app.services.validation_engine.validation_orchestrator import ValidationOrchestrator

class ValidationEngineService:
    @staticmethod
    def validate_labeled_document(db: Optional[Session], labeled_doc: LabeledDocument) -> ValidatedDocument:
        """
        Main entry point facade for validating a labeled document.
        """
        return ValidationOrchestrator.run_validation(db, labeled_doc)
