"""
Job matching API endpoints.
Handles intelligent job matching and recommendations.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from api.auth import get_current_user
from database.supabase_client import get_db

router = APIRouter()


@router.get("/", response_model=dict)
async def get_matches(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get job matches for current user.
    Returns ranked list of jobs with match scores.

    TODO: Implement actual matching algorithm in services/matcher.py
    """
    db = get_db()

    # Check if user has a CV profile
    profile = db.table("cv_profiles").select("id").eq("user_id", current_user["id"]).execute()

    if not profile.data:
        raise HTTPException(
            status_code=404,
            detail="No CV profile found. Please upload a CV first."
        )

    # Fetch matches (if they exist)
    result = db.table("job_matches").select(
        "*, jobs(*)"
    ).eq("user_id", current_user["id"]).order(
        "overall_score", desc=True
    ).limit(limit).execute()

    return {
        "matches": result.data,
        "count": len(result.data),
        "message": "Matching algorithm will be implemented in AI phase" if not result.data else None
    }


@router.post("/calculate", response_model=dict)
async def calculate_matches(current_user: dict = Depends(get_current_user)):
    """
    Trigger job matching calculation for current user.
    Calculates match scores for all active jobs.

    TODO: Implement in services/matcher.py
    """
    db = get_db()

    # Check if user has a CV profile
    profile = db.table("cv_profiles").select("id").eq("user_id", current_user["id"]).execute()

    if not profile.data:
        raise HTTPException(
            status_code=404,
            detail="No CV profile found. Please upload a CV first."
        )

    return {
        "message": "Match calculation triggered. This will be implemented in AI phase.",
        "status": "pending"
    }
