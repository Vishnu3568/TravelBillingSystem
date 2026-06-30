import re
from typing import List
from .chunker_interface import BaseChunker

class RecursiveCharacterChunker(BaseChunker):
    def __init__(self, separators: List[str] = None):
        self.separators = separators or ["\n\n", "\n", ".", "?", "!", " ", ""]

    def chunk(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        return self._split_text(text, self.separators, chunk_size, chunk_overlap)

    def _split_text(self, text: str, separators: List[str], chunk_size: int, chunk_overlap: int) -> List[str]:
        final_chunks = []
        
        if len(text) <= chunk_size:
            return [text.strip()]
            
        separator = ""
        next_seps = []
        for i, sep in enumerate(separators):
            if sep == "" or sep in text:
                separator = sep
                next_seps = separators[i+1:]
                break
                
        if separator != "":
            splits = text.split(separator)
        else:
            splits = list(text)
            
        current_doc = []
        current_len = 0
        
        for split in splits:
            if len(split) > chunk_size:
                if current_doc:
                    final_chunks.append(separator.join(current_doc).strip())
                    current_doc = []
                    current_len = 0
                    
                recursive_splits = self._split_text(split, next_seps, chunk_size, chunk_overlap)
                final_chunks.extend(recursive_splits)
            else:
                if current_len + len(split) + (len(separator) if current_doc else 0) <= chunk_size:
                    current_doc.append(split)
                    current_len += len(split) + (len(separator) if len(current_doc) > 1 else 0)
                else:
                    if current_doc:
                        final_chunks.append(separator.join(current_doc).strip())
                    
                    overlap_doc = []
                    overlap_len = 0
                    for prev_split in reversed(current_doc):
                        if overlap_len + len(prev_split) + (len(separator) if overlap_doc else 0) <= chunk_overlap:
                            overlap_doc.insert(0, prev_split)
                            overlap_len += len(prev_split) + (len(separator) if len(overlap_doc) > 1 else 0)
                        else:
                            break
                            
                    current_doc = overlap_doc
                    current_doc.append(split)
                    current_len = overlap_len + len(split) + (len(separator) if len(current_doc) > 1 else 0)
                    
        if current_doc:
            final_chunks.append(separator.join(current_doc).strip())
            
        return [c for c in final_chunks if c.strip()]
