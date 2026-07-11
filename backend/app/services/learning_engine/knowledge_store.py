import json
import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.models.learning import CompanyPatterns, VehiclePatterns, CorrectionHistory, KnowledgeBase, ReviewerStatistics

logger = logging.getLogger("knowledge_store")

class KnowledgeStore:
    @staticmethod
    def get_company_profile(db: Session, company_name: str) -> Dict[str, Any]:
        """
        Retrieves company layout profile parameters.
        """
        profile = db.query(CompanyPatterns).filter(CompanyPatterns.company_name == company_name).first()
        if not profile:
            return {}
        try:
            return {
                "company_name": profile.company_name,
                "layout_name": profile.layout_name,
                "field_locations": json.loads(profile.field_locations or "{}"),
                "preferred_labels": json.loads(profile.preferred_labels or "[]"),
                "average_confidence": profile.average_confidence,
                "extraction_success_rate": profile.extraction_success_rate
            }
        except Exception as e:
            logger.warning(f"Error parsing company profile JSON: {e}")
            return {}

    @staticmethod
    def get_vehicle_profile(db: Session, vehicle_type: str) -> Dict[str, Any]:
        """
        Retrieves vehicle layout profile parameters.
        """
        profile = db.query(VehiclePatterns).filter(VehiclePatterns.vehicle_type == vehicle_type).first()
        if not profile:
            return {}
        try:
            return {
                "vehicle_type": profile.vehicle_type,
                "layout_name": profile.layout_name,
                "recurring_structures": json.loads(profile.recurring_structures or "{}")
            }
        except Exception as e:
            logger.warning(f"Error parsing vehicle profile JSON: {e}")
            return {}

    @staticmethod
    def retrieve_learned_context(db: Session, company_name: str, vehicle_type: str = None) -> str:
        """
        Gathers all learned templates, spatial patterns, and historical corrections
        from the database, and returns a formatted text context block.
        This block is fed directly to the AI labeling prompt.
        """
        context_parts = []
        
        # 1. Company Layout Profiles
        if company_name:
            comp_prof = KnowledgeStore.get_company_profile(db, company_name)
            if comp_prof:
                context_parts.append(f"### Learned Template Layout for Company: {company_name}")
                context_parts.append(f"- Layout Layout Name: {comp_prof.get('layout_name')}")
                context_parts.append(f"- Preferred Header Labels: {', '.join(comp_prof.get('preferred_labels', []))}")
                
                locations = comp_prof.get("field_locations", {})
                if locations:
                    context_parts.append("- Known Field Coordinate Mappings (table index, row index, column index):")
                    for field, coord in locations.items():
                        context_parts.append(f"  * Field '{field}' is usually at Table {coord.get('table_number')}, Row {coord.get('row_index')}, Col {coord.get('column_index')}")

        # 2. Vehicle Column Layout Profiles
        if vehicle_type:
            veh_prof = KnowledgeStore.get_vehicle_profile(db, vehicle_type)
            if veh_prof:
                context_parts.append(f"### Learned Layout for Vehicle Type: {vehicle_type}")
                structures = veh_prof.get("recurring_structures", {})
                if structures:
                    for tbl, struct in structures.items():
                        context_parts.append(f"- {tbl} columns: {struct.get('columns')}, rows: {struct.get('rows')}")

        # 3. Spatial Patterns (from KnowledgeBase)
        spatial_record = db.query(KnowledgeBase).filter(KnowledgeBase.key == "spatial_relationships").first()
        if spatial_record and spatial_record.value:
            try:
                patterns = json.loads(spatial_record.value)
                if patterns:
                    context_parts.append("### Global Layout Rules Detected:")
                    # Filter for top spatial correlations
                    sorted_patterns = sorted(patterns, key=lambda x: x.get("count", 0), reverse=True)[:5]
                    for p in sorted_patterns:
                        context_parts.append(f"- Rule: {p.get('desc')} (Frequency Weight: {p.get('count')})")
            except Exception as e:
                logger.warning(f"Error parsing global rules: {e}")

        # 4. Common Corrections history
        corr_query = db.query(CorrectionHistory).filter(CorrectionHistory.company_name == company_name).limit(5).all()
        if corr_query:
            context_parts.append("### Historical Manual Reviewer Corrections:")
            for corr in corr_query:
                context_parts.append(f"- Field '{corr.field_type}': AI predicted '{corr.original_value}', but reviewer corrected it to '{corr.corrected_value}'")

        return "\n".join(context_parts) if context_parts else ""
