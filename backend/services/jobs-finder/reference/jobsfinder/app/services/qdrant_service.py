from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, MatchValue
)
from app.config import settings

class QdrantService:
    def __init__(self):
        if settings.QDRANT_PATH:
            self.client = QdrantClient(path=settings.QDRANT_PATH)
        else:
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )
        self.vector_size = settings.EMBEDDING_DIM
    
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
    
    def rename_collection(self, old_name: str, new_name: str) -> bool:
        """Rename a collection by creating new one and migrating data."""
        if not self.collection_exists(old_name):
            raise ValueError(f"Collection '{old_name}' does not exist")
        
        if self.collection_exists(new_name):
            raise ValueError(f"Collection '{new_name}' already exists")
        
        # Get all points from old collection
        scroll_result = self.client.scroll(
            collection_name=old_name,
            limit=10000,
            with_payload=True,
            with_vectors=True
        )
        
        points = scroll_result[0]
        if not points:
            # Empty collection, just create new one
            self.create_collection(new_name)
            self.client.delete_collection(old_name)
            return True
        
        # Create new collection
        self.create_collection(new_name)
        
        # Migrate points
        point_structs = [
            PointStruct(
                id=point.id,
                vector=point.vector,
                payload=point.payload
            )
            for point in points
        ]
        
        self.client.upsert(collection_name=new_name, points=point_structs)
        
        # Delete old collection
        self.client.delete_collection(old_name)
        return True
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        if not self.collection_exists(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist")
        
        self.client.delete_collection(collection_name)
        return True
    
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

qdrant_service = QdrantService()

