# Job Application Agent - Backend

FastAPI backend for AI-powered job application automation.

## Setup

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your PostgreSQL credentials
```

4. **Run development server:**
```bash
python main.py
# Or use uvicorn directly:
uvicorn main:app --reload --port 8000
```

5. **Access API documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── api/                 # API route handlers
│   ├── auth.py         # Authentication endpoints
│   ├── cv.py           # CV management
│   ├── jobs.py         # Job listings
│   └── matches.py      # Job matching
├── models/             # Pydantic models
│   ├── user.py
│   ├── cv.py
│   └── job.py
├── database/           # Database connections
│   └── postgres_client.py
└── services/           # Business logic (AI will go here)
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/token` - Login (get JWT token)
- `GET /api/auth/me` - Get current user info

### CV Management
- `POST /api/cv/upload` - Upload CV file
- `GET /api/cv/profile` - Get CV profile
- `DELETE /api/cv/profile` - Delete CV profile

### Jobs
- `GET /api/jobs` - Search jobs (with filters)
- `GET /api/jobs/{id}` - Get job details

### Matching
- `GET /api/matches` - Get job matches
- `POST /api/matches/calculate` - Trigger match calculation

## Testing

Create test users:
```bash
python scripts/create_test_users.py
```

## Development

The backend is structured to be AI-ready:
- All AI logic will go in `services/` folder
- Current endpoints return placeholder data
- Ready for integration with CV parser, RAG, and matching algorithms
