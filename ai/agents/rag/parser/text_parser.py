from .parser_interface import BaseParser

class TextParser(BaseParser):
    def parse(self, file_bytes: bytes, file_name: str) -> str:
        try:
            return file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return file_bytes.decode("latin-1", errors="ignore")
