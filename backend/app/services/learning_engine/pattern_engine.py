import logging
from typing import List, Dict, Any, Tuple
from app.services.field_labeling.field_models import LabeledDocument, LabeledElement

logger = logging.getLogger("pattern_engine")

class PatternEngine:
    @staticmethod
    def extract_spatial_relationships(labeled_doc: LabeledDocument) -> List[Dict[str, Any]]:
        """
        Scans all labeled elements in the document and determines spatial relations:
        - 'below': element_A is immediately under element_B (same table, row_index = prev_row + 1, same column)
        - 'beside': element_A is adjacent to element_B (same table, same row, column_index = prev_col + 1)
        - 'follows': element_A follows element_B in chronological cell order
        """
        relationships = []
        elements = labeled_doc.elements
        
        # Group by table
        tables: Dict[int, List[LabeledElement]] = {}
        for el in elements:
            coords = el.coordinates or {}
            table_num = coords.get("table_number")
            if table_num is not None:
                if table_num not in tables:
                    tables[table_num] = []
                tables[table_num].append(el)
                
        for table_num, tbl_elements in tables.items():
            # Check cell pairings
            for el_a in tbl_elements:
                coords_a = el_a.coordinates or {}
                row_a = coords_a.get("row_index")
                col_a = coords_a.get("column_index")
                
                for el_b in tbl_elements:
                    if el_a.id == el_b.id:
                        continue
                    coords_b = el_b.coordinates or {}
                    row_b = coords_b.get("row_index")
                    col_b = coords_b.get("column_index")
                    
                    # 1. Check if el_a is below el_b
                    if row_a == row_b + 1 and col_a == col_b:
                        relationships.append({
                            "type": "below",
                            "first_label": el_a.label,
                            "second_label": el_b.label,
                            "desc": f"{el_a.label} is below {el_b.label}"
                        })
                        
                    # 2. Check if el_a is beside el_b
                    if row_a == row_b and col_a == col_b + 1:
                        relationships.append({
                            "type": "beside",
                            "first_label": el_a.label,
                            "second_label": el_b.label,
                            "desc": f"{el_a.label} is beside {el_b.label}"
                        })
                        
                    # 3. Check if el_a follows el_b (e.g. driver bata follows extra hours in column index)
                    if row_a == row_b and col_a > col_b:
                        relationships.append({
                            "type": "follows",
                            "first_label": el_a.label,
                            "second_label": el_b.label,
                            "desc": f"{el_a.label} follows {el_b.label}"
                        })
                        
        return relationships

    @staticmethod
    def consolidate_patterns(existing_patterns: List[Dict[str, Any]], new_relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidates newly detected relationships with existing ones, incrementing a frequency count.
        """
        consolidated = {f"{p['type']}_{p['first_label']}_{p['second_label']}": p for p in existing_patterns}
        
        for r in new_relations:
            key = f"{r['type']}_{r['first_label']}_{r['second_label']}"
            if key in consolidated:
                consolidated[key]["count"] = consolidated[key].get("count", 1) + 1
            else:
                consolidated[key] = {
                    "type": r["type"],
                    "first_label": r["first_label"],
                    "second_label": r["second_label"],
                    "desc": r["desc"],
                    "count": 1
                }
                
        return list(consolidated.values())
