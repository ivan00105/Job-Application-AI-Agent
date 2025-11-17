"""
Autofill models for job application form filling.
"""
from pydantic import BaseModel
from typing import List, Optional, Literal


# ===== A11Y-ENHANCED MODELS =====

class A11yFormElement(BaseModel):
    """A11y-enhanced form element"""
    id: str  # elem_0, elem_1, etc.
    role: str  # textbox, button, checkbox, combobox, radio, etc.
    label: str  # Accessible name (stable!)
    type: str  # input type if applicable
    required: bool
    currentValue: str
    description: Optional[str] = ""


class AnalyzeFormRequest(BaseModel):
    """Request with A11y-enhanced elements"""
    elements: List[A11yFormElement]
    url: str
    company_name: Optional[str] = None


class FormAction(BaseModel):
    """Action to perform on a form element"""
    elementId: str  # Use element ID instead of selector
    label: str
    interaction: Literal["fill_text", "click", "select_option", "check", "need_options"]
    value: str
    confidence: Literal["high", "medium", "low"]
    reasoning: str


# ===== OLD DOM-BASED MODELS (DEPRECATED) =====

class FormElement(BaseModel):
    """DEPRECATED: Extracted form element with context"""
    tag: str
    type: str
    id: str
    name: str
    placeholder: str
    value: str
    required: bool
    label: str
    selector: str
    context: str


class AnalyzeFormResponse(BaseModel):
    """Response with list of actions to perform"""
    actions: List[FormAction]


# ===== OLD MODELS (DEPRECATED - kept for backward compatibility) =====

class FieldInfo(BaseModel):
    """Information about a form field"""
    id: str
    label: Optional[str] = None
    type: str  # text, email, tel, select, textarea, radio, checkbox, file
    placeholder: Optional[str] = None
    required: bool = False
    options: Optional[List[str]] = None  # For select/radio/checkbox
    value: Optional[str] = None  # Current value if any


class AnalyzeFieldsRequest(BaseModel):
    """Request to analyze form fields"""
    url: str
    company_name: Optional[str] = None
    fields: List[FieldInfo]


class FieldFillStrategy(BaseModel):
    """Strategy for filling a form field"""
    field_id: str
    action: Literal["fill", "ask_user", "skip"]
    value: Optional[str] = None
    confidence: Literal["high", "medium", "low"] = "low"
    reasoning: Optional[str] = None


class AnalyzeFieldsResponse(BaseModel):
    """Response with fill strategies for all fields"""
    strategies: List[FieldFillStrategy]
    total_fields: int
    auto_fill_count: int
    ask_user_count: int


class SaveAnswerRequest(BaseModel):
    """Request to save user's answer to memory"""
    field_label: str
    answer: str
    context_type: Literal["global", "company"]
    company_name: Optional[str] = None
    job_url: Optional[str] = None


class MemoryEntry(BaseModel):
    """A single memory entry"""
    id: str
    question_text: str
    answer_text: str
    context_key: str
    company_name: Optional[str] = None
    created_at: str


class GetMemoryResponse(BaseModel):
    """Response with user's saved memories"""
    memories: List[MemoryEntry]
    total: int


