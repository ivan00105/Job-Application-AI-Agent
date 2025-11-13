from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Collection Management Schemas
class CollectionCreate(BaseModel):
    name: str = Field(..., description="Collection name")

class CollectionRename(BaseModel):
    old_name: str = Field(..., description="Current collection name")
    new_name: str = Field(..., description="New collection name")

class CollectionInfo(BaseModel):
    name: str
    points_count: int
    vectors_count: int
    config: Dict[str, Any]

# Job Data Schemas
class JobDataCreate(BaseModel):
    job_id: int = Field(..., description="Unique job identifier")
    text: str = Field(..., description="Job description or text to embed")
    payload: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional metadata (title, company, location, etc.)"
    )

class JobDataSearch(BaseModel):
    query: str = Field(..., description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Number of results")
    score_threshold: Optional[float] = Field(
        default=None, 
        ge=0.0, 
        le=1.0, 
        description="Minimum similarity score threshold"
    )
    filter_conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filter conditions for payload fields"
    )
    use_llm_enhancement: Optional[bool] = Field(
        default=None,
        description="Override global LLM enhancement setting. If None, uses global setting."
    )
    # Structured filtering options
    company_filter: Optional[str] = Field(
        default=None,
        description="Filter by specific company name"
    )
    min_experience_years: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum years of experience (if mentioned in job requirements)"
    )
    certifications: Optional[List[str]] = Field(
        default=None,
        description="Filter by required certifications or skills (e.g., ['CISSP', 'CEH', 'PMP', 'AWS']). Case-insensitive search in job text."
    )

class JobSearchResult(BaseModel):
    id: int
    score: float
    payload: Dict[str, Any]

class JobDataDelete(BaseModel):
    job_ids: List[int] = Field(..., description="List of job IDs to delete")

# Response Schemas
class SuccessResponse(BaseModel):
    success: bool
    message: str

class SearchResponse(BaseModel):
    results: List[JobSearchResult]
    count: int

# Cybersecurity-specific search schema
class CybersecurityJobSearch(BaseModel):
    query: Optional[str] = Field(
        default=None,
        description="Additional search keywords (optional, will be combined with cybersecurity terms)"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Number of results")
    score_threshold: Optional[float] = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )
    company_filter: Optional[str] = Field(
        default=None,
        description="Filter by specific company name"
    )
    min_experience_years: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum years of experience (if mentioned in job requirements)"
    )
    certifications: Optional[List[str]] = Field(
        default=None,
        description="Filter by required certifications (e.g., ['CISSP', 'CEH', 'CISM'])"
    )

