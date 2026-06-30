import abc
from typing import List, Dict, Any

class BaseVectorStore(abc.ABC):
    @abc.abstractmethod
    def add_embeddings(
        self, 
        doc_id: str, 
        chunk_id: str, 
        vector: List[float], 
        text: str, 
        metadata: Dict[str, Any]
    ):
        """
        Adds a single embedding and its associated metadata to the store.
        """
        pass

    @abc.abstractmethod
    def similarity_search(
        self, 
        query_vector: List[float], 
        top_k: int, 
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top K chunks matching the query vector, optionally filtered by metadata.
        Returns a list of dicts: {"doc_id", "chunk_id", "text", "metadata", "score"}.
        """
        pass

    @abc.abstractmethod
    def delete_document(self, doc_id: str):
        """
        Deletes all chunks/vectors matching the document ID.
        """
        pass

    @abc.abstractmethod
    def save(self, file_path: str):
        """
        Saves the index to disk.
        """
        pass

    @abc.abstractmethod
    def load(self, file_path: str):
        """
        Loads the index from disk.
        """
        pass
