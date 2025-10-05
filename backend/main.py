"""
FastAPI main application.
Job Application Agent - AI-powered job application automation.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api import auth, cv, jobs, matches, interview
from config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Job Application Agent API...")
    print(f"📝 API Documentation: http://{settings.host}:{settings.port}/docs")
    yield
    # Shutdown
    print("👋 Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Job Application Agent API",
    description="AI-powered job search and application automation system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(cv.router, prefix="/api/cv", tags=["CV Management"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Job Listings"])
app.include_router(matches.router, prefix="/api/matches", tags=["Job Matching"])
app.include_router(interview.router, prefix="/api/interview", tags=["Interview Preparation"])


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
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True  # Enable auto-reload during development
    )
