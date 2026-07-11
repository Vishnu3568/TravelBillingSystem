from sqlalchemy.orm import Session
from app.models.learning import CompanyPatterns, VehiclePatterns
from app.services.predictive_engine.predictive_models import SmartRecommendations
from app.services.predictive_engine.pricing_recommender import PricingRecommender

class RecommendationEngine:
    @staticmethod
    def get_smart_recommendations(db: Session, company_name: str = None) -> SmartRecommendations:
        """
        Assembles layout template configurations, pricing rates, and validation options.
        """
        preferred_comp = "Standard Layout A"
        preferred_veh = "Toyota Crysta SUV template"
        
        # Pull template preferences if company_name provided
        if company_name:
            comp_profile = db.query(CompanyPatterns).filter(
                CompanyPatterns.company_name == company_name
            ).first()
            if comp_profile and comp_profile.layout_name:
                preferred_comp = comp_profile.layout_name

        # Pricing recommendations
        pricing_rate = PricingRecommender.get_suggested_rate(db, company_name)

        return SmartRecommendations(
            preferred_company_template=preferred_comp,
            preferred_vehicle_template=preferred_veh,
            suggested_pricing_per_km=pricing_rate,
            likely_fields=["companyName", "billNumber", "dutySlipNo", "totalAmount", "vehicleNumber"]
        )
