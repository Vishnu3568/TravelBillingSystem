import re
from typing import List
from .chunker_interface import BaseChunker

class SemanticChunker(BaseChunker):
    def chunk(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        if not text or not text.strip():
            return []
            
        sentences = re.split(r'(?<=[.?!])\s+', text)
        chunks = []
        current_chunk = []
        current_len = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) > chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                words = sentence.split(" ")
                word_chunk = []
                word_len = 0
                for w in words:
                    if word_len + len(w) + 1 <= chunk_size:
                        word_chunk.append(w)
                        word_len += len(w) + 1
                    else:
                        chunks.append(" ".join(word_chunk))
                        word_chunk = [w]
                        word_len = len(w)
                if word_chunk:
                    current_chunk = word_chunk
                    current_len = word_len
            else:
                if current_len + len(sentence) + 1 <= chunk_size:
                    current_chunk.append(sentence)
                    current_len += len(sentence) + 1
                else:
                    chunks.append(" ".join(current_chunk))
                    overlap_chunk = []
                    overlap_len = 0
                    for prev_s in reversed(current_chunk):
                        if overlap_len + len(prev_s) + 1 <= chunk_overlap:
                            overlap_chunk.insert(0, prev_s)
                            overlap_len += len(prev_s) + 1
                        else:
                            break
                    current_chunk = overlap_chunk
                    current_chunk.append(sentence)
                    current_len = overlap_len + len(sentence) + 1
                    
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return [c.strip() for c in chunks if c.strip()]
