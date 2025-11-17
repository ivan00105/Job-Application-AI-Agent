"""
Autofill API endpoints for job application form filling.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List, Dict, Any
import json
from pydantic import BaseModel

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


# ===== MODELS FOR PASS 2 (Dropdown Analysis) =====

class DropdownOption(BaseModel):
    """A single option in a dropdown"""
    text: str
    value: str

class DropdownOptionsData(BaseModel):
    """Options data for a custom dropdown"""
    elementId: str
    label: str
    options: List[DropdownOption]

class AnalyzeDropdownsRequest(BaseModel):
    """Request for Pass 2: Analyzing dropdown options"""
    dropdownOptions: List[DropdownOptionsData]
    url: str
    company_name: Optional[str] = None


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


@router.post("/analyze-dropdowns")
async def analyze_dropdowns(
    request: AnalyzeDropdownsRequest,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    PASS 2: Analyze custom dropdown options and return actions for selecting them.
    Called after Pass 1 when LLM flags dropdowns as "need_options".
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
    
    # Build a simple prompt for dropdown selection
    llm_service = get_llm_service()
    
    # Create a simplified prompt for just dropdown selection
    dropdown_prompt = build_dropdown_selection_prompt(
        request.dropdownOptions,
        cv_data,
        company_memory + global_memory
    )
    
    # Call LLM with simplified prompt
    response = await llm_service.generate_text(
        prompt=dropdown_prompt,
        temperature=0.1,
        max_tokens=2000
    )
    
    # Parse the response (should be JSON array of actions)
    from services.autofill.llm_form_filler import parse_llm_response
    actions = parse_llm_response(response)
    
    return AnalyzeFormResponse(actions=actions)


def build_dropdown_selection_prompt(dropdowns: List[DropdownOptionsData], cv_data: Dict, memory: List[Dict]) -> str:
    """Build a simplified prompt for Pass 2 dropdown selection"""
    from services.autofill.llm_form_filler import format_cv_summary, format_memory
    
    prompt_parts = []
    prompt_parts.append("You are analyzing custom dropdown options to select the best match based on user's CV and saved answers.")
    prompt_parts.append("\nUSER CV DATA:")
    prompt_parts.append(format_cv_summary(cv_data))
    prompt_parts.append("\nSAVED ANSWERS:")
    prompt_parts.append(format_memory(memory))
    prompt_parts.append("\nDROPDOWN OPTIONS TO ANALYZE:")
    
    for dropdown in dropdowns:
        prompt_parts.append(f"\nDropdown: {dropdown.label} (Element ID: {dropdown.elementId})")
        prompt_parts.append(f"Available options:")
        for i, opt in enumerate(dropdown.options, 1):
            prompt_parts.append(f"  {i}. {opt.text}")
    
    prompt_parts.append("\nTASK: For each dropdown above, return a JSON action to click the best matching option.")
    prompt_parts.append("\nReturn a JSON array like this:")
    prompt_parts.append('[')
    prompt_parts.append('  {')
    prompt_parts.append('    "elementId": "<dropdown_elementId>_option_<index>",')
    prompt_parts.append('    "label": "<option text>",')
    prompt_parts.append('    "interaction": "click",')
    prompt_parts.append('    "value": "<option text>",')
    prompt_parts.append('    "confidence": "high",')
    prompt_parts.append('    "reasoning": "Best match from CV/memory"')
    prompt_parts.append('  }')
    prompt_parts.append(']')
    prompt_parts.append('\nIMPORTANT: Use elementId format: "<dropdown_elementId>_option_<index>" where index is 0-based.')
    prompt_parts.append('For example, if dropdown elementId is "elem_5" and you want to select the 2nd option (index 1), use "elem_5_option_1"')
    
    return '\n'.join(prompt_parts)


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

