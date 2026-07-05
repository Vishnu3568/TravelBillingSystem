from __future__ import annotations

from typing import Any, Dict, List, Tuple

from docx.table import _Cell

from app.services.document_intelligence.coordinate_mapper import build_source_path, make_node_id
from app.services.document_intelligence.document_models import DocumentCell, DocumentRow, DocumentTable
from app.services.document_intelligence.formatting_parser import extract_border_information, extract_cell_formatting


def _get_grid_span(tc) -> int:
    tc_pr = getattr(tc, "tcPr", None)
    if tc_pr is not None and getattr(tc_pr, "gridSpan", None) is not None:
        value = getattr(tc_pr.gridSpan, "val", None)
        try:
            return int(value)
        except Exception:
            return 1
    return 1


def _get_vmerge(tc) -> str | None:
    tc_pr = getattr(tc, "tcPr", None)
    if tc_pr is None or getattr(tc_pr, "vMerge", None) is None:
        return None
    value = getattr(tc_pr.vMerge, "val", None)
    if value is None:
        return "continue"
    return str(value)


def _cell_text(cell: _Cell) -> str:
    return (cell.text or "").strip()


def _make_cell_coordinate(cell_id: str, page_number: int, table_id: str, row_index: int, column_index: int, rowspan: int, colspan: int, text: str, source_path: str) -> Dict[str, Any]:
    return {
        "cell_id": cell_id,
        "page_number": page_number,
        "table_id": table_id,
        "row_index": row_index,
        "column_index": column_index,
        "rowspan": rowspan,
        "colspan": colspan,
        "text": text,
        "source_path": source_path,
    }


def _upsert_merge_region(regions: Dict[str, Dict[str, Any]], anchor_id: str, region: Dict[str, Any]) -> None:
    if anchor_id not in regions:
        regions[anchor_id] = region
        return

    existing = regions[anchor_id]
    existing["rowspan"] = max(existing.get("rowspan", 1), region.get("rowspan", 1))
    existing["colspan"] = max(existing.get("colspan", 1), region.get("colspan", 1))
    existing.setdefault("coordinates", [])
    existing["coordinates"].extend(region.get("coordinates", []))
    if region.get("child_id"):
        existing.setdefault("child_ids", [])
        existing["child_ids"].append(region["child_id"])


def _add_merge_region(regions: Dict[str, Dict[str, Any]], anchor_id: str, region: Dict[str, Any]) -> None:
    if anchor_id not in regions:
        regions[anchor_id] = region
        return
    _upsert_merge_region(regions, anchor_id, region)


