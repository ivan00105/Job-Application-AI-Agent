"""
Job listings API endpoints.
Handles job search, filtering, and retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from models.job import Job, JobSearchParams
from api.auth import get_current_user
from database.supabase_client import get_db

router = APIRouter()


@router.get("/", response_model=dict)
async def search_jobs(
    query: Optional[str] = Query(None, description="Search query"),
    location: Optional[str] = Query(None, description="Job location"),
    min_salary: Optional[int] = Query(None, description="Minimum salary"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user)
):
    """
    Search and filter jobs.
    Returns paginated list of job postings.

    TODO: Implement vector similarity search when embeddings are ready.
    """
    db = get_db()

    # Build query
    query_builder = db.table("jobs").select("*", count="exact").eq("is_active", True)

    # Apply filters
    if location:
        query_builder = query_builder.ilike("location", f"%{location}%")

    if min_salary:
        query_builder = query_builder.gte("salary_min", min_salary)

    if query:
        # Simple text search for now
        query_builder = query_builder.or_(
            f"title.ilike.%{query}%,description.ilike.%{query}%,company.ilike.%{query}%"
        )

    # Execute with pagination
    result = query_builder.range(offset, offset + limit - 1).execute()

    return {
        "jobs": result.data,
        "total": result.count,
        "limit": limit,
        "offset": offset
    }


@router.get("/{job_id}", response_model=dict)
async def get_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific job.
    """
    db = get_db()

    result = db.table("jobs").select("*").eq("id", job_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")

    return result.data[0]
