from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models.bill import Bill
from app.services.predictive_engine.predictive_models import RevenueForecast

class ForecastEngine:
    @staticmethod
    def calculate_revenue_forecast(db: Session) -> RevenueForecast:
        """
        Uses historical bills to calculate daily, weekly, monthly,
        quarterly, and yearly revenue forecasts, factoring in seasonality.
        """
        # Fetch total billing in the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_total = db.query(func.sum(Bill.grand_total)).filter(
            Bill.bill_date >= thirty_days_ago
        ).scalar() or 0.0

        # Fetch global average monthly revenue
        total_revenue = db.query(func.sum(Bill.grand_total)).scalar() or 0.0
        min_date = db.query(func.min(Bill.bill_date)).scalar()
        
        days_span = 30
        if min_date:
            days_span = (datetime.utcnow() - min_date).days
            if days_span < 1:
                days_span = 1

        avg_daily = total_revenue / days_span
        
        # Apply seasonality based on current month (e.g. Q3 and winter holiday seasonality multipliers)
        curr_month = datetime.utcnow().month
        seasonality = 1.0
        if curr_month in (10, 11, 12): # Peak holiday/travel months
            seasonality = 1.25
        elif curr_month in (5, 6): # Summer dip
            seasonality = 0.85

        # If we have recent data, blend it with the historical daily average
        blended_daily = (avg_daily * 0.4) + ((recent_total / 30.0) * 0.6)
        if blended_daily <= 0:
            blended_daily = 5000.0 # Default starting business baseline for demo

        return RevenueForecast(
            daily=round(blended_daily * seasonality, 2),
            weekly=round(blended_daily * 7 * seasonality, 2),
            monthly=round(blended_daily * 30 * seasonality, 2),
            quarterly=round(blended_daily * 90 * seasonality, 2),
            yearly=round(blended_daily * 365 * seasonality, 2),
            seasonality_multiplier=seasonality
        )
