from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from app.models.bill import Bill
from app.models.company import Company
from app.models.vehicle import Vehicle
from app.models.learning import ReviewerStatistics, CorrectionHistory

class AnalyticsAssistant:
    @staticmethod
    def get_top_customers(db: Session, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Query companies sorted by total revenue billed.
        """
        results = db.query(
            Bill.company_name,
            func.sum(Bill.grand_total).label("total_rev")
        ).filter(Bill.company_name != None).group_by(Bill.company_name).order_by(
            func.sum(Bill.grand_total).desc()
        ).limit(limit).all()
        
        return [{"company": r[0], "total_revenue": r[1] or 0.0} for r in results]

    @staticmethod
    def get_most_used_vehicles(db: Session, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Query vehicles sorted by total count of duty slips.
        """
        results = db.query(
            Bill.vehicle_name,
            func.count(Bill.id).label("trip_count")
        ).filter(Bill.vehicle_name != None).group_by(Bill.vehicle_name).order_by(
            func.count(Bill.id).desc()
        ).limit(limit).all()
        
        return [{"vehicle": r[0], "trips": r[1]} for r in results]

    @staticmethod
    def get_monthly_revenue(db: Session) -> List[Dict[str, Any]]:
        """
        Calculates monthly billing totals.
        """
        # Query: strftime('%Y-%m', bill_date) on SQLite or standard date parts on MySQL
        # Since we use SQLite in tests and MySQL in dev, we can write a database-agnostic query using python-side sorting
        # or standard date aggregations.
        bills = db.query(Bill.bill_date, Bill.grand_total).all()
        monthly = {}
        for b_date, total in bills:
            if b_date:
                month_key = b_date.strftime("%Y-%m")
            else:
                month_key = "Unknown Month"
            monthly[month_key] = monthly.get(month_key, 0.0) + (total or 0.0)
            
        # Return sorted by month
        sorted_months = sorted(monthly.items())
        return [{"month": m, "revenue": rev} for m, rev in sorted_months]

    @staticmethod
    def get_reviewer_stats(db: Session) -> List[Dict[str, Any]]:
        """
        Retrieves action statistics per reviewer.
        """
        stats = db.query(ReviewerStatistics).all()
        return [
            {
                "reviewer": s.reviewer_username,
                "total_reviews": s.total_reviews,
                "total_edits": s.total_edits,
                "total_undos": s.total_undos,
                "total_restores": s.total_restores
            }
            for s in stats
        ]

    @staticmethod
    def get_most_corrected_fields(db: Session, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves which fields are corrected the most.
        """
        results = db.query(
            CorrectionHistory.field_type,
            func.count(CorrectionHistory.id).label("count")
        ).group_by(CorrectionHistory.field_type).order_by(
            func.count(CorrectionHistory.id).desc()
        ).limit(limit).all()
        
        return [{"field": r[0], "corrections": r[1]} for r in results]
