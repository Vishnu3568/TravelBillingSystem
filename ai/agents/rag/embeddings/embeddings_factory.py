from .embeddings_interface import BaseEmbeddings
from .gemini_embeddings import GeminiEmbeddings
from .mock_embeddings import MockEmbeddings
from config import settings


class EmbeddingsFactory:
    _gemini_client = None
    _mock_client = MockEmbeddings()

    @staticmethod
    def get_embeddings(strategy: str = None) -> BaseEmbeddings:
        if strategy is None:
            if settings.GEMINI_API_KEY:
                strategy = "gemini"
            else:
                strategy = "mock"
                
        if strategy.lower() == "gemini":
            if not EmbeddingsFactory._gemini_client:
                EmbeddingsFactory._gemini_client = GeminiEmbeddings()
            return EmbeddingsFactory._gemini_client
            
        return EmbeddingsFactory._mock_client
