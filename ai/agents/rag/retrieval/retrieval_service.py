import time
from typing import List, Dict, Any
from vectorstore import VectorStoreFactory
from embeddings import EmbeddingsFactory
from config import settings


class RetrievalService:
    @staticmethod
    def retrieve(
        query: str, 
        top_k: int = None, 
        threshold: float = None, 
        filter_metadata: dict = None
    ) -> List[Dict[str, Any]]:
        if top_k is None:
            top_k = settings.TOP_K
        if threshold is None:
            threshold = settings.SIMILARITY_THRESHOLD
            
        embedder = EmbeddingsFactory.get_embeddings()
        query_vector = embedder.embed_query(query)
        
        store = VectorStoreFactory.get_vector_store()
        raw_results = store.similarity_search(query_vector, top_k=top_k * 2, filter_metadata=filter_metadata)
        
        filtered_results = [r for r in raw_results if r["score"] >= threshold]
        return filtered_results[:top_k]
