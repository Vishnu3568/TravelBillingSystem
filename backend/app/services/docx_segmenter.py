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
    html_representation: Optional[str] = ""

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
            html_rep = "".join([f"<p>{line}</p>" for line in raw_text.split("\n") if line.strip()])
            return [
                BillChunk(
                    page_number=1,
                    raw_text=raw_text,
                    extracted_tables=[],
                    formatting_metadata={"legacy_doc": True},
                    html_representation=html_rep
                )
            ]

        try:
            doc = Document(io.BytesIO(file_bytes))
            chunks = []
            
            current_page = 1
            current_text_blocks = []
            current_tables = []
            current_html_blocks = []
            
            body = doc.element.body
            
            for child in body:
                # Check for Paragraph
                if child.tag.endswith('p'):
                    p = Paragraph(child, doc)
                    text = p.text.strip()
                    
                    # 1. Check for page break BEFORE this paragraph or NEW BILL HEADER
                    pPr = child.find(qn('w:pPr'))
                    has_break_before = False
                    if pPr is not None:
                        pbb = pPr.find(qn('w:pageBreakBefore'))
                        if pbb is not None:
                            has_break_before = True

                    # Check for repeating bill header (Bill No. 02, Bill No 03, Duty Slip, Sri Tulja Bhavani)
                    import re
                    is_new_bill_header = False
                    if text and (current_text_blocks or current_tables):
                        text_lower = text.lower()
                        if re.search(r"\b(bill|invoice)\s*(no|num|number|#)?[\.:\s]*\d+\b", text_lower) or "sri tulja bhavani" in text_lower:
                            combined_current = " ".join(current_text_blocks).lower()
                            if ("bill no" in combined_current or "duty slip" in combined_current or "sri tulja bhavani" in combined_current):
                                is_new_bill_header = True

                    if (has_break_before or is_new_bill_header) and (current_text_blocks or current_tables):
                        chunks.append(DocxSegmenterService._create_chunk(
                            current_page, current_text_blocks, current_tables, file_name, current_html_blocks
                        ))
                        current_page += 1
                        current_text_blocks = []
                        current_tables = []
                        current_html_blocks = []
                    
                    # Add paragraph text if any
                    if text:
                        current_text_blocks.append(text)
                        is_bold = any(run.bold for run in p.runs)
                        if is_bold:
                            current_html_blocks.append(f"<p><strong>{text}</strong></p>")
                        else:
                            current_html_blocks.append(f"<p>{text}</p>")
                    
                    # 2. Check for page breaks WITHIN this paragraph's runs (manual or rendered page breaks)
                    has_break_within = False
                    brs = child.xpath('.//w:br[@w:type="page"]')
                    if brs:
                        has_break_within = True
                    lrpbs = child.xpath('.//w:lastRenderedPageBreak')
                    if lrpbs:
                        has_break_within = True
                        
                    if has_break_within and (current_text_blocks or current_tables):
                        chunks.append(DocxSegmenterService._create_chunk(
                            current_page, current_text_blocks, current_tables, file_name, current_html_blocks
                        ))
                        current_page += 1
                        current_text_blocks = []
                        current_tables = []
                        current_html_blocks = []
                
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
                    
                    # Construct HTML table representation
                    tbl_html = '<table class="doc-table" style="border-collapse:collapse; width:100%; border:1px solid #ddd; margin:10px 0;">'
                    for row_data in table_data:
                        tbl_html += '<tr>'
                        for col_val in row_data:
                            tbl_html += f'<td style="border:1px solid #ddd; padding:8px;">{col_val}</td>'
                        tbl_html += '</tr>'
                    tbl_html += '</table>'
                    current_html_blocks.append(tbl_html)
                    
                    # Append visual Markdown table block into text blocks to preserve reading order
                    table_lines = []
                    for row_data in table_data:
                        table_lines.append(" | ".join([c for c in row_data]))
                    if table_lines:
                        current_text_blocks.append("\n" + "\n".join(table_lines) + "\n")
            
            # Save the final page chunk
            if current_text_blocks or current_tables:
                chunks.append(DocxSegmenterService._create_chunk(
                    current_page, current_text_blocks, current_tables, file_name, current_html_blocks
                ))
            
            # If no chunks were created, fallback to whole document
            if not chunks:
                from app.services.docx_extractor import DocxExtractionService
                raw_text = DocxExtractionService.extract_raw_text(file_bytes, file_name)
                html_rep = "".join([f"<p>{line}</p>" for line in raw_text.split("\n") if line.strip()])
                chunks.append(BillChunk(
                    page_number=1,
                    raw_text=raw_text,
                    extracted_tables=[],
                    formatting_metadata={"fallback": True},
                    html_representation=html_rep
                ))
                
            logger.info(f"Successfully segmented document {file_name} into {len(chunks)} pages")
            return chunks

        except Exception as e:
            logger.error(f"Failed to segment docx {file_name}: {e}. Falling back to single-page parser.")
            from app.services.docx_extractor import DocxExtractionService
            raw_text = DocxExtractionService.extract_raw_text(file_bytes, file_name)
            html_rep = "".join([f"<p>{line}</p>" for line in raw_text.split("\n") if line.strip()])
            return [
                BillChunk(
                    page_number=1,
                    raw_text=raw_text,
                    extracted_tables=[],
                    formatting_metadata={"exception_fallback": True},
                    html_representation=html_rep
                )
            ]

    @staticmethod
    def _create_chunk(page_num: int, text_blocks: List[str], tables: List[List[List[str]]], filename: str, html_blocks: List[str] = None) -> BillChunk:
        raw_text = "\n".join(text_blocks)
        html_rep = "\n".join(html_blocks) if html_blocks else ""
        if not html_rep:
            html_rep = "".join([f"<p>{b}</p>" for b in text_blocks])
        
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
            document_metadata={"filename": filename},
            html_representation=html_rep
        )
