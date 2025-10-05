"""
Authentication API endpoints.
Simple JWT-based authentication for POC.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

from models.user import User, UserCreate, Token, TokenData
from database.supabase_client import get_db
from config import get_settings

router = APIRouter()
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.access_token_expire_hours)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency to get current authenticated user from JWT token.
    Use this in route handlers that require authentication.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return {"id": user_id}
    except JWTError:
        raise credentials_exception


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """
    Register a new user.
    Creates user account in database.
    """
    db = get_db()

    # Check if username already exists
    existing = db.table("users").select("id").eq("username", user.username).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    result = db.table("users").insert({
        "username": user.username,
        "password_hash": hashed_password
    }).execute()

    return {"message": "User created successfully", "username": user.username}


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint (OAuth2 compatible).
    Returns JWT access token.
    """
    db = get_db()

    # Fetch user from database
    result = db.table("users").select("*").eq("username", form_data.username).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    user = result.data[0]

    # Verify password
    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Create access token
    access_token = create_access_token(data={"sub": user["id"]})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information.
    Protected endpoint that requires authentication.
    """
    db = get_db()

    result = db.table("users").select("id, username, created_at").eq("id", current_user["id"]).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    return result.data[0]
