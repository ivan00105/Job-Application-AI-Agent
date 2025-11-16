# Job Application AI Agent

AI-powered job search, CV matching, and auto-fill applications.

## Quick Start

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

That's it! No setup needed.

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

## Troubleshooting

### Extension button not appearing
- Reload page (Ctrl+R)
- Check extension enabled at chrome://extensions/
- Reload extension (click refresh icon)

### ERR_BLOCKED_BY_CLIENT
- Disable ad blocker for localhost:5173
- Or whitelist the extension

### Not logged in error
- Log into web app at localhost:5173
- Token syncs automatically

### No fields found
- Make sure you're on application form, not job listing
- Click "Apply" button on job site first

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
