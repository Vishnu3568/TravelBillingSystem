from __future__ import annotations

import logging
from typing import Dict, Any, List
from app.services.field_labeling.field_constants import FieldLabel

logger = logging.getLogger("confidence_engine")

class ConfidenceEngine:
    CONFIDENCE_THRESHOLD = 0.95

    @staticmethod
    def process_classifications(classifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Processes predictions and applies threshold rules. If self-assessed confidence
        is below 0.95, it coerces the label to UNKNOWN.
        """
        processed = []
        for c in classifications:
            c_id = c.get("id")
            label = c.get("label", FieldLabel.UNKNOWN.value)
            confidence = c.get("confidence", 0.0)

            if confidence < ConfidenceEngine.CONFIDENCE_THRESHOLD:
                logger.info(
                    "Coercing element %s label from %s to UNKNOWN due to low confidence: %s",
                    c_id, label, confidence
                )
                label = FieldLabel.UNKNOWN.value

            processed.append({
                "id": c_id,
                "label": label,
                "confidence": confidence
            })
        return processed
