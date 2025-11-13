"""
CV/Resume upload and management endpoints.
Handles PDF upload, text extraction, LLM parsing, and embedding generation.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
import json
from datetime import datetime

from models.cv import CVUploadResponse, CVProfileDB
from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient
from services.cv.parser_service import get_cv_parser_service, CVParserService
from services.shared.jobsengine_client import get_jobsengine_client, JobsEngineClient

router = APIRouter()


@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db),
    cv_parser: CVParserService = Depends(get_cv_parser_service)
):
    """
    Upload and parse a CV/resume PDF file.
    
    Process:
    1. Extract text from PDF using PyMuPDF
    2. Parse text into structured JSON using LLM
    3. Store in PostgreSQL
    4. Generate embedding and store in Qdrant
    """
    user_id = current_user["user_id"]
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Parse CV file (extract + LLM parse)
        result = await cv_parser.parse_cv_file(file.file)
        raw_text = result["raw_text"]
        parsed_data = result["parsed_data"]
        
        # Check if user already has a CV profile
        existing_sql = "SELECT id FROM cv_profiles WHERE user_id = $1"
        existing_row = await db.fetch_one(existing_sql, user_id)
        
        if existing_row:
            # Update existing profile
            profile_id = existing_row["id"]
            update_sql = """
                UPDATE cv_profiles
                SET raw_text = $1, parsed_data = $2, updated_at = $3, qdrant_synced = false
                WHERE id = $4
                RETURNING id
            """
            await db.execute(
                update_sql,
                raw_text,
                json.dumps(parsed_data),
                datetime.utcnow(),
                profile_id
            )
        else:
            # Insert new profile
            insert_sql = """
                INSERT INTO cv_profiles (user_id, raw_text, parsed_data)
                VALUES ($1, $2, $3)
                RETURNING id
            """
            profile_id = await db.fetch_val(
                insert_sql,
                user_id,
                raw_text,
                json.dumps(parsed_data)
            )
        
        # Generate and save embedding to Qdrant
        try:
            jobsengine = get_jobsengine_client()
            
            await jobsengine.save_cv_embedding(
                collection_name="cv_embeddings",
                cv_id=str(profile_id),
                text=raw_text,
                payload={"user_id": user_id}
            )
            
            # Update qdrant_synced flag
            await db.execute(
                "UPDATE cv_profiles SET qdrant_synced = true WHERE id = $1",
                profile_id
            )
            
            qdrant_synced = True
            
        except Exception as e:
            print(f"Warning: Failed to sync CV to Qdrant: {e}")
            qdrant_synced = False
        
        return CVUploadResponse(
            profile_id=str(profile_id),
            raw_text=raw_text,
            parsed_data=parsed_data,
            qdrant_synced=qdrant_synced,
            message="CV uploaded and parsed successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CV: {str(e)}")


@router.get("/profile", response_model=dict)
async def get_cv_profile(
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get the current user's CV profile.
    """
    user_id = current_user["user_id"]
    
    sql = """
        SELECT id, user_id, raw_text, parsed_data, qdrant_synced, created_at, updated_at
        FROM cv_profiles
        WHERE user_id = $1
    """
    
    row = await db.fetch_one(sql, user_id)
    
    if not row:
        raise HTTPException(status_code=404, detail="CV profile not found")
    
    result = dict(row)
    
    # Parse JSONB field
    if result.get("parsed_data"):
        result["parsed_data"] = json.loads(result["parsed_data"]) if isinstance(result["parsed_data"], str) else result["parsed_data"]
    
    return result


@router.delete("/profile")
async def delete_cv_profile(
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Delete the current user's CV profile.
    """
    user_id = current_user["user_id"]
    
    # Get profile ID for Qdrant deletion
    row = await db.fetch_one("SELECT id FROM cv_profiles WHERE user_id = $1", user_id)
    
    if not row:
        raise HTTPException(status_code=404, detail="CV profile not found")
    
    profile_id = row["id"]
    
    # Delete from PostgreSQL (this will cascade)
    await db.execute("DELETE FROM cv_profiles WHERE user_id = $1", user_id)
    
    # Try to delete from Qdrant
    try:
        jobsengine = get_jobsengine_client()
        await jobsengine.delete_job_data(
            collection_name="cv_embeddings",
            job_ids=[str(profile_id)]
        )
    except Exception as e:
        print(f"Warning: Failed to delete CV from Qdrant: {e}")
    
    return {"message": "CV profile deleted successfully"}


@router.put("/profile/sync")
async def sync_cv_to_qdrant(
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Manually sync CV to Qdrant (useful if automatic sync failed).
    """
    user_id = current_user["user_id"]
    
    sql = """
        SELECT id, raw_text, qdrant_synced
        FROM cv_profiles
        WHERE user_id = $1
    """
    
    row = await db.fetch_one(sql, user_id)
    
    if not row:
        raise HTTPException(status_code=404, detail="CV profile not found")
    
    if row["qdrant_synced"]:
        return {"message": "CV already synced to Qdrant", "synced": True}
    
    # Sync to Qdrant
    try:
        jobsengine = get_jobsengine_client()
        
        await jobsengine.save_cv_embedding(
            collection_name="cv_embeddings",
            cv_id=str(row["id"]),
            text=row["raw_text"],
            payload={"user_id": user_id}
        )
        
        # Update flag
        await db.execute(
            "UPDATE cv_profiles SET qdrant_synced = true WHERE id = $1",
            row["id"]
        )
        
        return {"message": "CV synced to Qdrant successfully", "synced": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync to Qdrant: {str(e)}")
