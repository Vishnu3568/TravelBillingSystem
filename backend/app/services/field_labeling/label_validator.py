from __future__ import annotations

from typing import Dict, Any, List, Set
from app.services.field_labeling.field_constants import FieldLabel

class LabelValidator:
    @staticmethod
    def validate_classifications(classifications: List[Dict[str, Any]], allowed_ids: Set[str]) -> List[Dict[str, Any]]:
        """
        Validates classification objects to ensure the labels are members of allowed
        enums, and the element IDs correspond to prepared element IDs.
        """
        validated = []
        allowed_labels = {l.value for l in FieldLabel}

        for c in classifications:
            c_id = c.get("id")
            label = c.get("label")
            confidence = c.get("confidence", 0.0)

            # Revert to UNKNOWN if label not recognized
            if label not in allowed_labels:
                label = FieldLabel.UNKNOWN.value

            # Skip classifications for elements we did not request
            if c_id not in allowed_ids:
                continue

            validated.append({
                "id": c_id,
                "label": label,
                "confidence": confidence
            })
        return validated
