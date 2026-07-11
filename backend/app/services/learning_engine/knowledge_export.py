import csv
import json
import io
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.models.learning import CompanyPatterns, VehiclePatterns, ConfidenceHistory, KnowledgeBase

class KnowledgeExport:
    @staticmethod
    def export_as_json(db: Session) -> str:
        """
        Exports the entire Knowledge Store (companies, vehicles, confidences, global heuristics) as a JSON string.
        """
        companies = db.query(CompanyPatterns).all()
        vehicles = db.query(VehiclePatterns).all()
        confidences = db.query(ConfidenceHistory).all()
        globals_kb = db.query(KnowledgeBase).all()

        data = {
            "companies": [
                {
                    "company_name": c.company_name,
                    "layout_name": c.layout_name,
                    "header_positions": json.loads(c.header_positions or "{}"),
                    "field_locations": json.loads(c.field_locations or "{}"),
                    "preferred_labels": json.loads(c.preferred_labels or "[]"),
                    "frequently_corrected_fields": json.loads(c.frequently_corrected_fields or "{}"),
                    "average_confidence": c.average_confidence,
                    "extraction_success_rate": c.extraction_success_rate
                }
                for c in companies
            ],
            "vehicles": [
                {
                    "vehicle_type": v.vehicle_type,
                    "layout_name": v.layout_name,
                    "recurring_structures": json.loads(v.recurring_structures or "{}")
                }
                for v in vehicles
            ],
            "confidences": [
                {
                    "field_label": conf.field_label,
                    "correct_predictions_count": conf.correct_predictions_count,
                    "corrected_predictions_count": conf.corrected_predictions_count,
                    "adaptive_confidence": conf.adaptive_confidence
                }
                for conf in confidences
            ],
            "global_heuristics": [
                {
                    "key": kb.key,
                    "value": json.loads(kb.value or "{}")
                }
                for kb in globals_kb
            ]
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def export_as_csv(db: Session) -> str:
        """
        Exports the Knowledge Store as a CSV string of consolidated layout records.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Type", "Identifier", "KeyName", "ValueDetail"])
        
        # 1. Company Layout Profiles
        companies = db.query(CompanyPatterns).all()
        for c in companies:
            writer.writerow(["Company", c.company_name, "layout_name", c.layout_name])
            writer.writerow(["Company", c.company_name, "field_locations", c.field_locations])
            writer.writerow(["Company", c.company_name, "average_confidence", str(c.average_confidence)])
            
        # 2. Vehicle Layout Profiles
        vehicles = db.query(VehiclePatterns).all()
        for v in vehicles:
            writer.writerow(["Vehicle", v.vehicle_type, "layout_name", v.layout_name])
            writer.writerow(["Vehicle", v.vehicle_type, "recurring_structures", v.recurring_structures])

        # 3. Field Confidences
        confidences = db.query(ConfidenceHistory).all()
        for conf in confidences:
            writer.writerow(["Confidence", conf.field_label, "adaptive_confidence", str(conf.adaptive_confidence)])

        return output.getvalue()
