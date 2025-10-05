"""
User-related Pydantic models for request/response validation.
"""
from pydantic import BaseModel, EmailField
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user model"""
    username: str


class UserCreate(UserBase):
    """User creation model"""
    password: str


class UserLogin(BaseModel):
    """User login credentials"""
    username: str
    password: str


class User(UserBase):
    """User model with database fields"""
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT token"""
    user_id: Optional[str] = None
