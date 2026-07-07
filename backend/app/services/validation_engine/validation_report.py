from __future__ import annotations

from typing import List
from app.services.field_labeling.field_models import LabeledDocument
from app.services.validation_engine.validation_models import (
    ValidatedDocument,
    ValidationIssue,
    ValidationSummary,
    Severity,
    Recommendation,
)

class ValidationReportGenerator:
    @staticmethod
    def generate_report(labeled_doc: LabeledDocument, issues: List[ValidationIssue]) -> ValidatedDocument:
        """
        Aggregates validation issues, computes overall quality and confidence scores,
        and assigns the final recommendation status (PASS, PASS_WITH_WARNINGS, MANUAL_REVIEW, FAIL).
        """
        error_count = sum(1 for iss in issues if iss.severity == Severity.ERROR)
        warning_count = sum(1 for iss in issues if iss.severity == Severity.WARNING)
        info_count = sum(1 for iss in issues if iss.severity == Severity.INFO)

        # 1. Compute Quality Score (starts at 100.0)
        quality_score = 100.0
        quality_score -= error_count * 15.0
        quality_score -= warning_count * 5.0
        quality_score -= info_count * 1.0
        quality_score = max(0.0, min(100.0, quality_score))

        # 2. Compute Average Confidence
        total_conf = sum(el.confidence for el in labeled_doc.elements)
        element_count = len(labeled_doc.elements)
        avg_confidence = (total_conf / element_count) if element_count > 0 else 1.0

        # 3. Determine Recommendation
        recommendation = Recommendation.PASS
        if error_count > 0:
            if error_count >= 2 or quality_score < 70.0:
                recommendation = Recommendation.FAIL
            else:
                recommendation = Recommendation.MANUAL_REVIEW
        elif warning_count > 0 or quality_score < 95.0:
            recommendation = Recommendation.PASS_WITH_WARNINGS
        else:
            recommendation = Recommendation.PASS

        summary = ValidationSummary(
            overall_quality_score=quality_score,
            average_confidence=avg_confidence,
            recommendation=recommendation,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count
        )

        return ValidatedDocument(
            metadata=labeled_doc.metadata,
            labeled_document=labeled_doc,
            validation_summary=summary,
            issues=issues
        )
