from sqlalchemy.orm import Session
from typing import List
from app.models.bill import Bill
from app.services.predictive_engine.predictive_models import PaymentPrediction

class PaymentPredictor:
    @staticmethod
    def predict_payments(db: Session) -> List[PaymentPrediction]:
        """
        Projects payment risk and collections timeline per company.
        """
        # Fetch distinct companies
        companies = db.query(Bill.company_name).distinct().all()
        predictions = []

        for (comp_name,) in companies:
            if not comp_name:
                continue
            
            # Simple simulation heuristic:
            # If average bill amount is high, increase late payment risk.
            # (In production, this queries actual payment settlement dates)
            bills = db.query(Bill).filter(Bill.company_name == comp_name).all()
            total_val = sum(b.grand_total for b in bills if b.grand_total)
            avg_val = total_val / len(bills) if bills else 0.0

            prob = 0.15
            days = 30
            risk = "LOW"

            if avg_val > 100000.0:
                prob = 0.55
                days = 45
                risk = "HIGH"
            elif avg_val > 40000.0:
                prob = 0.35
                days = 38
                risk = "MEDIUM"

            predictions.append(
                PaymentPrediction(
                    company_name=comp_name,
                    late_payment_probability=prob,
                    expected_collection_days=days,
                    risk_level=risk
                )
            )

        return predictions
