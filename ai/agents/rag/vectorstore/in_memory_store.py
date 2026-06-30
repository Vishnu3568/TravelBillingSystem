import math
import pickle
import os
from typing import List, Dict, Any
from .vectorstore_interface import BaseVectorStore

class InMemoryVectorStore(BaseVectorStore):
    def __init__(self):
        self.store: List[Dict[str, Any]] = []

    def add_embeddings(
        self, 
        doc_id: str, 
        chunk_id: str, 
        vector: List[float], 
        text: str, 
        metadata: Dict[str, Any]
    ):
        self.store = [item for item in self.store if item["chunk_id"] != chunk_id]
        self.store.append({
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "vector": vector,
            "text": text,
            "metadata": metadata or {}
        })

    def similarity_search(
        self, 
        query_vector: List[float], 
        top_k: int, 
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        results = []
        if not self.store or not query_vector:
            return results
            
        for item in self.store:
            if filter_metadata:
                match = True
                for k, v in filter_metadata.items():
                    if item["metadata"].get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            
            score = self._cosine_similarity(query_vector, item["vector"])
            results.append({
                "doc_id": item["doc_id"],
                "chunk_id": item["chunk_id"],
                "text": item["text"],
                "metadata": item["metadata"],
                "score": score
            })
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_document(self, doc_id: str):
        self.store = [item for item in self.store if item["doc_id"] != doc_id]

    def save(self, file_path: str):
        if os.path.dirname(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            pickle.dump(self.store, f)

    def load(self, file_path: str):
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                self.store = pickle.load(f)

    def _cosine_similarity(self, vecA: List[float], vecB: List[float]) -> float:
        if len(vecA) != len(vecB):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vecA, vecB))
        normA = sum(a * a for a in vecA)
        normB = sum(b * b for b in vecB)
        if normA == 0.0 or normB == 0.0:
            return 0.0
        return dot_product / (math.sqrt(normA) * math.sqrt(normB))
