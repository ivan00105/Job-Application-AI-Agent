"""
CV/Resume management API endpoints.
Handles CV upload, parsing, and profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel
import io
import json

from models.cv import CVProfile, CVUploadResponse
from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient
from services.cv.parser_service import get_cv_parser_service
from services.profile_scoring_service import ProfileScoringService

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
        raw_text = result.get("raw_text", "")

        # Automatically save the parsed CV to the database
        existing = await db.fetch_one("SELECT id FROM cv_profiles WHERE user_id = $1", current_user["id"])
        
        if existing:
            profile_id = existing["id"]
            await db.execute(
                "UPDATE cv_profiles SET raw_text = $1, parsed_data = $2, updated_at = NOW() WHERE id = $3",
                raw_text, json.dumps(parsed_data), profile_id
            )
            # Invalidate profile scoring cache when CV is updated
            await db.execute(
                "DELETE FROM profile_scoring_cache WHERE user_id = $1",
                current_user["id"]
            )
        else:
            profile_id = await db.fetch_val(
                "INSERT INTO cv_profiles (user_id, raw_text, parsed_data, created_at, updated_at) VALUES ($1, $2, $3, NOW(), NOW()) RETURNING id",
                current_user["id"], raw_text, json.dumps(parsed_data)
            )

        return {
            "message": "CV parsed and saved successfully",
            "filename": file.filename,
            "parsed_data": parsed_data,
            "profile_id": str(profile_id)
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
        # Invalidate profile scoring cache when CV is updated
        await db.execute(
            "DELETE FROM profile_scoring_cache WHERE user_id = $1",
            current_user["id"]
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


@router.get("/profile/scoring", response_model=dict)
async def get_profile_scoring(
    force_refresh: bool = Query(False, description="Force refresh by bypassing cache"),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get profile scoring analysis for radar diagram.
    Returns scores for 6 dimensions: Qualification, Experience, Technical Skills, Soft Skills, Tools & Platforms, Industry Knowledge.
    Uses cache if available, only calls LLM when CV is updated.
    Set force_refresh=True to bypass cache and force new analysis.
    """
    profile = await db.fetch_one("SELECT * FROM cv_profiles WHERE user_id = $1", current_user["id"])

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No CV profile found. Please upload a CV first."
        )

    profile_id = profile["id"]
    
    # Check cache first (unless force_refresh is True)
    cache = None
    if not force_refresh:
        cache = await db.fetch_one(
            "SELECT * FROM profile_scoring_cache WHERE user_id = $1 AND cv_profile_id = $2",
            current_user["id"], profile_id
        )

    if cache:
        # Parse JSONB fields if they're strings
        scores = cache.get("scores", {})
        if isinstance(scores, str):
            try:
                scores = json.loads(scores)
            except:
                scores = {}
        
        recommendations = cache.get("recommendations", [])
        if isinstance(recommendations, str):
            try:
                recommendations = json.loads(recommendations)
            except:
                recommendations = []
        
        competitor_insights = cache.get("competitor_insights", {})
        if isinstance(competitor_insights, str):
            try:
                competitor_insights = json.loads(competitor_insights)
            except:
                competitor_insights = {}
        
        basic_metrics = cache.get("basic_metrics", {})
        if isinstance(basic_metrics, str):
            try:
                basic_metrics = json.loads(basic_metrics)
            except:
                basic_metrics = {}
        
        # Return cached data
        return {
            "scores": scores,
            "strengths": cache.get("strengths", []),
            "weaknesses": cache.get("weaknesses", []),
            "recommendations": recommendations,
            "competitor_insights": competitor_insights,
            "basic_metrics": basic_metrics,
            "cached": True
        }

    # Parse parsed_data if it's a string
    parsed_data = profile.get("parsed_data")
    if isinstance(parsed_data, str):
        try:
            parsed_data = json.loads(parsed_data)
        except (json.JSONDecodeError, TypeError):
            parsed_data = {}
    
    if not parsed_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CV profile data is empty. Please upload a complete CV."
        )

    raw_text = profile.get("raw_text", "")

    # Analyze profile using AI service (only if not cached)
    scoring_service = ProfileScoringService()
    try:
        analysis = await scoring_service.analyze_profile(parsed_data, raw_text)
        
        # Cache the results
        await db.execute(
            """INSERT INTO profile_scoring_cache 
               (user_id, cv_profile_id, scores, strengths, weaknesses, recommendations, competitor_insights, basic_metrics, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
               ON CONFLICT (user_id) 
               DO UPDATE SET 
                 cv_profile_id = $2,
                 scores = $3,
                 strengths = $4,
                 weaknesses = $5,
                 recommendations = $6,
                 competitor_insights = $7,
                 basic_metrics = $8,
                 updated_at = NOW()""",
            current_user["id"],
            profile_id,
            json.dumps(analysis.get("scores", {})),
            analysis.get("strengths", []),
            analysis.get("weaknesses", []),
            json.dumps(analysis.get("recommendations", [])),
            json.dumps(analysis.get("competitor_insights", {})),
            json.dumps(analysis.get("basic_metrics", {}))
        )
        
        analysis["cached"] = False
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze profile: {str(e)}"
        )
