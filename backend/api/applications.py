"""
Application tracking API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from models.application import ApplicationCreate, Application, ApplicationWithJob, ApplicationStatus
from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient

router = APIRouter()


@router.post("/mark-applied", response_model=Application, status_code=status.HTTP_201_CREATED)
async def mark_job_applied(
    application: ApplicationCreate,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Mark a job as applied (manual tracking).
    """
    existing = await db.fetch_one(
        "SELECT id FROM applications WHERE user_id = $1 AND job_id = $2",
        current_user["id"], application.job_id
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job already marked as applied"
        )
    
    job_exists = await db.fetch_one("SELECT id FROM jobs WHERE id = $1", application.job_id)
    if not job_exists:
        raise HTTPException(status_code=404, detail="Job not found")
    
    app_id = await db.fetch_val(
        """INSERT INTO applications (user_id, job_id, status, notes, submitted_at)
           VALUES ($1, $2, $3, $4, NOW())
           RETURNING id""",
        current_user["id"], application.job_id, "applied", application.notes
    )
    
    result = await db.fetch_one(
        "SELECT * FROM applications WHERE id = $1", app_id
    )
    
    return {
        "id": str(result["id"]),
        "user_id": str(result["user_id"]),
        "job_id": str(result["job_id"]),
        "status": result["status"],
        "notes": result["notes"],
        "submitted_at": result["submitted_at"],
        "created_at": result["created_at"],
        "updated_at": result["updated_at"]
    }


@router.get("/", response_model=dict)
async def get_applications(
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get all applications for current user with job details.
    """
    applications = await db.fetch_all(
        """SELECT a.id, a.job_id, a.submitted_at, a.created_at,
                  j.id as j_id, j.title, j.company, j.location, j.salary,
                  j.description, j.url, j.posted_date
           FROM applications a
           LEFT JOIN jobs j ON a.job_id = j.id
           WHERE a.user_id = $1
           ORDER BY a.created_at DESC""",
        current_user["id"]
    )
    
    return {
        "applications": [{
            "id": str(app["id"]),
            "job_id": str(app["job_id"]),
            "applied_at": app["submitted_at"] or app["created_at"],
            "job": {
                "id": str(app["j_id"]) if app["j_id"] else str(app["job_id"]),
                "title": app["title"] or "Unknown",
                "company": app["company"] or "Unknown",
                "location": app["location"],
                "description": app["description"],
                "job_url": app["url"],
                "posted_date": app["posted_date"]
            }
        } for app in applications]
    }


@router.get("/status/{job_id}", response_model=ApplicationStatus)
async def check_application_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Check if user has applied to a specific job.
    """
    application = await db.fetch_one(
        "SELECT id FROM applications WHERE user_id = $1 AND job_id = $2",
        current_user["id"], job_id
    )
    
    if application:
        return {
            "job_id": job_id,
            "applied": True,
            "application_id": str(application["id"])
        }
    
    return {
        "job_id": job_id,
        "applied": False,
        "application_id": None
    }


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_application(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Remove application record (unmark as applied).
    """
    result = await db.execute(
        "DELETE FROM applications WHERE user_id = $1 AND job_id = $2",
        current_user["id"], job_id
    )
    
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Application not found")
    
    return None

