# Job Application Agent

AI-powered job search and application automation system.

## 📚 Documentation

**Essential Reading:**
- [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md) - Complete setup instructions for first-time users
- [DEVELOPMENT.md](DEVELOPMENT.md) - Quick reference for making changes (read this before coding!)
- [CONFIGURATION_SUMMARY.md](CONFIGURATION_SUMMARY.md) - Current deployment configuration

**Deployment & Configuration:**
- [DEPLOYMENT_CONFIG.md](DEPLOYMENT_CONFIG.md) - Production deployment guide
- [REVERSE_PROXY_SETUP.md](REVERSE_PROXY_SETUP.md) - Reverse proxy setup
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing and verification

**Additional Resources:**
- [backend/README.md](backend/README.md) - Backend API reference and structure
- [FEATURE_IDEAS.md](FEATURE_IDEAS.md) - Roadmap and planned features
- [docs/README.md](docs/README.md) - Complete documentation index

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

The database schema is already created in Supabase. Make sure you have:
- Supabase project URL
- Supabase anon key

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your Supabase credentials

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

### Current (Foundation)
- ✅ User authentication (JWT)
- ✅ CV upload interface
- ✅ Job listing browse
- ✅ Job matching interface
- ✅ Responsive UI with Tailwind CSS

### Coming Soon (AI Phase)
- 🔄 CV parsing with OCR
- 🔄 RAG-powered document generation
- 🔄 Intelligent job matching algorithm
- 🔄 Job scraping from multiple sources
- 🔄 Semi-automated application filling

## Development

### Backend
- FastAPI with async support
- JWT authentication
- Supabase PostgreSQL + pgvector
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

## Next Steps

1. Implement CV parser with OCR (PaddleOCR/EasyOCR)
2. Build job matching algorithm with vector similarity
3. Create RAG system for document generation
4. Add job scrapers for real data
5. Implement application automation

## License

POC Project - Academic Use
