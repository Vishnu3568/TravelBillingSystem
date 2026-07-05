from __future__ import annotations

from typing import List

from app.services.document_intelligence.document_models import DocumentLine, DocumentParagraph, DocumentRun
from app.services.document_intelligence.coordinate_mapper import build_source_path, make_node_id
from app.services.document_intelligence.formatting_parser import extract_run_formatting, extract_paragraph_formatting


def split_paragraph_lines(paragraph_text: str) -> List[str]:
    if not paragraph_text:
        return []
    lines = paragraph_text.splitlines()
    return lines if lines else [paragraph_text]


def build_paragraph_models(paragraph, page_number: int, paragraph_position: int, paragraph_index: int, page_prefix: str) -> DocumentParagraph:
    paragraph_format = extract_paragraph_formatting(paragraph)
    paragraph_id = make_node_id("paragraph", page_number, paragraph_position, str(paragraph_index))
    source_path = build_source_path(page_prefix, "paragraph", paragraph_index)

    runs: List[DocumentRun] = []
    for run_index, run in enumerate(getattr(paragraph, "runs", [])):
        run_text = run.text or ""
        run_format = extract_run_formatting(run)
        runs.append(
            DocumentRun(
                id=make_node_id("run", page_number, paragraph_position, f"{paragraph_index}-{run_index}"),
                page_number=page_number,
                position=run_index,
                text=run_text,
                run_index=run_index,
                font_name=run_format.get("font_name"),
                font_size=run_format.get("font_size"),
                bold=run_format.get("bold"),
                italic=run_format.get("italic"),
                underline=run_format.get("underline"),
                source_path=build_source_path(source_path, "run", run_index),
                metadata=run_format,
            )
        )

    lines: List[DocumentLine] = []
    for line_index, line_text in enumerate(split_paragraph_lines(paragraph.text or "")):
        lines.append(
            DocumentLine(
                id=make_node_id("line", page_number, paragraph_position, f"{paragraph_index}-{line_index}"),
                page_number=page_number,
                position=line_index,
                text=line_text,
                line_index=line_index,
                source_path=build_source_path(source_path, "line", line_index),
            )
        )

    return DocumentParagraph(
        id=paragraph_id,
        page_number=page_number,
        position=paragraph_position,
        text=paragraph.text or "",
        paragraph_index=paragraph_index,
        runs=runs,
        lines=lines,
        font_name=paragraph_format.get("font_name"),
        font_size=paragraph_format.get("font_size"),
        bold=paragraph_format.get("bold"),
        italic=paragraph_format.get("italic"),
        underline=paragraph_format.get("underline"),
        alignment=paragraph_format.get("alignment"),
        spacing_before=paragraph_format.get("spacing_before"),
        spacing_after=paragraph_format.get("spacing_after"),
        line_spacing=paragraph_format.get("line_spacing"),
        indentation_left=paragraph_format.get("indentation_left"),
        indentation_right=paragraph_format.get("indentation_right"),
        indentation_first_line=paragraph_format.get("indentation_first_line"),
        source_path=source_path,
        metadata=paragraph_format,
        is_page_break_before=False,
        contains_page_break=False,
    )
