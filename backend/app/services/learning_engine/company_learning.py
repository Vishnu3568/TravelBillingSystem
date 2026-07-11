import json
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.learning import CompanyPatterns
from app.services.field_labeling.field_models import LabeledDocument
from app.services.learning_engine.learning_models import CompanyLayoutProfile

logger = logging.getLogger("company_learning")

class CompanyLearning:
    @staticmethod
    def get_or_create_profile(db: Session, company_name: str) -> CompanyPatterns:
        """
        Retrieves the CompanyPatterns profile for the given company name, or creates a new default one.
        """
        if not company_name:
            company_name = "Default Company"
        profile = db.query(CompanyPatterns).filter(CompanyPatterns.company_name == company_name).first()
        if not profile:
            profile = CompanyPatterns(
                company_name=company_name,
                layout_name=f"Layout {company_name.replace(' ', '')[:8].upper()}",
                header_positions="{}",
                field_locations="{}",
                preferred_labels="[]",
                frequently_corrected_fields="{}",
                average_confidence=1.0,
                extraction_success_rate=1.0,
                updated_at=datetime.utcnow()
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    @staticmethod
    def update_profile_from_document(db: Session, company_name: str, labeled_doc: LabeledDocument, corrected_fields: list = None) -> CompanyPatterns:
        """
        Extracts structural locations, preferred labels, confidences, and coordinates
        from a processed document and updates the company profile.
        """
        profile = CompanyLearning.get_or_create_profile(db, company_name)
        
        # 1. Update average confidence
        total_conf = sum(el.confidence for el in labeled_doc.elements)
        el_count = len(labeled_doc.elements)
        doc_avg_conf = (total_conf / el_count) if el_count > 0 else 1.0
        
        # Calculate moving average
        profile.average_confidence = (profile.average_confidence * 0.7) + (doc_avg_conf * 0.3)
        
        # 2. Update field locations mapping (JSON dictionary: { label: coordinates })
        try:
            locations = json.loads(profile.field_locations or "{}")
        except Exception:
            locations = {}
            
        for el in labeled_doc.elements:
            if el.coordinates:
                locations[el.label] = el.coordinates
        profile.field_locations = json.dumps(locations)
        
        # 3. Update preferred labels (headers or field title texts)
        try:
            preferred = json.loads(profile.preferred_labels or "[]")
        except Exception:
            preferred = []
            
        for el in labeled_doc.elements:
            # If the text is a potential field label name (e.g. "Duty Slip No:")
            if el.text and el.text.endswith(":") and len(el.text) < 50:
                if el.text not in preferred:
                    preferred.append(el.text)
        profile.preferred_labels = json.dumps(preferred)
        
        # 4. Increment frequently corrected fields
        if corrected_fields:
            try:
                freq_corr = json.loads(profile.frequently_corrected_fields or "{}")
            except Exception:
                freq_corr = {}
            for f in corrected_fields:
                freq_corr[f] = freq_corr.get(f, 0) + 1
            profile.frequently_corrected_fields = json.dumps(freq_corr)
            
        profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(profile)
        logger.info(f"Company Profile updated for '{company_name}' (conf={profile.average_confidence:.2f})")
        return profile
