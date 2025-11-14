"""
Application models for tracking job applications.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApplicationCreate(BaseModel):
    """Create application request"""
    job_id: str
    notes: Optional[str] = None


class Application(BaseModel):
    """Application response"""
    id: str
    user_id: str
    job_id: str
    status: str
    notes: Optional[str] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class JobInfo(BaseModel):
    """Job information for application"""
    id: str
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    job_url: Optional[str] = None
    posted_date: Optional[datetime] = None


class ApplicationWithJob(BaseModel):
    """Application with job details"""
    id: str
    job_id: str
    applied_at: datetime
    job: JobInfo


class ApplicationStatus(BaseModel):
    """Application status check"""
    job_id: str
    applied: bool
    application_id: Optional[str] = None

