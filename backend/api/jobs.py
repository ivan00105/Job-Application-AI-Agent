"""
Job listings API endpoints.
Handles job search, filtering, and retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
import os
import sys
import json
import logging

from models.job import Job, JobSearchParams, JobDataSearch, JobSearchResult, SearchResponse
from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient

# Import from jobs-finder directory (handles hyphen in directory name)
services_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'jobs-finder')
sys.path.insert(0, services_path)
from qdrant_service import qdrant_service
from embedding_service import embedding_service
from llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=dict)
async def search_jobs(
    query: Optional[str] = Query(None, description="Search query"),
    location: Optional[str] = Query(None, description="Job location"),
    min_salary: Optional[int] = Query(None, description="Minimum salary"),
    hide_saved: bool = Query(False, description="Hide jobs user has saved"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Search and filter jobs with application status tracking.
    """
    conditions = ["j.is_active = TRUE"]
    params = [current_user["id"]]
    param_count = 2

    if hide_saved:
        # Hide jobs that have been saved (status = 'saved')
        conditions.append("(a.id IS NULL OR a.status != 'saved')")

    if location:
        conditions.append(f"j.location ILIKE ${param_count}")
        params.append(f"%{location}%")
        param_count += 1

    # Note: salary filtering not supported - database has TEXT field, not numeric min/max
    # if min_salary:
    #     conditions.append(f"j.salary_min >= ${param_count}")
    #     params.append(min_salary)
    #     param_count += 1

    if query:
        # Handle multiple keywords: split query and search for each term
        # This allows "axa manager" to find jobs with both "axa" and "manager"
        query_terms = query.strip().split()
        if len(query_terms) > 1:
            # Multiple keywords: use AND logic (all terms must match)
            term_conditions = []
            for term in query_terms:
                term_conditions.append(f"(j.title ILIKE ${param_count} OR j.description ILIKE ${param_count} OR j.company ILIKE ${param_count})")
                params.append(f"%{term}%")
                param_count += 1
            conditions.append(f"({' AND '.join(term_conditions)})")
        else:
            # Single keyword: simple search
            conditions.append(f"(j.title ILIKE ${param_count} OR j.description ILIKE ${param_count} OR j.company ILIKE ${param_count})")
            params.append(f"%{query}%")
            param_count += 1

    where_clause = " AND ".join(conditions)
    
    count_query = f"""
        SELECT COUNT(*) FROM jobs j
        LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
        WHERE {where_clause}
    """
    
    search_query = f"""
        SELECT j.*, 
               CASE WHEN a.id IS NOT NULL THEN true ELSE false END as applied,
               a.status as application_status,
               a.id as application_id
        FROM jobs j
        LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
        WHERE {where_clause}
        ORDER BY j.posted_date DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])

    total = await db.fetch_val(count_query, *params[:-2])
    jobs = await db.fetch_all(search_query, *params)

    return {
        "jobs": [dict(job) for job in jobs],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/recommended", response_model=dict)
async def get_recommended_jobs(
    limit: int = Query(25, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    hide_saved: bool = Query(False, description="Hide jobs user has saved"),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get recommended jobs for the user based on:
    1. CV profile matches (if CV exists)
    2. Similar jobs to saved jobs (if saved jobs exist)
    3. Latest jobs (fallback if no CV and no saved jobs)
    """
    recommended_jobs = []
    total = 0
    source = "latest"  # Track where recommendations came from
    
    try:
        # Try to get job matches from CV profile first
        profile = await db.fetch_one("SELECT id, raw_text, parsed_data FROM cv_profiles WHERE user_id = $1", current_user["id"])
        
        if profile:
            # First check if we have pre-calculated matches in job_matches table
            matches = await db.fetch_all(
                """SELECT jm.*, j.*, 
                          CASE WHEN a.id IS NOT NULL THEN true ELSE false END as applied,
                          a.status as application_status,
                          a.id as application_id
                   FROM job_matches jm
                   JOIN jobs j ON jm.job_id = j.id
                   LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
                   WHERE jm.user_id = $1 AND j.is_active = TRUE
                   ORDER BY jm.overall_score DESC
                   LIMIT $2 OFFSET $3""",
                current_user["id"], limit, offset
            )
            
            if matches:
                recommended_jobs = [dict(m) for m in matches]
                total = await db.fetch_val(
                    """SELECT COUNT(*) FROM job_matches jm
                       JOIN jobs j ON jm.job_id = j.id
                       WHERE jm.user_id = $1 AND j.is_active = TRUE""",
                    current_user["id"]
                )
                source = "cv_matches"
            else:
                # No pre-calculated matches, use CV profile for real-time vector search
                try:
                    # Build search query from CV profile
                    cv_query_parts = []
                    
                    # Use parsed_data if available
                    parsed_data = profile.get("parsed_data")
                    if parsed_data:
                        if isinstance(parsed_data, str):
                            try:
                                parsed_data = json.loads(parsed_data)
                            except:
                                parsed_data = {}
                        
                        # Extract key information from CV
                        if isinstance(parsed_data, dict):
                            # Extract skills
                            skills = parsed_data.get("skills", {})
                            if isinstance(skills, dict):
                                technical = skills.get("technical", [])
                                if technical:
                                    cv_query_parts.extend(technical[:10])  # Top 10 technical skills
                            
                            # Extract experiences
                            experiences = parsed_data.get("experiences", [])
                            if experiences:
                                for exp in experiences[:3]:  # Top 3 experiences
                                    if isinstance(exp, dict):
                                        title = exp.get("title", "")
                                        company = exp.get("company", "")
                                        if title:
                                            cv_query_parts.append(title)
                                        if company:
                                            cv_query_parts.append(company)
                            
                            # Extract summary
                            summary = parsed_data.get("summary", "")
                            if summary:
                                cv_query_parts.append(summary[:200])  # First 200 chars
                    
                    # Fallback to raw_text if parsed_data doesn't have enough info
                    if not cv_query_parts and profile.get("raw_text"):
                        raw_text = profile["raw_text"]
                        # Use first 500 characters of raw text
                        cv_query_parts.append(raw_text[:500])
                    
                    # If we have CV data, use it for vector search
                    if cv_query_parts:
                        cv_search_query = " ".join(cv_query_parts)
                        
                        try:
                            query_vector = await embedding_service.generate_embedding(cv_search_query)
                            collection_name = os.getenv("QDRANT_COLLECTION_NAME", "job_data")
                            
                            # Request more results to account for filtering and pagination
                            search_limit = min((limit + offset) * 2, 200)
                            
                            vector_results = qdrant_service.search_jobs(
                                collection_name=collection_name,
                                query_vector=query_vector,
                                limit=search_limit,
                                score_threshold=0.3  # Reasonable threshold for CV-based matching
                            )
                            
                            if vector_results:
                                # Extract job IDs from vector search results
                                # The payload contains job_id which is the PostgreSQL UUID
                                job_ids = []
                                for result in vector_results:
                                    payload = result.get('payload', {})
                                    job_id = payload.get('job_id')
                                    if job_id:
                                        job_ids.append(str(job_id))
                                
                                if job_ids:
                                    # Get already saved job IDs to exclude them if hide_saved is True
                                    saved_job_ids = []
                                    if hide_saved:
                                        saved_apps = await db.fetch_all(
                                            """SELECT job_id FROM applications 
                                               WHERE user_id = $1 AND status = 'saved'""",
                                            current_user["id"]
                                        )
                                        saved_job_ids = [str(app["job_id"]) for app in saved_apps]
                                    
                                    # Filter out saved jobs if needed
                                    if hide_saved and saved_job_ids:
                                        job_ids = [j_id for j_id in job_ids if j_id not in saved_job_ids]
                                    
                                    if job_ids:
                                        # Limit to requested amount
                                        job_ids = job_ids[:limit + offset]
                                        
                                        conditions = ["j.id = ANY($2::uuid[])", "j.is_active = TRUE"]
                                        params = [current_user["id"], job_ids]
                                        param_count = 3
                                        
                                        if hide_saved:
                                            conditions.append("(a.id IS NULL OR a.status != 'saved')")
                                        
                                        where_clause = " AND ".join(conditions)
                                        
                                        # Preserve order from vector search
                                        search_query_sql = f"""
                                            WITH ordered_ids AS (
                                                SELECT job_id, ord
                                                FROM unnest($2::uuid[]) WITH ORDINALITY AS t(job_id, ord)
                                            )
                                            SELECT j.*, 
                                                   CASE WHEN a.id IS NOT NULL THEN true ELSE false END as applied,
                                                   a.status as application_status,
                                                   a.id as application_id
                                            FROM jobs j
                                            LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
                                            INNER JOIN ordered_ids o ON j.id = o.job_id
                                            WHERE {where_clause}
                                            ORDER BY o.ord
                                            LIMIT ${param_count} OFFSET ${param_count + 1}
                                        """
                                        params.extend([limit, offset])
                                        
                                        recommended_jobs = await db.fetch_all(search_query_sql, *params)
                                        recommended_jobs = [dict(job) for job in recommended_jobs]
                                        
                                        # Count total (approximate, based on vector results)
                                        total = len(job_ids)
                                        source = "cv_vector_search"
                        except Exception as vector_err:
                            logger.warning(
                                f"Vector search with CV profile failed: {vector_err}. "
                                f"Falling back to saved jobs or latest jobs."
                            )
                            # Fall through to saved jobs or latest
                            pass
                except Exception as cv_err:
                    logger.warning(
                        f"Error processing CV profile for vector search: {cv_err}. "
                        f"Falling back to saved jobs or latest jobs."
                    )
                    # Fall through to saved jobs or latest
                    pass
        
        # If no CV matches, try to get similar jobs based on saved jobs
        if not recommended_jobs:
            saved_jobs = await db.fetch_all(
                """SELECT j.id, j.title, j.description, j.company
                   FROM applications a
                   JOIN jobs j ON a.job_id = j.id
                   WHERE a.user_id = $1 AND a.status IN ('saved', 'applied', 'interviewing')
                   LIMIT 5""",
                current_user["id"]
            )
            
            if saved_jobs:
                # Use saved jobs to find similar jobs via vector search
                try:
                    # Build a comprehensive query from all saved jobs
                    saved_query_parts = []
                    saved_job_ids = [str(j['id']) for j in saved_jobs]
                    
                    # Combine titles, companies, and descriptions from saved jobs
                    for saved_job in saved_jobs[:5]:  # Use up to 5 saved jobs
                        if saved_job.get('title'):
                            saved_query_parts.append(saved_job['title'])
                        if saved_job.get('company'):
                            saved_query_parts.append(saved_job['company'])
                        if saved_job.get('description'):
                            # Use first 200 chars of description
                            desc = saved_job['description'][:200] if len(saved_job.get('description', '')) > 200 else saved_job.get('description', '')
                            if desc:
                                saved_query_parts.append(desc)
                    
                    if saved_query_parts:
                        search_query = " ".join(saved_query_parts)
                        
                        # Try vector search for similar jobs
                        try:
                            query_vector = await embedding_service.generate_embedding(search_query)
                            collection_name = os.getenv("QDRANT_COLLECTION_NAME", "job_data")
                            
                            # Request more results to filter out already saved ones and account for pagination
                            search_limit = min((limit + offset) * 2, 200)
                            
                            vector_results = qdrant_service.search_jobs(
                                collection_name=collection_name,
                                query_vector=query_vector,
                                limit=search_limit,
                                score_threshold=0.3
                            )
                            
                            if vector_results:
                                # Extract job IDs from vector search results
                                # The payload contains job_id which is the PostgreSQL UUID
                                vector_job_ids = []
                                for result in vector_results:
                                    payload = result.get('payload', {})
                                    job_id = payload.get('job_id')
                                    if job_id:
                                        vector_job_ids.append(str(job_id))
                                
                                # Filter out already saved jobs
                                job_ids = [j_id for j_id in vector_job_ids if j_id not in saved_job_ids]
                                
                                # Also filter out saved jobs if hide_saved is True
                                if hide_saved:
                                    saved_apps = await db.fetch_all(
                                        """SELECT job_id FROM applications 
                                           WHERE user_id = $1 AND status = 'saved'""",
                                        current_user["id"]
                                    )
                                    saved_job_ids = [str(app["job_id"]) for app in saved_apps]
                                    job_ids = [j_id for j_id in job_ids if j_id not in saved_job_ids]
                                
                                if job_ids:
                                    # Limit to requested amount
                                    job_ids = job_ids[:limit + offset]
                                    
                                    conditions = ["j.id = ANY($2::uuid[])", "j.is_active = TRUE"]
                                    params = [current_user["id"], job_ids]
                                    param_count = 3
                                    
                                    if hide_saved:
                                        conditions.append("(a.id IS NULL OR a.status != 'saved')")
                                    
                                    where_clause = " AND ".join(conditions)
                                    
                                    # Preserve order from vector search
                                    search_query_sql = f"""
                                        WITH ordered_ids AS (
                                            SELECT job_id, ord
                                            FROM unnest($2::uuid[]) WITH ORDINALITY AS t(job_id, ord)
                                        )
                                        SELECT j.*, 
                                               CASE WHEN a.id IS NOT NULL THEN true ELSE false END as applied,
                                               a.status as application_status,
                                               a.id as application_id
                                        FROM jobs j
                                        LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
                                        INNER JOIN ordered_ids o ON j.id = o.job_id
                                        WHERE {where_clause}
                                        ORDER BY o.ord
                                        LIMIT ${param_count} OFFSET ${param_count + 1}
                                    """
                                    params.extend([limit, offset])
                                    
                                    recommended_jobs = await db.fetch_all(search_query_sql, *params)
                                    recommended_jobs = [dict(job) for job in recommended_jobs]
                                    
                                    # Count total (approximate, based on filtered vector results)
                                    total = len(job_ids)
                                    source = "similar_to_saved"
                        except Exception as vector_err:
                            logger.warning(
                                f"Vector search for similar jobs failed: {vector_err}. "
                                f"Falling back to latest jobs."
                            )
                            # Fall through to latest jobs
                            pass
                except Exception as e:
                    logger.warning(
                        f"Error finding similar jobs: {e}. "
                        f"Falling back to latest jobs."
                    )
                    # Fall through to latest jobs
                    pass
        
        # Fallback to latest jobs if no recommendations found
        if not recommended_jobs:
            conditions = ["j.is_active = TRUE"]
            params = [current_user["id"]]
            param_count = 2
            
            if hide_saved:
                conditions.append("(a.id IS NULL OR a.status != 'saved')")
            
            where_clause = " AND ".join(conditions)
            
            count_query = f"""
                SELECT COUNT(*) FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
                WHERE {where_clause}
            """
            
            search_query = f"""
                SELECT j.*, 
                       CASE WHEN a.id IS NOT NULL THEN true ELSE false END as applied,
                       a.status as application_status,
                       a.id as application_id
                FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
                WHERE {where_clause}
                ORDER BY j.posted_date DESC NULLS LAST, j.retrieved_date DESC
                LIMIT ${param_count} OFFSET ${param_count + 1}
            """
            params.extend([limit, offset])
            
            total = await db.fetch_val(count_query, *params[:-2])
            jobs = await db.fetch_all(search_query, *params)
            recommended_jobs = [dict(job) for job in jobs]
            source = "latest"
    
    except Exception as e:
        logger.error(f"Error getting recommended jobs: {e}. Falling back to latest jobs.")
        # Fallback to latest jobs on any error
        conditions = ["j.is_active = TRUE"]
        params = [current_user["id"]]
        param_count = 2
        
        if hide_saved:
            conditions.append("(a.id IS NULL OR a.status != 'saved')")
        
        where_clause = " AND ".join(conditions)
        
        count_query = f"""
            SELECT COUNT(*) FROM jobs j
            LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
            WHERE {where_clause}
        """
        
        search_query = f"""
            SELECT j.*, 
                   CASE WHEN a.id IS NOT NULL THEN true ELSE false END as applied,
                   a.status as application_status,
                   a.id as application_id
            FROM jobs j
            LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
            WHERE {where_clause}
            ORDER BY j.posted_date DESC NULLS LAST, j.retrieved_date DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([limit, offset])
        
        total = await db.fetch_val(count_query, *params[:-2])
        jobs = await db.fetch_all(search_query, *params)
        recommended_jobs = [dict(job) for job in jobs]
        source = "latest"
    
    return {
        "jobs": recommended_jobs,
        "total": total,
        "limit": limit,
        "offset": offset,
        "source": source  # Indicate where recommendations came from
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


@router.get("/{job_id}/similar", response_model=dict)
async def get_similar_jobs(
    job_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of similar jobs to return"),
    hide_saved: bool = Query(False, description="Hide jobs user has saved"),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Find similar jobs based on a specific job.
    Uses vector search to find jobs with similar descriptions, titles, and requirements.
    """
    try:
        # Get the job details
        job = await db.fetch_one("SELECT * FROM jobs WHERE id = $1", job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Build search query from job title, company, and description
        search_query_parts = []
        if job.get("title"):
            search_query_parts.append(job["title"])
        if job.get("company"):
            search_query_parts.append(job["company"])
        if job.get("description"):
            # Use first 500 chars of description
            desc = job["description"][:500] if len(job.get("description", "")) > 500 else job.get("description", "")
            if desc:
                search_query_parts.append(desc)
        
        if not search_query_parts:
            return {
                "jobs": [],
                "total": 0,
                "limit": limit,
                "offset": 0
            }
        
        search_query = " ".join(search_query_parts)
        
        # Use vector search to find similar jobs
        try:
            # Generate embedding for the job
            query_vector = await embedding_service.generate_embedding(search_query)
            collection_name = os.getenv("QDRANT_COLLECTION_NAME", "job_data")
            
            # Search for similar jobs (exclude the current job)
            search_limit = min(limit * 2, 100)  # Get more to filter out the current job
            
            vector_results = qdrant_service.search_jobs(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=search_limit,
                score_threshold=0.3  # Reasonable threshold for similarity
            )
            
            if vector_results:
                # Extract job IDs from vector search results
                job_ids = []
                for result in vector_results:
                    payload = result.get('payload', {})
                    result_job_id = payload.get('job_id')
                    if result_job_id and str(result_job_id) != str(job_id):  # Exclude the current job
                        job_ids.append(str(result_job_id))
                
                if not job_ids:
                    return {
                        "jobs": [],
                        "total": 0,
                        "limit": limit,
                        "offset": 0
                    }
                
                # Limit to requested amount
                job_ids = job_ids[:limit]
                
                # Get already saved/applied job IDs to exclude if hide_saved is True
                excluded_job_ids = []
                if hide_saved:
                    saved_apps = await db.fetch_all(
                        """SELECT job_id FROM applications 
                           WHERE user_id = $1 AND status = 'saved'""",
                        current_user["id"]
                    )
                    excluded_job_ids = [str(app["job_id"]) for app in saved_apps]
                
                # Filter out excluded jobs
                if excluded_job_ids:
                    job_ids = [j_id for j_id in job_ids if j_id not in excluded_job_ids]
                
                if not job_ids:
                    return {
                        "jobs": [],
                        "total": 0,
                        "limit": limit,
                        "offset": 0
                    }
                
                # Fetch jobs from database with application status
                conditions = ["j.id = ANY($2::uuid[])", "j.is_active = TRUE", "j.id != $3"]
                params = [current_user["id"], job_ids, job_id]
                param_count = 4
                
                if hide_saved:
                    conditions.append("(a.id IS NULL OR a.status != 'saved')")
                
                where_clause = " AND ".join(conditions)
                
                # Preserve order from vector search
                search_query_sql = f"""
                    WITH ordered_ids AS (
                        SELECT job_id, ord
                        FROM unnest($2::uuid[]) WITH ORDINALITY AS t(job_id, ord)
                    )
                    SELECT j.*, 
                           CASE WHEN a.id IS NOT NULL THEN true ELSE false END as applied,
                           a.status as application_status,
                           a.id as application_id
                    FROM jobs j
                    LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
                    INNER JOIN ordered_ids o ON j.id = o.job_id
                    WHERE {where_clause}
                    ORDER BY o.ord
                    LIMIT ${param_count}
                """
                params.append(limit)
                
                similar_jobs = await db.fetch_all(search_query_sql, *params)
                
                return {
                    "jobs": [dict(job) for job in similar_jobs],
                    "total": len(similar_jobs),
                    "limit": limit,
                    "offset": 0
                }
            else:
                return {
                    "jobs": [],
                    "total": 0,
                    "limit": limit,
                    "offset": 0
                }
        except Exception as vector_err:
            logger.warning(
                f"Vector search for similar jobs failed: {vector_err}. "
                f"Falling back to keyword search."
            )
            # Fallback to keyword search
            conditions = ["j.is_active = TRUE", "j.id != $2"]
            params = [current_user["id"], job_id]
            param_count = 3
            
            if hide_saved:
                conditions.append("(a.id IS NULL OR a.status != 'saved')")
            
            # Build keyword search from job title and company
            if job.get("title"):
                title_terms = job["title"].split()[:3]  # Use first 3 words
                title_conditions = []
                for term in title_terms:
                    title_conditions.append(f"(j.title ILIKE ${param_count} OR j.description ILIKE ${param_count})")
                    params.append(f"%{term}%")
                    param_count += 1
                if title_conditions:
                    conditions.append(f"({' OR '.join(title_conditions)})")
            
            where_clause = " AND ".join(conditions)
            
            search_query_sql = f"""
                SELECT j.*, 
                       CASE WHEN a.id IS NOT NULL THEN true ELSE false END as applied,
                       a.status as application_status,
                       a.id as application_id
                FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
                WHERE {where_clause}
                ORDER BY j.posted_date DESC
                LIMIT ${param_count}
            """
            params.append(limit)
            
            similar_jobs = await db.fetch_all(search_query_sql, *params)
            
            return {
                "jobs": [dict(job) for job in similar_jobs],
                "total": len(similar_jobs),
                "limit": limit,
                "offset": 0
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error finding similar jobs: {str(e)}")


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


@router.post("/search-vector", response_model=dict)
async def search_jobs_vector_with_db(
    search: JobDataSearch,
    location: Optional[str] = Query(None, description="Job location filter"),
    hide_saved: bool = Query(False, description="Hide jobs user has saved"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Search for jobs using vector similarity search and merge with database data.
    This endpoint combines semantic search with application status tracking,
    location filtering, and pagination support.
    
    Returns jobs in the same format as the keyword search endpoint for frontend compatibility.
    
    Falls back to keyword search if vector search services (Qdrant/Ollama) are unavailable.
    """
    try:
        # Get collection name (default to "job_data" if not specified)
        collection_name = search.collection_name or os.getenv("QDRANT_COLLECTION_NAME", "job_data")
        
        # Try to use vector search, but fallback to keyword search if services unavailable
        try:
            # Enhance query using LLM if enabled
            enhanced_query = search.query
            use_llm = search.use_llm_enhancement
            if use_llm is None:
                # Check global setting
                enable_llm = os.getenv("ENABLE_LLM_QUERY_ENHANCEMENT", "true").lower() == "true"
                use_llm = enable_llm
            
            if use_llm:
                try:
                    enhanced_query = await llm_service.enhance_job_search_query(search.query)
                except Exception as llm_err:
                    # LLM enhancement failed, use original query
                    logger.warning(
                        f"LLM enhancement failed, using original query: {llm_err}"
                    )
                    enhanced_query = search.query
            
            # Generate embedding for enhanced query
            try:
                query_vector = await embedding_service.generate_embedding(enhanced_query)
            except Exception as embed_err:
                # Embedding generation failed, fallback to keyword search
                raise ValueError(f"Embedding service unavailable: {str(embed_err)}")
            
            # Build filter conditions for Qdrant
            filter_conditions = search.filter_conditions or {}
            if search.company_filter:
                filter_conditions['company'] = search.company_filter
            if location:
                filter_conditions['location'] = location
            
            # Request more results to account for database filtering and pagination
            search_limit = min((limit + offset) * 2, 200)  # Get more results for filtering
            
            # Set score threshold - use provided value or default to None (no threshold)
            # For complex queries, we want to be more lenient to get results
            # Qdrant uses cosine similarity: 1.0 = identical, 0.0 = completely different
            # Typical good matches: 0.6-0.9, acceptable: 0.4-0.6
            score_threshold = search.score_threshold
            if score_threshold is None:
                # No threshold by default - return all results sorted by relevance
                # This allows complex queries to still get results even if similarity is lower
                score_threshold = None
            # If threshold is set too high (>0.7), it might filter out valid results for complex queries
            
            # Search in Qdrant
            try:
                qdrant_results = qdrant_service.search_jobs(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=search_limit,
                    score_threshold=score_threshold,
                    filter_conditions=filter_conditions if filter_conditions else None
                )
                
                # Log search results for debugging
                if qdrant_results:
                    scores = [r.get('score', 0) for r in qdrant_results]
                    logger.debug(f"Vector search found {len(qdrant_results)} results")
                    logger.debug(f"Score range: min={min(scores):.4f}, max={max(scores):.4f}, avg={sum(scores)/len(scores):.4f}")
                    if score_threshold is not None:
                        logger.debug(f"Using score threshold: {score_threshold}")
                else:
                    logger.debug(f"Vector search returned 0 results (threshold: {score_threshold})")
                    # If no results and threshold is set, try without threshold
                    if score_threshold is not None and score_threshold > 0.3:
                        logger.debug(f"Retrying with lower threshold (0.3) for complex query...")
                        qdrant_results = qdrant_service.search_jobs(
                            collection_name=collection_name,
                            query_vector=query_vector,
                            limit=search_limit,
                            score_threshold=0.3,  # Lower threshold for complex queries
                            filter_conditions=filter_conditions if filter_conditions else None
                        )
                        if qdrant_results:
                            scores = [r.get('score', 0) for r in qdrant_results]
                            logger.debug(f"Retry found {len(qdrant_results)} results with lower threshold")
                            logger.debug(f"Score range: min={min(scores):.4f}, max={max(scores):.4f}")
                            
            except Exception as qdrant_err:
                # Qdrant search failed, fallback to keyword search
                raise ValueError(f"Qdrant service unavailable: {str(qdrant_err)}")
            
            # Apply post-processing filters (certifications, experience)
            filtered_results = filter_job_results(
                results=qdrant_results,
                company_filter=None,  # Already filtered at Qdrant level
                min_experience_years=search.min_experience_years,
                certifications=search.certifications,
                limit=search_limit
            )
            
            if not filtered_results:
                logger.warning(f"All {len(qdrant_results)} Qdrant results were filtered out by post-processing")
            
            # Extract job IDs from Qdrant results
            # The payload contains job_id which is the PostgreSQL UUID
            job_ids = []
            for result in filtered_results:
                payload = result.get('payload', {})
                # The payload should contain job_id (UUID string from PostgreSQL)
                job_id = payload.get('job_id')
                if job_id:
                    job_ids.append(str(job_id))
            
            if not job_ids:
                return {
                    "jobs": [],
                    "total": 0,
                    "limit": limit,
                    "offset": offset
                }
            
            # Build SQL query to fetch jobs from database with application status
            # Use unnest to preserve order from vector search
            conditions = ["j.id = ANY($2::uuid[])", "j.is_active = TRUE"]
            params = [current_user["id"], job_ids]
            param_count = 3
            
            if hide_saved:
                # Hide jobs that have been saved (status = 'saved')
                conditions.append("(a.id IS NULL OR a.status != 'saved')")
            
            # Location filtering: if not already filtered in Qdrant, filter in SQL
            if location and 'location' not in filter_conditions:
                conditions.append(f"j.location ILIKE ${param_count}")
                params.append(f"%{location}%")
                param_count += 1
            
            where_clause = " AND ".join(conditions)
            
            # Preserve order from vector search by using unnest with ordinality
            # This maintains the relevance ranking from vector search
            search_query = f"""
                WITH ordered_ids AS (
                    SELECT job_id, ord
                    FROM unnest($2::uuid[]) WITH ORDINALITY AS t(job_id, ord)
                )
            SELECT j.*, 
                   CASE WHEN a.id IS NOT NULL THEN true ELSE false END as applied,
                   a.status as application_status,
                   a.id as application_id
            FROM jobs j
            LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
            INNER JOIN ordered_ids o ON j.id = o.job_id
            WHERE {where_clause}
            ORDER BY o.ord
            LIMIT ${param_count} OFFSET ${param_count + 1}
            """
            params.extend([limit, offset])
            
            # Count total matching jobs
            count_query = f"""
                SELECT COUNT(*) FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
                WHERE {where_clause}
            """
            total = await db.fetch_val(count_query, *params[:-2])
            jobs = await db.fetch_all(search_query, *params)
            
            return {
                "jobs": [dict(job) for job in jobs],
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        except ValueError as vector_err:
            # Vector search services unavailable, fallback to keyword search
            logger.warning(
                f"Vector search unavailable ({vector_err}), falling back to keyword search"
            )
            # Fall through to keyword search below
            raise vector_err
    
    except ValueError as e:
        # If it's a vector service error, fallback to keyword search
        if "unavailable" in str(e).lower():
            # Fallback to keyword search
            conditions = ["j.is_active = TRUE"]
            params = [current_user["id"]]
            param_count = 2

            if hide_saved:
                # Hide jobs that have been saved (status = 'saved')
                conditions.append("(a.id IS NULL OR a.status != 'saved')")

            if location:
                conditions.append(f"j.location ILIKE ${param_count}")
                params.append(f"%{location}%")
                param_count += 1

            if search.query:
                # Handle multiple keywords: split query and search for each term
                query_terms = search.query.strip().split()
                if len(query_terms) > 1:
                    # Multiple keywords: use AND logic (all terms must match)
                    term_conditions = []
                    for term in query_terms:
                        term_conditions.append(f"(j.title ILIKE ${param_count} OR j.description ILIKE ${param_count} OR j.company ILIKE ${param_count})")
                        params.append(f"%{term}%")
                        param_count += 1
                    conditions.append(f"({' AND '.join(term_conditions)})")
                else:
                    # Single keyword: simple search
                    conditions.append(f"(j.title ILIKE ${param_count} OR j.description ILIKE ${param_count} OR j.company ILIKE ${param_count})")
                    params.append(f"%{search.query}%")
                    param_count += 1

            where_clause = " AND ".join(conditions)
            
            count_query = f"""
                SELECT COUNT(*) FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
                WHERE {where_clause}
            """
            
            search_query = f"""
                SELECT j.*, 
                       CASE WHEN a.id IS NOT NULL THEN true ELSE false END as applied,
                       a.status as application_status,
                       a.id as application_id
                FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
                WHERE {where_clause}
                ORDER BY j.posted_date DESC
                LIMIT ${param_count} OFFSET ${param_count + 1}
            """
            params.extend([limit, offset])

            total = await db.fetch_val(count_query, *params[:-2])
            jobs = await db.fetch_all(search_query, *params)

            return {
                "jobs": [dict(job) for job in jobs],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # For any other error, try keyword search as fallback
        logger.warning(
            f"Vector search error: {str(e)}, falling back to keyword search"
        )
        try:
            conditions = ["j.is_active = TRUE"]
            params = [current_user["id"]]
            param_count = 2

            if hide_saved:
                # Hide jobs that have been saved (status = 'saved')
                conditions.append("(a.id IS NULL OR a.status != 'saved')")

            if location:
                conditions.append(f"j.location ILIKE ${param_count}")
                params.append(f"%{location}%")
                param_count += 1

            if search.query:
                # Handle multiple keywords: split query and search for each term
                query_terms = search.query.strip().split()
                if len(query_terms) > 1:
                    # Multiple keywords: use AND logic (all terms must match)
                    term_conditions = []
                    for term in query_terms:
                        term_conditions.append(f"(j.title ILIKE ${param_count} OR j.description ILIKE ${param_count} OR j.company ILIKE ${param_count})")
                        params.append(f"%{term}%")
                        param_count += 1
                    conditions.append(f"({' AND '.join(term_conditions)})")
                else:
                    # Single keyword: simple search
                    conditions.append(f"(j.title ILIKE ${param_count} OR j.description ILIKE ${param_count} OR j.company ILIKE ${param_count})")
                    params.append(f"%{search.query}%")
                    param_count += 1

            where_clause = " AND ".join(conditions)
            
            count_query = f"""
                SELECT COUNT(*) FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
                WHERE {where_clause}
            """
            
            search_query = f"""
                SELECT j.*, 
                       CASE WHEN a.id IS NOT NULL THEN true ELSE false END as applied,
                       a.status as application_status,
                       a.id as application_id
                FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id AND a.user_id = $1
                WHERE {where_clause}
                ORDER BY j.posted_date DESC
                LIMIT ${param_count} OFFSET ${param_count + 1}
            """
            params.extend([limit, offset])

            total = await db.fetch_val(count_query, *params[:-2])
            jobs = await db.fetch_all(search_query, *params)

            return {
                "jobs": [dict(job) for job in jobs],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        except Exception as fallback_err:
            raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(fallback_err)}")