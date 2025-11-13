"""
Job listings API endpoints.
Handles job search, filtering, and retrieval using PostgreSQL + Qdrant.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import json

from models.job import Job, JobSearchParams
from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient
from services.shared.jobsengine_client import get_jobsengine_client, JobsEngineClient

router = APIRouter()


@router.get("/", response_model=dict)
async def search_jobs(
    query: Optional[str] = Query(None, description="Search query"),
    location: Optional[str] = Query(None, description="Job location"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Search and filter jobs.
    Returns paginated list of job postings.
    
    If query is provided, uses vector similarity search via Qdrant.
    Otherwise, returns regular filtered results from PostgreSQL.
    """
    
    if query:
        # Vector similarity search via Qdrant
        jobsengine = get_jobsengine_client()
        
        try:
            # Search in Qdrant
            results = await jobsengine.search_similar_jobs(
                collection_name="job_embeddings",
                query_text=query,
                limit=limit,
                score_threshold=0.3
            )
            
            # Extract job IDs from Qdrant results
            job_ids = [result["id"] for result in results]
            
            if not job_ids:
                return {"jobs": [], "total": 0, "limit": limit, "offset": offset}
            
            # Fetch job details from PostgreSQL
            sql = """
                SELECT id, title, company, company_url, description, requirements, 
                       location, salary, url, source, posted_date, retrieved_date,
                       application_type, is_active
                FROM jobs
                WHERE id = ANY($1::uuid[]) AND is_active = true
            """
            
            if location:
                sql += " AND location ILIKE $2"
                rows = await db.fetch_all(sql, job_ids, f"%{location}%")
            else:
                rows = await db.fetch_all(sql, job_ids)
            
            jobs = [dict(row) for row in rows]
            
            # Add similarity scores to jobs
            score_map = {r["id"]: r["score"] for r in results}
            for job in jobs:
                job["similarity_score"] = score_map.get(job["id"], 0.0)
            
            # Sort by similarity score
            jobs.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return {
                "jobs": jobs,
                "total": len(jobs),
                "limit": limit,
                "offset": 0,
                "search_type": "vector"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")
    
    else:
        # Regular PostgreSQL search
        where_clauses = ["is_active = true"]
        params = []
        param_count = 1
        
        if location:
            where_clauses.append(f"location ILIKE ${param_count}")
            params.append(f"%{location}%")
            param_count += 1
        
        where_sql = " AND ".join(where_clauses)
        
        # Count total
        count_sql = f"SELECT COUNT(*) FROM jobs WHERE {where_sql}"
        total = await db.fetch_val(count_sql, *params)
        
        # Fetch paginated results
        sql = f"""
            SELECT id, title, company, company_url, description, requirements,
                   location, salary, url, source, posted_date, retrieved_date,
                   application_type, is_active
            FROM jobs
            WHERE {where_sql}
            ORDER BY posted_date DESC NULLS LAST
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([limit, offset])
        
        rows = await db.fetch_all(sql, *params)
        jobs = [dict(row) for row in rows]
        
        return {
            "jobs": jobs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "search_type": "sql"
        }


@router.get("/{job_id}", response_model=dict)
async def get_job(
    job_id: str,  # UUID
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get detailed information about a specific job.
    """
    sql = """
        SELECT id, title, company, company_url, description, requirements,
               location, salary, url, source, posted_date, retrieved_date,
               application_type, is_active, qdrant_synced
        FROM jobs
        WHERE id = $1::uuid
    """
    
    row = await db.fetch_one(sql, job_id)
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return dict(row)


@router.post("/", response_model=dict)
async def create_job(
    job: Job,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Create a new job posting.
    Inserts into PostgreSQL and generates embedding in Qdrant.
    """
    sql = """
        INSERT INTO jobs (title, company, company_url, description, requirements,
                         location, salary, url, source, posted_date, application_type, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING id
    """
    
    job_id = await db.fetch_val(
        sql,
        job.title, job.company, job.company_url, job.description, job.requirements,
        job.location, job.salary, job.url, job.source, job.posted_date,
        job.application_type, job.is_active
    )
    
    # Generate and save embedding to Qdrant
    try:
        jobsengine = get_jobsengine_client()
        
        # Combine title, description, and requirements for embedding
        text_to_embed = f"{job.title}\n{job.description}"
        if job.requirements:
            text_to_embed += f"\n{job.requirements}"
        
        await jobsengine.save_job_embedding(
            collection_name="job_embeddings",
            job_id=str(job_id),  # Convert UUID to string
            text=text_to_embed,
            payload={
                "title": job.title,
                "company": job.company,
                "location": job.location
            }
        )
        
        # Update qdrant_synced flag
        await db.execute(
            "UPDATE jobs SET qdrant_synced = true WHERE id = $1",
            job_id
        )
        
    except Exception as e:
        # Job is still created in PostgreSQL, just not in Qdrant
        print(f"Warning: Failed to sync job {job_id} to Qdrant: {e}")
    
    return {"id": str(job_id), "message": "Job created successfully"}
