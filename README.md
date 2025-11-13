# Job Application Agent

AI-powered job search and application automation system.

## Quick Start

**First time setup:**
1. See [SETUP.md](SETUP.md) for installation instructions
2. Read [DEVELOPMENT.md](DEVELOPMENT.md) before making changes

**Already set up?**
```bash
# Start backend
cd backend && python main.py

# Start frontend
npm run dev
```

## Architecture

```
├── backend/              # FastAPI + PostgreSQL
│   ├── api/             # REST endpoints
│   ├── services/        # Business logic
│   │   ├── shared/      # Shared services (Qdrant client)
│   │   ├── cv/          # CV parsing
│   │   ├── jobs/        # Job matching
│   │   └── interview/   # Interview prep
│   ├── models/          # Pydantic models
│   └── database/        # PostgreSQL client
│
├── jobsengine/          # Vector search service (Qdrant + Embeddings)
│
└── src/                 # React frontend
    ├── pages/           # Page components
    ├── components/      # Reusable components
    └── api/             # API client
```

## Features

**Current:**
- ✅ User authentication (JWT)
- ✅ CV upload & parsing
- ✅ Job search with vector similarity
- ✅ CV-to-job matching
- ✅ Interview preparation

**Coming Soon:**
- Job scraping automation
- RAG-powered cover letter generation
- Application auto-fill
- Advanced interview prep with RAG

## Tech Stack

**Backend:**
- FastAPI (async Python)
- PostgreSQL (metadata storage)
- Qdrant (vector search via JobsEngine)
- Ollama (LLM for parsing & generation)

**Frontend:**
- React 18 + TypeScript
- React Router
- Tailwind CSS
- Axios

## Documentation

- [SETUP.md](SETUP.md) - Installation & setup
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development guide
- [backend/README.md](backend/README.md) - Backend API reference
- [FEATURE_IDEAS.md](FEATURE_IDEAS.md) - Feature roadmap

## Test Accounts

- `testuser1` / `password123`
- `testuser2` / `password123`
- `demo` / `demo123`

## License

POC Project - Academic Use
