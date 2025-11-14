"""
Qdrant service for vector storage and search.
Handles job embeddings storage in Qdrant for job search functionality.
"""
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, MatchValue
)
# Try to import from backend.config, fallback to direct config import
try:
    from backend.config import get_settings
except ImportError:
    try:
        from config import get_settings
    except ImportError:
        # If config doesn't have get_settings, we'll use os.getenv directly
        get_settings = None
import os
import logging

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for Qdrant vector database operations for job search"""
    
    def __init__(self):
        # Get Qdrant settings from environment (with fallback to defaults)
        settings = get_settings() if get_settings else None
        qdrant_host = os.getenv("QDRANT_HOST", getattr(settings, "qdrant_host", "localhost") if settings else "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", getattr(settings, "qdrant_port", 6333) if settings else 6333))
        qdrant_path = os.getenv("QDRANT_PATH", getattr(settings, "qdrant_path", None) if settings else None)
        embedding_dim = int(os.getenv("EMBEDDING_DIM", getattr(settings, "embedding_dim", 1024) if settings else 1024))
        
        # Initialize Qdrant client
        if qdrant_path:
            self.client = QdrantClient(path=qdrant_path)
        else:
            self.client = QdrantClient(
                host=qdrant_host,
                port=qdrant_port
            )
        
        self.vector_size = embedding_dim
    
    # Collection Management
    def create_collection(self, collection_name: str) -> bool:
        """Create a new collection."""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                raise ValueError(f"Collection '{collection_name}' already exists")
            raise
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        collections = self.client.get_collections()
        return [col.name for col in collections.collections]
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        try:
            self.client.get_collection(collection_name)
            return True
        except:
            return False
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information."""
        collection = self.client.get_collection(collection_name)
        return {
            "name": collection_name,
            "points_count": collection.points_count,
            "vectors_count": collection.vectors_count,
            "config": {
                "vector_size": collection.config.params.vectors.size,
                "distance": collection.config.params.vectors.distance
            }
        }
    
    # Data Management
    def save_job_data(
        self, 
        collection_name: str, 
        job_id: int, 
        vector: List[float], 
        payload: Dict[str, Any]
    ) -> bool:
        """Save or update job data in collection."""
        if not self.collection_exists(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist")
        
        point = PointStruct(
            id=job_id,
            vector=vector,
            payload=payload
        )
        
        self.client.upsert(collection_name=collection_name, points=[point])
        return True
    
    def search_jobs(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar jobs and rank by similarity."""
        if not self.collection_exists(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist")
        
        # Build filter if conditions provided
        search_filter = None
        if filter_conditions:
            must_conditions = []
            for key, value in filter_conditions.items():
                must_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            search_filter = Filter(must=must_conditions)
        
        # Perform search
        search_results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=search_filter
        )
        
        # Format results with similarity scores (sorted by score descending)
        results = []
        for result in search_results:
            results.append({
                "id": result.id,
                "score": result.score,  # Similarity score (higher is more similar)
                "payload": result.payload
            })
        
        return results
    
    def delete_job_data(
        self, 
        collection_name: str, 
        job_ids: List[int]
    ) -> bool:
        """Delete job data by IDs."""
        if not self.collection_exists(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist")
        
        self.client.delete(
            collection_name=collection_name,
            points_selector=job_ids
        )
        return True
    
    def get_job_by_id(
        self, 
        collection_name: str, 
        job_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID."""
        if not self.collection_exists(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist")
        
        result = self.client.retrieve(
            collection_name=collection_name,
            ids=[job_id],
            with_payload=True,
            with_vectors=False
        )
        
        if result:
            point = result[0]
            return {
                "id": point.id,
                "payload": point.payload
            }
        return None


# Singleton instance
qdrant_service = QdrantService()

