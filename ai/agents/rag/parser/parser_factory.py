import os
from typing import Dict
from .parser_interface import BaseParser
from .text_parser import TextParser
from .json_parser import JsonParser
from .csv_parser import CsvParser
from .excel_parser import ExcelParser
from .docx_parser import DocxParser
from .pptx_parser import PptxParser
from .pdf_parser import PdfParser

class ParserFactory:
    _parsers: Dict[str, BaseParser] = {
        ".txt": TextParser(),
        ".md": TextParser(),
        ".markdown": TextParser(),
        ".json": JsonParser(),
        ".csv": CsvParser(),
        ".xlsx": ExcelParser(),
        ".xls": ExcelParser(),
        ".docx": DocxParser(),
        ".doc": DocxParser(),
        ".pptx": PptxParser(),

        ".pdf": PdfParser()
    }
    
    @staticmethod
    def get_parser(file_name: str) -> BaseParser:
        ext = os.path.splitext(file_name.lower())[1]
        parser = ParserFactory._parsers.get(ext)
        if not parser:
            return ParserFactory._parsers[".txt"]
        return parser
