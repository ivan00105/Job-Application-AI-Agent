"""
Job listings API endpoints.
Handles job search, filtering, and retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
import os
import sys

from models.job import Job, JobSearchParams, JobDataSearch, JobSearchResult, SearchResponse
from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient

# Import from jobs-finder directory (handles hyphen in directory name)
services_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'jobs-finder')
sys.path.insert(0, services_path)
from qdrant_service import qdrant_service
from embedding_service import embedding_service
from llm_service import llm_service

router = APIRouter()


@router.get("/", response_model=dict)
async def search_jobs(
    query: Optional[str] = Query(None, description="Search query"),
    location: Optional[str] = Query(None, description="Job location"),
    min_salary: Optional[int] = Query(None, description="Minimum salary"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Search and filter jobs using PostgreSQL + Qdrant vector search.
    """
    conditions = ["is_active = TRUE"]
    params = []
    param_count = 1

    if location:
        conditions.append(f"location ILIKE ${param_count}")
        params.append(f"%{location}%")
        param_count += 1

    if min_salary:
        conditions.append(f"salary_min >= ${param_count}")
        params.append(min_salary)
        param_count += 1

    if query:
        conditions.append(f"(title ILIKE ${param_count} OR description ILIKE ${param_count} OR company ILIKE ${param_count})")
        params.append(f"%{query}%")
        param_count += 1

    where_clause = " AND ".join(conditions)
    count_query = f"SELECT COUNT(*) FROM jobs WHERE {where_clause}"
    search_query = f"SELECT * FROM jobs WHERE {where_clause} ORDER BY posted_date DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
    params.extend([limit, offset])

    total = await db.fetch_val(count_query, *params[:-2])
    jobs = await db.fetch_all(search_query, *params)

    return {
        "jobs": [dict(job) for job in jobs],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/{job_id}", response_model=dict)
async def get_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get detailed information about a specific job.
    """
    query = "SELECT * FROM jobs WHERE id = $1"
    job = await db.fetch_one(query, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return dict(job)


def filter_job_results(
    results: List[Dict[str, Any]],
    company_filter: Optional[str] = None,
    min_experience_years: Optional[int] = None,
    certifications: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Post-process and filter job search results based on structured criteria.
    
    Args:
        results: List of search results from Qdrant
        company_filter: Filter by company name
        min_experience_years: Minimum years of experience required
        certifications: List of certifications/skills to filter by
        limit: Maximum number of results to return
        
    Returns:
        Filtered list of results
    """
    filtered_results = []
    
    for result in results:
        payload = result.get('payload', {})
        
        # Build searchable text from job data
        job_text = (
            payload.get('job_title', '') + ' ' +
            payload.get('job_responsibilities', '') + ' ' +
            payload.get('job_requirements', '') + ' ' +
            payload.get('description', '')
        ).lower()
        
        # Filter by company if specified
        if company_filter:
            company = payload.get('company', '').lower()
            if company_filter.lower() not in company:
                continue
        
        # Filter by certifications/skills if specified
        if certifications:
            has_cert = any(
                cert.lower() in job_text 
                for cert in certifications
            )
            if not has_cert:
                continue
        
        # Filter by minimum experience if specified
        if min_experience_years:
            # Try to extract years from requirements text
            experience_keywords = [
                f"{min_experience_years} years",
                f"{min_experience_years}+ years",
                f"{min_experience_years} year",
                f"{min_experience_years}+ year",
                f"minimum {min_experience_years} years",
                f"at least {min_experience_years} years",
                f"min {min_experience_years} years"
            ]
            
            # Check if any experience requirement matches
            has_experience = any(
                keyword in job_text 
                for keyword in experience_keywords
            )
            
            # Also check for higher experience levels (up to 5 years more)
            if not has_experience:
                for years in range(min_experience_years + 1, min_experience_years + 6):
                    if (f"{years} years" in job_text or 
                        f"{years}+ years" in job_text or
                        f"{years} year" in job_text):
                        has_experience = True
                        break
            
            # If we can't find explicit experience and requirement is high, be strict
            if not has_experience and min_experience_years > 3:
                continue
        
        filtered_results.append(result)
    
    # Limit results after filtering
    return filtered_results[:limit]


@router.post("/search", response_model=SearchResponse)
async def search_jobs_vector(
    search: JobDataSearch,
    current_user: dict = Depends(get_current_user)
):
    """
    Search for jobs using vector similarity search.
    Uses LLM to enhance the search query for better results.
    Supports structured filtering by company, experience, and certifications.
    
    This endpoint performs semantic search on job embeddings stored in Qdrant.
    """
    try:
        # Get collection name (default to "job_data" if not specified)
        collection_name = search.collection_name or os.getenv("QDRANT_COLLECTION_NAME", "job_data")
        
        # Enhance query using LLM if enabled
        enhanced_query = search.query
        use_llm = search.use_llm_enhancement
        if use_llm is None:
            # Check global setting
            enable_llm = os.getenv("ENABLE_LLM_QUERY_ENHANCEMENT", "true").lower() == "true"
            use_llm = enable_llm
        
        if use_llm:
            enhanced_query = await llm_service.enhance_job_search_query(search.query)
        
        # Generate embedding for enhanced query
        query_vector = await embedding_service.generate_embedding(enhanced_query)
        
        # Build filter conditions for Qdrant (company filter can be done at Qdrant level)
        filter_conditions = search.filter_conditions or {}
        if search.company_filter:
            filter_conditions['company'] = search.company_filter
        
        # Search in Qdrant (request more results if we need to filter post-search)
        search_limit = search.limit
        if search.certifications or search.min_experience_years:
            # Request more results to account for filtering
            search_limit = min(search.limit * 3, 100)
        
        results = qdrant_service.search_jobs(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=search_limit,
            score_threshold=search.score_threshold,
            filter_conditions=filter_conditions if filter_conditions else None
        )
        
        # Apply post-processing filters (certifications, experience)
        # Note: company filter is already applied via Qdrant filter_conditions
        filtered_results = filter_job_results(
            results=results,
            company_filter=None,  # Already filtered at Qdrant level
            min_experience_years=search.min_experience_years,
            certifications=search.certifications,
            limit=search.limit
        )
        
        # Convert to response format
        search_results = [
            JobSearchResult(
                id=result['id'],
                score=result['score'],
                payload=result['payload']
            )
            for result in filtered_results
        ]
        
        return SearchResponse(
            results=search_results,
            count=len(search_results)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")
