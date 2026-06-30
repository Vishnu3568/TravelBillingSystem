import os
from pydantic import BaseModel

class Settings(BaseModel):
    PORT: int = int(os.getenv("RAG_PORT", 9002))
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "faiss")
    
    # Chunking config
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 500))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 50))
    
    # Retrieval config
    TOP_K: int = int(os.getenv("TOP_K", 5))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", 0.5))
    RERANKER_ENABLED: bool = os.getenv("RERANKER_ENABLED", "false").lower() == "true"
    
    # Cache settings
    CACHE_DIR: str = os.getenv("CACHE_DIR", "./.cache")
    LLM_CACHE_ENABLED: bool = os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true"

settings = Settings()
