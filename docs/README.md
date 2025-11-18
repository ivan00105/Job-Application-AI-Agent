# Job Application AI Agent

AI-powered job search, CV matching, and auto-fill applications.

## Quick Start

Get the backend API, web client, and browser extension running locally in minutes.

### Backend
```bash
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

### Frontend  
```bash
npm run dev
```

### Chrome Extension
```bash
cd extension
pip install Pillow
python create-icons.py
# chrome://extensions/ → Load unpacked → Select extension/ folder
```

### Database Setup
Set up PostgreSQL before running the backend services:

1. Install PostgreSQL 15+ locally or use a managed instance
2. Create a dedicated database and user
3. Apply the schema using `backend/migrations/initialised_schema.sql`
4. Configure the connection in `backend/.env`

## 📚 Documentation

**Essential Reading:**
- [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md) - Complete setup instructions for first-time users

**Configuration Examples:**
- `nginx.conf.example` - Nginx reverse proxy configuration example
- `Caddyfile.example` - Caddy reverse proxy configuration example

## Features

- **CV Management**: Upload PDF, auto-parse to structured JSON
- **Job Search**: Vector similarity search using Qdrant
- **AI Matching**: Score CV-to-job fit with explanations
- **Auto-Fill**: Purple floating button on job sites - click to auto-fill forms
- **Interview Prep**: AI-generated practice questions

## Auto-Fill Usage

1. **Install extension** (see above)
2. **Log in** to web app → Token syncs automatically
3. **Navigate** to any job application page
4. **Look for purple button** (bottom-right corner)
5. **Click it** when you're ready to auto-fill
6. **Review** filled fields and submit

That's it! No extra browser setup needed.

Additional backend/AI configuration:

1. Install and start [Ollama](https://ollama.ai) for local embeddings, then run:
   ```bash
   ollama pull bge-m3
   ```
2. Copy the backend environment template and customize it:
   ```bash
   cp backend/.env.example backend/.env
   ```
3. Edit the new `.env` and add:
   - PostgreSQL credentials
   - An OpenRouter API key from https://openrouter.ai/keys

### Button Status:
- "AI Auto-Fill" → Ready (click me!)
- "Analyzing..." → Checking page type
- "Scraping..." → Finding form fields  
- "Filling..." → AI filling with your CV
- "✓ Done" → Complete! Review and submit

## Tech Stack

**Backend:** FastAPI, PostgreSQL, Qdrant, Ollama, OpenRouter  
**Frontend:** React, TypeScript, Tailwind  
**Extension:** Chrome Manifest V3

## Environment Setup

Create `backend/.env`:
```bash
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=job_application_db
DB_USER=postgres
DB_PASSWORD=your_password
JWT_SECRET_KEY=your_secret
OLLAMA_BASE_URL=http://localhost:11434
OPENROUTER_API_KEY=your_key
QDRANT_URL=http://your_qdrant:6333
```

## Project Structure

```
backend/
├── api/              # FastAPI endpoints
├── models/           # Pydantic models
├── services/         # Business logic
│   ├── autofill/    # Auto-fill AI logic
│   ├── cv/          # CV parsing
│   └── jobs/        # Job matching
└── database/        # PostgreSQL client

src/
├── components/      # React components
├── pages/          # Page components
└── api/            # API client

extension/
├── manifest.json   # Extension config
├── content.js      # Form scraping & filling
├── background.js   # API communication
└── popup.html/js   # Extension UI
```

## Product Status

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

## Troubleshooting

### Extension button not appearing
- Reload the page (Ctrl+R)
- Check the extension is enabled at chrome://extensions/
- Reload the extension (click the refresh icon)

### ERR_BLOCKED_BY_CLIENT
- Disable ad blocker for localhost:5173
- Or whitelist the extension

### Not logged in error
- Log into the web app at http://localhost:5173
- The extension token syncs automatically after login

## Architecture

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

### AI Readiness
- Backend services folder prepared for AI components
- Vector embeddings supported in the database
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

### No fields found
- Make sure you're on application form, not job listing
- Click "Apply" button on job site first

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Technology Stack

- **Backend:** FastAPI, PostgreSQL, OpenRouter (LLM), Ollama (embeddings)
- **Frontend:** React 18, TypeScript, Tailwind CSS
- **AI Services:** OpenRouter API, Ollama (local embeddings)
- **Database:** PostgreSQL with Qdrant for vector search

## License

MIT
