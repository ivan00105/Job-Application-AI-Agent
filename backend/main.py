"""
FastAPI main application.
Job Application Agent - AI-powered job application automation.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api import auth, cv, jobs, matches, applications, interview
from config import get_settings, get_base_url
from database.postgres_client import get_postgres_client

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    base_url = get_base_url(settings)
    print(f"Starting Job Application Agent API on {settings.host}:{settings.port}")
    print(f"External URL: {base_url}")
    print(f"Connecting to PostgreSQL at {settings.postgres_host}:{settings.postgres_port}")
    
    if settings.root_path:
        print(f"Root path configured: {settings.root_path}")
    
    db_client = get_postgres_client()
    await db_client.connect()
    print("PostgreSQL connected")
    
    print(f"JobsEngine URL: {settings.jobsengine_url}")
    print(f"Ollama URL: {settings.ollama_url}")
    print(f"API docs: {base_url}/docs")
    
    yield
    
    print("Shutting down...")
    await db_client.disconnect()
    print("PostgreSQL disconnected")


# Initialize FastAPI app
app = FastAPI(
    title="Job Application Agent API",
    description="AI-powered job search and application automation system",
    version="1.0.0",
    lifespan=lifespan,
    root_path=settings.root_path or "",  # Support for reverse proxy subpaths
)

# Parse allowed origins from config
allowed_origins_list = [
    origin.strip() 
    for origin in settings.allowed_origins.split(",") 
    if origin.strip()
]

# CORS middleware for React frontend (supports remote access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list if allowed_origins_list else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Proxy header middleware to handle X-Forwarded-* headers
class ProxyHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware to handle proxy headers for reverse proxy setups"""
    
    async def dispatch(self, request: Request, call_next):
        # Trust proxy headers if configured
        if settings.trusted_proxy_hosts == "*" or request.client.host in settings.trusted_proxy_hosts.split(","):
            # Forwarded headers are automatically handled by Starlette/FastAPI
            # when root_path is set, but we ensure they're processed correctly
            pass
        
        response = await call_next(request)
        return response

app.add_middleware(ProxyHeaderMiddleware)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(cv.router, prefix="/api/cv", tags=["CV Management"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Job Listings"])
app.include_router(matches.router, prefix="/api/matches", tags=["Job Matching"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(interview.router, prefix="/api/interview", tags=["Interview"])


@app.get("/")
def root():
    """Root endpoint - API health check"""
    return {
        "message": "Job Application Agent API",
        "status": "running",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}


if __name__ == "__main__":
    # Parse trusted proxy hosts for uvicorn
    if settings.trusted_proxy_hosts == "*":
        forwarded_ips = "*"
    else:
        forwarded_ips = [ip.strip() for ip in settings.trusted_proxy_hosts.split(",") if ip.strip()]
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,  # Enable auto-reload during development
        proxy_headers=True,  # Trust proxy headers (X-Forwarded-For, etc.)
        forwarded_allow_ips=forwarded_ips,  # Trust proxy IPs
    )
