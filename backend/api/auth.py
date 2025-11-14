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
from database.postgres_client import get_db, PostgresClient
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
        return {"user_id": user_id, "id": user_id}  # Include both for compatibility
    except JWTError:
        raise credentials_exception


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: PostgresClient = Depends(get_db)):
    """
    Register a new user.
    Creates user account in database.
    """
    # Check if username already exists
    existing = await db.fetch_one(
        "SELECT id FROM users WHERE username = $1",
        user.username
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    user_id = await db.fetch_val(
        "INSERT INTO users (username, password_hash) VALUES ($1, $2) RETURNING id",
        user.username,
        hashed_password
    )

    return {"message": "User created successfully", "username": user.username, "user_id": str(user_id)}


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: PostgresClient = Depends(get_db)):
    """
    Login endpoint (OAuth2 compatible).
    Returns JWT access token.
    """
    # Fetch user from database
    user = await db.fetch_one(
        "SELECT id, username, password_hash FROM users WHERE username = $1",
        form_data.username
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Verify password
    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user["id"])})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user), db: PostgresClient = Depends(get_db)):
    """
    Get current user information.
    Protected endpoint that requires authentication.
    """
    user = await db.fetch_one(
        "SELECT id, username, created_at FROM users WHERE id = $1",
        current_user["user_id"]
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return dict(user)
