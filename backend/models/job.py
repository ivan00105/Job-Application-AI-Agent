"""
Job-related models.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime


class Job(BaseModel):
    """Job posting model"""
    id: Optional[str] = None  # UUID from PostgreSQL
    title: str
    company: Optional[str] = None
    company_url: Optional[str] = None
    description: str
    requirements: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    url: str  # The unique URL from the source
    source: Optional[str] = None  # 'LinkedIn', 'JobsDB', etc.
    posted_date: Optional[datetime] = None
    retrieved_date: Optional[datetime] = None
    application_type: Optional[str] = None  # 'external_form', 'email', 'easy_apply'
    is_active: bool = True
    qdrant_synced: bool = False


class JobSearchParams(BaseModel):
    """Job search parameters"""
    query: Optional[str] = None
    location: Optional[str] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    limit: int = 20
    offset: int = 0


class JobMatch(BaseModel):
    """Job match with scoring"""
    job: Job
    overall_score: float
    skill_score: Optional[float] = None
    experience_score: Optional[float] = None
    location_score: Optional[float] = None
    keyword_score: Optional[float] = None
    explanation: Optional[str] = None


class JobDataSearch(BaseModel):
    """Job search request for vector search"""
    query: str
    limit: int = 10
    score_threshold: Optional[float] = None
    filter_conditions: Optional[dict] = None
    use_llm_enhancement: Optional[bool] = None
    company_filter: Optional[str] = None
    min_experience_years: Optional[int] = None
    certifications: Optional[List[str]] = None
    collection_name: str = "job_data"


class JobSearchResult(BaseModel):
    """Single job search result"""
    id: int
    score: float
    payload: dict


class SearchResponse(BaseModel):
    """Job search response"""
    results: List[JobSearchResult]
    count: int
