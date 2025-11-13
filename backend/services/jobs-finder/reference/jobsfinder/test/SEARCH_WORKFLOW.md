# Job Search Workflow Documentation

This document explains the complete workflow of the enhanced job search system.

## Overview

The job search system uses a multi-stage pipeline that combines:
1. **LLM Query Enhancement** (OpenRouter GPT-OSS-120B)
2. **Vector Embedding** (BGE-M3 via Ollama)
3. **Vector Search** (Qdrant)
4. **Structured Filtering** (Post-processing)

## Complete Workflow

```
User Query
    ↓
[Optional] LLM Query Enhancement
    ↓
Generate Embedding Vector
    ↓
Vector Search in Qdrant
    ↓
[Optional] Structured Filtering
    ↓
Return Results
```

## Step-by-Step Process

### Step 1: User Submits Search Request

**API Endpoint:** `POST /jobs/{collection_name}/search`

**Request Body:**
```json
{
  "query": "Python developer",
  "limit": 10,
  "score_threshold": 0.3,
  "use_llm_enhancement": true,  // Optional: override global setting
  "company_filter": "Jane Street",  // Optional
  "min_experience_years": 3,  // Optional
  "certifications": ["Python", "SQL"]  // Optional
}
```

### Step 2: LLM Query Enhancement (If Enabled)

**Condition:** `ENABLE_LLM_QUERY_ENHANCEMENT=true` AND `OPENROUTER_API_KEY` is set

**Process:**
1. Check if LLM enhancement is enabled (global setting or per-request override)
2. If enabled, send original query to OpenRouter GPT-OSS-120B
3. LLM expands query with:
   - Synonyms and related terms
   - Common job title variations
   - Relevant technical skills and tools
   - Industry-specific terminology

**Example:**
- **Input:** "Python developer"
- **Output:** "Python developer software engineer programmer application developer backend engineer frontend engineer Python Django Flask FastAPI backend development"

**Fallback:** If LLM fails or is disabled, use original query

### Step 3: Generate Embedding Vector

**Service:** `embedding_service.generate_embedding()`

**Process:**
1. Take enhanced (or original) query text
2. Send to Ollama BGE-M3 model
3. Generate 1024-dimensional embedding vector
4. Vector represents semantic meaning of the query

**Technical Details:**
- Model: BGE-M3 (via Ollama)
- Dimension: 1024
- Format: List[float] (1024 floats)

### Step 4: Vector Search in Qdrant

**Service:** `qdrant_service.search_jobs()`

**Process:**
1. Connect to Qdrant vector database
2. Search collection using cosine similarity
3. Apply Qdrant-level filters (if any):
   - `company_filter` (if provided) - efficient database-level filtering
   - `filter_conditions` (custom payload filters)
4. Request results (may request more if post-filtering is needed)

**Search Parameters:**
- `query_vector`: 1024-dimensional embedding
- `limit`: Number of results (may be increased if post-filtering needed)
- `score_threshold`: Minimum similarity score (0.0-1.0)
- `filter_conditions`: Qdrant payload filters

**Scoring:**
- Cosine similarity between query vector and job vectors
- Higher score = more similar
- Results sorted by score (descending)

### Step 5: Post-Processing Filtering (If Needed)

**Function:** `filter_job_results()`

**Applied When:**
- `certifications` filter is provided
- `min_experience_years` filter is provided
- (Note: `company_filter` is already applied at Qdrant level)

**Process:**
1. For each result from Qdrant:
   - Extract job text (title + responsibilities + requirements)
   - Convert to lowercase for case-insensitive matching
   
2. **Certification Filtering:**
   - Check if any certification/skill appears in job text
   - If not found, exclude the job
   
3. **Experience Filtering:**
   - Search for experience keywords in job text:
     - "X years", "X+ years", "minimum X years", etc.
   - Also check for higher experience levels (X+1 to X+5 years)
   - If no experience found and requirement > 3 years, exclude job
   
4. **Limit Results:**
   - Apply final limit after filtering
   - Return top N matching jobs

