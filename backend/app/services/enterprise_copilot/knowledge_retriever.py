import json
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.models.learning import CorrectionHistory, CompanyPatterns, VehiclePatterns, ConfidenceHistory

class KnowledgeRetriever:
    @staticmethod
    def get_recent_corrections(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves recent reviewer edits.
        """
        corrections = db.query(CorrectionHistory).order_by(CorrectionHistory.timestamp.desc()).limit(limit).all()
        return [
            {
                "field": c.field_type,
                "original": c.original_value,
                "corrected": c.corrected_value,
                "company": c.company_name,
                "vehicle": c.vehicle_number,
                "reviewer": c.reviewer,
                "reason": c.reason
            }
            for c in corrections
        ]

    @staticmethod
    def get_company_templates(db: Session) -> List[Dict[str, Any]]:
        """
        Retrieves all learned company template layouts.
        """
        profiles = db.query(CompanyPatterns).all()
        result = []
        for p in profiles:
            try:
                result.append({
                    "company_name": p.company_name,
                    "layout_name": p.layout_name,
                    "frequently_corrected_fields": json.loads(p.frequently_corrected_fields or "{}"),
                    "preferred_labels": json.loads(p.preferred_labels or "[]"),
                    "average_confidence": p.average_confidence
                })
            except Exception:
                pass
        return result

    @staticmethod
    def get_vehicle_structures(db: Session) -> List[Dict[str, Any]]:
        """
        Retrieves all vehicle structures learned.
        """
        profiles = db.query(VehiclePatterns).all()
        result = []
        for p in profiles:
            try:
                result.append({
                    "vehicle_type": p.vehicle_type,
                    "recurring_structures": json.loads(p.recurring_structures or "{}")
                })
            except Exception:
                pass
        return result
