"""
Supabase database client and connection management.
"""
from supabase import create_client, Client
from functools import lru_cache
from config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """Get singleton Supabase client instance"""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)


# Convenience function for direct access
def get_db() -> Client:
    """Get database client for dependency injection"""
    return get_supabase_client()
