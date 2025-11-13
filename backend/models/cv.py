"""
CV/Resume related models.
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class ContactInfo(BaseModel):
    """Contact information from CV"""
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[str] = None


class Experience(BaseModel):
    """Work experience entry"""
    company: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    achievements: List[str] = []


class Education(BaseModel):
    """Education entry"""
    institution: str
    degree: str
    field: Optional[str] = None
    graduation: Optional[str] = None


class Skills(BaseModel):
    """Skills categorization"""
    technical: List[str] = []
    soft: List[str] = []
    languages: List[str] = []


class CVProfile(BaseModel):
    """Complete CV profile structure"""
    contact: ContactInfo
    summary: Optional[str] = None
    experiences: List[Experience] = []
    education: List[Education] = []
    skills: Skills
    certifications: List[str] = []


class CVUploadResponse(BaseModel):
    """Response after CV upload"""
    profile_id: str
    raw_text: str
    parsed_data: Dict[str, Any]  # Changed from CVProfile to allow flexible LLM output
    qdrant_synced: bool = False
    message: str = "CV uploaded and parsed successfully"


class CVProfileDB(BaseModel):
    """CV profile as stored in database"""
    id: str  # UUID
    user_id: str  # UUID
    raw_text: Optional[str] = None
    parsed_data: Dict[str, Any] = {}  # JSONB data
    qdrant_synced: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
