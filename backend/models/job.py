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
