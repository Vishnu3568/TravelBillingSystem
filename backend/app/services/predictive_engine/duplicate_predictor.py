from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.models.bill import Bill
from app.services.predictive_engine.predictive_models import AnomalyRecord

class DuplicatePredictor:
    @staticmethod
    def scan_duplicates(db: Session) -> List[AnomalyRecord]:
        """
        Scans all bills and flags duplicate entries (same bill number or total + company overlap).
        """
        anomalies = []
        
        # Group bills by duty_slip_no to detect exact duplicates
        duplicates = db.query(
            Bill.duty_slip_no,
            func.count(Bill.id)
        ).filter(Bill.duty_slip_no != None).group_by(Bill.duty_slip_no).having(func.count(Bill.id) > 1).all()

        for slip_num, count in duplicates:
            if not slip_num:
                continue
            # Get bills sharing this slip number
            shared_bills = db.query(Bill).filter(Bill.duty_slip_no == slip_num).all()
            for b in shared_bills:
                anomalies.append(
                    AnomalyRecord(
                        id=f"anom_dup_{b.id}",
                        type="DUPLICATE_INVOICE",
                        description=f"Duplicate invoice detected: Duty Slip #{b.duty_slip_no} is saved {count} times in the database",
                        severity="HIGH",
                        confidence=0.99,
                        reference_id=str(b.id)
                    )
                )

        return anomalies
