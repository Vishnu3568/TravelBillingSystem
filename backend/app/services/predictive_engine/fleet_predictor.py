from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.models.bill import Bill

class FleetPredictor:
    @staticmethod
    def get_fleet_utilization(db: Session) -> float:
        """
        Estimates what percentage of vehicles are actively running trips.
        """
        # Active vehicle is one with trips in the last 15 days
        fifteen_days_ago = datetime.utcnow() - timedelta(days=15)
        
        total_unique = db.query(func.count(func.distinct(Bill.vehicle_name))).scalar() or 0
        active_unique = db.query(func.count(func.distinct(Bill.vehicle_name))).filter(
            Bill.bill_date >= fifteen_days_ago
        ).scalar() or 0

        if total_unique == 0:
            return 0.85 # Default fallback demo utilization
            
        return round(float(active_unique) / total_unique, 2)

    @staticmethod
    def get_inactive_vehicles(db: Session) -> List[str]:
        """
        Lists vehicles that haven't logged any trips in the last 30 days.
        """
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Get all vehicles
        all_vehs = {r[0] for r in db.query(Bill.vehicle_name).distinct().all() if r[0]}
        # Get active vehicles
        active_vehs = {r[0] for r in db.query(Bill.vehicle_name).filter(
            Bill.bill_date >= thirty_days_ago
        ).distinct().all() if r[0]}

        return list(all_vehs - active_vehs)
