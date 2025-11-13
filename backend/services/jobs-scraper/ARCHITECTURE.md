# Job Scraping Service Architecture

## Overview

The job scraping service is designed to scrape job postings from multiple sources, process them, and store them in both PostgreSQL (direct connection) for structured data and Qdrant for vector-based semantic search.

## Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Job Scraper Service                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Scraper    │─────▶│   Processor  │                    │
│  │  (jobspy)    │      │  (NLP/Parse) │                    │
│  └──────────────┘      └──────────────┘                    │
│         │                      │                             │
│         │                      │                             │
│         ▼                      ▼                             │
│  ┌──────────────────────────────────────────┐              │
│  │      Orchestrator (Main Service)          │              │
│  └──────────────────────────────────────────┘              │
│         │                      │                             │
│         │                      │                             │
│    ┌────┴────┐          ┌─────┴─────┐                      │
│    │         │          │           │                        │
│    ▼         ▼          ▼           ▼                        │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌────────┐                 │
│  │PostgreSQL│ │Qdrant│ │Embedding│ │Config│                 │
│  │(Direct)  │ │      │ │ Service │ │      │                 │
│  └──────┘  └──────┘  └──────┘  └────────┘                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Configuration Module (`config.py`)
- **Purpose**: Centralized configuration management
- **Responsibilities**:
  - Load environment variables from `.env` file
  - Provide settings for:
    - PostgreSQL connection (direct connection)
    - Qdrant connection
    - Embedding service (Ollama/OpenAI)
    - Scraping parameters
- **Environment Variables**:
  ```env
  # PostgreSQL (Direct Connection)
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5432
  POSTGRES_DATABASE=your_database_name
  POSTGRES_USER=your_username
  POSTGRES_PASSWORD=your_password
  # Alternative: Use connection string
  # POSTGRES_CONNECTION_STRING=postgresql://user:password@host:port/database
  
  # Qdrant
  QDRANT_HOST=localhost
  QDRANT_PORT=6333
  QDRANT_PATH=./qdrant_db  # Optional: for local mode
  
  # Embedding Service
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_EMBEDDING_MODEL=bge-m3
  EMBEDDING_DIM=1024
  
  # Scraping Configuration
  SCRAPE_SITES=["indeed", "linkedin", "google"]
  SCRAPE_RESULTS_WANTED=1000
  SCRAPE_HOURS_OLD=720
  ```

### 2. Job Scraper Service (`scraper.py`)
- **Purpose**: Scrape jobs from multiple sources
- **Responsibilities**:
  - Use `jobspy` library to scrape from Indeed, LinkedIn, Google
  - Handle scraping parameters (location, search terms, etc.)
  - Return structured job data
- **Dependencies**: `python-jobspy`
- **Output**: Pandas DataFrame with job data

### 3. Job Processor (`processor.py`)
- **Purpose**: Process and enrich scraped job data
- **Responsibilities**:
  - Extract duties and responsibilities using NLP (spaCy)
  - Clean and normalize job descriptions
  - Extract structured information (salary, location, requirements)
  - Prepare data for database storage
- **Dependencies**: `spacy`, `pandas`

### 4. Database Service (`database_service.py`)
- **Purpose**: Handle PostgreSQL operations (direct connection)
- **Responsibilities**:
  - Connect to PostgreSQL using psycopg2
  - Insert/update jobs in `jobs` table
  - Handle duplicate detection
  - Store structured job data
  - Update embeddings in PostgreSQL (optional, for pgvector)
- **Schema**: Uses existing `jobs` table from migrations
- **Connection**: Direct PostgreSQL connection (not via Supabase client)
- **Fields**:
  - `id` (UUID)
  - `title`, `company`, `description`
  - `requirements` (TEXT[])
  - `location`, `salary_min`, `salary_max`
  - `url`, `source`, `posted_date`
  - `embedding` (vector(768) for pgvector)
  - `scraped_at`, `is_active`

### 5. Qdrant Service (`qdrant_service.py`)
- **Purpose**: Handle vector storage for semantic search
- **Responsibilities**:
  - Create/manage collections
  - Store job embeddings with metadata
  - Support vector similarity search
- **Collection Structure**:
  - Collection name: `job_data` (configurable)
  - Vector dimension: 1024 (BGE-M3) or 768 (other models)
  - Payload: Job metadata (title, company, location, etc.)

