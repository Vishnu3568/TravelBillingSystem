from sqlalchemy.orm import Session
from app.services.predictive_engine.predictive_models import ExtractionPrediction

class ConfidencePredictor:
    @staticmethod
    def predict_extraction_confidence(db: Session, company_name: str = None) -> ExtractionPrediction:
        """
        Uses historical review statistics to estimate accuracy, validation scores,
        and manual review triggers for upcoming imports.
        """
        # Default starting values
        success_prob = 0.94
        review_likelihood = 0.10
        expected_val_score = 0.97
        expected_conf = 0.93

        # We can trace company patterns confidence
        from app.models.learning import CompanyPatterns
        if company_name:
            pat = db.query(CompanyPatterns).filter(CompanyPatterns.company_name == company_name).first()
            if pat and pat.average_confidence:
                expected_conf = pat.average_confidence
                success_prob = pat.average_confidence + 0.02
                review_likelihood = max(0.01, 1.0 - pat.average_confidence)
                expected_val_score = pat.average_confidence + 0.04

        return ExtractionPrediction(
            extraction_success_probability=round(min(0.99, success_prob), 2),
            manual_review_likelihood=round(max(0.01, review_likelihood), 2),
            expected_validation_score=round(min(1.0, expected_val_score), 2),
            expected_confidence=round(expected_conf, 2)
        )
