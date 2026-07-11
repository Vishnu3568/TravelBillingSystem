import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.learning import CorrectionHistory
from app.services.learning_engine.learning_models import CorrectionRecord

logger = logging.getLogger("correction_store")

class CorrectionStore:
    @staticmethod
    def get_max_version(db: Session, field_type: str, company: str, vehicle: str) -> int:
        """
        Retrieves the maximum version number of corrections recorded for a specific field, company, and vehicle.
        """
        query = db.query(func.max(CorrectionHistory.version)).filter(
            CorrectionHistory.field_type == field_type
        )
        if company:
            query = query.filter(CorrectionHistory.company_name == company)
        if vehicle:
            query = query.filter(CorrectionHistory.vehicle_number == vehicle)
            
        result = query.scalar()
        return result if result is not None else 0

    @staticmethod
    def get_correction_count(db: Session, field_type: str, company: str, vehicle: str) -> int:
        """
        Counts existing corrections for a given field/company/vehicle.
        """
        query = db.query(func.count(CorrectionHistory.id)).filter(
            CorrectionHistory.field_type == field_type
        )
        if company:
            query = query.filter(CorrectionHistory.company_name == company)
        if vehicle:
            query = query.filter(CorrectionHistory.vehicle_number == vehicle)
            
        return query.scalar() or 0

    @staticmethod
    def save_correction(db: Session, record: CorrectionRecord) -> CorrectionHistory:
        """
        Saves a new correction record with updated version numbers and counts.
        Never overwrites.
        """
        # Determine next version and count
        max_ver = CorrectionStore.get_max_version(
            db, record.field_type, record.company_name, record.vehicle_number
        )
        corr_cnt = CorrectionStore.get_correction_count(
            db, record.field_type, record.company_name, record.vehicle_number
        )

        db_correction = CorrectionHistory(
            original_value=record.original_value,
            corrected_value=record.corrected_value,
            field_type=record.field_type,
            table_number=record.table_number,
            row_index=record.row_index,
            column_index=record.column_index,
            company_name=record.company_name,
            vehicle_number=record.vehicle_number,
            bill_number=record.bill_number,
            reviewer=record.reviewer,
            timestamp=datetime.utcnow(),
            reason=record.reason,
            ai_confidence=record.ai_confidence,
            validation_status=record.validation_status,
            correction_count=corr_cnt + 1,
            version=max_ver + 1
        )
        db.add(db_correction)
        db.commit()
        db.refresh(db_correction)
        logger.info(f"Correction stored: Field '{record.field_type}' ({record.original_value} -> {record.corrected_value}) ver={max_ver+1}")
        return db_correction
