# Job Search API Testing Guide

Complete guide for testing the job search API endpoint.

## 📋 Overview

The job search API provides vector-based semantic search for jobs stored in Qdrant. It supports:
- Semantic search using embeddings
- LLM query enhancement (optional)
- Company filtering
- Experience level filtering
- Certification/skill filtering
- Similarity score thresholding

## 🚀 Quick Start

### 1. Prerequisites Checklist

Before testing, ensure:

- [ ] Backend API server is running (`python backend/main.py`)
- [ ] Test user exists (run `python backend/scripts/create_test_users.py`)
- [ ] Qdrant is running with job data
- [ ] Environment variables are set (see below)

### 2. Run Quick Test

```bash
python backend/scripts/jobs-finder/quick_test.py
```

This will verify:
- ✅ API server connectivity
- ✅ Authentication
- ✅ Basic search functionality

## 📝 Test Scripts

### `quick_test.py` - Start Here! ⚡
**Purpose:** Fastest way to verify everything works

```bash
python backend/scripts/jobs-finder/quick_test.py
```

**What it tests:**
- Server health check
- Authentication
- Basic search query

**Best for:** First-time setup verification

---

### `test_simple_search.py` - Quick Single Query
**Purpose:** Test a specific search query quickly

```bash
# Default query
python backend/scripts/jobs-finder/test_simple_search.py

# Custom query
python backend/scripts/jobs-finder/test_simple_search.py "machine learning engineer"
```

**What it tests:**
- Single search with LLM enhancement
- Displays top 5 results

**Best for:** Quick ad-hoc testing

---

### `test_search_with_filters.py` - Filter Examples
**Purpose:** Learn how to use different filters

```bash
python backend/scripts/jobs-finder/test_search_with_filters.py
```

**What it demonstrates:**
- Company filtering
- Experience filtering
- Certification filtering
- Combined filters
- Score thresholds

**Best for:** Learning filter syntax

---

### `test_job_search_api.py` - Full Test Suite
**Purpose:** Comprehensive testing of all features

```bash
python backend/scripts/jobs-finder/test_job_search_api.py
```

**What it tests:**
1. Basic search
2. LLM enhancement (on/off)
3. Company filtering
4. Experience filtering
5. Certifications filtering
6. Score threshold
7. Combined filters
8. Custom collections
9. Edge cases
10. Error handling

**Best for:** Complete feature validation

## 🔧 API Endpoint Details

### Endpoint
```
POST /api/jobs/search
```

### Authentication
Required - Bearer token from `/api/auth/token`

### Request Body
```json
{
  "query": "Python developer",
  "limit": 10,
  "collection_name": "job_data",
  "use_llm_enhancement": true,
  "company_filter": "Google",
  "min_experience_years": 3,
  "certifications": ["AWS", "Docker"],
  "score_threshold": 0.7,
  "filter_conditions": {
    "location": "San Francisco"
  }
}
```

### Response
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
        "job_requirements": "...",
        "job_responsibilities": "...",
        "url": "https://..."
      }
    }
  ],
  "count": 1
}
```

## 🔑 Environment Variables

Create/update `.env` file in project root:

```env
# API Configuration
API_BASE_URL=http://localhost:8000

# Test User (optional - defaults provided)
TEST_USERNAME=testuser1
TEST_PASSWORD=password123

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=job_data
# QDRANT_PATH=./qdrant_db  # Optional: for local file storage

# Embedding Service
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=1024

# LLM Enhancement (Optional)
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openrouter/gpt-oss-120b
ENABLE_LLM_QUERY_ENHANCEMENT=true
```

## 🧪 Manual Testing with cURL

### 1. Get Authentication Token
```bash
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser1&password=password123"
```

### 2. Search Jobs
```bash
curl -X POST "http://localhost:8000/api/jobs/search" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python developer",
    "limit": 10,
    "use_llm_enhancement": true
  }'
