from __future__ import annotations

from typing import List
from app.services.field_labeling.field_models import LabeledDocument
from app.services.validation_engine.validation_models import ValidationIssue, Severity
from app.services.validation_engine.validation_rules import ValidationRulesConfig

class ConfidenceValidator:
    @staticmethod
    def validate(labeled_doc: LabeledDocument) -> List[ValidationIssue]:
        issues = []
        for el in labeled_doc.elements:
            conf = el.confidence

            if conf < ValidationRulesConfig.MIN_CONFIDENCE_WARNING:
                issues.append(
                    ValidationIssue(
                        field=el.label,
                        severity=Severity.ERROR,
                        message=f"Element {el.id} has dangerously low confidence: {conf * 100:.1f}%. Manual Review Required.",
                        coordinates=el.coordinates,
                        confidence=conf,
                        rule_violated="LOW_CONFIDENCE_ERROR",
                        suggested_correction="Verify cell values and re-classify."
                    )
                )
            elif conf < ValidationRulesConfig.MIN_CONFIDENCE_PASS:
                issues.append(
                    ValidationIssue(
                        field=el.label,
                        severity=Severity.WARNING,
                        message=f"Element {el.id} has moderate confidence: {conf * 100:.1f}%. Verify accuracy.",
                        coordinates=el.coordinates,
                        confidence=conf,
                        rule_violated="LOW_CONFIDENCE_WARNING",
                        suggested_correction="Check if value is correct."
                    )
                )
        return issues
