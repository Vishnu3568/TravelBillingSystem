import json
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.models.bill import Bill
from app.models.learning import CorrectionHistory
from app.services.predictive_engine.predictive_models import AnomalyRecord

class AnomalyDetector:
    @staticmethod
    def detect_anomalies(db: Session) -> List[AnomalyRecord]:
        """
        Runs heuristics over active bills to flag outliers and suspicious trends.
        """
        anomalies = []
        bills = db.query(Bill).all()
        
        # Calculate general average amount
        avg_amount = db.query(func.avg(Bill.grand_total)).scalar() or 5000.0

        for b in bills:
            # 1. Unusual bill amount (5x standard average amount)
            if b.grand_total and b.grand_total > (avg_amount * 5):
                anomalies.append(
                    AnomalyRecord(
                        id=f"anom_amt_{b.id}",
                        type="UNUSUAL_AMOUNT",
                        description=f"Bill #{b.bill_number} has an unusually high total of ₹{b.grand_total} (avg: ₹{avg_amount:.0f})",
                        severity="HIGH",
                        confidence=0.95,
                        reference_id=str(b.id)
                    )
                )

            # 2. Impossible Travel Duration (average speed > 120 km/h)
            if b.total_kms and b.total_hours and b.total_hours > 0:
                speed = b.total_kms / b.total_hours
                if speed > 120.0:
                    anomalies.append(
                        AnomalyRecord(
                            id=f"anom_spd_{b.id}",
                            type="IMPOSSIBLE_DURATION",
                            description=f"Bill #{b.bill_number} reports average travel speed of {speed:.1f} km/h ({b.total_kms} km in {b.total_hours} hrs)",
                            severity="HIGH",
                            confidence=0.99,
                            reference_id=str(b.id)
                        )
                    )

            # 3. Abnormal Toll Charges (> 50% of the total amount)
            # Parse dynamic toll if present
            toll_val = 0.0
            if b.dynamic_charges:
                try:
                    chg_dict = json.loads(b.dynamic_charges)
                    for k, v in chg_dict.items():
                        if "toll" in k.lower():
                            toll_val = float(v)
                except Exception:
                    pass

            if toll_val > 0 and b.grand_total and (toll_val / b.grand_total) > 0.5:
                anomalies.append(
                    AnomalyRecord(
                        id=f"anom_toll_{b.id}",
                        type="ABNORMAL_CHARGES",
                        description=f"Bill #{b.bill_number} has abnormally high toll charges of ₹{toll_val} representing over 50% of the total bill",
                        severity="MEDIUM",
                        confidence=0.90,
                        reference_id=str(b.id)
                    )
                )

            # 4. Repeated Reviewer Edits
            corrections_cnt = db.query(func.count(CorrectionHistory.id)).filter(
                CorrectionHistory.bill_number == b.bill_number
            ).scalar() or 0
            
            if corrections_cnt >= 3:
                anomalies.append(
                    AnomalyRecord(
                        id=f"anom_edits_{b.id}",
                        type="REPEATED_EDITS",
                        description=f"Bill #{b.bill_number} has {corrections_cnt} manual reviewer edits, indicating parsing volatility",
                        severity="MEDIUM",
                        confidence=0.95,
                        reference_id=str(b.id)
                    )
                )

        return anomalies
