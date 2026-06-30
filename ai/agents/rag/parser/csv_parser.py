import csv
import io
from .parser_interface import BaseParser

class CsvParser(BaseParser):
    def parse(self, file_bytes: bytes, file_name: str) -> str:
        try:
            text = file_bytes.decode("utf-8", errors="ignore")
            reader = csv.reader(io.StringIO(text))
            markdown_table = []
            for row in reader:
                markdown_table.append(" | ".join(row))
            return "\n".join(markdown_table)
        except Exception as e:
            return f"Failed to parse CSV file {file_name}: {str(e)}"
