"""
Configuration settings for the application.
Loads environment variables and provides centralized config access.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Supabase
    supabase_url: str
    supabase_key: str

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

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
