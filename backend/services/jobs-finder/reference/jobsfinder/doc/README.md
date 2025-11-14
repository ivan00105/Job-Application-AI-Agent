# Job Data Vector Search API

A Python FastAPI application for managing job data in Qdrant vector database with BGE-M3 embeddings via Ollama and intelligent query enhancement using OpenRouter's GPT-OSS-120B.

## Prerequisites

1. **Qdrant**: Install and run Qdrant server
   ```bash
   # Download from https://qdrant.tech/documentation/quick-start/
   # Or use pip: pip install qdrant-client (for local mode)
   ```

2. **Ollama**: Install and run Ollama with BGE-M3 model
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull bge-m3
   ```

3. **OpenRouter** (Optional but recommended): Get API key for LLM query enhancement
   ```bash
   # Sign up at https://openrouter.ai
   # Get your API key from https://openrouter.ai/keys
   ```

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your settings:
   ```env
   # Qdrant Configuration
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   # Or use local file-based storage:
   # QDRANT_PATH=./qdrant_db
   
   # Ollama Configuration
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_EMBEDDING_MODEL=bge-m3
   
   # Embedding Configuration
   EMBEDDING_DIM=1024
   
   # OpenRouter LLM Configuration (for intelligent query enhancement)
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   OPENROUTER_MODEL=openrouter/gpt-oss-120b
   OPENROUTER_TEMPERATURE=0.7
   OPENROUTER_MAX_TOKENS=200
   OPENROUTER_HTTP_REFERER=https://github.com/your-repo
   ENABLE_LLM_QUERY_ENHANCEMENT=true
   ```

## Running the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API documentation available at: http://localhost:8000/docs

## API Endpoints

### Collections

- `POST /collections/` - Create a collection
- `GET /collections/` - List all collections
- `GET /collections/{name}` - Get collection info
- `PUT /collections/rename` - Rename a collection
- `DELETE /collections/{name}` - Delete a collection

### Jobs

- `POST /jobs/{collection_name}/save` - Save job data
- `POST /jobs/{collection_name}/search` - Search jobs by keyword
- `DELETE /jobs/{collection_name}/delete` - Delete job data

## Example Usage

### Create a collection
```bash
curl -X POST "http://localhost:8000/collections/" \
  -H "Content-Type: application/json" \
  -d '{"name": "software_jobs"}'
```

### Save job data
```bash
curl -X POST "http://localhost:8000/jobs/software_jobs/save" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "text": "Looking for a Python developer with experience in machine learning",
    "payload": {
      "title": "ML Engineer",
      "company": "Tech Corp",
      "location": "San Francisco"
    }
  }'
```

### Search jobs (with LLM query enhancement)
```bash
curl -X POST "http://localhost:8000/jobs/software_jobs/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python machine learning",
    "limit": 5
  }'
```

The search endpoint automatically enhances queries using LLM (if enabled) to improve search results. For example:
- "Python developer" → Enhanced to include related terms like "software engineer", "Django", "Flask", etc.
- "data analyst" → Enhanced with "data scientist", "SQL", "Tableau", "analytics", etc.

## Configuration

All configuration parameters are stored in the `.env` file:

- **QDRANT_HOST**: Qdrant server hostname (default: localhost)
- **QDRANT_PORT**: Qdrant server port (default: 6333)
- **QDRANT_PATH**: Optional path for local file-based Qdrant storage
- **OLLAMA_BASE_URL**: Ollama server URL (default: http://localhost:11434)
- **OLLAMA_EMBEDDING_MODEL**: Embedding model name (default: bge-m3)
- **EMBEDDING_DIM**: Embedding vector dimension (default: 1024 for BGE-M3)
- **OPENROUTER_API_KEY**: OpenRouter API key for LLM query enhancement (optional)
- **OPENROUTER_BASE_URL**: OpenRouter API base URL (default: https://openrouter.ai/api/v1)
- **OPENROUTER_MODEL**: OpenRouter model to use (default: openrouter/gpt-oss-120b)
- **OPENROUTER_TEMPERATURE**: LLM temperature for query enhancement (default: 0.7)
- **OPENROUTER_MAX_TOKENS**: Max tokens for LLM response (default: 200)
- **ENABLE_LLM_QUERY_ENHANCEMENT**: Enable/disable LLM query enhancement (default: true)

## Features

- ✅ Collection management: create, list, rename, delete
- ✅ Job data management: save, search (with similarity ranking), delete
- ✅ BGE-M3 embeddings via Ollama
- ✅ **Intelligent LLM-powered query enhancement** using OpenRouter's GPT-OSS-120B
- ✅ Similarity-based search with cosine distance
- ✅ Filtering by payload fields
- ✅ Score thresholding for results
- ✅ All configuration via `.env` file

The API returns results sorted by similarity score (higher = more similar). Results include the similarity score, job ID, and payload metadata.

### LLM Query Enhancement

The search endpoint uses LLM to intelligently enhance user queries before performing vector search. This makes the search more generic and smart, working for any job type (not just cybersecurity). The LLM:

- Expands queries with relevant synonyms and related terms
- Adds common job title variations
- Includes relevant technical skills and tools
- Maintains the original search intent
- Works for any job category (software, data, finance, marketing, etc.)

If LLM enhancement is disabled or API key is not provided, the system falls back to using the original query directly.

