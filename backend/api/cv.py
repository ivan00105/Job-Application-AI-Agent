"""
CV/Resume management API endpoints.
Handles CV upload, parsing, and profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import Optional

from models.cv import CVProfile, CVUploadResponse
from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient

router = APIRouter()


@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Upload and parse a CV/resume. Accepts PDF, DOCX files.
    """
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )

    content = await file.read()

    existing = await db.fetch_one("SELECT id FROM cv_profiles WHERE user_id = $1", current_user["id"])

    if existing:
        profile_id = existing["id"]
        await db.execute(
            "UPDATE cv_profiles SET raw_text = $1, parsed_data = $2, updated_at = NOW() WHERE id = $3",
            "Placeholder text - parsing not yet implemented", {}, profile_id
        )
    else:
        profile_id = await db.fetch_val(
            "INSERT INTO cv_profiles (user_id, raw_text, parsed_data) VALUES ($1, $2, $3) RETURNING id",
            current_user["id"], "Placeholder text - parsing not yet implemented", {}
        )

    return {
        "profile_id": str(profile_id),
        "message": "CV uploaded successfully. Parsing will be implemented in AI phase.",
        "filename": file.filename
    }


@router.get("/profile", response_model=dict)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get user's CV profile.
    """
    profile = await db.fetch_one("SELECT * FROM cv_profiles WHERE user_id = $1", current_user["id"])

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No CV profile found. Please upload a CV first."
        )

    return dict(profile)


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Delete user's CV profile.
    """
    await db.execute("DELETE FROM cv_profiles WHERE user_id = $1", current_user["id"])
    return None
