import json
from .parser_interface import BaseParser

class JsonParser(BaseParser):
    def parse(self, file_bytes: bytes, file_name: str) -> str:
        try:
            data = json.loads(file_bytes.decode("utf-8", errors="ignore"))
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"Failed to parse JSON file {file_name}: {str(e)}"
