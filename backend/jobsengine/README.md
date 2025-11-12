# Job Data Vector Search API

A Python FastAPI application for managing job data in Qdrant vector database with BGE-M3 embeddings via Ollama.

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

### Search jobs
```bash
curl -X POST "http://localhost:8000/jobs/software_jobs/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python machine learning",
    "limit": 5
  }'
```

## Configuration

All configuration parameters are stored in the `.env` file:

- **QDRANT_HOST**: Qdrant server hostname (default: localhost)
- **QDRANT_PORT**: Qdrant server port (default: 6333)
- **QDRANT_PATH**: Optional path for local file-based Qdrant storage
- **OLLAMA_BASE_URL**: Ollama server URL (default: http://localhost:11434)
- **OLLAMA_EMBEDDING_MODEL**: Embedding model name (default: bge-m3)
- **EMBEDDING_DIM**: Embedding vector dimension (default: 1024 for BGE-M3)

## Features

- ✅ Collection management: create, list, rename, delete
- ✅ Job data management: save, search (with similarity ranking), delete
- ✅ BGE-M3 embeddings via Ollama
- ✅ Similarity-based search with cosine distance
- ✅ Filtering by payload fields
- ✅ Score thresholding for results
- ✅ All configuration via `.env` file

The API returns results sorted by similarity score (higher = more similar). Results include the similarity score, job ID, and payload metadata.

