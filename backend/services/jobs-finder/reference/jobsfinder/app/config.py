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
    
    # OpenRouter LLM settings
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openrouter/gpt-oss-120b"
    OPENROUTER_TEMPERATURE: float = 0.7
    OPENROUTER_MAX_TOKENS: int = 200
    OPENROUTER_HTTP_REFERER: Optional[str] = None  # Optional: your app URL for OpenRouter tracking
    
    # LLM query enhancement (enable/disable)
    ENABLE_LLM_QUERY_ENHANCEMENT: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

