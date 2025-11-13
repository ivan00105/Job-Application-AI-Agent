# Setup Guide

Quick setup instructions for the Job Application Agent.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Access to PostgreSQL database
- Access to JobsEngine service (Qdrant + Embeddings)

## Backend Setup

### 1. Create .env File

Create `backend/.env`:

```env
# PostgreSQL (Friend's database)
POSTGRES_HOST=pg.groture.com
POSTGRES_PORT=5130
POSTGRES_DB=job_agent
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# JobsEngine & Ollama (Get URLs from friend)
JOBSENGINE_URL=http://friend-url:8001
OLLAMA_URL=http://friend-url:11434
OLLAMA_CHAT_MODEL=llama3

# Security (Generate: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your_generated_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Server
HOST=0.0.0.0
PORT=8000
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Run Database Migration

```bash
python scripts/run_migration.py
```

### 4. Create Test Users

```bash
python scripts/create_test_users.py
```

### 5. Start Backend

```bash
python main.py
```

API docs: http://localhost:8000/docs

## Frontend Setup

```bash
npm install
npm run dev
```

Frontend: http://localhost:5173

## Test Credentials

- `testuser1` / `password123`
- `testuser2` / `password123`
- `demo` / `demo123`

## Troubleshooting

**Cannot connect to PostgreSQL:**
- Check `.env` credentials
- Verify database exists
- Test connection: `psql -h pg.groture.com -p 5130 -U username -d job_agent`

**Cannot connect to JobsEngine:**
- Verify JobsEngine is running
- Check JOBSENGINE_URL in `.env`
- Test: `curl http://jobsengine-url:8001/collections/`

**Import errors:**
- Make sure you're in `backend/` directory
- Check virtual environment is activated
- Reinstall: `pip install -r requirements.txt`

For more details, see `DEVELOPMENT.md`.

