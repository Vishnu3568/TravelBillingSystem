import abc
from typing import List

class BaseEmbeddings(abc.ABC):
    @abc.abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Generates embedding vector for a single query string.
        """
        pass

    @abc.abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embedding vectors for a list of document strings.
        """
        pass
