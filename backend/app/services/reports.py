from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, date, timedelta
from typing import List
from app.models.bill import Bill
from app.models.company import Company
from app.models.vehicle import Vehicle
from app.schemas.report import ReportSummaryResponse, TopEntityResponse

class ReportService:
    @staticmethod
    def get_summary(db: Session) -> ReportSummaryResponse:
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        tomorrow_start = today_start + timedelta(days=1)
        
        month_start = datetime(today.year, today.month, 1)
        if today.month == 12:
            next_month_start = datetime(today.year + 1, 1, 1)
        else:
            next_month_start = datetime(today.year, today.month + 1, 1)

        # 1. Today's stats
        today_stats = db.query(
            func.count(Bill.id),
            func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0)
        ).filter(Bill.bill_date >= today_start, Bill.bill_date < tomorrow_start).first()

        # 2. Monthly stats
        month_stats = db.query(
            func.count(Bill.id),
            func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0)
        ).filter(Bill.bill_date >= month_start, Bill.bill_date < next_month_start).first()

        # 3. Global counts
        total_bills = db.query(func.count(Bill.id)).scalar() or 0
        total_companies = db.query(func.count(Company.id)).scalar() or 0
        total_vehicles = db.query(func.count(Vehicle.id)).scalar() or 0

        return ReportSummaryResponse(
            todayBillsCount=today_stats[0] or 0,
            todayRevenue=float(today_stats[1] or 0.0),
            monthlyBillsCount=month_stats[0] or 0,
            monthlyRevenue=float(month_stats[1] or 0.0),
            totalBillsCount=total_bills,
            totalCompanies=total_companies,
            totalVehicles=total_vehicles
        )

    @staticmethod
    def get_top_companies(db: Session) -> List[TopEntityResponse]:
        results = db.query(
            Bill.company_name.label("name"),
            func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0).label("revenue")
        ).group_by(Bill.company_name).order_by(func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0).desc()).limit(5).all()

        return [TopEntityResponse(name=r.name or "Unknown", revenue=float(r.revenue)) for r in results]

    @staticmethod
    def get_top_vehicles(db: Session) -> List[TopEntityResponse]:
        results = db.query(
            Bill.vehicle_name.label("name"),
            func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0).label("revenue")
        ).group_by(Bill.vehicle_name).order_by(func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0).desc()).limit(5).all()

        return [TopEntityResponse(name=r.name or "Unknown", revenue=float(r.revenue)) for r in results]
