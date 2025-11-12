from fastapi import APIRouter, HTTPException
from typing import Optional, List
from app.models.schemas import (
    JobDataCreate, JobDataSearch, JobDataDelete,
    SearchResponse, SuccessResponse, CybersecurityJobSearch
)
from app.services.qdrant_service import qdrant_service
from app.services.embedding_service import embedding_service

router = APIRouter(prefix="/jobs", tags=["Jobs"])

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
    """Search for jobs by keyword and rank by similarity."""
    try:
        # Generate embedding for query
        query_vector = await embedding_service.generate_embedding(search.query)
        
        # Search in Qdrant
        results = qdrant_service.search_jobs(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=search.limit,
            score_threshold=search.score_threshold,
            filter_conditions=search.filter_conditions
        )
        
        return SearchResponse(
            results=results,
            count=len(results)
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

@router.post("/{collection_name}/search/cybersecurity", response_model=SearchResponse)
async def search_cybersecurity_jobs(
    collection_name: str, 
    search: CybersecurityJobSearch
):
    """
    Search for cybersecurity-related jobs with enhanced query and filtering.
    
    This endpoint is optimized for finding cybersecurity, information security,
    and IT security positions. It automatically includes relevant cybersecurity
    keywords in the search query.
    """
    try:
        # Build enhanced query with cybersecurity keywords
        cybersecurity_keywords = [
            "cybersecurity", "cyber security", "information security", "IT security",
            "network security", "application security", "cloud security", "data security",
            "security engineer", "security analyst", "security architect", "penetration testing",
            "vulnerability assessment", "security operations", "SOC", "SIEM",
            "threat detection", "incident response", "security compliance", "risk management",
            "security audit", "security assessment", "CISSP", "CEH", "CISM", "CISA",
            "security consultant", "security specialist", "security administrator"
        ]
        
        # Combine user query with cybersecurity terms
        if search.query:
            query_text = f"{search.query} {' '.join(cybersecurity_keywords[:10])}"
        else:
            query_text = " ".join(cybersecurity_keywords)
        
        # Generate embedding for enhanced query
        query_vector = await embedding_service.generate_embedding(query_text)
        
        # Build filter conditions
        filter_conditions = {}
        if search.company_filter:
            filter_conditions['company'] = search.company_filter
        
        # Search in Qdrant
        results = qdrant_service.search_jobs(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=search.limit,
            score_threshold=search.score_threshold,
            filter_conditions=filter_conditions if filter_conditions else None
        )
        
        # Post-process results for additional filtering
        filtered_results = []
        for result in results:
            payload = result.get('payload', {})
            job_text = (
                payload.get('job_title', '') + ' ' +
                payload.get('job_responsibilities', '') + ' ' +
                payload.get('job_requirements', '')
            ).lower()
            
            # Filter by certifications if specified
            if search.certifications:
                has_cert = any(
                    cert.lower() in job_text 
                    for cert in search.certifications
                )
                if not has_cert:
                    continue
            
            # Filter by minimum experience if specified
            if search.min_experience_years:
                # Try to extract years from requirements text
                # This is a simple heuristic - could be improved
                experience_keywords = [
                    f"{search.min_experience_years} years",
                    f"{search.min_experience_years}+ years",
                    f"minimum {search.min_experience_years} years",
                    f"at least {search.min_experience_years} years"
                ]
                # Check if any experience requirement matches
                has_experience = any(
                    keyword in job_text 
                    for keyword in experience_keywords
                )
                # Also check for higher experience levels
                for years in range(search.min_experience_years, search.min_experience_years + 5):
                    if f"{years} years" in job_text or f"{years}+ years" in job_text:
                        has_experience = True
                        break
                
                # If we can't find explicit experience, include it anyway
                # (some jobs may not specify years clearly)
                if not has_experience and search.min_experience_years > 3:
                    # For higher experience requirements, be more strict
                    continue
            
            filtered_results.append(result)
        
        # Limit results after filtering
        filtered_results = filtered_results[:search.limit]
        
        return SearchResponse(
            results=filtered_results,
            count=len(filtered_results)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching cybersecurity jobs: {str(e)}")

