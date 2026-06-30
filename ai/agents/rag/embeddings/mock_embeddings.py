import hashlib
from typing import List
from .embeddings_interface import BaseEmbeddings

class MockEmbeddings(BaseEmbeddings):
    def __init__(self, dimension: int = 768):
        self.dimension = dimension

    def embed_query(self, text: str) -> List[float]:
        return self._hash_text(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_text(t) for t in texts]

    def _hash_text(self, text: str) -> List[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vector = []
        for i in range(self.dimension):
            byte_idx = (i * 7) % len(h)
            val = float(h[byte_idx]) / 255.0
            vector.append(val)
        return vector
