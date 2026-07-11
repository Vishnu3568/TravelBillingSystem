import json
import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.models.learning import KnowledgeBase
from app.schemas.ai import AiBillResponse
from app.services.field_labeling.field_models import LabeledDocument, LabeledElement
from app.services.learning_engine.correction_store import CorrectionStore
from app.services.learning_engine.learning_models import CorrectionRecord
from app.services.learning_engine.confidence_learning import ConfidenceLearning
from app.services.learning_engine.company_learning import CompanyLearning
from app.services.learning_engine.vehicle_learning import VehicleLearning
from app.services.learning_engine.feedback_processor import FeedbackProcessor
from app.services.learning_engine.pattern_engine import PatternEngine

logger = logging.getLogger("learning_orchestrator")

LABEL_TO_FIELD_MAP = {
    "HEADER_COMPANY": "companyName",
    "HEADER_BILL_NUMBER": "billNumber",
    "HEADER_DATE": "billDate",
    "HEADER_DUTY_SLIP": "dutySlipNo",
    "TRIP_DATE": "tripDate",
    "VEHICLE_NUMBER": "vehicleNumber",
    "VEHICLE_TYPE": "vehicleType",
    "AC_NON_AC": "acNonAc",
    "TOTAL_KMS": "totalKms",
    "TOTAL_HOURS": "totalHours",
    "EXTRA_KM_FORMULA": "extraKms",
    "EXTRA_HOUR_FORMULA": "extraHours",
    "TRIP_TYPE": "tripType",
    "PRICING_TYPE": "pricingType",
    "BASE_PACKAGE": "baseAmount",
    "DRIVER_BATA": "driverBata",
    "PARKING": "parking",
    "TOLL": "toll",
    "NIGHT_CHARGES": "nightCharges",
    "OTHER_CHARGE": "otherCharges",
    "NOTES": "notes",
    "GUEST_NAME": "contactPerson",
    "BOOKED_BY": "bookedBy",
    "MANAGER_NAME": "managerName",
    "TOTAL_AMOUNT": "totalAmount"
}

class LearningOrchestrator:
    @staticmethod
    def process_save(db: Session, bill: AiBillResponse, username: str) -> None:
        """
        Main save processor called when a bill is accepted/saved.
        Compares final fields with AI predicted elements, records corrections,
        adjusts field confidences, extracts spatial relationships, and updates profiles.
        """
        # Parse labeled document
        labeled_doc_raw = bill.labeledDocument
        if not labeled_doc_raw:
            logger.info("No labeledDocument in payload. Skipping learning execution.")
            return

        try:
            labeled_doc = LabeledDocument.model_validate(labeled_doc_raw)
        except Exception as e:
            logger.warning(f"Error parsing labeledDocument metadata: {e}")
            return

        corrected_fields = []
        
        # 1. Compare fields to identify corrections
        for label, field in LABEL_TO_FIELD_MAP.items():
            # Find AI element
            ai_el = next((el for el in labeled_doc.elements if el.label == label), None)
            final_val = getattr(bill, field, None)
            
            # Normalize strings for comparison
            ai_val_clean = str(ai_el.text).strip() if (ai_el and ai_el.text) else ""
            final_val_clean = str(final_val).strip() if final_val is not None else ""
            
            # Skip empty comparisons or placeholders
            if not ai_val_clean and not final_val_clean:
                continue

            was_corrected = False
            # Normalize common placeholder values like '---' or 'null'
            if ai_val_clean.lower() in ("---", "null", "unknown"):
                ai_val_clean = ""
            if final_val_clean.lower() in ("---", "null", "unknown"):
                final_val_clean = ""

            if ai_val_clean != final_val_clean:
                was_corrected = True
                corrected_fields.append(field)
                
                # Save correction record
                record = CorrectionRecord(
                    original_value=ai_val_clean or "None",
                    corrected_value=final_val_clean or "None",
                    field_type=field,
                    table_number=ai_el.coordinates.get("table_number") if ai_el else None,
                    row_index=ai_el.coordinates.get("row_index") if ai_el else None,
                    column_index=ai_el.coordinates.get("column_index") if ai_el else None,
                    company_name=bill.companyName,
                    vehicle_number=bill.vehicleNumber,
                    bill_number=bill.billNumber,
                    reviewer=username,
                    reason="Manual correction during review workspace submit",
                    ai_confidence=ai_el.confidence if ai_el else 0.0,
                    validation_status="EDITED"
                )
                CorrectionStore.save_correction(db, record)
                FeedbackProcessor.process_reviewer_action(db, username, "EDIT")
            
            # Update adaptive confidence
            ConfidenceLearning.record_prediction_result(db, label, was_corrected)

        # 2. Extract and Consolidate spatial relationships
        relations = PatternEngine.extract_spatial_relationships(labeled_doc)
        if relations:
            kb_entry = db.query(KnowledgeBase).filter(KnowledgeBase.key == "spatial_relationships").first()
            if not kb_entry:
                kb_entry = KnowledgeBase(key="spatial_relationships", value="[]")
                db.add(kb_entry)
            
            try:
                existing_patterns = json.loads(kb_entry.value or "[]")
            except Exception:
                existing_patterns = []
                
            consolidated = PatternEngine.consolidate_patterns(existing_patterns, relations)
            kb_entry.value = json.dumps(consolidated)
            db.commit()

        # 3. Update profiles
        if bill.companyName:
            CompanyLearning.update_profile_from_document(db, bill.companyName, labeled_doc, corrected_fields)
        if bill.vehicleType:
            VehicleLearning.update_profile_from_document(db, bill.vehicleType, labeled_doc)

        # 4. Log successful save
        FeedbackProcessor.process_reviewer_action(db, username, "SAVE")
