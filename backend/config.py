"""
Configuration settings for the application.
Loads environment variables and provides centralized config access.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Supabase (optional - for backward compatibility)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # PostgreSQL (for direct PostgreSQL connection)
    postgres_host: Optional[str] = None
    postgres_port: int = 5432
    postgres_database: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_connection_string: Optional[str] = None

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 24

    # AI API Keys (optional for now)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Qdrant Configuration (for job search)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_path: Optional[str] = None
    qdrant_collection_name: str = "job_data"

    # Embedding Service Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "bge-m3"
    embedding_dim: int = 1024

    # LLM Configuration (OpenRouter)
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openrouter/gpt-oss-120b"
    enable_llm_query_enhancement: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
