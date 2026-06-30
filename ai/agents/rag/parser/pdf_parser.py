import io
import pypdf
from .parser_interface import BaseParser

class PdfParser(BaseParser):
    def parse(self, file_bytes: bytes, file_name: str) -> str:
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            output = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                output.append(f"## Page {i+1}")
                if text:
                    output.append(text.strip())
                output.append("")
            return "\n".join(output)
        except Exception as e:
            return f"Failed to parse PDF file {file_name}: {str(e)}"
