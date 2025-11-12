import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Qdrant settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_PATH: Optional[str] = None  # For local mode, set to a path like "./qdrant_db"
    
    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EMBEDDING_MODEL: str = "bge-m3"
    
    # Embedding dimensions (BGE-M3 produces 1024-dimensional embeddings)
    EMBEDDING_DIM: int = 1024
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

