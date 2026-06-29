import json
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.models.bill import Bill
from app.models.company import Company
from app.models.vehicle import Vehicle
from app.services.gemini import gemini_service
from app.schemas.dashboard import DashboardStatsDTO, StatEntry

class AnalyticsService:
    @staticmethod
    def get_ai_insights(db: Session) -> Dict[str, Any]:
        stats_dto = AnalyticsService._get_dashboard_stats(db)
        return gemini_service.generate_insights(stats_dto.model_dump())

    @staticmethod
    def _get_dashboard_stats(db: Session) -> DashboardStatsDTO:
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # 1. Total revenue & bill count
        total_revenue = db.query(
            func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0)
        ).scalar() or 0.0
        bill_count = db.query(func.count(Bill.id)).scalar() or 0

        # 2. Company stats
        company_query = db.query(
            Bill.company_name.label("name"),
            func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0).label("amount"),
            func.count(Bill.id).label("count")
        ).group_by(Bill.company_name).order_by(func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0).desc()).all()
        
        company_stats = [StatEntry(name=q.name or "Unknown", amount=float(q.amount), count=q.count) for q in company_query]

        # 3. Vehicle usage stats (by vehicle type)
        vehicle_query = db.query(
            Bill.vehicle_type.label("name"),
            func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0).label("amount"), # Hibernate projection maps amount too
            func.count(Bill.id).label("count")
        ).group_by(Bill.vehicle_type).order_by(func.count(Bill.id).desc()).all()
        
        vehicle_stats = [StatEntry(name=q.name or "Unknown", amount=float(q.amount), count=q.count) for q in vehicle_query]

        # 4. Monthly revenue stats
        # MySQL MONTHNAME() and MONTH() equivalent in SQLAlchemy
        # For cross-platform compatibility, we can query dates and format them in Python, or use extract()
        # Java does: function('MONTHNAME', b.billDate) and function('MONTH', b.billDate)
        monthly_query = db.query(
            func.min(Bill.bill_date).label("date_val"),
            func.coalesce(func.sum(func.coalesce(Bill.grand_total, Bill.amount)), 0.0).label("amount"),
            func.count(Bill.id).label("count")
        ).filter(Bill.bill_date >= six_months_ago).group_by(
            extract('year', Bill.bill_date),
            extract('month', Bill.bill_date)
        ).order_by(extract('year', Bill.bill_date), extract('month', Bill.bill_date)).all()

        monthly_revenue = []
        for q in monthly_query:
            month_name = q.date_val.strftime("%B") if q.date_val else "Unknown"
            monthly_revenue.append(StatEntry(name=month_name, amount=float(q.amount), count=q.count))

        # 5. Charges breakdown
        charges = db.query(
            func.coalesce(func.sum(Bill.driver_bata), 0.0).label("bata"),
            func.coalesce(func.sum(Bill.toll), 0.0).label("toll"),
            func.coalesce(func.sum(Bill.parking), 0.0).label("parking"),
            func.coalesce(func.sum(Bill.night_charges), 0.0).label("night"),
            func.coalesce(func.sum(Bill.other_charges), 0.0).label("other")
        ).first()

        charge_stats = [
            StatEntry(name="Driver Bata", amount=float(charges.bata or 0.0), count=None),
            StatEntry(name="Toll", amount=float(charges.toll or 0.0), count=None),
            StatEntry(name="Parking", amount=float(charges.parking or 0.0), count=None),
            StatEntry(name="Night Charges", amount=float(charges.night or 0.0), count=None),
            StatEntry(name="Other", amount=float(charges.other or 0.0), count=None)
        ]

        return DashboardStatsDTO(
            totalRevenue=float(total_revenue),
            billCount=bill_count,
            companyStats=company_stats,
            vehicleStats=vehicle_stats,
            monthlyRevenue=monthly_revenue,
            chargeStats=charge_stats
        )

    @staticmethod
    def ask_assistant(db: Session, query: str, bill_id: Optional[int], username: str) -> Dict[str, Any]:
        session_id = f"{username}_bill_{bill_id}" if bill_id else f"{username}_global"
        context_type = "BILL" if bill_id else "GLOBAL"

        payload = {
            "userQuery": query,
            "sessionId": session_id,
            "contextType": context_type
        }

        if bill_id:
            bill = db.query(Bill).filter(Bill.id == bill_id).first()
            if bill:
                charges_list = []
                if bill.dynamic_charges:
                    try:
                        charges_list = json.loads(bill.dynamic_charges)
                    except Exception:
                        pass
                
                payload["billData"] = {
                    "billNumber": bill.bill_number,
                    "companyName": bill.company_name,
                    "totalKm": bill.total_kms,
                    "totalHours": bill.total_hours,
                    "totalAmount": bill.grand_total,
                    "charges": charges_list
                }
            else:
                payload["contextType"] = "GLOBAL"

        if payload["contextType"] == "GLOBAL":
            stats = AnalyticsService._get_dashboard_stats(db)
            
            # Fetch top 5 recent bills
            recent_bills_query = db.query(Bill).order_by(Bill.created_at.desc()).limit(5).all()
            recent_bills = [{
                "number": b.bill_number,
                "company": b.company_name,
                "total": b.grand_total
            } for b in recent_bills_query]

            company_count = db.query(func.count(Company.id)).scalar() or 0
            vehicle_count = db.query(func.count(Vehicle.id)).scalar() or 0

            payload["aggregatedData"] = {
                "totalRevenue": stats.totalRevenue,
                "companyCount": company_count,
                "vehicleCount": vehicle_count,
                "topCompanies": [{"name": c.name, "revenue": c.amount} for c in stats.companyStats[:5]],
                "recentBills": recent_bills
            }

        return gemini_service.ask_assistant(payload)

    @staticmethod
    def generate_suggestions(db: Session, current_bill: Dict[str, Any]) -> Dict[str, Any]:
        company_name = current_bill.get("companyName")
        vehicle_type = current_bill.get("vehicleType")

        if not company_name or not vehicle_type:
            return {"suggestions": []}

        # Fetch last 10 bills matching company name & vehicle type
        historical_bills = db.query(Bill).filter(
            Bill.company_name == company_name,
            Bill.vehicle_type == vehicle_type
        ).order_by(Bill.created_at.desc()).limit(10).all()

        if not historical_bills:
            return {"suggestions": []}

        # Calculate averages
        avg_bata = sum(b.driver_bata or 0.0 for b in historical_bills) / len(historical_bills)
        avg_toll = sum(b.toll or 0.0 for b in historical_bills) / len(historical_bills)
        avg_parking = sum(b.parking or 0.0 for b in historical_bills) / len(historical_bills)

        common_charges = []
        if sum(1 for b in historical_bills if (b.driver_bata or 0) > 0) > 5:
            common_charges.append("Driver Bata")
        if sum(1 for b in historical_bills if (b.toll or 0) > 0) > 5:
            common_charges.append("Toll")
        if sum(1 for b in historical_bills if (b.parking or 0) > 0) > 5:
            common_charges.append("Parking")

        recent_similar = [{
            "amount": b.grand_total,
            "kms": b.total_kms,
            "hours": b.total_hours
        } for b in historical_bills[:3]]

        payload = {
            "currentBill": current_bill,
            "historicalPatterns": {
                "averageDriverBata": avg_bata,
                "averageToll": avg_toll,
                "averageParking": avg_parking,
                "commonCharges": common_charges,
                "recentSimilarBills": recent_similar
            }
        }

        return gemini_service.generate_suggestions(payload)
