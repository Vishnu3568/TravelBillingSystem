from typing import Dict, Any, Tuple
import json

class EntityMapper:
    @staticmethod
    def get_node_id(entity_type: str, entity_id_or_val: Any) -> str:
        """
        Generates a standard unique Graph Node identifier.
        """
        clean_val = str(entity_id_or_val).strip().replace(" ", "_")
        return f"{entity_type.lower()}:{clean_val}"

    @staticmethod
    def map_entity(entity_type: str, record: Any) -> Tuple[str, Dict[str, Any]]:
        """
        Normalizes database records to graph node properties.
        Returns a tuple: (graph_node_id, properties_dict)
        """
        properties = {}
        node_id = ""

        entity_lower = entity_type.strip().lower()

        if entity_lower == "company":
            node_id = EntityMapper.get_node_id("company", record.name)
            properties = {
                "name": record.name,
                "address": getattr(record, "address", "Imported via AI"),
            }
        elif entity_lower == "bill":
            node_id = EntityMapper.get_node_id("bill", record.id)
            properties = {
                "bill_number": record.bill_number,
                "duty_slip_no": record.duty_slip_no,
                "grand_total": record.grand_total,
                "bill_date": record.bill_date.isoformat() if record.bill_date else None,
                "created_by": record.created_by
            }
        elif entity_lower == "vehicle":
            # Normalize vehicle registration number
            reg_num = getattr(record, "registration_number", str(record)).strip()
            node_id = EntityMapper.get_node_id("vehicle", reg_num)
            properties = {
                "registration_number": reg_num,
                "type": getattr(record, "type", "Car")
            }
        elif entity_lower == "reviewer":
            reviewer_name = str(record).strip()
            node_id = EntityMapper.get_node_id("reviewer", reviewer_name)
            properties = {"username": reviewer_name}
        elif entity_lower == "driver":
            driver_name = str(record).strip()
            node_id = EntityMapper.get_node_id("driver", driver_name)
            properties = {"name": driver_name}
        elif entity_lower == "validation_report":
            # For validation reports associated with bills
            node_id = EntityMapper.get_node_id("validation_report", record.get("bill_id", "0"))
            properties = {
                "overall_score": record.get("overall_score", 1.0),
                "issues_count": len(record.get("issues", []))
            }
        elif entity_lower == "correction":
            node_id = EntityMapper.get_node_id("correction", record.id)
            properties = {
                "field": record.field_type,
                "original": record.original_value,
                "corrected": record.corrected_value,
                "reviewer": record.reviewer
            }
        elif entity_lower == "conversation":
            node_id = EntityMapper.get_node_id("conversation", record.get("session_id", "0"))
            properties = {
                "session_id": record.get("session_id"),
                "turns": len(record.get("history", []))
            }
        else:
            # General fallback
            rec_id = getattr(record, "id", str(record))
            node_id = EntityMapper.get_node_id(entity_type, rec_id)
            properties = {"info": str(record)}

        return node_id, properties
