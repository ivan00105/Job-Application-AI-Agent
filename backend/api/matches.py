"""
Job matching API endpoints.
Handles intelligent job matching and recommendations.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient

router = APIRouter()


@router.get("/", response_model=dict)
async def get_matches(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get job matches for current user.
    """
    profile = await db.fetch_one("SELECT id FROM cv_profiles WHERE user_id = $1", current_user["id"])

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No CV profile found. Please upload a CV first."
        )

    matches = await db.fetch_all(
        """SELECT jm.*, j.* FROM job_matches jm
           JOIN jobs j ON jm.job_id = j.id
           WHERE jm.user_id = $1
           ORDER BY jm.overall_score DESC
           LIMIT $2""",
        current_user["id"], limit
    )

    return {
        "matches": [dict(m) for m in matches],
        "count": len(matches),
        "message": "Matching algorithm will be implemented in AI phase" if not matches else None
    }


@router.post("/calculate", response_model=dict)
async def calculate_matches(
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Trigger job matching calculation for current user.
    """
    profile = await db.fetch_one("SELECT id FROM cv_profiles WHERE user_id = $1", current_user["id"])

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No CV profile found. Please upload a CV first."
        )

    return {
        "message": "Match calculation triggered. This will be implemented in AI phase.",
        "status": "pending"
    }
