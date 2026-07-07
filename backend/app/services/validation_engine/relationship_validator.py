from __future__ import annotations

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.vehicle import Vehicle
from app.services.field_labeling.field_constants import FieldLabel
from app.services.field_labeling.field_models import LabeledDocument
from app.services.validation_engine.validation_models import ValidationIssue, Severity

logger = logging.getLogger("relationship_validator")

class RelationshipValidator:
    @staticmethod
    def validate(db: Optional[Session], labeled_doc: LabeledDocument) -> List[ValidationIssue]:
        issues = []

        # Index elements by label
        by_label = {}
        for el in labeled_doc.elements:
            by_label.setdefault(el.label, []).append(el)

        # 1. Vehicle Number vs Vehicle Type check (with DB)
        veh_nums = by_label.get(FieldLabel.VEHICLE_NUMBER.value, [])
        veh_types = by_label.get(FieldLabel.VEHICLE_TYPE.value, [])
        if db and veh_nums and veh_types:
            v_num = veh_nums[0].text.strip()
            v_type_doc = veh_types[0].text.strip().lower()
            
            # Clean vehicle registration number (remove spaces, hyphens)
            import re
            cleaned_num = re.sub(r'[-\s]', '', v_num).upper()
            
            try:
                # Query DB to find matching vehicle
                vehicle = db.query(Vehicle).filter(
                    re.sub(r'[-\s]', '', Vehicle.registration_number).upper() == cleaned_num
                ).first()
                
                if vehicle:
                    v_type_db = (vehicle.type or "").strip().lower()
                    # Check close matching (substring)
                    if v_type_db and v_type_db not in v_type_doc and v_type_doc not in v_type_db:
                        issues.append(
                            ValidationIssue(
                                field=FieldLabel.VEHICLE_NUMBER.value,
                                severity=Severity.WARNING,
                                message=f"Vehicle type mismatch: Vehicle '{v_num}' is registered as '{vehicle.type}' in DB, but document lists '{veh_types[0].text}'.",
                                coordinates=veh_nums[0].coordinates,
                                confidence=veh_nums[0].confidence,
                                rule_violated="VEHICLE_TYPE_MISMATCH",
                                suggested_correction=f"Change to '{vehicle.type}'."
                            )
                        )
            except Exception as e:
                logger.warning("Vehicle relation validation failed: %s", e)

        # 2. Booked By Location Check
        booked_bys = by_label.get(FieldLabel.BOOKED_BY.value, [])
        for el in booked_bys:
            coords = el.coordinates or {}
            # If Booked By is near the bottom row of a table or contains signature words
            text_lower = el.text.lower()
            if "signature" in text_lower or "authorised" in text_lower:
                issues.append(
                    ValidationIssue(
                        field=FieldLabel.BOOKED_BY.value,
                        severity=Severity.ERROR,
                        message=f"Booked By element contains signature or authorisation footer keyword: '{el.text}'. Possible layout extraction overlap.",
                        coordinates=el.coordinates,
                        confidence=el.confidence,
                        rule_violated="BOOKED_BY_FOOTER_OVERLAP",
                        suggested_correction="Check if cell was misclassified."
                    )
                )

        # 3. Amount in Words vs Total Amount check
        amounts = by_label.get(FieldLabel.TOTAL_AMOUNT.value, [])
        words_list = by_label.get(FieldLabel.AMOUNT_WORDS.value, [])
        if amounts and words_list:
            total_str = amounts[0].text.strip()
            words_str = words_list[0].text.strip().lower()
            
            # Extract float
            try:
                import re
                match = re.search(r'[\d\.]+', total_str)
                if match:
                    total_val = float(match.group(0))
                    # Simple heuristic checks for digits
                    total_int = int(total_val)
                    
                    # Convert digit to word keywords to check presence
                    digit_words = {
                        1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
                        6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
                        11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
                        16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty",
                        30: "thirty", 40: "forty", 50: "fifty", 60: "sixty", 70: "seventy",
                        80: "eighty", 90: "ninety", 100: "hundred", 1000: "thousand"
                    }
                    
                    # Check if the words contains the matching thousands or hundreds digit if high enough
                    if total_int >= 1000:
                        thousands_digit = total_int // 1000
                        if thousands_digit in digit_words:
                            word = digit_words[thousands_digit]
                            if word not in words_str and "thousand" not in words_str:
                                issues.append(
                                    ValidationIssue(
                                        field=FieldLabel.AMOUNT_WORDS.value,
                                        severity=Severity.WARNING,
                                        message=f"Amount in words '{words_list[0].text}' might not correspond to Total Amount '{total_str}' (expected keyword 'thousand').",
                                        coordinates=words_list[0].coordinates,
                                        confidence=words_list[0].confidence,
                                        rule_violated="AMOUNT_WORDS_MISMATCH",
                                        suggested_correction="Verify invoice amount words."
                                    )
                                )
            except Exception:
                pass

        # 4. Guest Name Location Check
        guests = by_label.get(FieldLabel.GUEST_NAME.value, [])
        for el in guests:
            if "tulja" in el.text.lower() or "bhavani" in el.text.lower():
                issues.append(
                    ValidationIssue(
                        field=FieldLabel.GUEST_NAME.value,
                        severity=Severity.ERROR,
                        message=f"Guest Name '{el.text}' matches provider agency 'Sri Tulja Bhavani Travels'. Possible extraction overlap.",
                        coordinates=el.coordinates,
                        confidence=el.confidence,
                        rule_violated="GUEST_PROVIDER_OVERLAP",
                        suggested_correction="Extract guest name cell exactly."
                    )
                )

        return issues
