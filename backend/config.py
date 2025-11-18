"""
Configuration settings for the application.
Loads environment variables and provides centralized config access.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # PostgreSQL (for direct PostgreSQL connection)
    postgres_host: Optional[str] = None
    postgres_port: int = 5432
    postgres_db: Optional[str] = None  # Added for compatibility
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
    
    # External/Public URL (for reverse proxy or remote access)
    # This is the URL that clients should use to access the API
    # Examples:
    #   - Direct access: http://YOUR_SERVER_IP:8000
    #   - Reverse proxy: https://your-domain.com
    #   - Local dev: http://localhost:8000
    external_url: Optional[str] = None  # If None, will be auto-generated from host/port
    
    # Reverse Proxy Configuration
    trusted_proxy_hosts: str = "*"  # Comma-separated list of trusted proxy IPs, or "*" for all
    root_path: Optional[str] = None  # Root path if app is behind a subpath (e.g., "/api")
    allowed_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"  # Comma-separated list of allowed origins

    # Qdrant Configuration (for job search)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_path: Optional[str] = None
    qdrant_collection_name: str = "job_data"

    # JobsEngine Service (for compatibility with services)
    jobsengine_url: Optional[str] = None
    
    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"  # For CV parser compatibility
    ollama_chat_model: str = "llama3"  # For LLM generation
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "bge-m3"
    embedding_dim: int = 1024

    # LLM Configuration (OpenRouter)
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-oss-120b"
    enable_llm_query_enhancement: bool = True
    
    # CV Generation Configuration
    use_agentic_cv_generation: bool = True  # Use agentic multi-step reasoning for CV generation

    # Scraping Configuration
    scrape_sites: str = '["indeed", "linkedin", "google"]'
    scrape_results_wanted: int = 1000
    scrape_hours_old: int = 720

    # Processing Configuration
    batch_size: int = 10
    enable_duplicate_detection: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def get_base_url(settings: Optional[Settings] = None) -> str:
    """
    Get the base URL for the API.
    Uses external_url if set, otherwise constructs from host/port.
    """
    if settings is None:
        settings = get_settings()
    
    if settings.external_url:
        # Remove trailing slash if present
        return settings.external_url.rstrip('/')
    
    # Auto-generate from host/port
    if settings.host == "0.0.0.0":
        # For 0.0.0.0, use localhost for local access
        return f"http://localhost:{settings.port}"
    else:
        return f"http://{settings.host}:{settings.port}"
