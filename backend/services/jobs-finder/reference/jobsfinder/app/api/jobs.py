from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from app.models.schemas import (
    JobDataCreate, JobDataSearch, JobDataDelete,
    SearchResponse, SuccessResponse, CybersecurityJobSearch
)
from app.services.qdrant_service import qdrant_service
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service
from app.config import settings

router = APIRouter(prefix="/jobs", tags=["Jobs"])

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
            payload.get('job_requirements', '')
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

@router.post("/{collection_name}/save", response_model=SuccessResponse)
async def save_job_data(collection_name: str, job_data: JobDataCreate):
    """Save or update job data in a collection."""
    try:
        # Generate embedding
        vector = await embedding_service.generate_embedding(job_data.text)
        
        # Save to Qdrant
        qdrant_service.save_job_data(
            collection_name=collection_name,
            job_id=job_data.job_id,
            vector=vector,
            payload=job_data.payload
        )
        
        return SuccessResponse(
            success=True,
            message=f"Job data with ID {job_data.job_id} saved successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving job data: {str(e)}")

@router.post("/{collection_name}/search", response_model=SearchResponse)
async def search_jobs(collection_name: str, search: JobDataSearch):
    """
    Search for jobs by keyword and rank by similarity.
    Uses LLM to enhance the search query for better results.
    Supports structured filtering by company, experience, and certifications.
    """
    try:
        # Enhance query using LLM if enabled
        enhanced_query = search.query
        use_llm = search.use_llm_enhancement if search.use_llm_enhancement is not None else settings.ENABLE_LLM_QUERY_ENHANCEMENT
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
        
        return SearchResponse(
            results=filtered_results,
            count=len(filtered_results)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")

@router.delete("/{collection_name}/delete", response_model=SuccessResponse)
async def delete_job_data(collection_name: str, delete: JobDataDelete):
    """Delete job data by IDs."""
    try:
        qdrant_service.delete_job_data(
            collection_name=collection_name,
            job_ids=delete.job_ids
        )
        
        return SuccessResponse(
            success=True,
            message=f"Deleted {len(delete.job_ids)} job(s) successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting job data: {str(e)}")

