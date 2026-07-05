from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DocumentNode(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    page_number: int
    position: int
    text: str = ""
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    alignment: Optional[str] = None
    vertical_alignment: Optional[str] = None
    horizontal_alignment: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    table_id: Optional[str] = None
    row_index: Optional[int] = None
    column_index: Optional[int] = None
    rowspan: Optional[int] = None
    colspan: Optional[int] = None
    cell_width: Optional[float] = None
    cell_height: Optional[float] = None
    source_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentRun(DocumentNode):
    run_index: Optional[int] = None


class DocumentLine(DocumentNode):
    line_index: Optional[int] = None
    run_ids: List[str] = Field(default_factory=list)


class DocumentParagraph(DocumentNode):
    paragraph_index: Optional[int] = None
    lines: List[DocumentLine] = Field(default_factory=list)
    runs: List[DocumentRun] = Field(default_factory=list)
    spacing_before: Optional[float] = None
    spacing_after: Optional[float] = None
    line_spacing: Optional[float] = None
    indentation_left: Optional[float] = None
    indentation_right: Optional[float] = None
    indentation_first_line: Optional[float] = None
    is_page_break_before: bool = False
    contains_page_break: bool = False


class DocumentCell(DocumentNode):
    cell_index: Optional[int] = None
    is_header: bool = False
    is_merged: bool = False
    merge_role: Optional[str] = None
    border_info: Dict[str, Any] = Field(default_factory=dict)
    paragraph_ids: List[str] = Field(default_factory=list)
    merged_parent_id: Optional[str] = None


class DocumentRow(DocumentNode):
    row_index: Optional[int] = None
    cells: List[DocumentCell] = Field(default_factory=list)
    is_header_row: bool = False
    border_info: Dict[str, Any] = Field(default_factory=dict)


class DocumentTable(DocumentNode):
    table_number: int = 1
    number_of_rows: int = 0
    number_of_columns: int = 0
    merged_cells: List[Dict[str, Any]] = Field(default_factory=list)
    cell_coordinates: List[Dict[str, Any]] = Field(default_factory=list)
    header_rows: List[int] = Field(default_factory=list)
    border_info: Dict[str, Any] = Field(default_factory=dict)
    rows: List[DocumentRow] = Field(default_factory=list)


class DocumentPage(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    page_number: int
    position: int
    title: Optional[str] = None
    paragraphs: List[DocumentParagraph] = Field(default_factory=list)
    tables: List[DocumentTable] = Field(default_factory=list)
    reading_order: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    revision: Optional[str] = None
    version: Optional[str] = None
    extraction_engine: str = "document_intelligence"
    extraction_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    source_format: Optional[str] = None


class DocumentCoordinate(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    object_type: str
    source_id: str
    source_path: str
    page_number: int
    position: int
    table_number: Optional[int] = None
    row_index: Optional[int] = None
    column_index: Optional[int] = None
    rowspan: Optional[int] = None
    colspan: Optional[int] = None
    text: str = ""


class EnterpriseDocument(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    metadata: DocumentMetadata
    pages: List[DocumentPage] = Field(default_factory=list)
    paragraphs: List[DocumentParagraph] = Field(default_factory=list)
    tables: List[DocumentTable] = Field(default_factory=list)
    cells: List[DocumentCell] = Field(default_factory=list)
    lines: List[DocumentLine] = Field(default_factory=list)
    runs: List[DocumentRun] = Field(default_factory=list)
    coordinates: List[DocumentCoordinate] = Field(default_factory=list)
    reading_order: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    def to_json(self) -> Dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)
