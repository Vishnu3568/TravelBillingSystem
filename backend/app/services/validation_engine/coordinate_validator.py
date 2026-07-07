from __future__ import annotations

from typing import List
from app.services.field_labeling.field_models import LabeledDocument
from app.services.validation_engine.validation_models import ValidationIssue, Severity

class CoordinateValidator:
    @staticmethod
    def validate(labeled_doc: LabeledDocument) -> List[ValidationIssue]:
        issues = []
        for el in labeled_doc.elements:
            coords = el.coordinates
            if not coords:
                issues.append(
                    ValidationIssue(
                        field=el.label,
                        severity=Severity.ERROR,
                        message=f"Element {el.id} has missing coordinates metadata.",
                        coordinates=coords,
                        confidence=el.confidence,
                        rule_violated="COORDINATE_MISSING",
                        suggested_correction="Re-extract document layout structurally."
                    )
                )
                continue

            page = coords.get("page_number")
            if not page or page < 1:
                issues.append(
                    ValidationIssue(
                        field=el.label,
                        severity=Severity.ERROR,
                        message=f"Element {el.id} has invalid page number coordinate: {page}.",
                        coordinates=coords,
                        confidence=el.confidence,
                        rule_violated="INVALID_PAGE_COORDINATE",
                        suggested_correction="Check document bounds."
                    )
                )

            # Table specific coordinate checks
            table_no = coords.get("table_number")
            if table_no is not None:
                row = coords.get("row_index")
                col = coords.get("column_index")
                
                if table_no < 1 or row is None or col is None or row < 0 or col < 0:
                    issues.append(
                        ValidationIssue(
                            field=el.label,
                            severity=Severity.ERROR,
                            message=f"Table cell element {el.id} has out-of-bound indexes. Row: {row}, Col: {col}, Table: {table_no}.",
                            coordinates=coords,
                            confidence=el.confidence,
                            rule_violated="INVALID_CELL_INDEXES",
                            suggested_correction="Verify table geometry."
                        )
                    )
        return issues