**Example Filtering:**
```python
# Job text: "3-5 years relevant working experience..."
# Filter: min_experience_years=3
# Result: ✅ Included (matches "3-5 years")

# Job text: "Python developer with SQL experience..."
# Filter: certifications=["Python", "SQL"]
# Result: ✅ Included (contains both)
```

### Step 6: Return Results

**Response Format:**
```json
{
  "results": [
    {
      "id": 1,
      "score": 0.6894,
      "payload": {
        "job_title": "Software Engineer",
        "company": "Jane Street",
        "job_requirements": "...",
        "job_responsibilities": "...",
        "job_date": "15/10/2025"
      }
    },
    ...
  ],
  "count": 5
}
```

## Workflow Diagram

```
┌─────────────────┐
│  User Query     │
│  "Python dev"   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ LLM Enhancement?       │
│ (if enabled)           │
│                         │
│ "Python developer       │
│  software engineer      │
│  programmer..."         │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Generate Embedding      │
│ (BGE-M3 via Ollama)     │
│                         │
│ [0.123, -0.456, ...]    │
│ (1024 dimensions)       │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Vector Search (Qdrant) │
│                         │
│ - Cosine similarity     │
│ - Company filter        │
│ - Score threshold       │
│                         │
│ Returns top N results   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Post-Processing Filters │
│ (if needed)             │
│                         │
│ - Certifications        │
│ - Experience years      │
│                         │
│ Filter & limit results  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Return Results          │
│ (sorted by score)       │
└─────────────────────────┘
```

## Configuration Options

### Global Settings (`.env` file)

```env
# LLM Enhancement
ENABLE_LLM_QUERY_ENHANCEMENT=true
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openrouter/gpt-oss-120b
OPENROUTER_TEMPERATURE=0.7
OPENROUTER_MAX_TOKENS=200

# Embedding
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=1024

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### Per-Request Options

- `use_llm_enhancement`: Override global LLM setting
- `company_filter`: Filter by company name
- `min_experience_years`: Filter by experience requirement
- `certifications`: Filter by skills/certifications
- `score_threshold`: Minimum similarity score
- `limit`: Number of results to return

## Performance Considerations

1. **LLM Enhancement:**
   - Adds ~1-2 seconds per request
   - Can be disabled for faster searches
   - Falls back gracefully if API fails

2. **Vector Search:**
   - Very fast (milliseconds)
   - Scales well with large datasets
   - Company filtering at this level is efficient

3. **Post-Processing Filtering:**
   - Text-based matching (slower than vector search)
   - Only applied when needed
   - System requests more results (3x limit) to account for filtering

## Example Use Cases

### Use Case 1: Simple Search
```json
{
  "query": "data analyst",
  "limit": 10
}
```
**Workflow:** Query → LLM Enhancement → Embedding → Vector Search → Results

### Use Case 2: Company-Specific Search
```json
{
  "query": "developer",
  "company_filter": "Jane Street",
  "limit": 5
}
```
**Workflow:** Query → LLM Enhancement → Embedding → Vector Search (with company filter) → Results

### Use Case 3: Filtered Search
```json
{
  "query": "engineer",
  "min_experience_years": 5,
  "certifications": ["Python", "AWS"],
  "limit": 10
}
```
**Workflow:** Query → LLM Enhancement → Embedding → Vector Search → Post-filtering (experience + certs) → Results

### Use Case 4: No LLM Enhancement
```json
{
  "query": "Python developer",
  "use_llm_enhancement": false,
  "limit": 10
}
```
**Workflow:** Query → Embedding → Vector Search → Results (skips LLM step)

## Error Handling

1. **LLM Failure:**
   - Falls back to original query
   - Search continues normally
   - No error returned to user

2. **Embedding Failure:**
   - Returns HTTP 500 error
   - User sees error message

3. **Qdrant Failure:**
   - Returns HTTP 500 error
   - User sees error message

4. **No Results:**
   - Returns empty results array
   - `count: 0`
   - Not an error condition

## Best Practices

1. **Enable LLM Enhancement** for better search quality
2. **Use Company Filter** at Qdrant level (more efficient)
3. **Use Certifications Filter** for specific skill requirements
4. **Set Appropriate Limits** based on expected results
5. **Use Score Threshold** to filter low-quality matches