### 6. Embedding Service (`embedding_service.py`)
- **Purpose**: Generate embeddings for job descriptions
- **Responsibilities**:
  - Generate embeddings using Ollama or other services
  - Support batch processing
  - Handle different embedding models
- **Models Supported**:
  - BGE-M3 (1024 dimensions) via Ollama
  - Other models via OpenAI/Anthropic

### 7. Main Orchestrator (`job_scraper_service.py`)
- **Purpose**: Coordinate all components
- **Responsibilities**:
  - Orchestrate scraping workflow
  - Coordinate data flow between services
  - Handle errors and retries
  - Provide progress tracking
  - Manage batch processing
- **Workflow**:
  1. Initialize services (config, database, Qdrant, embedding)
  2. Scrape jobs using scraper
  3. Process jobs (NLP extraction)
  4. For each job:
     - Check for duplicates in PostgreSQL
     - Generate embedding
     - Save to PostgreSQL
     - Save to Qdrant
  5. Report results

## Data Flow

```
1. Scrape Jobs
   └─▶ jobspy.scrape_jobs()
       └─▶ Returns DataFrame

2. Process Jobs
   └─▶ Extract duties/responsibilities
   └─▶ Clean and normalize
       └─▶ Returns processed DataFrame

3. For each job:
   ├─▶ Check duplicate in PostgreSQL
   ├─▶ Generate embedding
   │   └─▶ embedding_service.generate_embedding()
   ├─▶ Save to PostgreSQL
   │   └─▶ database_service.save_job()
   └─▶ Save to Qdrant
       └─▶ qdrant_service.save_job_data()
```

## File Structure

```
backend/services/jobs-scraper/
├── ARCHITECTURE.md          # This file
├── config.py                # Configuration management
├── scraper.py               # Job scraping using jobspy
├── processor.py             # Job data processing
├── database_service.py      # PostgreSQL (direct connection) operations
├── qdrant_service.py        # Qdrant vector operations
├── embedding_service.py     # Embedding generation
├── job_scraper_service.py   # Main orchestrator
└── __init__.py              # Package initialization
```

## Usage Example

```python
from services.jobs_scraper.job_scraper_service import JobScraperService

# Initialize service
scraper = JobScraperService()

# Scrape and save jobs
result = await scraper.scrape_and_save(
    search_term="Software Engineer",
    location="Hong Kong",
    results_wanted=1000
)

print(f"Scraped {result['scraped']} jobs")
print(f"Saved {result['saved']} jobs to database")
print(f"Failed {result['failed']} jobs")
```

## Error Handling

- **Scraping Errors**: Retry with exponential backoff
- **Database Errors**: Log and continue with next job
- **Qdrant Errors**: Log and continue (jobs still saved to PostgreSQL)
- **Embedding Errors**: Retry up to 3 times, then skip

## Performance Considerations

- **Batch Processing**: Process embeddings in batches
- **Duplicate Detection**: Use database queries to check existing jobs
- **Rate Limiting**: Respect scraping source rate limits
- **Memory Management**: Process jobs in chunks to avoid memory issues

## Important Notes

### Embedding Dimension Mismatch

The PostgreSQL schema uses `vector(768)` for embeddings, but the default embedding model (BGE-M3) produces 1024-dimensional vectors. The service handles this by:

- **PostgreSQL**: Only stores embeddings if they match the schema dimension (768). For 1024-dim embeddings, they are skipped in PostgreSQL but still stored in Qdrant.
- **Qdrant**: Stores all embeddings regardless of dimension (supports any dimension).

**Recommendations:**
- Use a 768-dim embedding model (e.g., `nomic-embed-text`) if you want embeddings in both PostgreSQL and Qdrant
- Or update the PostgreSQL schema to use `vector(1024)` if using BGE-M3
- Or store embeddings only in Qdrant (current default behavior with BGE-M3)

## Future Enhancements

1. **Scheduling**: Add cron-like scheduling for periodic scraping
2. **Incremental Updates**: Only scrape new jobs since last run
3. **Multi-threading**: Parallel processing for embeddings
4. **Monitoring**: Add metrics and logging
5. **API Endpoints**: Expose scraping via REST API
6. **Webhooks**: Notify on new job postings
7. **Dimension Alignment**: Auto-detect and handle embedding dimension mismatches

