from fastapi import FastAPI
from app.api import collections, jobs

app = FastAPI(
    title="Job Data Vector Search API",
    description="API for managing job data in Qdrant vector database with BGE-M3 embeddings",
    version="1.0.0"
)

# Include routers
app.include_router(collections.router)
app.include_router(jobs.router)

@app.get("/")
async def root():
    return {
        "message": "Job Data Vector Search API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

