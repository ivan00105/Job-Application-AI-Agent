"""
Qdrant service for vector storage and search.
Handles job embeddings storage in Qdrant.
"""
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from .config import get_scraper_settings
import logging

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for Qdrant vector database operations"""
    
    def __init__(self):
        self.settings = get_scraper_settings()
        
        # Initialize Qdrant client
        if self.settings.qdrant_path:
            self.client = QdrantClient(path=self.settings.qdrant_path)
        else:
            self.client = QdrantClient(
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port
            )
        
        self.vector_size = self.settings.embedding_dim
        self.collection_name = self.settings.qdrant_collection_name
    
    def collection_exists(self, collection_name: Optional[str] = None) -> bool:
        """Check if a collection exists"""
        name = collection_name or self.collection_name
        try:
            self.client.get_collection(name)
            return True
        except Exception:
            return False
    
    def create_collection(self, collection_name: Optional[str] = None) -> bool:
        """Create a new collection if it doesn't exist"""
        name = collection_name or self.collection_name
        
        if self.collection_exists(name):
            logger.info(f"Collection '{name}' already exists")
            return True
        
        try:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection '{name}'")
            return True
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            return False
    
    def ensure_collection(self, collection_name: Optional[str] = None) -> bool:
        """Ensure collection exists, create if it doesn't"""
        name = collection_name or self.collection_name
        if not self.collection_exists(name):
            return self.create_collection(name)
        return True
    
    def save_job_data(
        self,
        job_id: str,
        vector: List[float],
        payload: Dict[str, Any],
        collection_name: Optional[str] = None
    ) -> bool:
        """
        Save or update job data in Qdrant.
        
        Args:
            job_id: Unique job identifier (can be UUID string or integer)
            vector: Embedding vector
            payload: Job metadata (title, company, location, etc.)
            collection_name: Optional collection name (uses default if not provided)
        """
        name = collection_name or self.collection_name
        
        # Ensure collection exists
        if not self.ensure_collection(name):
            logger.error(f"Failed to ensure collection '{name}' exists")
            return False
        
        try:
            # Convert job_id to integer if it's a UUID string (use hash)
            point_id = self._job_id_to_point_id(job_id)
            
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
            
            self.client.upsert(
                collection_name=name,
                points=[point]
            )
            
            logger.debug(f"Saved job to Qdrant: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving job to Qdrant: {str(e)}")
            return False
    
    def _job_id_to_point_id(self, job_id: str) -> int:
        """
        Convert job ID (UUID string) to integer point ID for Qdrant.
        Uses a consistent hash function to ensure the same job_id always maps to the same point_id.
        """
        import hashlib
        # Use SHA256 hash for consistency (same job_id always produces same point_id)
        hash_obj = hashlib.sha256(job_id.encode('utf-8'))
        # Convert to integer (use first 16 hex digits to avoid overflow)
        return int(hash_obj.hexdigest()[:16], 16) % (10 ** 18)
    
    def delete_job_data(
        self,
        job_id: str,
        collection_name: Optional[str] = None
    ) -> bool:
        """Delete job data from Qdrant"""
        name = collection_name or self.collection_name
        
        try:
            point_id = self._job_id_to_point_id(job_id)
            self.client.delete(
                collection_name=name,
                points_selector=[point_id]
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting job from Qdrant: {str(e)}")
            return False
    
    def find_similar_jobs(
        self,
        vector: List[float],
        similarity_threshold: float = 0.95,
        limit: int = 5,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar jobs using vector similarity search.
        
        Args:
            vector: Embedding vector of the job to check
            similarity_threshold: Minimum similarity score (0.0-1.0, higher = more similar)
            limit: Maximum number of results to return
            collection_name: Optional collection name
            
        Returns:
            List of similar jobs with their scores and job_ids
        """
        name = collection_name or self.collection_name
        
        if not self.collection_exists(name):
            return []
        
        try:
            # Search for similar vectors
            search_results = self.client.search(
                collection_name=name,
                query_vector=vector,
                limit=limit,
                score_threshold=similarity_threshold
            )
            
            results = []
            for result in search_results:
                payload = result.payload or {}
                results.append({
                    "job_id": payload.get("job_id"),
                    "score": result.score,  # Similarity score (0.0-1.0)
                    "title": payload.get("title", ""),
                    "company": payload.get("company", ""),
                    "location": payload.get("location", ""),
                    "point_id": result.id
                })
            
            return results
        except Exception as e:
            logger.error(f"Error searching for similar jobs: {str(e)}")
            return []
    
    def find_duplicate_job(
        self,
        vector: List[float],
        title: str,
        company: str,
        location: Optional[str] = None,
        similarity_threshold: float = 0.95,
        collection_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Find if a duplicate job exists using vector similarity and metadata matching.
        
        Args:
            vector: Embedding vector of the job to check
            title: Job title
            company: Company name
            location: Job location (optional, for additional matching)
            similarity_threshold: Minimum similarity score (default: 0.95 = 95% similar)
            collection_name: Optional collection name
            
        Returns:
            Existing job_id if duplicate found, None otherwise
        """
        # Find similar jobs using vector search
        similar_jobs = self.find_similar_jobs(
            vector=vector,
            similarity_threshold=similarity_threshold,
            limit=10,  # Check top 10 similar jobs
            collection_name=collection_name
        )
        
        if not similar_jobs:
            return None
        
        # Check if any similar job matches title, company, and optionally location
        title_lower = title.lower().strip()
        company_lower = company.lower().strip()
        location_lower = location.lower().strip() if location else None
        
        for job in similar_jobs:
            job_title = job.get("title", "").lower().strip()
            job_company = job.get("company", "").lower().strip()
            job_location = job.get("location", "").lower().strip() if job.get("location") else None
            
            # Check if title and company match (fuzzy matching)
            title_match = title_lower == job_title or (
                title_lower in job_title or job_title in title_lower
            )
            company_match = company_lower == job_company or (
                company_lower in job_company or job_company in company_lower
            )
            
            # If location is provided, also check location match
            if location_lower:
                location_match = location_lower == job_location or (
                    location_lower in job_location or job_location in location_lower
                ) if job_location else False
            else:
                location_match = True  # If no location provided, don't require location match
            
            # If title, company match, and (location matches or not required), it's a duplicate
            if title_match and company_match and location_match:
                job_id = job.get("job_id")
                logger.info(
                    f"Found duplicate job via vector search: {title} at {company} "
                    f"(similarity: {job['score']:.3f}, existing ID: {job_id})"
                )
                return str(job_id) if job_id else None
        
        return None
    
    def get_collection_info(self, collection_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get collection information"""
        name = collection_name or self.collection_name
        
        try:
            collection = self.client.get_collection(name)
            return {
                "name": name,
                "points_count": collection.points_count,
                "vectors_count": collection.vectors_count,
                "config": {
                    "vector_size": collection.config.params.vectors.size,
                    "distance": collection.config.params.vectors.distance
                }
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return None

