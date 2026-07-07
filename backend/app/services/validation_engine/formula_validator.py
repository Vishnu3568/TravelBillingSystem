from __future__ import annotations

import re
from typing import List, Optional
from app.services.field_labeling.field_constants import FieldLabel
from app.services.field_labeling.field_models import LabeledDocument
from app.services.validation_engine.validation_models import ValidationIssue, Severity
from app.services.validation_engine.validation_rules import ValidationRulesConfig

class FormulaValidator:
    @staticmethod
    def validate(labeled_doc: LabeledDocument) -> List[ValidationIssue]:
        issues = []

        # Index elements by label
        by_label = {}
        for el in labeled_doc.elements:
            by_label.setdefault(el.label, []).append(el)

        def safe_float(label: str, default: float = 0.0) -> float:
            items = by_label.get(label, [])
            if not items:
                return default
            val_str = items[0].text.strip()
            # Clean non-numeric characters except dots
            cleaned = re.sub(r'[^\d\.]', '', val_str)
            try:
                return float(cleaned) if cleaned else default
            except ValueError:
                return default

        # 1. Extra KM Formula Verification
        extra_km_formula_el = by_label.get(FieldLabel.EXTRA_KM_FORMULA.value, [])
        extra_km_amt_el = by_label.get(FieldLabel.EXTRA_KM_AMOUNT.value, [])
        if extra_km_formula_el and extra_km_amt_el:
            formula_text = extra_km_formula_el[0].text.strip()
            claimed_amt = safe_float(FieldLabel.EXTRA_KM_AMOUNT.value)
            
            computed_val = FormulaValidator._eval_multiplication(formula_text)
            if computed_val is not None:
                if abs(computed_val - claimed_amt) > ValidationRulesConfig.ARITHMETIC_TOLERANCE:
                    issues.append(
                        ValidationIssue(
                            field=FieldLabel.EXTRA_KM_AMOUNT.value,
                            severity=Severity.WARNING,
                            message=f"Extra KM amount mismatch: Formula '{formula_text}' computes to ₹{computed_val:.2f}, but document states '{extra_km_amt_el[0].text}'.",
                            coordinates=extra_km_amt_el[0].coordinates,
                            confidence=extra_km_amt_el[0].confidence,
                            rule_violated="EXTRA_KM_FORMULA_MISMATCH",
                            suggested_correction=f"Value should be '{computed_val:.2f}'."
                        )
                    )

        # 2. Extra Hour Formula Verification
        extra_hr_formula_el = by_label.get(FieldLabel.EXTRA_HOUR_FORMULA.value, [])
        extra_hr_amt_el = by_label.get(FieldLabel.EXTRA_HOUR_AMOUNT.value, [])
        if extra_hr_formula_el and extra_hr_amt_el:
            formula_text = extra_hr_formula_el[0].text.strip()
            claimed_amt = safe_float(FieldLabel.EXTRA_HOUR_AMOUNT.value)
            
            computed_val = FormulaValidator._eval_multiplication(formula_text)
            if computed_val is not None:
                if abs(computed_val - claimed_amt) > ValidationRulesConfig.ARITHMETIC_TOLERANCE:
                    issues.append(
                        ValidationIssue(
                            field=FieldLabel.EXTRA_HOUR_AMOUNT.value,
                            severity=Severity.WARNING,
                            message=f"Extra Hour amount mismatch: Formula '{formula_text}' computes to ₹{computed_val:.2f}, but document states '{extra_hr_amt_el[0].text}'.",
                            coordinates=extra_hr_amt_el[0].coordinates,
                            confidence=extra_hr_amt_el[0].confidence,
                            rule_violated="EXTRA_HOUR_FORMULA_MISMATCH",
                            suggested_correction=f"Value should be '{computed_val:.2f}'."
                        )
                    )

        # 3. Grand Total Calculation check
        # baseAmount + bata + toll + parking + permit + other + extra_kms_amt + extra_hours_amt == totalAmount
        base_amt = safe_float(FieldLabel.BASE_PACKAGE.value)
        driver_bata = safe_float(FieldLabel.DRIVER_BATA.value)
        toll = safe_float(FieldLabel.TOLL.value)
        parking = safe_float(FieldLabel.PARKING.value)
        permit = safe_float(FieldLabel.PERMIT.value)
        other = safe_float(FieldLabel.OTHER_CHARGE.value)
        
        extra_km_amt = safe_float(FieldLabel.EXTRA_KM_AMOUNT.value)
        extra_hr_amt = safe_float(FieldLabel.EXTRA_HOUR_AMOUNT.value)
        
        # If extra KM/Hour amounts are missing but formulas are present, evaluate them
        if extra_km_amt == 0.0 and extra_km_formula_el:
            eval_val = FormulaValidator._eval_multiplication(extra_km_formula_el[0].text.strip())
            if eval_val is not None:
                extra_km_amt = eval_val

        if extra_hr_amt == 0.0 and extra_hr_formula_el:
            eval_val = FormulaValidator._eval_multiplication(extra_hr_formula_el[0].text.strip())
            if eval_val is not None:
                extra_hr_amt = eval_val

        claimed_total = safe_float(FieldLabel.TOTAL_AMOUNT.value)
        computed_total = base_amt + driver_bata + toll + parking + permit + other + extra_km_amt + extra_hr_amt

        if claimed_total > 0.0:
            if abs(claimed_total - computed_total) > ValidationRulesConfig.ARITHMETIC_TOLERANCE:
                total_el = by_label.get(FieldLabel.TOTAL_AMOUNT.value, [])
                issues.append(
                    ValidationIssue(
                        field=FieldLabel.TOTAL_AMOUNT.value,
                        severity=Severity.ERROR,
                        message=f"Grand Total mismatch: Claimed total is ₹{claimed_total:.2f}, but sum of components computes to ₹{computed_total:.2f}.",
                        coordinates=total_el[0].coordinates if total_el else None,
                        confidence=total_el[0].confidence if total_el else None,
                        rule_violated="GRAND_TOTAL_ARITHMETIC_MISMATCH",
                        suggested_correction=f"Check if any components are mislabeled. Computed: '{computed_total:.2f}'."
                    )
                )

        return issues

    @staticmethod
    def _eval_multiplication(text: str) -> Optional[float]:
        # E.g. "28x15" or "3 * 150"
        match = re.search(r'(\d+(?:\.\d+)?)\s*[xX\*]\s*(\d+(?:\.\d+)?)', text)
        if match:
            try:
                val1 = float(match.group(1))
                val2 = float(match.group(2))
                return val1 * val2
            except ValueError:
                pass
        return None
