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
            key = settings.GEMINI_API_KEY
            # Only use gemini if key is present and not the default mock placeholder
            if key and key != "AIzaSyDmncG2GztNQgfJhXuGIRE1ej2Q9ghEVoc" and not key.startswith("YOUR_"):
                strategy = "gemini"
            else:
                strategy = "mock"
                
        if strategy.lower() == "gemini":
            if not EmbeddingsFactory._gemini_client:
                EmbeddingsFactory._gemini_client = GeminiEmbeddings()
            return EmbeddingsFactory._gemini_client
            
        return EmbeddingsFactory._mock_client

