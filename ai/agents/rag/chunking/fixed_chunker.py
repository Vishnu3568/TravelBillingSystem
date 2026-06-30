from typing import List
from .chunker_interface import BaseChunker

class FixedSizeChunker(BaseChunker):
    def chunk(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        chunks = []
        if not text or not text.strip():
            return chunks
        
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end].strip())
            start += chunk_size - chunk_overlap
            if chunk_overlap >= chunk_size:
                start += chunk_size
        return chunks
