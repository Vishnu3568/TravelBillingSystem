import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.learning import VehiclePatterns
from app.services.field_labeling.field_models import LabeledDocument

logger = logging.getLogger("vehicle_learning")

class VehicleLearning:
    @staticmethod
    def get_or_create_profile(db: Session, vehicle_type: str) -> VehiclePatterns:
        """
        Retrieves the VehiclePatterns profile for a vehicle type, or creates a new one.
        """
        if not vehicle_type:
            vehicle_type = "Standard"
        profile = db.query(VehiclePatterns).filter(VehiclePatterns.vehicle_type == vehicle_type).first()
        if not profile:
            profile = VehiclePatterns(
                vehicle_type=vehicle_type,
                layout_name=f"Layout {vehicle_type.replace(' ', '')[:8].upper()}",
                recurring_structures="{}",
                updated_at=datetime.utcnow()
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    @staticmethod
    def update_profile_from_document(db: Session, vehicle_type: str, labeled_doc: LabeledDocument) -> VehiclePatterns:
        """
        Learns table layouts (e.g., cell column spans, header count) associated with the vehicle type.
        """
        profile = VehicleLearning.get_or_create_profile(db, vehicle_type)
        
        # Determine unique columns/table sizes present in labeled document
        tables = {}
        for el in labeled_doc.elements:
            coords = el.coordinates or {}
            t_num = coords.get("table_number")
            if t_num is not None:
                if t_num not in tables:
                    tables[t_num] = {"max_cols": 0, "max_rows": 0}
                col = coords.get("column_index", 0)
                row = coords.get("row_index", 0)
                tables[t_num]["max_cols"] = max(tables[t_num]["max_cols"], col + 1)
                tables[t_num]["max_rows"] = max(tables[t_num]["max_rows"], row + 1)
                
        try:
            structures = json.loads(profile.recurring_structures or "{}")
        except Exception:
            structures = {}
            
        # Record structural columns
        for t_num, size in tables.items():
            key = f"table_{t_num}"
            structures[key] = {
                "columns": size["max_cols"],
                "rows": size["max_rows"],
                "elements_labeled": len([el for el in labeled_doc.elements if el.coordinates.get("table_number") == t_num])
            }
            
        profile.recurring_structures = json.dumps(structures)
        profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(profile)
        logger.info(f"Vehicle Profile updated for type '{vehicle_type}' with structures: {structures}")
        return profile
