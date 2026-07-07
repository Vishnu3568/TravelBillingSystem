from __future__ import annotations

import logging
from typing import Dict, Any, List
from app.services.document_intelligence.document_models import EnterpriseDocument
from app.services.field_labeling.field_models import LabeledElement, LabeledDocument
from app.services.field_labeling.field_classifier import FieldClassifier
from app.services.field_labeling.confidence_engine import ConfidenceEngine
from app.services.field_labeling.label_validator import LabelValidator

logger = logging.getLogger("labeling_orchestrator")

class LabelingOrchestrator:
    @staticmethod
    def orchestrate_labeling(doc: EnterpriseDocument) -> LabeledDocument:
        """
        Orchestrates the classification pipeline:
        1. Prepares spatial/neighboring context for cells and paragraphs.
        2. Batches elements for classification.
        3. Invokes the FieldClassifier.
        4. Runs ConfidenceEngine and LabelValidator.
        5. Returns the fully assembled LabeledDocument.
        """
        prepared_elements = LabelingOrchestrator._prepare_elements(doc)
        if not prepared_elements:
            return LabeledDocument(metadata=doc.metadata, elements=[])

        # Batch elements in chunks of 30 to stay within prompt token bounds
        batch_size = 30
        classifications: List[Dict[str, Any]] = []
        
        allowed_ids = {el["id"] for el in prepared_elements}

        for i in range(0, len(prepared_elements), batch_size):
            batch = prepared_elements[i:i + batch_size]
            logger.info("Processing classification batch %d/%d", i // batch_size + 1, (len(prepared_elements) + batch_size - 1) // batch_size)
            try:
                batch_classifications = FieldClassifier.classify_elements(batch)
                classifications.extend(batch_classifications)
            except Exception as e:
                logger.error("Batch classification failed: %s", e)
                # Fallback to rules for this batch
                batch_fallback = FieldClassifier._local_rule_classify(batch)
                classifications.extend(batch_fallback)

        # Apply confidence thresholds
        processed_classifications = ConfidenceEngine.process_classifications(classifications)

        # Validate structure and allowed labels
        validated_classifications = LabelValidator.validate_classifications(
            processed_classifications, allowed_ids
        )

        # Create lookup map for easy assembly
        label_map = {c["id"]: c for c in validated_classifications}

        labeled_elements: List[LabeledElement] = []
        for el in prepared_elements:
            el_id = el["id"]
            class_info = label_map.get(el_id, {"label": "UNKNOWN", "confidence": 0.50})
            
            labeled_elements.append(
                LabeledElement(
                    id=el_id,
                    text=el["text"],
                    coordinates=el["coordinates"],
                    formatting=el["formatting"],
                    label=class_info["label"],
                    confidence=class_info["confidence"]
                )
            )

        return LabeledDocument(
            metadata=doc.metadata,
            elements=labeled_elements
        )

    @staticmethod
    def _prepare_elements(doc: EnterpriseDocument) -> List[Dict[str, Any]]:
        prepared = []

        # Iterate page-by-page to reconstruct tables and neighbor relations
        for page in doc.pages:
            # Build table grid lookup maps for neighbors
            table_grids = {}
            for table in page.tables:
                grid = {}
                for row in table.rows:
                    for cell in row.cells:
                        row_idx = cell.row_index or 0
                        col_idx = cell.column_index or 0
                        rowspan = cell.rowspan or 1
                        colspan = cell.colspan or 1
                        for r in range(rowspan):
                            for c in range(colspan):
                                grid[(row_idx + r, col_idx + c)] = cell
                table_grids[table.id] = (table, grid)

            # Reconstruct reading order list to find paragraph neighbors
            elements_list = page.reading_order

            for idx, item in enumerate(elements_list):
                item_type = item.get("type")
                item_id = item.get("id")

                if item_type == "paragraph":
                    # Locate paragraph model
                    paragraph = next((p for p in page.paragraphs if p.id == item_id), None)
                    if not paragraph or not paragraph.text.strip():
                        continue

                    # Find paragraph neighbors outside tables
                    above_text = None
                    below_text = None
                    if idx > 0:
                        prev_item = elements_list[idx - 1]
                        if prev_item.get("type") == "paragraph":
                            above_text = prev_item.get("text")
                    if idx < len(elements_list) - 1:
                        next_item = elements_list[idx + 1]
                        if next_item.get("type") == "paragraph":
                            below_text = next_item.get("text")

                    # Add prepared paragraph
                    prepared.append({
                        "id": paragraph.id,
                        "text": paragraph.text,
                        "coordinates": {
                            "page_number": page.page_number,
                            "position": paragraph.position,
                            "source_path": paragraph.source_path
                        },
                        "formatting": {
                            "bold": paragraph.bold,
                            "italic": paragraph.italic,
                            "underline": paragraph.underline,
                            "font_size": paragraph.font_size,
                            "font_name": paragraph.font_name,
                            "alignment": paragraph.alignment
                        },
                        "neighbors": {
                            "left": None,
                            "right": None,
                            "above": above_text,
                            "below": below_text
                        },
                        "column_header": None,
                        "table_position": None,
                        "reading_order_position": item.get("order")
                    })

                elif item_type == "table":
                    # Locate table model
                    table, grid = table_grids.get(item_id, (None, None))
                    if not table or not grid:
                        continue

                    # Walk through all unique cells in table
                    visited_cell_ids = set()
                    for row in table.rows:
                        for cell in row.cells:
                            if cell.id in visited_cell_ids or not cell.text.strip():
                                continue
                            visited_cell_ids.add(cell.id)

                            row_idx = cell.row_index or 0
                            col_idx = cell.column_index or 0
                            rowspan = cell.rowspan or 1
                            colspan = cell.colspan or 1

                            # Compute neighbors inside table grid
                            left_cell = grid.get((row_idx, col_idx - 1))
                            right_cell = grid.get((row_idx, col_idx + colspan))
                            above_cell = grid.get((row_idx - 1, col_idx))
                            below_cell = grid.get((row_idx + rowspan, col_idx))

                            left_text = left_cell.text if left_cell and left_cell.id != cell.id else None
                            right_text = right_cell.text if right_cell and right_cell.id != cell.id else None
                            above_text = above_cell.text if above_cell and above_cell.id != cell.id else None
                            below_text = below_cell.text if below_cell and below_cell.id != cell.id else None

                            # Column header is cell in row 0 of the same column
                            header_cell = grid.get((0, col_idx))
                            header_text = header_cell.text if header_cell and row_idx > 0 else None

                            prepared.append({
                                "id": cell.id,
                                "text": cell.text,
                                "coordinates": {
                                    "page_number": page.page_number,
                                    "table_number": table.table_number,
                                    "row_index": row_idx,
                                    "column_index": col_idx,
                                    "rowspan": rowspan,
                                    "colspan": colspan,
                                    "source_path": cell.source_path
                                },
                                "formatting": {
                                    "bold": cell.bold,
                                    "italic": cell.italic,
                                    "underline": cell.underline,
                                    "font_size": cell.font_size,
                                    "font_name": cell.font_name,
                                    "alignment": cell.alignment,
                                    "vertical_alignment": cell.vertical_alignment,
                                    "background_color": cell.background_color,
                                    "text_color": cell.text_color
                                },
                                "neighbors": {
                                    "left": left_text,
                                    "right": right_text,
                                    "above": above_text,
                                    "below": below_text
                                },
                                "column_header": header_text,
                                "table_position": {
                                    "table_number": table.table_number,
                                    "num_rows": table.number_of_rows,
                                    "num_columns": table.number_of_columns
                                },
                                "reading_order_position": item.get("order")
                            })

        return prepared