```

## 🐛 Troubleshooting

### Authentication Fails
**Problem:** `401 Unauthorized` or authentication error

**Solutions:**
1. Verify test user exists:
   ```bash
   python backend/scripts/create_test_users.py
   ```
2. Check username/password in script or `.env`
3. Verify token endpoint is accessible

### Connection Error
**Problem:** `Cannot connect to API server`

**Solutions:**
1. Check if server is running:
   ```bash
   curl http://localhost:8000/health
   ```
2. Verify `API_BASE_URL` in script or `.env`
3. Check firewall/network settings

### No Results Found
**Problem:** Search returns 0 results

**Solutions:**
1. Verify Qdrant is running:
   ```bash
   curl http://localhost:6333/collections
   ```
2. Check collection name matches your data
3. Try a broader search query
4. Lower `score_threshold` (default is None)
5. Verify job data exists in Qdrant

### LLM Enhancement Not Working
**Problem:** LLM enhancement doesn't improve results

**Solutions:**
1. Check `OPENROUTER_API_KEY` is set in `.env`
2. LLM enhancement is optional - search works without it
3. Set `use_llm_enhancement: false` to disable
4. Check OpenRouter API status

### Import Errors
**Problem:** Python import errors when running scripts

**Solutions:**
1. Ensure you're in the project root or backend directory
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Verify Python path includes project root

### Qdrant Connection Error
**Problem:** Cannot connect to Qdrant

**Solutions:**
1. Verify Qdrant is running:
   ```bash
   # Check if Qdrant is accessible
   curl http://localhost:6333/health
   ```
2. Check `QDRANT_HOST` and `QDRANT_PORT` in `.env`
3. If using local file storage, verify `QDRANT_PATH` exists

## 📊 Expected Results

### Successful Search
- Status code: `200 OK`
- Response contains `results` array
- Each result has `id`, `score`, and `payload`
- `count` matches number of results

### No Results
- Status code: `200 OK`
- `results` array is empty
- `count` is `0`

### Error Responses
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid token
- `404 Not Found`: Collection doesn't exist
- `500 Internal Server Error`: Server-side error

## 🎯 Test Scenarios

### Scenario 1: Basic Search
```json
{
  "query": "software engineer",
  "limit": 10
}
```

### Scenario 2: Company-Specific Search
```json
{
  "query": "engineer",
  "limit": 10,
  "company_filter": "Google"
}
```

### Scenario 3: Experience-Based Search
```json
{
  "query": "developer",
  "limit": 10,
  "min_experience_years": 5
}
```

### Scenario 4: Certification-Based Search
```json
{
  "query": "cloud engineer",
  "limit": 10,
  "certifications": ["AWS", "Kubernetes"]
}
```

### Scenario 5: High-Quality Matches Only
```json
{
  "query": "machine learning",
  "limit": 10,
  "score_threshold": 0.8
}
```

### Scenario 6: Combined Filters
```json
{
  "query": "backend developer",
  "limit": 10,
  "company_filter": "Microsoft",
  "min_experience_years": 3,
  "certifications": ["Python", "Django"],
  "use_llm_enhancement": true
}
```

## 📈 Performance Tips

1. **Limit Results:** Use appropriate `limit` (default: 10, max: 100)
2. **Score Threshold:** Use `score_threshold` to filter low-quality matches
3. **LLM Enhancement:** Enable for better semantic matching, disable for speed
4. **Collection Name:** Use specific collections for faster searches
5. **Filters:** Apply filters early to reduce search space

## 🔗 Related Documentation

- API Documentation: `http://localhost:8000/docs` (when server is running)
- Qdrant Documentation: https://qdrant.tech/documentation/
- Main README: `backend/scripts/jobs-finder/README.md`

## 💡 Tips

- Start with `quick_test.py` to verify setup
- Use `test_simple_search.py` for quick queries
- Run `test_job_search_api.py` for comprehensive testing
- Check API docs at `/docs` for interactive testing
- Monitor Qdrant logs for search performance
- Adjust `score_threshold` based on your data quality

---

**Need Help?** Check the main README or review the test script source code for examples.

