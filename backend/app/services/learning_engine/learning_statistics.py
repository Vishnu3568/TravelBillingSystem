import json
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from app.models.learning import CorrectionHistory, CompanyPatterns, VehiclePatterns, ReviewerStatistics, ConfidenceHistory, KnowledgeBase
from app.services.learning_engine.learning_models import LearningStatisticsSummary

class LearningStatistics:
    @staticmethod
    def get_statistics(db: Session) -> LearningStatisticsSummary:
        """
        Gathers database metrics to summarize system learning progress.
        """
        # 1. Total Corrections
        total_corr = db.query(func.count(CorrectionHistory.id)).scalar() or 0

        # 2. Most Corrected Fields
        field_counts = db.query(
            CorrectionHistory.field_type,
            func.count(CorrectionHistory.id)
        ).group_by(CorrectionHistory.field_type).all()
        most_corrected = {f: c for f, c in field_counts}

        # 3. Top Companies corrected
        comp_counts = db.query(
            CorrectionHistory.company_name,
            func.count(CorrectionHistory.id)
        ).filter(CorrectionHistory.company_name != None).group_by(CorrectionHistory.company_name).limit(5).all()
        top_companies = [{"company": comp, "corrections": cnt} for comp, cnt in comp_counts]

        # 4. Top Vehicles corrected
        veh_counts = db.query(
            CorrectionHistory.vehicle_number,
            func.count(CorrectionHistory.id)
        ).filter(CorrectionHistory.vehicle_number != None).group_by(CorrectionHistory.vehicle_number).limit(5).all()
        top_vehicles = [{"vehicle": veh, "corrections": cnt} for veh, cnt in veh_counts]

        # 5. Reviewer activity
        rev_counts = db.query(
            CorrectionHistory.reviewer,
            func.count(CorrectionHistory.id)
        ).filter(CorrectionHistory.reviewer != None).group_by(CorrectionHistory.reviewer).all()
        reviewer_activity = {rev: cnt for rev, cnt in rev_counts}

        # 6. Confidence Trends (current adaptive confidence levels)
        conf_trends_query = db.query(ConfidenceHistory).all()
        confidence_trends = {c.field_label: c.adaptive_confidence for c in conf_trends_query}

        # 7. Pattern Growth (total templates learned)
        comp_patt_cnt = db.query(func.count(CompanyPatterns.id)).scalar() or 0
        veh_patt_cnt = db.query(func.count(VehiclePatterns.id)).scalar() or 0
        pattern_growth = comp_patt_cnt + veh_patt_cnt

        # 8. Knowledge Base Size
        kb_entry = db.query(KnowledgeBase).filter(KnowledgeBase.key == "spatial_relationships").first()
        kb_size = 0
        if kb_entry and kb_entry.value:
            try:
                patterns = json.loads(kb_entry.value)
                kb_size = len(patterns)
            except Exception:
                kb_size = 0

        # 9. Learning Accuracy
        # Total correct predictions / total predictions
        total_correct = db.query(func.sum(ConfidenceHistory.correct_predictions_count)).scalar() or 0
        total_corrected = db.query(func.sum(ConfidenceHistory.corrected_predictions_count)).scalar() or 0
        total_preds = total_correct + total_corrected
        accuracy = (total_correct / total_preds) if total_preds > 0 else 1.0

        return LearningStatisticsSummary(
            total_corrections=total_corr,
            learning_accuracy=round(accuracy, 4),
            most_corrected_fields=most_corrected,
            top_companies=top_companies,
            top_vehicles=top_vehicles,
            reviewer_activity=reviewer_activity,
            confidence_trends=confidence_trends,
            pattern_growth=pattern_growth,
            knowledge_base_size=kb_size
        )
