"""
CV/Resume management API endpoints.
Handles CV upload, parsing, and profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import Optional

from models.cv import CVProfile, CVUploadResponse
from api.auth import get_current_user
from database.supabase_client import get_db

router = APIRouter()


@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and parse a CV/resume.
    Accepts PDF, DOCX files.

    TODO: Implement actual parsing logic in services/cv_parser.py
    For now, returns placeholder response.
    """
    # Validate file type
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )

    # Read file content
    content = await file.read()

    # TODO: Call CV parsing service
    # For now, create placeholder profile
    db = get_db()

    # Check if user already has a profile
    existing = db.table("cv_profiles").select("id").eq("user_id", current_user["id"]).execute()

    if existing.data:
        # Update existing profile
        profile_id = existing.data[0]["id"]
        db.table("cv_profiles").update({
            "raw_text": "Placeholder text - parsing not yet implemented",
            "parsed_data": {},
            "updated_at": "now()"
        }).eq("id", profile_id).execute()
    else:
        # Create new profile
        result = db.table("cv_profiles").insert({
            "user_id": current_user["id"],
            "raw_text": "Placeholder text - parsing not yet implemented",
            "parsed_data": {}
        }).execute()
        profile_id = result.data[0]["id"]

    return {
        "profile_id": profile_id,
        "message": "CV uploaded successfully. Parsing will be implemented in AI phase.",
        "filename": file.filename
    }


@router.get("/profile", response_model=dict)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get user's CV profile.
    Returns parsed CV data and metadata.
    """
    db = get_db()

    result = db.table("cv_profiles").select("*").eq("user_id", current_user["id"]).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No CV profile found. Please upload a CV first."
        )

    return result.data[0]


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(current_user: dict = Depends(get_current_user)):
    """
    Delete user's CV profile.
    """
    db = get_db()

    db.table("cv_profiles").delete().eq("user_id", current_user["id"]).execute()

    return None
