# Job Scraping Service

A comprehensive service for scraping jobs from multiple sources (Indeed, LinkedIn, Google), processing them with NLP, and storing them in both PostgreSQL (direct connection) and Qdrant for vector-based semantic search.

## Features

- **Multi-source Scraping**: Scrapes from Indeed, LinkedIn, and Google Jobs
- **NLP Processing**: Extracts duties, responsibilities, and requirements using spaCy
- **Dual Storage**: Saves structured data to PostgreSQL and embeddings to Qdrant
- **Duplicate Detection**: Automatically detects and skips duplicate jobs
- **Batch Processing**: Efficient batch processing for embeddings
- **Configurable**: Highly configurable via environment variables

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install spaCy Model (Optional but Recommended)

```bash
python -m spacy download en_core_web_sm
```

### 3. Configure Environment Variables

Add the following to your `.env` file in the project root:

```env
# PostgreSQL Configuration - Required
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
# Alternative: Use connection string instead of individual parameters
# POSTGRES_CONNECTION_STRING=postgresql://user:password@host:port/database

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
# QDRANT_PATH=./qdrant_db  # Optional: for local file-based storage

# Embedding Service (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=1024

# Scraping Configuration (Optional - defaults shown)
SCRAPE_SITES=["indeed", "linkedin", "google"]
SCRAPE_RESULTS_WANTED=1000
SCRAPE_HOURS_OLD=720

# Qdrant Collection Name
QDRANT_COLLECTION_NAME=job_data

# Processing Configuration
BATCH_SIZE=10
ENABLE_DUPLICATE_DETECTION=true
```

### 4. Start Required Services

**Qdrant** (choose one):
- **Docker**: `docker run -p 6333:6333 qdrant/qdrant`
- **Local**: Install Qdrant and run locally

**Ollama** (for embeddings):
- Install Ollama: https://ollama.ai
- Pull the embedding model: `ollama pull bge-m3`

## Usage

### Basic Usage

```python
import asyncio
from services.jobs_scraper.job_scraper_service import JobScraperService

async def main():
    scraper = JobScraperService()
    
    result = await scraper.scrape_and_save(
        search_term="Software Engineer",
        location="Hong Kong",
        results_wanted=100
    )
    
    print(f"Scraped: {result['scraped']}")
    print(f"Saved: {result['saved']}")

asyncio.run(main())
```

### Advanced Usage

```python
result = await scraper.scrape_and_save(
    search_term="Data Analyst",
    location="Hong Kong",
    google_search_term="Data Analyst jobs in Hong Kong",
    results_wanted=500,
    hours_old=360,  # 15 days
    sites=["indeed", "linkedin"],  # Only specific sites
    country_indeed="Hong Kong",
    batch_size=20  # Larger batch size
)
```

### Run Example Script

```bash
cd backend
python -m services.jobs_scraper.example_usage
```

## Configuration Options

### Scraping Parameters

- `search_term`: Job search term (e.g., "Software Engineer")
- `location`: Job location (e.g., "Hong Kong")
- `google_search_term`: Custom Google search term (optional)
- `results_wanted`: Number of results to fetch (default: 1000)
- `hours_old`: Maximum age of jobs in hours (default: 720 = 30 days)
- `sites`: List of sites to scrape (default: ["indeed", "linkedin", "google"])
- `country_indeed`: Country for Indeed search (default: same as location)

### Environment Variables

See [ARCHITECTURE.md](ARCHITECTURE.md) for complete list of environment variables.

## Output

The service returns a dictionary with the following statistics:

```python
{
    "scraped": int,        # Number of jobs scraped
    "saved": int,          # Number of jobs saved to PostgreSQL
    "failed": int,         # Number of jobs that failed to save
    "skipped": int,        # Number of duplicate jobs skipped
    "qdrant_saved": int,   # Number of jobs saved to Qdrant
    "qdrant_failed": int   # Number of jobs that failed to save to Qdrant
}
```

## Data Storage

### PostgreSQL

Jobs are stored in the `jobs` table with the following structure:
- Structured data (title, company, description, requirements, etc.)
- Embeddings (if dimension matches schema - 768 dimensions)
- Metadata (location, salary, URL, source, posted date)

### Qdrant

Jobs are stored in Qdrant with:
- Vector embeddings (any dimension supported)
- Payload metadata (title, company, location, description, etc.)
- Used for semantic search and similarity matching

## Embedding Dimension Note

The PostgreSQL schema uses `vector(768)`, but BGE-M3 produces 1024-dimensional vectors. The service handles this by:

- **PostgreSQL**: Only stores 768-dim embeddings (skips 1024-dim embeddings)
- **Qdrant**: Stores all embeddings regardless of dimension

To store embeddings in both databases, either:
1. Use a 768-dim embedding model (e.g., `nomic-embed-text`)
2. Update PostgreSQL schema to `vector(1024)`
3. Store embeddings only in Qdrant (current default with BGE-M3)

## Troubleshooting

### Common Issues

1. **Qdrant Connection Error**
   - Ensure Qdrant is running: `docker ps | grep qdrant`
   - Check `QDRANT_HOST` and `QDRANT_PORT` in `.env`

2. **Ollama Connection Error**
   - Ensure Ollama is running: `ollama list`
   - Check `OLLAMA_BASE_URL` in `.env`
   - Verify model is installed: `ollama pull bge-m3`

3. **PostgreSQL Connection Error**
   - Verify `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` in `.env`
   - Check network connectivity
   - Ensure PostgreSQL server is running and accessible
   - Verify database exists and user has proper permissions

4. **spaCy Model Not Found**
   - Install model: `python -m spacy download en_core_web_sm`
   - Or disable NLP processing (service will still work)

5. **No Jobs Scraped**
   - Check internet connection
   - Verify scraping sites are accessible
   - Try reducing `results_wanted` for testing

## Development

### Project Structure

```
backend/services/jobs-scraper/
├── ARCHITECTURE.md          # Architecture documentation
├── README.md                 # This file
├── config.py                # Configuration management
├── scraper.py               # Job scraping using jobspy
├── processor.py             # Job data processing
├── database_service.py      # PostgreSQL operations
├── qdrant_service.py        # Qdrant operations
├── embedding_service.py     # Embedding generation
├── job_scraper_service.py   # Main orchestrator
├── example_usage.py         # Usage examples
└── __init__.py              # Package initialization
```

### Adding New Features

1. **New Scraping Source**: Extend `scraper.py`
2. **New Processing Logic**: Extend `processor.py`
3. **New Storage Backend**: Create new service class and integrate in `job_scraper_service.py`

## License

Part of the Job Application AI Agent project.

