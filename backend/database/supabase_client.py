"""
Supabase database client and connection management.
Supports both Supabase and direct PostgreSQL connections.
"""
from functools import lru_cache
from config import get_settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Optional Supabase import - only import if available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None  # type: ignore
    logger.warning("Supabase package not installed. Database features will be limited.")


@lru_cache()
def get_supabase_client() -> Optional[Client]:
    """Get singleton Supabase client instance (optional)"""
    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase package not available. Install with: pip install supabase")
        return None
    
    settings = get_settings()
    
    if not settings.supabase_url or not settings.supabase_key:
        logger.warning("Supabase not configured. Some endpoints may not work.")
        return None
    
    try:
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        return None


# Convenience function for direct access
def get_db() -> Optional[Client]:
    """Get database client for dependency injection"""
    client = get_supabase_client()
    if client is None:
        logger.warning("Database client not available. Ensure Supabase or PostgreSQL is configured.")
    return client
