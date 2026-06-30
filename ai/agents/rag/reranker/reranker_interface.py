import abc
from typing import List, Dict, Any

class BaseReranker(abc.ABC):
    @abc.abstractmethod
    def rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Reranks query match candidates and returns them sorted by new scores.
        """
        pass
