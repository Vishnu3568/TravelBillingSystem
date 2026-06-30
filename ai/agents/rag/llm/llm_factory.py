from .llm_interface import BaseLlmClient
from .gemini_llm import GeminiLlmClient

class LlmFactory:
    _client_instance = GeminiLlmClient()
    
    @staticmethod
    def get_llm_client() -> BaseLlmClient:
        return LlmFactory._client_instance
