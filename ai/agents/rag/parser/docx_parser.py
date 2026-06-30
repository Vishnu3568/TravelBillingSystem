import io
from docx import Document
from .parser_interface import BaseParser

class DocxParser(BaseParser):
    def parse(self, file_bytes: bytes, file_name: str) -> str:
        try:
            doc = Document(io.BytesIO(file_bytes))
            full_text = []
            
            # Traverse document body element by element to preserve order
            body = doc.element.body
            from docx.text.paragraph import Paragraph
            from docx.table import Table
            
            for child in body:
                if child.tag.endswith('p'):
                    p = Paragraph(child, doc)
                    if p.text.strip():
                        full_text.append(p.text.strip())
                elif child.tag.endswith('tbl'):
                    t = Table(child, doc)
                    for row in t.rows:
                        row_data = [cell.text.strip() if cell.text else "" for cell in row.cells]
                        cleaned_row = []
                        prev = None
                        for c in row_data:
                            if c == prev and c != "":
                                cleaned_row.append("")
                            else:
                                cleaned_row.append(c)
                                prev = c
                        full_text.append(" | ".join(cleaned_row))
                    full_text.append("")
                    
            return "\n".join(full_text)
        except Exception as e:
            try:
                doc = Document(io.BytesIO(file_bytes))
                return "\n".join([p.text for p in doc.paragraphs])
            except Exception:
                return f"Failed to parse Word document {file_name}: {str(e)}"
