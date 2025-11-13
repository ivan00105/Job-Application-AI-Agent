# Job Search API Test Scripts

This directory contains test scripts for the job search API endpoint (`POST /api/jobs/search`).

## Quick Start

**First time testing?** Start with the quick verification:
```bash
python backend/scripts/jobs-finder/quick_test.py
```

This will verify:
- API server is running
- Authentication works
- Search endpoint is accessible
- Basic search returns results

## Test Scripts

### 0. `quick_test.py` - Quick Verification ⚡
Fastest way to verify the API is working. Checks server, auth, and basic search.

**Usage:**
```bash
python backend/scripts/jobs-finder/quick_test.py
```

### 1. `test_job_search_api.py` - Comprehensive Test Suite
Full test suite with multiple scenarios:
- Basic search
- LLM enhancement on/off
- Company filtering
- Experience filtering
- Certifications filtering
- Score threshold
- Combined filters
- Edge cases

**Usage:**
```bash
python backend/scripts/jobs-finder/test_job_search_api.py
```

### 2. `test_simple_search.py` - Quick Test
Simple script for quick testing with a single query.

**Usage:**
```bash
# With default query
python backend/scripts/jobs-finder/test_simple_search.py

# With custom query
python backend/scripts/jobs-finder/test_simple_search.py "Python developer"
```

### 3. `test_search_with_filters.py` - Filter Examples
Demonstrates various filter options with examples.

**Usage:**
```bash
python backend/scripts/jobs-finder/test_search_with_filters.py
```

## Prerequisites

1. **Backend API Server Running**
   ```bash
   cd backend
   python main.py
   ```
   Server should be running on `http://localhost:8000`

2. **Test User Created**
   ```bash
   python backend/scripts/create_test_users.py
   ```

3. **Qdrant Running**
   - Qdrant should be running with job data in the collection
   - Default collection name: `job_data`

4. **Environment Variables** (optional)
   ```bash
   export API_BASE_URL=http://localhost:8000
   export TEST_USERNAME=testuser1
   export TEST_PASSWORD=password123
   export QDRANT_COLLECTION_NAME=job_data
   ```

## API Endpoint Details

**Endpoint:** `POST /api/jobs/search`

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "query": "Python developer",
  "limit": 10,
  "collection_name": "job_data",
  "use_llm_enhancement": true,
  "company_filter": "Google",
  "min_experience_years": 3,
  "certifications": ["AWS", "Docker"],
  "score_threshold": 0.7
}
```

**Response:**
```json
{
  "results": [
    {
      "id": 123,
      "score": 0.85,
      "payload": {
        "job_title": "Senior Python Developer",
        "company": "Google",
        "location": "San Francisco, CA",
        "description": "...",
        ...
      }
    }
  ],
  "count": 1
}
```

## Troubleshooting

### Authentication Fails
- Ensure test user exists: `python backend/scripts/create_test_users.py`
- Check username/password in script or environment variables

### Connection Error
- Verify API server is running: `curl http://localhost:8000/health`
- Check API_BASE_URL environment variable

### No Results Found
- Verify Qdrant is running and has data
- Check collection name matches your data
- Try a broader search query
- Lower the score_threshold if set too high

### LLM Enhancement Not Working
- Check if `OPENROUTER_API_KEY` is set in `.env`
- LLM enhancement is optional - search works without it
- Set `use_llm_enhancement: false` to disable

## Example Output

```
================================================================================
JOB SEARCH API TEST SUITE
================================================================================
API Base URL: http://localhost:8000
Search Endpoint: http://localhost:8000/api/jobs/search
Collection: job_data
================================================================================

🔐 Authenticating...
✅ Authentication successful

================================================================================
TEST 1: Basic Job Search
================================================================================

🔍 Searching: 'Python developer'
✅ Found 5 results

Top results:
--------------------------------------------------------------------------------

1. Senior Python Developer
   Company: Tech Corp
   Location: San Francisco, CA
   Similarity Score: 0.9234
   Description: We are looking for an experienced Python developer...

--------------------------------------------------------------------------------
```

