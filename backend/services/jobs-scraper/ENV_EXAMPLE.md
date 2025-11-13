# Environment Variables Example

This document shows the required environment variables for the job scraping service.

## Required PostgreSQL Configuration

Add these to your `.env` file in the project root:

```env
# PostgreSQL Configuration (Direct Connection)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
```

**OR** use a connection string instead:

```env
# Alternative: PostgreSQL Connection String
POSTGRES_CONNECTION_STRING=postgresql://username:password@host:port/database
```

## Optional Configuration

```env
# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
# QDRANT_PATH=./qdrant_db  # Optional: for local file-based storage
QDRANT_COLLECTION_NAME=job_data

# Embedding Service (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=1024

# Alternative: OpenAI Embeddings
# USE_OPENAI_EMBEDDINGS=true
# OPENAI_API_KEY=sk-...
# OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Scraping Configuration
SCRAPE_SITES=["indeed", "linkedin", "google"]
SCRAPE_RESULTS_WANTED=1000
SCRAPE_HOURS_OLD=720

# Processing Configuration
BATCH_SIZE=10
ENABLE_DUPLICATE_DETECTION=true
```

## Example .env File

Here's a complete example `.env` file:

```env
# PostgreSQL
POSTGRES_HOST=pg.groture.com
POSTGRES_PORT=5433
POSTGRES_DATABASE=ai.jobsfinder
POSTGRES_USER=ai.jobsfinder
POSTGRES_PASSWORD=your_password_here

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=job_data

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=1024

# Scraping
SCRAPE_SITES=["indeed", "linkedin", "google"]
SCRAPE_RESULTS_WANTED=1000
SCRAPE_HOURS_OLD=720
BATCH_SIZE=10
```

## Notes

- All PostgreSQL parameters are **required** unless using `POSTGRES_CONNECTION_STRING`
- The service reads the `.env` file from the project root directory
- Make sure your PostgreSQL database has the `jobs` table created (see migrations)
- Ensure the `vector` extension is enabled in PostgreSQL for embedding support

