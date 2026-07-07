from __future__ import annotations

from typing import List, Set
from app.services.field_labeling.field_constants import FieldLabel

class ValidationRulesConfig:
    # Set of labels that MUST exist in a valid bill
    REQUIRED_LABELS: Set[str] = {
        FieldLabel.HEADER_COMPANY.value,
        FieldLabel.HEADER_DUTY_SLIP.value,
        FieldLabel.VEHICLE_NUMBER.value,
        FieldLabel.TOTAL_AMOUNT.value,
        FieldLabel.HEADER_DATE.value
    }

    # Tolerance for floating point differences in formulas
    ARITHMETIC_TOLERANCE: float = 2.0

    # Minimum confidence to avoid error/manual review
    MIN_CONFIDENCE_PASS: float = 0.98
    MIN_CONFIDENCE_WARNING: float = 0.95
