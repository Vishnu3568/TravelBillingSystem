from __future__ import annotations

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.bill import Bill
from app.services.field_labeling.field_constants import FieldLabel
from app.services.field_labeling.field_models import LabeledDocument
from app.services.validation_engine.validation_models import ValidationIssue, Severity

logger = logging.getLogger("duplicate_detector")

class DuplicateDetector:
    @staticmethod
    def validate(db: Optional[Session], labeled_doc: LabeledDocument) -> List[ValidationIssue]:
        """
        Detects duplicates:
        - DB check for existing (duty_slip_no, company_name) combination.
        - DB check for existing bill_number.
        """
        issues = []

        # Index elements by label
        by_label = {}
        for el in labeled_doc.elements:
            by_label.setdefault(el.label, []).append(el)

        # 1. DB duplicate checks
        duty_slips = by_label.get(FieldLabel.HEADER_DUTY_SLIP.value, [])
        companies = by_label.get(FieldLabel.HEADER_COMPANY.value, [])
        
        if db and duty_slips and companies:
            ds_val = duty_slips[0].text.strip()
            comp_val = companies[0].text.strip()
            
            if ds_val and comp_val:
                try:
                    existing = db.query(Bill).filter(
                        Bill.duty_slip_no == ds_val,
                        Bill.company_name == comp_val
                    ).first()
                    
                    if existing:
                        issues.append(
                            ValidationIssue(
                                field=FieldLabel.HEADER_DUTY_SLIP.value,
                                severity=Severity.WARNING,
                                message=f"Duplicate DB warning: Duty Slip '{ds_val}' already exists in DB for company '{comp_val}'.",
                                coordinates=duty_slips[0].coordinates,
                                confidence=duty_slips[0].confidence,
                                rule_violated="DUPLICATE_DUTY_SLIP_DB",
                                suggested_correction="Verify if this slip was already imported."
                            )
                        )
                except Exception as e:
                    logger.warning("Duplicate DB query failed: %s", e)

        # 2. Check duplicate bill numbers
        bill_nums = by_label.get(FieldLabel.HEADER_BILL_NUMBER.value, [])
        if db and bill_nums:
            bill_num_val = bill_nums[0].text.strip()
            if bill_num_val and bill_num_val != "UNKNOWN":
                try:
                    existing = db.query(Bill).filter(Bill.bill_number == bill_num_val).first()
                    if existing:
                        issues.append(
                            ValidationIssue(
                                field=FieldLabel.HEADER_BILL_NUMBER.value,
                                severity=Severity.WARNING,
                                message=f"Duplicate DB warning: Bill Number '{bill_num_val}' already exists in DB.",
                                coordinates=bill_nums[0].coordinates,
                                confidence=bill_nums[0].confidence,
                                rule_violated="DUPLICATE_BILL_NUMBER_DB",
                                suggested_correction="Verify invoice number."
                            )
                        )
                except Exception as e:
                    logger.warning("Duplicate Bill Number query failed: %s", e)

        return issues
