"""
Embedding service for generating job search query embeddings.
Uses Ollama embedding models.
"""
import httpx
from typing import List
import os
import logging

logger = logging.getLogger(__name__)

# Try to import config, fallback to os.getenv
try:
    from backend.config import get_settings
    _use_config = True
except ImportError:
    try:
        from config import get_settings
        _use_config = True
    except ImportError:
        _use_config = False


class EmbeddingService:
    """Service for generating embeddings for job search"""
    
    def __init__(self):
        # Get settings from config if available, otherwise from environment
        if _use_config:
            try:
                settings = get_settings()
                self.base_url = settings.ollama_base_url or "http://localhost:11434"
                self.model = settings.ollama_embedding_model or "bge-m3"
            except Exception as e:
                logger.warning(f"Failed to load config, using environment variables: {str(e)}")
                self._load_from_env()
        else:
            self._load_from_env()
    
    def _load_from_env(self):
        """Load settings from environment variables"""
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text using Ollama."""
        return await self._generate_ollama_embedding(text)
    
    async def _generate_ollama_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["embedding"]
        except httpx.ConnectError as e:
            error_msg = (
                f"Failed to connect to Ollama at {self.base_url}. "
                f"Please ensure Ollama is running and accessible. "
                f"Error: {str(e)}"
            )
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_msg = (
                f"Ollama API returned error status {e.response.status_code}: {e.response.text}. "
                f"Model: {self.model}, URL: {self.base_url}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except Exception as e:
            error_msg = f"Error generating Ollama embedding: {str(e)}. URL: {self.base_url}, Model: {self.model}"
            logger.error(error_msg)
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings


# Singleton instance
embedding_service = EmbeddingService()

