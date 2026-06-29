import numpy as np
from typing import List, Dict, Any

class RagAgent:
    def __init__(self):
        # In-memory vector store: list of dicts with keys: bill_id, text, embedding, metadata
        self.indexed_store: List[Dict[str, Any]] = []

    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        a = np.array(vec_a)
        b = np.array(vec_b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def index_bill(self, bill_id: int, text: str, embedding: List[float], metadata: Dict[str, Any] = None) -> bool:
        if not embedding:
            return False
        # Remove existing index if any
        self.indexed_store = [b for b in self.indexed_store if b["bill_id"] != bill_id]
        self.indexed_store.append({
            "bill_id": bill_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {}
        })
        return True

    def retrieve_context(self, query_embedding: List[float], score_threshold: float = 0.6, limit: int = 3) -> str:
        if not query_embedding or not self.indexed_store:
            return ""
        
        scored_bills = []
        for item in self.indexed_store:
            score = self.cosine_similarity(query_embedding, item["embedding"])
            if score > score_threshold:
                scored_bills.append((score, item))
        
        # Sort by similarity descending
        scored_bills.sort(key=lambda x: x[0], reverse=True)
        top_items = scored_bills[:limit]
        
        if not top_items:
            return ""
            
        context_lines = []
        context_lines.append("\nRETRIEVED RELEVANT BILLS (RAG CONTEXT):")
        for score, item in top_items:
            context_lines.append(f"- Bill #{item['bill_id']} (Similarity: {score:.3f}): {item['text']}")
        return "\n".join(context_lines) + "\n"

    def clear_store(self) -> None:
        self.indexed_store.clear()

rag_agent = RagAgent()
