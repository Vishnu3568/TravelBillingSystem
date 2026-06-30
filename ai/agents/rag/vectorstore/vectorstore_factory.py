from .vectorstore_interface import BaseVectorStore
from .in_memory_store import InMemoryVectorStore

class VectorStoreFactory:
    _store_instance = InMemoryVectorStore()
    
    @staticmethod
    def get_vector_store() -> BaseVectorStore:
        return VectorStoreFactory._store_instance
