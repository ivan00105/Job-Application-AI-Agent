# Local Setup Guide - Job Application Agent with Interview Prep

Complete guide for setting up this project on your local machine.

---

## 📋 Prerequisites

Before you begin, ensure you have:
- **Python 3.9+** installed
- **Node.js 18+** and npm installed
- **PostgreSQL 15+** installed locally (or access to a PostgreSQL server)
- **Git** installed

---

## 🗄️ Part 1: PostgreSQL Database Setup

### Step 1: Install PostgreSQL

1. Download PostgreSQL 15+ from [postgresql.org/download](https://www.postgresql.org/download/)
2. Install both the database server and the `psql` command-line client
3. Remember the superuser password you choose during installation

### Step 2: Create a Database and User

1. Open a terminal and run `psql -U postgres`
2. Create a dedicated database user and database:
   ```sql
   CREATE USER job_agent WITH PASSWORD 'your-strong-password';
   CREATE DATABASE job_agent OWNER job_agent;
   \q
   ```
3. Update `backend/.env` later with these values

### Step 3: Apply Database Migrations

You can run migrations with the helper script or manually via `psql`.

**Option A: Using the Python helper script**
```bash
cd backend
python scripts/run_migration.py
```

**Option B: Using psql directly**
```bash
psql -U job_agent -d job_agent -f backend/migrations/create_initial_schema.sql
psql -U job_agent -d job_agent -f backend/migrations/add_application_statuses.sql
psql -U job_agent -d job_agent -f backend/migrations/create_preparation_tables.sql
psql -U job_agent -d job_agent -f backend/migrations/create_interview_tables_postgres.sql
```

### Step 4: Verify Database

1. Go to **Table Editor** in Supabase dashboard
2. You should see these tables:
   - `users`
   - `cv_profiles`
   - `jobs`
   - `job_matches`
   - `applications`
   - `interview_questions`
   - `interview_sessions`
   - `interview_responses`
   - `interview_knowledge_base`
   - `interview_performance_analytics`

---

## 🐍 Part 2: Backend Setup (Python/FastAPI)

### Step 1: Navigate to Backend Folder

```bash
cd backend
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows (Command Prompt):
venv\Scripts\activate

# On Windows (PowerShell):
venv\Scripts\Activate.ps1
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, Supabase client, AI libraries, and other dependencies.

### Step 4: Configure Environment Variables

Create a `.env` file in the `backend/` folder:

```bash
# Copy the example file
cp .env.example .env

# Then edit .env with your values
```

Edit `backend/.env` with your actual values:

```env
# PostgreSQL Configuration (REQUIRED)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=job_agent
POSTGRES_USER=job_agent
POSTGRES_PASSWORD=your-strong-password

# API Configuration (REQUIRED)
SECRET_KEY=your-super-secret-key-change-this-to-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Server Configuration (Optional)
HOST=0.0.0.0
PORT=8000

# AI API Keys (Optional - for interview evaluation)
OPENAI_API_KEY=sk-...your_key  # For GPT-4 evaluation
ANTHROPIC_API_KEY=sk-ant-...your_key  # For Claude evaluation
# Leave blank to use mock evaluation for testing
```

**Important Notes:**
- Use the PostgreSQL credentials you created in Part 1
- Generate a secure `SECRET_KEY` (run: `openssl rand -hex 32`)
- AI keys are optional - the system has mock evaluation for testing without them

### Step 5: Seed Initial Data

```bash
# Create test users
python scripts/create_test_users.py

# Seed interview questions
python scripts/seed_interview_questions.py
```

This creates:
- 3 test user accounts
- 14 sample interview questions (IT and Finance domains)

### Step 6: Run the Backend Server

```bash
python main.py
```

You should see:
```
🚀 Starting Job Application Agent API...
📝 API Documentation: http://0.0.0.0:8000/docs
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ Backend is now running at: **http://localhost:8000**

📚 API docs available at: **http://localhost:8000/docs**

**Keep this terminal open!**

---

## ⚛️ Part 3: Frontend Setup (React/TypeScript)

Open a **NEW terminal window** (keep backend running).

### Step 1: Navigate to Project Root

```bash
cd /path/to/your/project
# (Make sure you're in the root folder, not backend/)
```

### Step 2: Install Node Dependencies

```bash
npm install
```

This installs React, TypeScript, Vite, Tailwind CSS, and other frontend dependencies.

### Step 3: Configure Environment Variables

Create or update the frontend `.env` at the project root with:

```env
VITE_API_URL=http://localhost:8000
```

Set this to whatever host/port your backend is using.

### Step 4: Run the Frontend Development Server

```bash
npm run dev
```

You should see:
```
VITE v5.4.8  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

✅ Frontend is now running at: **http://localhost:5173**

---

## 🎉 Part 4: Test the Application

### Step 1: Open in Browser

Go to: **http://localhost:5173**

### Step 2: Login

Use one of the test accounts:
- **Username:** `testuser1`
- **Password:** `password123`

Or:
- **Username:** `demo`
- **Password:** `demo123`

### Step 3: Explore Features

#### Available Features:

1. **Dashboard** - View job matches (placeholder)
2. **Jobs** - Browse job listings (empty for now)
3. **Interview Prep** ⭐ NEW!
   - Start IT or Finance practice sessions
   - Answer interview questions
   - Get AI feedback with detailed scores
   - View performance analytics
4. **My CV** - Upload CV (placeholder)

#### Test Interview Prep:

1. Click **"Interview Prep"** in navigation
2. Choose **"Start IT Interview"** or **"Start Finance Interview"**
3. Answer the questions (minimum 10 characters)
4. Submit to get AI evaluation
5. Continue through all questions
6. View results and analytics

---

## 🔧 Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError` when running backend
```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Problem:** Database connection errors
```bash
# Solution: Check backend/.env has correct Supabase credentials
# Test connection in Supabase dashboard
```

**Problem:** Port 8000 already in use
```bash
# Solution: Change port in backend/.env
PORT=8001

# Or kill the process using port 8000
# On Linux/Mac:
lsof -ti:8000 | xargs kill -9
# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Frontend Issues

**Problem:** `npm install` fails
```bash
# Solution: Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Problem:** Port 5173 already in use
```bash
# Solution: Vite will automatically use next available port
# Or specify port:
npm run dev -- --port 3000
```

**Problem:** "Cannot connect to backend" errors
```bash
# Solution: Ensure backend is running on http://localhost:8000
# Check browser console for CORS errors
```

### Database Issues

**Problem:** Migrations fail to apply
```bash
# Solution: Check for existing tables with same names
# In Supabase SQL Editor, run:
DROP TABLE IF EXISTS interview_questions CASCADE;
# Then re-run migration
```

**Problem:** No test users exist
```bash
# Solution: Re-run the seeding script
cd backend
python scripts/create_test_users.py
```

---

## 📁 Project Structure

```
job-agent/
├── backend/                      # Python FastAPI backend
│   ├── api/                     # API route handlers
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── cv.py               # CV management
│   │   ├── jobs.py             # Job listings
│   │   ├── matches.py          # Job matching
│   │   └── interview.py        # Interview prep endpoints ⭐
│   ├── models/                  # Pydantic data models
│   │   ├── user.py
│   │   ├── cv.py
│   │   ├── job.py
│   │   └── interview.py        # Interview models ⭐
│   ├── services/                # Business logic
│   │   └── interview_service.py # AI evaluation ⭐
│   ├── database/                # Database client
│   ├── scripts/                 # Utility scripts
│   │   ├── create_test_users.py
│   │   └── seed_interview_questions.py ⭐
│   ├── .env                     # Environment variables (create this!)
│   ├── main.py                  # FastAPI entry point
│   └── requirements.txt         # Python dependencies
│
├── src/                         # React TypeScript frontend
│   ├── api/                    # API client layer
│   │   ├── client.ts           # Axios setup & existing APIs
│   │   └── interviewClient.ts  # Interview API client ⭐
│   ├── components/             # Reusable components
│   │   ├── Layout.tsx          # Navigation layout (updated) ⭐
│   │   └── ProtectedRoute.tsx  # Auth guard
│   ├── context/                # React context
│   │   └── AuthContext.tsx     # Authentication state
│   ├── pages/                  # Page components
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── JobsPage.tsx
│   │   ├── ProfilePage.tsx
│   │   ├── InterviewPrepPage.tsx      # Interview hub ⭐
│   │   ├── InterviewSessionPage.tsx   # Active session ⭐
│   │   ├── InterviewResultsPage.tsx   # Session results ⭐
│   │   └── InterviewAnalyticsPage.tsx # Performance analytics ⭐
│   ├── App.tsx                 # Main app with routing (updated) ⭐
│   └── index.css               # Global styles
│
├── backend/migrations/          # Database migrations
│   ├── create_initial_schema.sql
│   ├── add_application_statuses.sql
│   ├── create_preparation_tables.sql
│   └── create_interview_tables_postgres.sql ⭐
│
├── .env                         # Frontend environment variables
├── package.json                 # Node dependencies
├── vite.config.ts              # Vite configuration
├── tailwind.config.js          # Tailwind CSS config
└── README.md                    # Project overview
```

⭐ = New files for Interview Preparation feature

---

## 🚀 What's Next?

### Current Features (Working Now)
✅ User authentication with JWT
✅ CV upload interface (parsing not implemented yet)
✅ Job browsing UI (no real data yet)
✅ **Interview Preparation System** (fully functional!)
  - IT and Finance domain questions
  - AI-powered evaluation
  - Performance tracking
  - Analytics dashboard

### Future AI Features (Not Yet Implemented)
🔄 CV parsing with OCR (PaddleOCR)
🔄 Job scraping (JobsDB, LinkedIn, Indeed)
🔄 Vector-based job matching algorithm
🔄 RAG-powered resume/cover letter generation
🔄 Semi-automated application filling

### Ideas for Enhancement

**Interview Prep Enhancements:**
1. Add more question categories (system design, coding challenges)
2. Implement RAG knowledge base with lecture notes
3. Add job-specific interview preparation
4. Implement difficulty progression based on performance
5. Add voice recording for answers
6. Compare answers with ideal responses side-by-side

**General Features:**
1. User profile page with settings
2. Job bookmarking/favorites
3. Application tracking dashboard
4. Email notifications
5. Chrome extension for job scraping
6. LinkedIn integration
7. Company research assistant

---

## 🔐 Security Notes

**For Development:**
- Test users have weak passwords - this is OK for local development
- SECRET_KEY should be changed for any deployment
- API keys should never be committed to git

**For Production:**
- Use strong passwords
- Configure PostgreSQL roles/permissions carefully (RLS if needed)
- Use environment variables for all secrets
- Enable HTTPS
- Add rate limiting
- Implement proper error handling

---

## 📞 Getting Help

**Common Commands:**

```bash
# Backend
cd backend
source venv/bin/activate
python main.py

# Frontend
npm run dev

# Database check
psql -U job_agent -d job_agent -c '\dt'

# View API docs
# http://localhost:8000/docs
```

**Useful Links:**
- PostgreSQL Docs: https://www.postgresql.org/docs/
- FastAPI Docs: https://fastapi.tiangolo.com
- React Docs: https://react.dev
- Tailwind CSS: https://tailwindcss.com

---

## ✅ Setup Checklist

Use this checklist to track your setup progress:

### Database Setup
- [ ] Installed PostgreSQL locally or provisioned a server
- [ ] Created `job_agent` database and user
- [ ] Applied `backend/migrations/create_initial_schema.sql`
- [ ] Applied `backend/migrations/add_application_statuses.sql`
- [ ] Applied `backend/migrations/create_preparation_tables.sql`
- [ ] Applied `backend/migrations/create_interview_tables_postgres.sql`
- [ ] Verified tables exist via `\dt` in `psql`

### Backend Setup
- [ ] Installed Python 3.9+
- [ ] Created virtual environment
- [ ] Installed dependencies
- [ ] Created `backend/.env` file
- [ ] Added PostgreSQL credentials
- [ ] Generated SECRET_KEY
- [ ] Created test users
- [ ] Seeded interview questions
- [ ] Started backend server successfully
- [ ] Verified API docs at /docs

### Frontend Setup
- [ ] Installed Node.js 18+
- [ ] Installed npm dependencies
- [ ] Updated `.env` with `VITE_API_URL`
- [ ] Started frontend dev server
- [ ] Opened app in browser
- [ ] Logged in successfully
- [ ] Tested interview prep feature

### Optional (AI Features)
- [ ] Added OPENAI_API_KEY or ANTHROPIC_API_KEY
- [ ] Tested real AI evaluation

---

**You're all set! Enjoy building with the Job Application Agent! 🎉**