def parse_table(table, page_number: int, table_number: int, table_position: int, page_prefix: str) -> DocumentTable:
    table_id = make_node_id("table", page_number, table_position, str(table_number))
    table_source_path = build_source_path(page_prefix, "table", table_number)

    rows: List[DocumentRow] = []
    merged_cells: List[Dict[str, Any]] = []
    cell_coordinates: List[Dict[str, Any]] = []
    merge_regions: Dict[str, Dict[str, Any]] = {}
    active_vertical_merges: Dict[int, Tuple[str, int]] = {}
    max_columns = 0

    for row_index, row in enumerate(table.rows):
        row_cells: List[DocumentCell] = []
        logical_column = 0
        physical_cells = list(getattr(row._tr, "tc_lst", []))

        for cell_index, tc in enumerate(physical_cells):
            cell = _Cell(tc, row)
            colspan = _get_grid_span(tc)
            vmerge = _get_vmerge(tc)
            cell_text = _cell_text(cell)
            cell_format = extract_cell_formatting(cell)
            border_info = extract_border_information(tc.tcPr if getattr(tc, "tcPr", None) is not None else tc)
            source_path = build_source_path(table_source_path, "row", row_index, "cell", logical_column)
            cell_id = make_node_id("cell", page_number, row_index, f"{table_number}-{logical_column}")
            rowspan = 1
            merged_parent_id = None
            merge_role = None

            if vmerge == "restart":
                merge_role = "restart"
                for offset in range(colspan):
                    active_vertical_merges[logical_column + offset] = (cell_id, 1)
                _add_merge_region(
                    merge_regions,
                    cell_id,
                    {
                        "anchor_id": cell_id,
                        "page_number": page_number,
                        "table_id": table_id,
                        "row_index": row_index,
                        "column_index": logical_column,
                        "rowspan": 1,
                        "colspan": colspan,
                        "coordinates": [
                            _make_cell_coordinate(cell_id, page_number, table_id, row_index, logical_column, 1, colspan, cell_text, source_path)
                        ],
                    },
                )
            elif vmerge == "continue":
                merge_role = "continue"
                anchor = active_vertical_merges.get(logical_column)
                if anchor is not None:
                    merged_parent_id = anchor[0]
                    row_span_count = anchor[1] + 1
                    for offset in range(colspan):
                        active_vertical_merges[logical_column + offset] = (anchor[0], row_span_count)
                    rowspan = row_span_count
                    _upsert_merge_region(
                        merge_regions,
                        anchor[0],
                        {
                            "anchor_id": anchor[0],
                            "child_id": cell_id,
                            "page_number": page_number,
                            "table_id": table_id,
                            "row_index": row_index,
                            "column_index": logical_column,
                            "rowspan": rowspan,
                            "colspan": colspan,
                            "coordinates": [
                                _make_cell_coordinate(cell_id, page_number, table_id, row_index, logical_column, rowspan, colspan, cell_text, source_path)
                            ],
                        }
                    )
            elif colspan > 1:
                merge_role = "horizontal"
                _add_merge_region(
                    merge_regions,
                    cell_id,
                    {
                        "anchor_id": cell_id,
                        "page_number": page_number,
                        "table_id": table_id,
                        "row_index": row_index,
                        "column_index": logical_column,
                        "rowspan": 1,
                        "colspan": colspan,
                        "coordinates": [
                            _make_cell_coordinate(cell_id, page_number, table_id, row_index, logical_column + offset, 1, 1, cell_text, source_path)
                            for offset in range(colspan)
                        ],
                    },
                )

            cell_model = DocumentCell(
                id=cell_id,
                page_number=page_number,
                position=cell_index,
                text=cell_text,
                table_id=table_id,
                row_index=row_index,
                column_index=logical_column,
                rowspan=rowspan,
                colspan=colspan,
                cell_width=cell_format.get("cell_width"),
                cell_height=cell_format.get("cell_height"),
                font_name=cell_format.get("font_name"),
                font_size=cell_format.get("font_size"),
                bold=cell_format.get("bold"),
                italic=cell_format.get("italic"),
                underline=cell_format.get("underline"),
                alignment=cell_format.get("alignment"),
                source_path=source_path,
                metadata=cell_format,
                cell_index=cell_index,
                is_header=row_index == 0,
                is_merged=(colspan > 1 or vmerge is not None),
                merge_role=merge_role,
                border_info=border_info,
                paragraph_ids=[],
                merged_parent_id=merged_parent_id,
            )
            row_cells.append(cell_model)
            cell_coordinates.append(
                _make_cell_coordinate(cell_id, page_number, table_id, row_index, logical_column, rowspan, colspan, cell_text, source_path)
            )
            logical_column += colspan

        max_columns = max(max_columns, logical_column)
        row_model = DocumentRow(
            id=make_node_id("row", page_number, table_position, f"{table_number}-{row_index}"),
            page_number=page_number,
            position=row_index,
            text="",
            row_index=row_index,
            cells=row_cells,
            is_header_row=row_index == 0,
            source_path=build_source_path(table_source_path, "row", row_index),
            border_info=extract_border_information(getattr(row._tr, "trPr", None) or row._tr),
        )
        rows.append(row_model)

    table_tbl_pr = getattr(table._tbl, "tblPr", None)
    table_border_info = extract_border_information(table_tbl_pr if table_tbl_pr is not None else table._tbl)
    header_rows = [0] if rows else []

    for region in merge_regions.values():
        merged_cells.append(region)

    return DocumentTable(
        id=table_id,
        page_number=page_number,
        position=table_position,
        text="",
        table_number=table_number,
        number_of_rows=len(rows),
        number_of_columns=max_columns,
        merged_cells=merged_cells,
        cell_coordinates=cell_coordinates,
        header_rows=header_rows,
        border_info=table_border_info,
        rows=rows,
        source_path=table_source_path,
    )
