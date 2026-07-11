import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.learning import ConfidenceHistory

logger = logging.getLogger("confidence_learning")

class ConfidenceLearning:
    @staticmethod
    def get_or_create_profile(db: Session, field_label: str) -> ConfidenceHistory:
        """
        Retrieves the ConfidenceHistory profile for a given field label, or creates it.
        """
        profile = db.query(ConfidenceHistory).filter(ConfidenceHistory.field_label == field_label).first()
        if not profile:
            profile = ConfidenceHistory(
                field_label=field_label,
                correct_predictions_count=0,
                corrected_predictions_count=0,
                adaptive_confidence=1.0,
                updated_at=datetime.utcnow()
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    @staticmethod
    def record_prediction_result(db: Session, field_label: str, was_corrected: bool) -> ConfidenceHistory:
        """
        Tracks the success or failure of predictions for a given label and adapts the confidence accordingly.
        - Boosts confidence if consistently correct.
        - Penalizes confidence if repeatedly corrected.
        """
        profile = ConfidenceLearning.get_or_create_profile(db, field_label)
        
        if was_corrected:
            profile.corrected_predictions_count += 1
            # Penalty formula: reduce confidence by 5% per correction, min 0.3
            penalty = 0.05 * profile.corrected_predictions_count
            profile.adaptive_confidence = max(0.3, min(1.0, 1.0 - penalty))
        else:
            profile.correct_predictions_count += 1
            # Reward formula: increase confidence by 0.2% per correct count, max 1.0
            reward = 0.002 * profile.correct_predictions_count
            # Apply adaptive calculation relative to correction penalty
            penalty = 0.05 * profile.corrected_predictions_count
            profile.adaptive_confidence = max(0.3, min(1.0, 1.0 - penalty + reward))
            
        profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(profile)
        logger.info(f"Confidence updated for '{field_label}': was_corrected={was_corrected}, adaptive_conf={profile.adaptive_confidence:.4f}")
        return profile
