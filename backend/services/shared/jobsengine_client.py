"""JobsEngine client for vector search operations via Qdrant"""
import httpx
from typing import List, Dict, Any, Optional
from config import get_settings


class JobsEngineClient:
    """Client for JobsEngine service (Qdrant + Embeddings)"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.jobsengine_url
        self.timeout = httpx.Timeout(60.0)
    
    async def create_collection(self, collection_name: str) -> Dict[str, Any]:
        """Create a new Qdrant collection"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/collections/",
                json={"name": collection_name}
            )
            response.raise_for_status()
            return response.json()
    
    async def list_collections(self) -> List[str]:
        """List all Qdrant collections"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/collections/")
            response.raise_for_status()
            return response.json()
    
    async def save_job_embedding(
        self, 
        collection_name: str,
        job_id: str,
        text: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save job data and generate embedding"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/jobs/{collection_name}/save",
                json={
                    "job_id": job_id,
                    "text": text,
                    "payload": payload or {}
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def save_cv_embedding(
        self,
        collection_name: str,
        cv_id: str,
        text: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save CV data and generate embedding"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/jobs/{collection_name}/save",
                json={
                    "job_id": cv_id,
                    "text": text,
                    "payload": payload or {}
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def search_similar_jobs(
        self,
        collection_name: str,
        query_text: str,
        limit: int = 20,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar items using text query"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/jobs/{collection_name}/search",
                json={
                    "query": query_text,
                    "limit": limit,
                    "score_threshold": score_threshold,
                    "filter_conditions": filter_conditions
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
    
    async def save_agent_memory_embedding(
        self,
        collection_name: str,
        memory_id: int,
        question_text: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save agent memory question and generate embedding"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/jobs/{collection_name}/save",
                json={
                    "job_id": memory_id,
                    "text": question_text,
                    "payload": payload or {}
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def search_agent_memory(
        self,
        collection_name: str,
        question_text: str,
        user_id: str,
        context_key: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search agent memory for similar questions"""
        filter_conditions = {"user_id": user_id}
        if context_key:
            filter_conditions["context_key"] = context_key
        
        return await self.search_similar_jobs(
            collection_name=collection_name,
            query_text=question_text,
            limit=limit,
            score_threshold=score_threshold,
            filter_conditions=filter_conditions
        )
    
    async def delete_job_data(
        self,
        collection_name: str,
        job_ids: List[str]
    ) -> Dict[str, Any]:
        """Delete data from Qdrant"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.base_url}/jobs/{collection_name}/delete",
                json={"job_ids": job_ids}
            )
            response.raise_for_status()
            return response.json()


_jobsengine_client: Optional[JobsEngineClient] = None


def get_jobsengine_client() -> JobsEngineClient:
    """Get singleton JobsEngine client instance"""
    global _jobsengine_client
    if _jobsengine_client is None:
        _jobsengine_client = JobsEngineClient()
    return _jobsengine_client

