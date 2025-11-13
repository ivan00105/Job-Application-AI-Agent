"""
Job matching API endpoints.
Implements CV-to-job vector similarity matching via Qdrant.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import json

from models.job import JobMatch, Job
from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient
from services.shared.jobsengine_client import get_jobsengine_client, JobsEngineClient

router = APIRouter()


@router.get("/", response_model=dict)
async def get_job_matches(
    limit: int = Query(20, ge=1, le=100, description="Number of matches"),
    score_threshold: float = Query(0.3, ge=0.0, le=1.0, description="Minimum similarity score"),
    location_filter: Optional[str] = Query(None, description="Filter by location"),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get job matches for the current user based on their CV.
    
    Process:
    1. Get user's CV from PostgreSQL
    2. Search for similar jobs in Qdrant using CV text
    3. Fetch job details from PostgreSQL
    4. Return ranked matches
    """
    user_id = current_user["user_id"]
    
    # Get user's CV
    cv_sql = """
        SELECT id, raw_text, qdrant_synced
        FROM cv_profiles
        WHERE user_id = $1
    """
    
    cv_row = await db.fetch_one(cv_sql, user_id)
    
    if not cv_row:
        raise HTTPException(
            status_code=404,
            detail="CV profile not found. Please upload your CV first."
        )
    
    if not cv_row["qdrant_synced"]:
        raise HTTPException(
            status_code=400,
            detail="CV not yet synced to vector database. Please try again in a moment."
        )
    
    # Search for similar jobs using CV text
    try:
        jobsengine = get_jobsengine_client()
        
        results = await jobsengine.search_similar_jobs(
            collection_name="job_embeddings",
            query_text=cv_row["raw_text"],
            limit=limit * 2,  # Get more results to allow for filtering
            score_threshold=score_threshold
        )
        
        if not results:
            return {
                "matches": [],
                "total": 0,
                "message": "No matching jobs found. Try lowering the score threshold."
            }
        
        # Extract job IDs
        job_ids = [result["id"] for result in results]
        
        # Fetch job details from PostgreSQL
        where_clauses = ["id = ANY($1::uuid[])", "is_active = true"]
        params = [job_ids]
        param_count = 2
        
        if location_filter:
            where_clauses.append(f"location ILIKE ${param_count}")
            params.append(f"%{location_filter}%")
            param_count += 1
        
        where_sql = " AND ".join(where_clauses)
        
        jobs_sql = f"""
            SELECT id, title, company, company_url, description, requirements,
                   location, salary, url, source, posted_date, retrieved_date,
                   application_type, is_active
            FROM jobs
            WHERE {where_sql}
        """
        
        job_rows = await db.fetch_all(jobs_sql, *params)
        
        # Create score map
        score_map = {r["id"]: r["score"] for r in results}
        
        # Build matches
        matches = []
        for row in job_rows:
            job_dict = dict(row)
            job_id = job_dict["id"]
            similarity_score = score_map.get(job_id, 0.0)
            
            matches.append({
                "job": job_dict,
                "overall_score": similarity_score * 100,  # Convert to 0-100 scale
                "skill_score": None,  # Can be computed separately if needed
                "experience_score": None,
                "location_score": None,
                "keyword_score": None,
                "explanation": f"Similarity score: {similarity_score:.2%}"
            })
        
        # Sort by score
        matches.sort(key=lambda x: x["overall_score"], reverse=True)
        
        # Limit to requested number
        matches = matches[:limit]
        
        return {
            "matches": matches,
            "total": len(matches),
            "cv_id": str(cv_row["id"])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job matches: {str(e)}"
        )


@router.post("/save")
async def save_job_match(
    job_id: str,  # UUID
    overall_score: float,
    skill_score: Optional[float] = None,
    experience_score: Optional[float] = None,
    location_score: Optional[float] = None,
    keyword_score: Optional[float] = None,
    explanation: Optional[dict] = None,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Save a job match result to the database.
    Useful for caching match scores.
    """
    user_id = current_user["user_id"]
    
    sql = """
        INSERT INTO job_matches 
        (user_id, job_id, overall_score, skill_score, experience_score, 
         location_score, keyword_score, explanation)
        VALUES ($1, $2::uuid, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (user_id, job_id) 
        DO UPDATE SET
            overall_score = EXCLUDED.overall_score,
            skill_score = EXCLUDED.skill_score,
            experience_score = EXCLUDED.experience_score,
            location_score = EXCLUDED.location_score,
            keyword_score = EXCLUDED.keyword_score,
            explanation = EXCLUDED.explanation,
            calculated_at = NOW()
        RETURNING id
    """
    
    match_id = await db.fetch_val(
        sql,
        user_id, job_id, overall_score, skill_score, experience_score,
        location_score, keyword_score, json.dumps(explanation or {})
    )
    
    return {"id": str(match_id), "message": "Match saved successfully"}


@router.get("/saved", response_model=dict)
async def get_saved_matches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get previously saved/cached job matches.
    """
    user_id = current_user["user_id"]
    
    sql = """
        SELECT 
            jm.id, jm.overall_score, jm.skill_score, jm.experience_score,
            jm.location_score, jm.keyword_score, jm.explanation, jm.calculated_at,
            j.id as job_id, j.title, j.company, j.company_url, j.description, 
            j.requirements, j.location, j.salary, j.url, j.source, j.posted_date,
            j.retrieved_date, j.application_type, j.is_active
        FROM job_matches jm
        JOIN jobs j ON jm.job_id = j.id
        WHERE jm.user_id = $1 AND j.is_active = true
        ORDER BY jm.overall_score DESC
        LIMIT $2 OFFSET $3
    """
    
    rows = await db.fetch_all(sql, user_id, limit, offset)
    
    matches = []
    for row in rows:
        row_dict = dict(row)
        
        job = {
            "id": row_dict["job_id"],
            "title": row_dict["title"],
            "company": row_dict["company"],
            "company_url": row_dict["company_url"],
            "description": row_dict["description"],
            "requirements": row_dict["requirements"],
            "location": row_dict["location"],
            "salary": row_dict["salary"],
            "url": row_dict["url"],
            "source": row_dict["source"],
            "posted_date": row_dict["posted_date"],
            "retrieved_date": row_dict["retrieved_date"],
            "application_type": row_dict["application_type"],
            "is_active": row_dict["is_active"]
        }
        
        match = {
            "id": str(row_dict["id"]),
            "job": job,
            "overall_score": row_dict["overall_score"],
            "skill_score": row_dict["skill_score"],
            "experience_score": row_dict["experience_score"],
            "location_score": row_dict["location_score"],
            "keyword_score": row_dict["keyword_score"],
            "explanation": row_dict["explanation"],
            "calculated_at": row_dict["calculated_at"]
        }
        
        matches.append(match)
    
    # Get total count
    count_sql = """
        SELECT COUNT(*) 
        FROM job_matches jm
        JOIN jobs j ON jm.job_id = j.id
        WHERE jm.user_id = $1 AND j.is_active = true
    """
    total = await db.fetch_val(count_sql, user_id)
    
    return {
        "matches": matches,
        "total": total,
        "limit": limit,
        "offset": offset
    }
