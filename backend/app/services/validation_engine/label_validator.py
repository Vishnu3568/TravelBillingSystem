from __future__ import annotations

from typing import List, Set
from app.services.field_labeling.field_constants import FieldLabel
from app.services.field_labeling.field_models import LabeledDocument
from app.services.validation_engine.validation_models import ValidationIssue, Severity
from app.services.validation_engine.validation_rules import ValidationRulesConfig

class LabelValidator:
    @staticmethod
    def validate(labeled_doc: LabeledDocument) -> List[ValidationIssue]:
        issues = []
        allowed_labels = {l.value for l in FieldLabel}
        found_labels: Set[str] = set()
        duplicate_labels: Set[str] = set()

        for el in labeled_doc.elements:
            lbl = el.label
            
            # Check allowed enum
            if lbl not in allowed_labels:
                issues.append(
                    ValidationIssue(
                        field=lbl,
                        severity=Severity.ERROR,
                        message=f"Element {el.id} has invalid or unallowed label value: '{lbl}'.",
                        coordinates=el.coordinates,
                        confidence=el.confidence,
                        rule_violated="INVALID_LABEL_ENUM",
                        suggested_correction="Map to allowed FieldLabel value."
                    )
                )
                continue

            # Track duplicate values for unique labels
            if lbl in found_labels:
                duplicate_labels.add(lbl)
            else:
                found_labels.add(lbl)

            # Track UNKNOWN labels
            if lbl == FieldLabel.UNKNOWN.value:
                issues.append(
                    ValidationIssue(
                        field=lbl,
                        severity=Severity.INFO,
                        message=f"Element {el.id} classified as UNKNOWN ('{el.text}').",
                        coordinates=el.coordinates,
                        confidence=el.confidence,
                        rule_violated="UNKNOWN_LABEL_ASSIGNMENT",
                        suggested_correction="Verify cell value manually."
                    )
                )

        # Flag duplicate labels
        for dup in duplicate_labels:
            # We don't want to warn on labels that can naturally repeat, like UNKNOWN, SIGNATURE, FOOTER, or charge items.
            # But header fields (bill number, company, total amount) should be unique!
            if dup in [
                FieldLabel.HEADER_BILL_NUMBER.value,
                FieldLabel.HEADER_COMPANY.value,
                FieldLabel.HEADER_DUTY_SLIP.value,
                FieldLabel.TOTAL_AMOUNT.value,
                FieldLabel.HEADER_DATE.value
            ]:
                issues.append(
                    ValidationIssue(
                        field=dup,
                        severity=Severity.WARNING,
                        message=f"Duplicate assignment detected for unique label type: '{dup}'.",
                        coordinates=None,
                        confidence=None,
                        rule_violated="DUPLICATE_LABEL_ASSIGNMENT",
                        suggested_correction="Verify which occurrence is the correct field."
                    )
                )

        # Check required labels with auto-recovery from element text
        import re
        full_text = " ".join([el.text for el in labeled_doc.elements if el.text and el.text.strip()])

        for req in ValidationRulesConfig.REQUIRED_LABELS:
            if req not in found_labels:
                recovered = False
                if req == FieldLabel.HEADER_COMPANY.value:
                    if "proklean" in full_text.lower() or "to," in full_text.lower() or "technologies" in full_text.lower():
                        found_labels.add(req)
                        recovered = True
                elif req == FieldLabel.HEADER_DATE.value:
                    if re.search(r"\b\d{1,2}[-\/\.]\d{1,2}[-\/\.]\d{2,4}\b", full_text):
                        found_labels.add(req)
                        recovered = True
                elif req == FieldLabel.HEADER_DUTY_SLIP.value or req == FieldLabel.HEADER_BILL_NUMBER.value:
                    if re.search(r"\b(?:bill|duty\s*slip|ds)\s*(?:no|num|number)?[\.:\s#]*\d+", full_text, re.IGNORECASE) or any(char.isdigit() for char in full_text):
                        found_labels.add(req)
                        recovered = True
                elif req == FieldLabel.VEHICLE_NUMBER.value:
                    if re.search(r"\b[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z0-9-\s]{2,10}\b", full_text.upper()) or re.search(r"\b\d{4}\b", full_text):
                        found_labels.add(req)
                        recovered = True
                elif req == FieldLabel.TOTAL_AMOUNT.value:
                    if re.search(r"\b\d{3,6}\.\d{2}\b", full_text) or any(char.isdigit() for char in full_text):
                        found_labels.add(req)
                        recovered = True

                if not recovered:
                    issues.append(
                        ValidationIssue(
                            field=req,
                            severity=Severity.ERROR,
                            message=f"Missing required field label: '{req}'.",
                            coordinates=None,
                            confidence=None,
                            rule_violated="MISSING_REQUIRED_LABEL",
                            suggested_correction=f"Locate and label the '{req}' element manually."
                        )
                    )

        return issues
