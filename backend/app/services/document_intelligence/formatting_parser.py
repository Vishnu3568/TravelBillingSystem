from __future__ import annotations

from typing import Any, Dict, Optional

from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def extract_paragraph_formatting(paragraph) -> Dict[str, Any]:
    style = paragraph.style if getattr(paragraph, "style", None) else None
    format_obj = paragraph.paragraph_format if getattr(paragraph, "paragraph_format", None) else None
    first_run = paragraph.runs[0] if getattr(paragraph, "runs", None) else None
    font = first_run.font if first_run and getattr(first_run, "font", None) else None

    alignment_value = None
    alignment = getattr(paragraph, "alignment", None)
    if alignment == WD_ALIGN_PARAGRAPH.LEFT:
        alignment_value = "LEFT"
    elif alignment == WD_ALIGN_PARAGRAPH.CENTER:
        alignment_value = "CENTER"
    elif alignment == WD_ALIGN_PARAGRAPH.RIGHT:
        alignment_value = "RIGHT"
    elif alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
        alignment_value = "JUSTIFY"

    return {
        "font_name": getattr(font, "name", None),
        "font_size": _safe_float(getattr(getattr(font, "size", None), "pt", None)),
        "bold": getattr(font, "bold", None),
        "italic": getattr(font, "italic", None),
        "underline": getattr(font, "underline", None),
        "alignment": alignment_value,
        "spacing_before": _safe_float(getattr(getattr(format_obj, "space_before", None), "pt", None)),
        "spacing_after": _safe_float(getattr(getattr(format_obj, "space_after", None), "pt", None)),
        "line_spacing": _safe_float(getattr(format_obj, "line_spacing", None)),
        "indentation_left": _safe_float(getattr(getattr(format_obj, "left_indent", None), "pt", None)),
        "indentation_right": _safe_float(getattr(getattr(format_obj, "right_indent", None), "pt", None)),
        "indentation_first_line": _safe_float(getattr(getattr(format_obj, "first_line_indent", None), "pt", None)),
        "style_name": getattr(style, "name", None),
    }


def extract_run_formatting(run) -> Dict[str, Any]:
    font = getattr(run, "font", None)
    color = getattr(font, "color", None)
    return {
        "font_name": getattr(font, "name", None),
        "font_size": _safe_float(getattr(getattr(font, "size", None), "pt", None)),
        "bold": getattr(font, "bold", None),
        "italic": getattr(font, "italic", None),
        "underline": getattr(font, "underline", None),
        "text_color": getattr(color, "rgb", None) or getattr(color, "theme_color", None),
    }


def extract_cell_formatting(cell) -> Dict[str, Any]:
    first_paragraph = cell.paragraphs[0] if getattr(cell, "paragraphs", None) else None
    first_run = first_paragraph.runs[0] if first_paragraph and getattr(first_paragraph, "runs", None) else None
    font = first_run.font if first_run and getattr(first_run, "font", None) else None
    color = getattr(font, "color", None)

    paragraph_alignment = None
    horizontal_alignment = None
    if first_paragraph is not None:
        alignment = getattr(first_paragraph, "alignment", None)
        if alignment is not None:
            paragraph_alignment = str(alignment)
            horizontal_alignment = str(alignment)

    vertical_alignment = None
    cell_vertical_alignment = getattr(cell, "vertical_alignment", None)
    if cell_vertical_alignment == WD_CELL_VERTICAL_ALIGNMENT.TOP:
        vertical_alignment = "TOP"
    elif cell_vertical_alignment == WD_CELL_VERTICAL_ALIGNMENT.CENTER:
        vertical_alignment = "CENTER"
    elif cell_vertical_alignment == WD_CELL_VERTICAL_ALIGNMENT.BOTTOM:
        vertical_alignment = "BOTTOM"

    tc = getattr(cell, "_tc", None)
    tc_pr = getattr(tc, "tcPr", None)
    width = None
    height = None
    background_color = None
    if tc_pr is not None and getattr(tc_pr, "tcW", None) is not None:
        width = _safe_float(getattr(tc_pr.tcW, "w", None))
    row = getattr(cell, "_parent", None)
    if row is not None and getattr(row, "height", None) is not None:
        height = _safe_float(getattr(row.height, "pt", None))

    if tc_pr is not None and getattr(tc_pr, "shd", None) is not None:
        background_color = getattr(tc_pr.shd, "fill", None) or getattr(tc_pr.shd, "color", None)

    text_color = getattr(color, "rgb", None) or getattr(color, "theme_color", None)

    return {
        "alignment": paragraph_alignment,
        "horizontal_alignment": horizontal_alignment,
        "vertical_alignment": vertical_alignment,
        "cell_width": width,
        "cell_height": height,
        "background_color": background_color,
        "text_color": text_color,
        "font_name": getattr(font, "name", None),
        "font_size": _safe_float(getattr(getattr(font, "size", None), "pt", None)),
        "bold": getattr(font, "bold", None),
        "italic": getattr(font, "italic", None),
        "underline": getattr(font, "underline", None),
    }


def extract_border_information(container) -> Dict[str, Any]:
    border_info: Dict[str, Any] = {}
    borders = getattr(container, "tcBorders", None) or getattr(container, "tblBorders", None)
    if borders is None:
        tc_pr = getattr(container, "tcPr", None) or getattr(container, "tblPr", None)
        if tc_pr is None:
            return border_info
        borders = getattr(tc_pr, "tcBorders", None) or getattr(tc_pr, "tblBorders", None)
    if borders is None:
        return border_info

    for name in ["top", "bottom", "left", "right", "insideH", "insideV"]:
        side = getattr(borders, name, None)
        if side is None:
            continue
        border_info[name] = {
            "val": getattr(side, "val", None),
            "sz": getattr(side, "sz", None),
            "space": getattr(side, "space", None),
            "color": getattr(side, "color", None),
        }
    return border_info
