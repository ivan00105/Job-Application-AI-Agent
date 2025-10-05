"""
Job-related models.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime


class Job(BaseModel):
    """Job posting model"""
    id: str
    title: str
    company: str
    description: str
    requirements: List[str]
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    url: Optional[str] = None
    source: Optional[str] = None
    posted_date: Optional[date] = None
    is_active: bool = True


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
    skill_score: float
    experience_score: float
    explanation: str
