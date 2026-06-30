import io
import logging
from docx import Document
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
from docx.text.paragraph import Paragraph
from docx.table import Table
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

logger = logging.getLogger("docx_segmenter")

class BillChunk(BaseModel):
    page_number: int
    company_name: Optional[str] = None
    raw_text: str
    extracted_tables: List[List[List[str]]] = []
    formatting_metadata: Dict[str, Any] = {}
    document_metadata: Dict[str, Any] = {}

class DocxSegmenterService:
    @staticmethod
    def segment_docx(file_bytes: bytes, file_name: str) -> List[BillChunk]:
        """
        Segments a .docx file into page-by-page chunks using OpenXML structural elements.
        Preserves reading order, layout tables, and extracts text one page at a time.
        """
        file_name_lower = file_name.lower() if file_name else ""
        
        # If it is a legacy .doc file, we cannot segment pages structurally. 
        # Treat the entire text as a single chunk.
        if file_name_lower.endswith(".doc"):
            logger.info("Legacy .doc detected. Returning entire text as single chunk.")
            from app.services.docx_extractor import DocxExtractionService
            raw_text = DocxExtractionService._extract_doc_fallback(file_bytes)
            return [
                BillChunk(
                    page_number=1,
                    raw_text=raw_text,
                    extracted_tables=[],
                    formatting_metadata={"legacy_doc": True}
                )
            ]

        try:
            doc = Document(io.BytesIO(file_bytes))
            chunks = []
            
            current_page = 1
            current_text_blocks = []
            current_tables = []
            
            body = doc.element.body
            
            for child in body:
                # Check for Paragraph
                if child.tag.endswith('p'):
                    p = Paragraph(child, doc)
                    text = p.text.strip()
                    
                    # 1. Check for page break BEFORE this paragraph (PageBreakBefore paragraph property)
                    pPr = child.find(qn('w:pPr'))
                    has_break_before = False
                    if pPr is not None:
                        pbb = pPr.find(qn('w:pageBreakBefore'))
                        if pbb is not None:
                            has_break_before = True
                    
                    if has_break_before and (current_text_blocks or current_tables):
                        chunks.append(DocxSegmenterService._create_chunk(
                            current_page, current_text_blocks, current_tables, file_name
                        ))
                        current_page += 1
                        current_text_blocks = []
                        current_tables = []
                    
                    # Add paragraph text if any
                    if text:
                        current_text_blocks.append(text)
                    
                    # 2. Check for page breaks WITHIN this paragraph's runs (manual or rendered page breaks)
                    has_break_within = False
                    # Check for w:br w:type="page"
                    brs = child.xpath('.//w:br[@w:type="page"]')
                    if brs:
                        has_break_within = True
                    # Check for w:lastRenderedPageBreak (inserted by MS Word engine)
                    lrpbs = child.xpath('.//w:lastRenderedPageBreak')
                    if lrpbs:
                        has_break_within = True
                        
                    if has_break_within:
                        chunks.append(DocxSegmenterService._create_chunk(
                            current_page, current_text_blocks, current_tables, file_name
                        ))
                        current_page += 1
                        current_text_blocks = []
                        current_tables = []
                
                # Check for Table
                elif child.tag.endswith('tbl'):
                    t = Table(child, doc)
                    table_data = []
                    
                    for row in t.rows:
                        row_data = []
                        # Retrieve unique text fields while handling cell horizontal merges
                        prev_text = None
                        for cell in row.cells:
                            cell_text = cell.text.strip() if cell.text else ""
                            # If adjacent cells are merged, python-docx repeats the text.
                            # We can keep empty strings or skip duplicates to preserve clean tabular layout.
                            if cell_text == prev_text and cell_text != "":
                                row_data.append("")
                            else:
                                row_data.append(cell_text)
                                prev_text = cell_text
                        table_data.append(row_data)
                    
                    current_tables.append(table_data)
                    
                    # Append visual Markdown table block into text blocks to preserve reading order
                    table_lines = []
                    for row_data in table_data:
                        table_lines.append(" | ".join([c for c in row_data]))
                    if table_lines:
                        current_text_blocks.append("\n" + "\n".join(table_lines) + "\n")
            
            # Save the final page chunk
            if current_text_blocks or current_tables:
                chunks.append(DocxSegmenterService._create_chunk(
                    current_page, current_text_blocks, current_tables, file_name
                ))
            
            # If no chunks were created, fallback to whole document
            if not chunks:
                from app.services.docx_extractor import DocxExtractionService
                raw_text = DocxExtractionService.extract_raw_text(file_bytes, file_name)
                chunks.append(BillChunk(
                    page_number=1,
                    raw_text=raw_text,
                    extracted_tables=[],
                    formatting_metadata={"fallback": True}
                ))
                
            logger.info(f"Successfully segmented document {file_name} into {len(chunks)} pages")
            return chunks

        except Exception as e:
            logger.error(f"Failed to segment docx {file_name}: {e}. Falling back to single-page parser.")
            from app.services.docx_extractor import DocxExtractionService
            raw_text = DocxExtractionService.extract_raw_text(file_bytes, file_name)
            return [
                BillChunk(
                    page_number=1,
                    raw_text=raw_text,
                    extracted_tables=[],
                    formatting_metadata={"exception_fallback": True}
                )
            ]

    @staticmethod
    def _create_chunk(page_num: int, text_blocks: List[str], tables: List[List[List[str]]], filename: str) -> BillChunk:
        raw_text = "\n".join(text_blocks)
        
        # Try to guess the company name from the first few lines of text
        company_name = None
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        if lines:
            # Check first 5 lines for typical corporate nouns
            for line in lines[:5]:
                line_lower = line.lower()
                if any(x in line_lower for x in ["travels", "logistics", "tours", "billing", "invoice", "solutions", "limited", "pvt"]):
                    company_name = line
                    break
        
        return BillChunk(
            page_number=page_num,
            company_name=company_name,
            raw_text=raw_text,
            extracted_tables=tables,
            formatting_metadata={},
            document_metadata={"filename": filename}
        )
