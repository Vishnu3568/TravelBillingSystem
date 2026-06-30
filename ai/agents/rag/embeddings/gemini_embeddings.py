import logging
import requests
from typing import List
from .embeddings_interface import BaseEmbeddings
from config import settings


logger = logging.getLogger("gemini_embeddings")

class GeminiEmbeddings(BaseEmbeddings):
    def __init__(self, model_name: str = "embedding-001"):
        self.model_name = model_name
        self.api_key = settings.GEMINI_API_KEY
        
    def embed_query(self, text: str) -> List[float]:
        vectors = self.embed_documents([text])
        return vectors[0] if vectors else [0.0] * 768

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            logger.warning("Gemini API key is not configured. Returning default zero vectors.")
            return [[0.0] * 768 for _ in texts]
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:embedContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        embeddings = []
        for text in texts:
            payload = {
                "content": {
                    "parts": [{"text": text}]
                }
            }
            try:
                res = requests.post(url, json=payload, headers=headers, timeout=20)
                res.raise_for_status()
                val = res.json()["embedding"]["values"]
                embeddings.append(val)
            except Exception as e:
                logger.error(f"Failed to fetch Gemini embedding: {e}")
                embeddings.append([0.0] * 768)
        return embeddings
