"""
Autofill API endpoints for job application form filling.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import json

from models.autofill import (
    # New models
    AnalyzeFormRequest,
    AnalyzeFormResponse,
    FormAction,
    # Old models (deprecated)
    AnalyzeFieldsRequest,
    AnalyzeFieldsResponse,
    FieldFillStrategy,
    SaveAnswerRequest,
    GetMemoryResponse,
    MemoryEntry
)
from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient
from services.autofill.memory_service import (
    get_memory,
    get_all_memory,
    save_memory,
    delete_memory
)
from services.autofill.llm_form_filler import analyze_and_fill_form
import importlib.util
import sys
from pathlib import Path

router = APIRouter()


def get_llm_service():
    """Dependency to get LLM service instance"""
    # Import from jobs-finder folder (has hyphen, can't use regular import)
    llm_service_path = Path(__file__).parent.parent / "services" / "jobs-finder" / "llm_service.py"
    spec = importlib.util.spec_from_file_location("llm_service_module", llm_service_path)
    llm_service_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(llm_service_module)
    return llm_service_module.LLMService()


# ===== NEW LLM-BASED ENDPOINT =====

@router.post("/analyze-form")
async def analyze_form(
    request: AnalyzeFormRequest,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    NEW: Analyze form elements and return actions to perform.
    Accepts structured element list instead of HTML for better efficiency.
    Single LLM call handles both structure understanding and value filling.
    """
    user_id = current_user['id']
    
    # Get user's CV
    cv_profile = await db.fetch_one(
        "SELECT parsed_data FROM cv_profiles WHERE user_id = $1",
        user_id
    )
    
    if not cv_profile:
        raise HTTPException(status_code=404, detail="CV not found. Please upload your CV first.")
    
    cv_data = cv_profile['parsed_data']
    if isinstance(cv_data, str):
        cv_data = json.loads(cv_data)
    
    # Get user's memory
    company_memory = []
    global_memory = []
    
    if request.company_name:
        company_memory = await get_all_memory(db, user_id, company_name=request.company_name)
    global_memory = await get_all_memory(db, user_id, context_type='global')
    
    # Convert FormElement Pydantic models to dicts
    elements_dict = [el.dict() if hasattr(el, 'dict') else el for el in request.elements]
    
    # Single LLM call for everything
    llm_service = get_llm_service()
    actions = await analyze_and_fill_form(
        elements=elements_dict,  # Pass structured elements
        cv_data=cv_data,
        company_memory=company_memory,
        global_memory=global_memory,
        llm_service=llm_service
    )
    
    return AnalyzeFormResponse(actions=actions)


# ===== OLD ENDPOINT (DEPRECATED) =====
# This endpoint has been replaced by /analyze-form (LLM-based approach)
# The old services (field_matcher, batch_llm_filler, llm_filler) have been archived

@router.post("/analyze-fields")
async def analyze_form_fields(
    request: AnalyzeFieldsRequest,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    DEPRECATED: This endpoint is no longer supported.
    Please use /api/autofill/analyze-form instead (new LLM-based approach).
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint is deprecated. Please use /api/autofill/analyze-form instead."
    )


@router.post("/save-answer", status_code=status.HTTP_201_CREATED)
async def save_user_answer(
    request: SaveAnswerRequest,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Save user's answer to memory for future use.
    """
    user_id = current_user["id"]
    
    memory_id = await save_memory(
        db=db,
        user_id=user_id,
        field_label=request.field_label,
        answer=request.answer,
        context_type=request.context_type,
        company_name=request.company_name,
        job_url=request.job_url
    )
    
    return {
        "memory_id": memory_id,
        "message": "Answer saved successfully"
    }


@router.get("/memory", response_model=GetMemoryResponse)
async def get_user_memory(
    company_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get user's saved answers from memory.
    Can filter by company_name.
    """
    user_id = current_user["id"]
    
    memories = await get_all_memory(
        db=db,
        user_id=user_id,
        company_name=company_name
    )
    
    memory_entries = [
        MemoryEntry(
            id=str(mem['id']),
            question_text=mem['question_text'],
            answer_text=mem['answer_text'] or '',
            context_key=mem['context_key'],
            company_name=mem.get('company_name'),
            created_at=str(mem['created_at'])
        )
        for mem in memories
    ]
    
    return GetMemoryResponse(
        memories=memory_entries,
        total=len(memory_entries)
    )


@router.delete("/memory/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory_entry(
    memory_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Delete a memory entry.
    """
    user_id = current_user["id"]
    
    success = await delete_memory(db, user_id, memory_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory entry not found"
        )
    
    return None

