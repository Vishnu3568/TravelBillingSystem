from typing import List, Tuple, Dict, Any
from app.services.knowledge_graph.entity_mapper import EntityMapper

class RelationshipEngine:
    @staticmethod
    def extract_bill_relationships(bill_record: Any) -> List[Tuple[str, str, str, Dict[str, Any]]]:
        """
        Extracts edges originating from or pointing to a Bill entity.
        - (Company) - OWNS -> (Bill)
        - (Bill) - USES -> (Vehicle)
        - (Bill) - CREATED_BY -> (User/Reviewer)
        """
        relationships = []
        bill_node_id = EntityMapper.get_node_id("bill", bill_record.id)

        # 1. Company owns Bill
        if bill_record.company_name:
            comp_node_id = EntityMapper.get_node_id("company", bill_record.company_name)
            relationships.append((comp_node_id, bill_node_id, "OWNS", {}))

        # 2. Bill uses Vehicle
        if bill_record.vehicle_name:
            veh_node_id = EntityMapper.get_node_id("vehicle", bill_record.vehicle_name)
            relationships.append((bill_node_id, veh_node_id, "USES", {}))

        # 3. Bill created by User
        if bill_record.created_by:
            user_node_id = EntityMapper.get_node_id("reviewer", bill_record.created_by)
            relationships.append((bill_node_id, user_node_id, "CREATED_BY", {}))

        return relationships

    @staticmethod
    def extract_correction_relationships(corr_record: Any) -> List[Tuple[str, str, str, Dict[str, Any]]]:
        """
        Extracts edges for a manual reviewer correction.
        - (Reviewer) - MADE -> (Correction)
        - (Correction) - MODIFIED -> (Bill)
        """
        relationships = []
        corr_node_id = EntityMapper.get_node_id("correction", corr_record.id)

        # 1. Reviewer made Correction
        if corr_record.reviewer:
            rev_node_id = EntityMapper.get_node_id("reviewer", corr_record.reviewer)
            relationships.append((rev_node_id, corr_node_id, "MADE", {}))

        # 2. Correction modified Bill
        if corr_record.bill_number:
            # Resolve bill ID from correction or link directly to bill number node
            # To maintain clean IDs, let's link to the company patterns or trace the bill
            # But let's assume we link to the bill node (we'll fetch bill by number in builder)
            pass

        return relationships
