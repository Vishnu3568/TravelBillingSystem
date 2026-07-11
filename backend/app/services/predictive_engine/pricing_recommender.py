from sqlalchemy.orm import Session
from app.models.bill import Bill

class PricingRecommender:
    @staticmethod
    def get_suggested_rate(db: Session, company_name: str = None, vehicle_type: str = None) -> float:
        """
        Determines standard billing rate per kilometer based on historical data.
        """
        # Default fallback rate
        default_rate = 18.0
        
        query = db.query(Bill)
        if company_name:
            query = query.filter(Bill.company_name == company_name)
        if vehicle_type:
            query = query.filter(Bill.vehicle_type == vehicle_type)
            
        bills = query.all()
        rates = []
        for b in bills:
            # Estimate rate = grand_total / total_kms
            if b.total_kms and b.total_kms > 0 and b.grand_total:
                rates.append(b.grand_total / b.total_kms)
                
        if rates:
            return round(sum(rates) / len(rates), 2)
            
        # Vehicle baseline defaults
        if vehicle_type:
            vt = vehicle_type.lower()
            if "crysta" in vt or "suv" in vt:
                return 22.50
            if "sedan" in vt:
                return 16.50
                
        return default_rate
