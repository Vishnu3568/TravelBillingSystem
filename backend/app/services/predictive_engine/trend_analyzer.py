from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.models.bill import Bill

class TrendAnalyzer:
    @staticmethod
    def analyze_growth_trends(db: Session) -> Dict[str, Any]:
        """
        Groups bills by company to detect which ones are growing in billing volume
        versus which ones are declining.
        """
        # Fetch current month and last month bill totals per company
        now = datetime.utcnow()
        first_of_this_month = datetime(now.year, now.month, 1)
        first_of_last_month = (first_of_this_month - timedelta(days=5)).replace(day=1)

        this_month_totals = db.query(
            Bill.company_name,
            func.sum(Bill.grand_total)
        ).filter(Bill.bill_date >= first_of_this_month).group_by(Bill.company_name).all()

        last_month_totals = db.query(
            Bill.company_name,
            func.sum(Bill.grand_total)
        ).filter(
            Bill.bill_date >= first_of_last_month,
            Bill.bill_date < first_of_this_month
        ).group_by(Bill.company_name).all()

        tm_dict = {name: val or 0.0 for name, val in this_month_totals if name}
        lm_dict = {name: val or 0.0 for name, val in last_month_totals if name}

        growing = []
        declining = []

        # Find growth/declines
        all_companies = set(tm_dict.keys()).union(lm_dict.keys())
        for c in all_companies:
            prev = lm_dict.get(c, 0.0)
            curr = tm_dict.get(c, 0.0)
            
            if prev == 0:
                if curr > 0:
                    growing.append(c)
            else:
                pct = (curr - prev) / prev
                if pct > 0.05:
                    growing.append(c)
                elif pct < -0.05:
                    declining.append(c)

        return {
            "growing_companies": growing,
            "declining_companies": declining
        }
