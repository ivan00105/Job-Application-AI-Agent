"""
CV/Resume management API endpoints.
Handles CV upload, parsing, and profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import Optional, Dict, Any
from pydantic import BaseModel
import io
import json

from models.cv import CVProfile, CVUploadResponse
from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient
from services.cv.parser_service import get_cv_parser_service

router = APIRouter()


class CVSaveRequest(BaseModel):
    """Request model for saving CV data"""
    parsed_data: Dict[str, Any]


@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Upload and parse a CV/resume using PyMuPDF/python-docx + LLM (OpenRouter/Ollama).
    Returns parsed JSON for form editing.
    """
    allowed_types = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx"
    }
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )

    try:
        content = await file.read()
        parser = get_cv_parser_service()
        file_type = allowed_types[file.content_type]
        
        file_obj = io.BytesIO(content)
        result = await parser.parse_cv_file(file_obj, file_type)
        
        parsed_data = result["parsed_data"]

        return {
            "message": "CV parsed successfully",
            "filename": file.filename,
            "parsed_data": parsed_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse CV: {str(e)}"
        )


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

    result = dict(profile)
    
    # Parse parsed_data if it's a string (JSONB column returns as dict, but ensure compatibility)
    if isinstance(result.get("parsed_data"), str):
        try:
            result["parsed_data"] = json.loads(result["parsed_data"])
        except (json.JSONDecodeError, TypeError):
            result["parsed_data"] = {}
    
    return result


@router.post("/profile/save", response_model=dict)
async def save_cv_profile(
    cv_data: CVSaveRequest,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Save or update CV profile data (for manual entry or editing).
    """
    existing = await db.fetch_one("SELECT id FROM cv_profiles WHERE user_id = $1", current_user["id"])

    if existing:
        profile_id = existing["id"]
        await db.execute(
            "UPDATE cv_profiles SET parsed_data = $1, updated_at = NOW() WHERE id = $2",
            json.dumps(cv_data.parsed_data), profile_id
        )
    else:
        profile_id = await db.fetch_val(
            "INSERT INTO cv_profiles (user_id, raw_text, parsed_data) VALUES ($1, $2, $3) RETURNING id",
            current_user["id"], "", json.dumps(cv_data.parsed_data)
        )

    return {
        "profile_id": str(profile_id),
        "message": "CV profile saved successfully"
    }


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
