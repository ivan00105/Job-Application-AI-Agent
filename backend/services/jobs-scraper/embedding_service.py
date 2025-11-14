"""
Embedding service for generating job description embeddings.
Supports Ollama and OpenAI embedding models.
"""
import httpx
from typing import List
from .config import get_scraper_settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings"""
    
    def __init__(self):
        self.settings = get_scraper_settings()
        self.base_url = self.settings.ollama_base_url
        self.model = self.settings.ollama_embedding_model
        self.use_openai = self.settings.use_openai_embeddings
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if self.use_openai and self.settings.openai_api_key:
            return await self._generate_openai_embedding(text)
        else:
            return await self._generate_ollama_embedding(text)
    
    async def _generate_ollama_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
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
        except Exception as e:
            logger.error(f"Error generating Ollama embedding: {str(e)}")
            raise
    
    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.settings.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.settings.openai_embedding_model,
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
        """
        Generate embeddings for multiple texts.
        Processes sequentially to avoid overwhelming the service.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for i, text in enumerate(texts):
            try:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)
                if (i + 1) % 10 == 0:
                    logger.info(f"Generated {i + 1}/{len(texts)} embeddings")
            except Exception as e:
                logger.error(f"Error generating embedding for text {i}: {str(e)}")
                # Use zero vector as fallback
                dim = self.settings.embedding_dim
                embeddings.append([0.0] * dim)
        
        return embeddings

