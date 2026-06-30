import hashlib
from typing import Dict, Any, Optional

class SemanticCache:
    def __init__(self):
        self.embedding_cache: Dict[str, Any] = {}
        self.llm_cache: Dict[str, Any] = {}
        self.search_cache: Dict[str, Any] = {}
        
    def get_embedding(self, text: str) -> Optional[Any]:
        key = self._hash(text)
        return self.embedding_cache.get(key)
        
    def set_embedding(self, text: str, vector: Any):
        key = self._hash(text)
        self.embedding_cache[key] = vector
        
    def get_llm(self, prompt: str) -> Optional[str]:
        key = self._hash(prompt)
        return self.llm_cache.get(key)
        
    def set_llm(self, prompt: str, response: str):
        key = self._hash(prompt)
        self.llm_cache[key] = response

    def _hash(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

semantic_cache = SemanticCache()
