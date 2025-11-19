# Setup Guide

This is the canonical guide for running the job-search platform, web dashboard, and Chrome auto-fill extension. Follow the sections below in order—everything else (docs, READMEs, blog posts) point back here.

---

## Table of Contents

1. [Pre-flight checklist](#pre-flight-checklist)
2. [PostgreSQL & database schema](#postgresql--database-schema)
3. [Backend (FastAPI)](#backend-fastapi)
4. [Frontend (React/Vite)](#frontend-reactvite)
5. [Chrome extension](#chrome-extension)
6. [Supporting AI services](#supporting-ai-services)
7. [Seed data & helper scripts](#seed-data--helper-scripts)
8. [Environment variable reference](#environment-variable-reference)
9. [Troubleshooting](#troubleshooting)
10. [Security checklist](#security-checklist)

---

## Pre-flight checklist

Install or provision the following before touching the repo:

| Tool | Version | Notes |
| --- | --- | --- |
| Python | 3.9+ | Used for the FastAPI backend and helper scripts |
| Node.js | 18+ | Needed for the Vite/React web app |
| npm | ships with Node | `pnpm`/`yarn` also work if you prefer |
| PostgreSQL | 15+ | Primary datastore |
| Git | latest | Required for cloning and keeping up to date |
| Chrome / Chromium | latest | To load the development extension |
| Optional: Docker | latest | For local PostgreSQL/Qdrant if you do not want native installs |

---

## PostgreSQL & database schema

1. **Install PostgreSQL 15+**  
   Download from [postgresql.org/download](https://www.postgresql.org/download/) and ensure `psql` is on your PATH.

2. **Create a dedicated role and database**
   ```sql
   -- inside psql (run: psql -U postgres)
   CREATE USER job_agent WITH PASSWORD 'replace-with-strong-password';
   CREATE DATABASE job_agent OWNER job_agent;
   \q
   ```

3. **Apply the schema**
   ```bash
   # Option A: direct psql
   psql -U job_agent -d job_agent -f backend/migrations/initialised_schema.sql

   # Option B: helper script (wraps the same file)
   cd backend
   python scripts/run_migration.py
   ```

4. **Verify tables exist**
   ```bash
   psql -U job_agent -d job_agent -c '\dt'
   ```
   Expect tables such as `users`, `jobs`, `applications`, `tailored_cvs`, `interview_sessions`, etc.

---

## Backend (FastAPI)

1. **Create and activate a virtual environment**
   ```bash
   cd backend
   python -m venv venv
   # macOS/Linux
   source venv/bin/activate
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env`**
   ```bash
   cp .env.example .env
   ```
   Fill in the values from the [Environment reference](#environment-variable-reference) below.

4. **Run database migrations (if you skipped the earlier section)**
   ```bash
   python scripts/run_migration.py
   ```

5. **Seed development data (optional but handy)**
   ```bash
   python scripts/create_test_users.py
   python scripts/seed_interview_questions.py
   ```

6. **Start the API**
   ```bash
   python main.py
   ```
   - API: http://localhost:8000  
   - Docs: http://localhost:8000/docs

Keep the terminal open; the React app and extension talk to this server.

---

## Frontend (React/Vite)

1. Install dependencies (from repo root or `src/` folder depending on your workflow)
   ```bash
   npm install
   ```
2. Start Vite:
   ```bash
   npm run dev
   ```
3. Vite prints a URL (default `http://localhost:5173`). Leave this running.

---

## Chrome extension

1. Build icons (only needed the first time or when updating)
   ```bash
   cd extension
   pip install Pillow
   python create-icons.py
   ```
2. Load the unpacked extension:
   - Open `chrome://extensions`
   - Enable **Developer mode**
   - Click **Load unpacked** → select the `extension/` folder
3. A purple “AI Auto-Fill” button should appear on job forms once the backend + frontend are running and you are logged into the web app.

---

## Supporting AI services

### OpenRouter (LLM API)
1. Create an account at [openrouter.ai](https://openrouter.ai/keys).
2. Generate an API key and store it in `backend/.env` as `OPENROUTER_API_KEY`.
3. Optionally tweak `OPENROUTER_MODEL` (default `openai/gpt-oss-120b`) or `OPENROUTER_MAX_TOKENS`.

### Ollama (local embeddings)
1. Install from [ollama.ai](https://ollama.ai).
2. Start the Ollama server (`ollama serve`).
3. Pull the embedding model used by the project:
   ```bash
   ollama pull bge-m3
   ```
4. Confirm `OLLAMA_BASE_URL` and `OLLAMA_EMBEDDING_MODEL` in `.env`.

Optional services such as Qdrant can be pointed to via the environment file if you run vector search externally.

---

## Seed data & helper scripts

All scripts live in `backend/scripts/`:

| Script | Purpose |
| --- | --- |
| `run_migration.py` | Applies the combined SQL schema |
| `create_test_users.py` | Inserts sample accounts for staging/demo |
| `seed_interview_questions.py` | Loads baseline interview prompts |
| `jobs-scraper/*.py` | Scheduled scraping & maintenance utilities |

Run scripts with the virtual environment activated so dependencies resolve correctly.

---

## Environment variable reference

`backend/.env` template (trim or extend as needed):

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=job_agent
POSTGRES_USER=job_agent
POSTGRES_PASSWORD=your-strong-password

# Auth
SECRET_KEY=generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Services
HOST=0.0.0.0
PORT=8000
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=openai/gpt-oss-120b
OPENROUTER_MAX_TOKENS=8000
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=bge-m3

# Optional flags
KEEP_CV_FILES=false
LOG_LEVEL=info
```

**Important:** `.env` is git-ignored. Never commit real keys, passwords, or JWT secrets.

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Extension button is missing | Reload the page, confirm you are on a form (not list view), verify the extension is enabled |
| “Not logged in” toast | Visit http://localhost:5173, log in, and refresh the job page so the token syncs |
| `ERR_BLOCKED_BY_CLIENT` | Disable ad blockers for `localhost:5173` |
| Backend cannot reach PostgreSQL | Double-check credentials in `.env` and ensure PostgreSQL accepts TCP connections |
| LLM requests fail | Confirm `OPENROUTER_API_KEY` and network egress; inspect backend logs |
| Embedding errors | Ensure Ollama is running and the `bge-m3` model is downloaded |

---

## Security checklist

- [x] `.env`, `.env.local`, and other secret files are ignored by Git  
- [x] API keys live only in environment variables or secret managers  
- [x] Sample values in docs use placeholders (`your-secret-here`)  
- [x] Before making the repo public, re-run a secret scan (e.g., `trufflehog`, `gitleaks`)  
- [x] Rotate any key you accidentally exposed during development  
- [x] Review browser-extension code before publishing to the Chrome Web Store

When in doubt, delete the suspect credential, generate a new one, and update the environment file.

---

Happy building!
