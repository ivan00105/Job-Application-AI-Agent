# Job Application Agent

AI-powered job search and application automation system.

## 📚 Documentation

**Essential Reading:**
- [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md) - Complete setup instructions for first-time users

**Configuration Examples:**
- `nginx.conf.example` - Nginx reverse proxy configuration example
- `Caddyfile.example` - Caddy reverse proxy configuration example

## Project Structure

```
├── backend/           # FastAPI backend (Python)
│   ├── api/          # API endpoints
│   ├── models/       # Pydantic models
│   ├── services/     # Business logic (AI will go here)
│   └── database/     # Database connections
│
├── src/              # React frontend (TypeScript)
│   ├── api/         # API client
│   ├── components/  # React components
│   ├── context/     # React context (auth)
│   └── pages/       # Page components
```

## Quick Start

### 1. Database Setup

Set up PostgreSQL database and apply the schema:

1. Install PostgreSQL 15+ locally or use a remote server
2. Create a database and user
3. Apply the schema using `backend/migrations/initialised_schema.sql`
4. Configure connection in `backend/.env`

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install and start Ollama (required for embeddings)
# Download from https://ollama.ai, then run:
ollama pull bge-m3

# Configure environment
cp .env.example .env
# Edit .env and add:
# - PostgreSQL credentials
# - OpenRouter API key (get from https://openrouter.ai/keys)

# Create test users
python scripts/create_test_users.py

# Run server
python main.py
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

### 3. Frontend Setup

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs at: http://localhost:5173

## Test Credentials

After running the test user script:
- Username: `testuser1` | Password: `password123`
- Username: `testuser2` | Password: `password123`
- Username: `demo` | Password: `demo123`

## Features

### Current Features
- ✅ User authentication (JWT)
- ✅ CV upload and parsing (PDF/DOCX with LLM extraction)
- ✅ Job listing browse and search
- ✅ Job matching interface
- ✅ Application tracking
- ✅ Interview preparation system
- ✅ Tailored CV generation
- ✅ Cover letter generation
- ✅ Responsive UI with Tailwind CSS

### Coming Soon
- 🔄 Enhanced job matching algorithm
- 🔄 Additional job scraping sources
- 🔄 Advanced application automation

## Development

### Backend
- FastAPI with async support
- JWT authentication
- PostgreSQL database
- OpenRouter for LLM calls
- Ollama for embeddings
- Auto-generated API docs

### Frontend
- React 18 with TypeScript
- React Router for navigation
- Axios for API calls
- Tailwind CSS for styling

## Architecture

The system is designed to be AI-ready:
- Backend services folder prepared for AI components
- Vector embeddings supported in database
- API structure ready for ML integration
- All placeholder endpoints return proper responses

## CV Parsing Template

The CV parser uses OpenRouter/Ollama to extract structured data from PDF/DOCX files following this JSON schema:

```json
{
  "personal_info": {
    "first_name", "last_name", "email", "phone", "location",
    "linkedin", "github", "website"
  },
  "professional_summary": "string",
  "work_experience": [{"job_title", "company", "location", "start_date", "end_date", "responsibilities": []}],
  "education": [{"degree", "field_of_study", "institution", "location", "graduation_year", "gpa"}],
  "skills": {"technical": [], "soft": [], "tools": []},
  "certifications": [{"name", "issuer", "date_obtained", "expiry_date"}],
  "languages": [{"language", "proficiency"}],
  "projects": [{"name", "description", "technologies": [], "url"}]
}
```

See `backend/services/cv/parser_service.py` for the full template used by the LLM.

## Technology Stack

- **Backend:** FastAPI, PostgreSQL, OpenRouter (LLM), Ollama (Embeddings)
- **Frontend:** React 18, TypeScript, Tailwind CSS
- **AI Services:** OpenRouter API, Ollama (local embeddings)
- **Database:** PostgreSQL with Qdrant for vector search

## License

POC Project - Academic Use
