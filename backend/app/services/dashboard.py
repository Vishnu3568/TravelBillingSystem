from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
from typing import List
from app.models.bill import Bill
from app.models.company import Company
from app.models.vehicle import Vehicle
from app.models.payment import Payment
from app.models.audit_log import AuditLog
from app.schemas.dashboard import (
    OwnerDashboardResponse, DashboardStats, RecentBill, UserActivity, RevenueTrend
)

class DashboardService:
    @staticmethod
    def get_owner_dashboard(db: Session) -> OwnerDashboardResponse:
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        tomorrow_start = today_start + timedelta(days=1)
        
        month_start = datetime(today.year, today.month, 1)
        if today.month == 12:
            next_month_start = datetime(today.year + 1, 1, 1)
        else:
            next_month_start = datetime(today.year, today.month + 1, 1)

        # 1. Total Bill & Payment amounts
        total_bill_amount = db.query(
            func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0)
        ).scalar() or 0.0

        total_payment_amount = db.query(
            func.coalesce(func.sum(Payment.amount), 0.0)
        ).scalar() or 0.0

        pending_payments = max(0.0, total_bill_amount - total_payment_amount)

        # Today & monthly revenue/counts
        today_count = db.query(func.count(Bill.id)).filter(Bill.bill_date >= today_start, Bill.bill_date < tomorrow_start).scalar() or 0
        today_revenue = db.query(func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0)).filter(Bill.bill_date >= today_start, Bill.bill_date < tomorrow_start).scalar() or 0.0
        month_revenue = db.query(func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0)).filter(Bill.bill_date >= month_start, Bill.bill_date < next_month_start).scalar() or 0.0

        company_count = db.query(func.count(Company.id)).scalar() or 0
        vehicle_count = db.query(func.count(Vehicle.id)).scalar() or 0

        stats = DashboardStats(
            todayBillsCount=today_count,
            todayRevenue=float(today_revenue),
            monthlyRevenue=float(month_revenue),
            pendingPayments=float(pending_payments),
            totalCompanies=company_count,
            totalVehicles=vehicle_count
        )

        # 2. Revenue Trend (Last 6 months)
        # In Python: generate last 6 months (offsets 0 to 5)
        revenue_trend = []
        months_to_calc = []
        for i in range(5, -1, -1):
            # Calculate YearMonth offset
            y = today.year
            m = today.month - i
            while m <= 0:
                m += 12
                y -= 1
            months_to_calc.append((y, m))

        for y, m in months_to_calc:
            m_start = datetime(y, m, 1)
            if m == 12:
                m_next = datetime(y + 1, 1, 1)
            else:
                m_next = datetime(y, m + 1, 1)
                
            rev = db.query(
                func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0)
            ).filter(Bill.bill_date >= m_start, Bill.bill_date < m_next).scalar() or 0.0
            
            month_name = m_start.strftime("%b") # Short name like Jan, Feb
            revenue_trend.append(RevenueTrend(month=month_name, revenue=float(rev)))

        # 3. Recent Bills (top 5 by bill_date desc)
        recent_bills_models = db.query(Bill).order_by(Bill.bill_date.desc()).limit(5).all()
        recent_bills = []
        for b in recent_bills_models:
            amount = float(b.grand_total if b.grand_total is not None else (b.amount or 0.0))
            
            # Paid amount for this bill
            paid_amount = db.query(
                func.coalesce(func.sum(Payment.amount), 0.0)
            ).filter(Payment.bill_id == b.id).scalar() or 0.0
            
            pending_amount = max(0.0, amount - paid_amount)
            
            # Status resolution
            if pending_amount <= 0:
                status = "Paid"
            elif b.bill_date and b.bill_date.date() < today:
                status = "Overdue"
            else:
                status = "Pending"
                
            bill_date_str = b.bill_date.strftime("%Y-%m-%d") if b.bill_date else None
            
            # Resolve vehicle reg
            reg_num = b.vehicle_name
            if not reg_num and b.vehicle:
                reg_num = b.vehicle.registration_number

            # Resolve company name
            comp_name = b.company_name
            if not comp_name and b.company:
                comp_name = b.company.name

            recent_bills.append(RecentBill(
                id=b.id,
                billNumber=b.bill_number or f"BILL-{b.id}",
                companyName=comp_name or "Unassigned",
                vehicleRegistrationNumber=reg_num or "Unassigned",
                amount=amount,
                paidAmount=float(paid_amount),
                pendingAmount=float(pending_amount),
                status=status,
                billDate=bill_date_str
            ))

        # 4. Recent User Activity (top 5 audit logs desc)
        activity_models = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(5).all()
        activity = []
        for a in activity_models:
            action_time_str = a.created_at.strftime("%Y-%m-%dT%H:%M:%S") if a.created_at else None
            activity.append(UserActivity(
                id=a.id,
                action=a.action or "Activity recorded",
                performedBy=a.username or "System",
                actionTime=action_time_str
            ))

        return OwnerDashboardResponse(
            stats=stats,
            revenueTrend=revenue_trend,
            recentBills=recent_bills,
            recentUsersActivity=activity
        )
