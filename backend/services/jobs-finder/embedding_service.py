"""
Embedding service for generating job search query embeddings.
Supports Ollama and OpenAI embedding models.
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
                self.use_openai = os.getenv("USE_OPENAI_EMBEDDINGS", "false").lower() == "true"
                self.openai_api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
                self.openai_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            except Exception as e:
                logger.warning(f"Failed to load config, using environment variables: {str(e)}")
                self._load_from_env()
        else:
            self._load_from_env()
    
    def _load_from_env(self):
        """Load settings from environment variables"""
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3")
        self.use_openai = os.getenv("USE_OPENAI_EMBEDDINGS", "false").lower() == "true"
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if self.use_openai and self.openai_api_key:
            return await self._generate_openai_embedding(text)
        else:
            try:
                return await self._generate_ollama_embedding(text)
            except (ConnectionError, ValueError) as e:
                # If Ollama fails and OpenAI is available, try OpenAI as fallback
                if self.openai_api_key and not self.use_openai:
                    logger.warning(
                        f"Ollama embedding failed, attempting OpenAI fallback: {str(e)}"
                    )
                    try:
                        return await self._generate_openai_embedding(text)
                    except Exception as openai_err:
                        logger.error(f"OpenAI fallback also failed: {str(openai_err)}")
                        raise e  # Raise original Ollama error
                raise
    
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
            # If OpenAI is available, suggest using it as fallback
            if self.openai_api_key:
                logger.warning(
                    f"Ollama unavailable. Consider setting USE_OPENAI_EMBEDDINGS=true "
                    f"to use OpenAI embeddings as fallback."
                )
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
    
    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.openai_model,
                        "input": text
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {str(e)}")
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

