"""
Configuration settings for the job scraping service.
Loads environment variables from .env file in the root directory.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache


class JobScraperSettings(BaseSettings):
    """Job scraper settings loaded from environment variables"""
    
    # PostgreSQL Configuration (Direct Connection)
    postgres_host: str
    postgres_port: int = 5432
    # Support both POSTGRES_DATABASE and POSTGRES_DB
    postgres_database: Optional[str] = Field(default=None, alias="POSTGRES_DB")
    postgres_user: str
    postgres_password: str
    # Optional: PostgreSQL connection string (alternative to individual parameters)
    postgres_connection_string: Optional[str] = None
    
    @field_validator('postgres_database', mode='before')
    @classmethod
    def get_database_name(cls, v):
        # Support both POSTGRES_DATABASE and POSTGRES_DB
        import os
        return os.getenv('POSTGRES_DATABASE') or os.getenv('POSTGRES_DB') or v
    
    @field_validator('postgres_database')
    @classmethod
    def validate_database(cls, v):
        if v is None:
            raise ValueError("postgres_database is required (set POSTGRES_DATABASE or POSTGRES_DB)")
        return v
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_path: Optional[str] = None  # For local mode, set to a path like "./qdrant_db"
    
    # Embedding Service Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "bge-m3"
    embedding_dim: int = 1024  # BGE-M3 produces 1024-dimensional embeddings
    
    # Alternative: OpenAI/Anthropic embeddings (optional)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    use_openai_embeddings: bool = False
    openai_embedding_model: str = "text-embedding-3-small"  # 1536 dimensions
    
    # Scraping Configuration
    scrape_sites: List[str] = ["indeed", "linkedin", "google"]
    scrape_results_wanted: int = 1000
    scrape_hours_old: int = 720  # 30 days
    
    # Collection name for Qdrant
    qdrant_collection_name: str = "job_data"
    
    # Processing Configuration
    batch_size: int = 10  # Batch size for embedding generation
    enable_duplicate_detection: bool = True
    use_vector_duplicate_detection: bool = True  # Use Qdrant vector search for duplicate detection
    duplicate_similarity_threshold: float = 0.95  # Similarity threshold for duplicate detection (0.0-1.0)
    
    # Calculate .env file path
    _config_dir = os.path.dirname(__file__)
    _backend_env = os.path.join(os.path.dirname(os.path.dirname(_config_dir)), ".env")
    _root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_config_dir)))), ".env")
    _env_file = _backend_env if os.path.exists(_backend_env) else (_root_env if os.path.exists(_root_env) else _backend_env)
    
    model_config = {
        "env_file": _env_file,
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra fields like POSTGRES_DB
    }


@lru_cache()
def get_scraper_settings() -> JobScraperSettings:
    """Get cached scraper settings instance"""
    return JobScraperSettings()

