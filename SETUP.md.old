# Setup Guide - Job Application Agent

Complete setup guide for running the application.

## Prerequisites

- Python 3.9+ (for backend)
- Node.js 18+ (for frontend)
- Supabase account (database already configured)

## Database Setup

✅ **Already Complete!**

The database schema has been created with:
- Users table (authentication)
- CV profiles table with vector embeddings
- Jobs table with vector search
- Job matches table
- Applications table
- pgvector extension enabled

## Backend Setup

### 1. Navigate to backend folder
```bash
cd backend
```

### 2. Create Python virtual environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment configuration
The `.env` file is already created with Supabase credentials. You can add AI API keys later:
```bash
# backend/.env already contains:
# - SUPABASE_URL
# - SUPABASE_KEY
# - SECRET_KEY

# Optional: Add AI API keys when needed
# OPENAI_API_KEY=your_key
# GROQ_API_KEY=your_key
```

### 5. Create test users
```bash
python scripts/create_test_users.py
```

This creates three test accounts:
- `testuser1` / `password123`
- `testuser2` / `password123`
- `demo` / `demo123`

### 6. Run the backend server
```bash
python main.py
```

Backend will run at: **http://localhost:8000**

API documentation: **http://localhost:8000/docs**

## Frontend Setup

### 1. Navigate to project root
```bash
cd ..  # If you're in backend folder
```

### 2. Install dependencies
```bash
npm install
```

### 3. Run development server
```bash
npm run dev
```

Frontend will run at: **http://localhost:5173**

## Testing the Application

### 1. Start Backend
```bash
# Terminal 1
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

### 2. Start Frontend
```bash
# Terminal 2 (new terminal)
npm run dev
```

### 3. Access the Application

Open browser: **http://localhost:5173**

Login with test account:
- Username: `testuser1`
- Password: `password123`

### 4. Test Features

**Current Working Features:**
- ✅ User login/logout
- ✅ CV upload (placeholder - parsing not yet implemented)
- ✅ Job browsing (no jobs yet - scraping not yet implemented)
- ✅ Job matches view (algorithm not yet implemented)
- ✅ Responsive UI with navigation

**Coming in AI Phase:**
- 🔄 CV parsing with OCR
- 🔄 Job matching algorithm
- 🔄 Document generation (resume/cover letter)
- 🔄 Job scraping
- 🔄 Application automation

## API Testing

You can test the API directly at: **http://localhost:8000/docs**

The Swagger UI provides:
- Interactive API documentation
- Try out all endpoints
- See request/response schemas
- Test authentication

### Example API Flow:

1. **Login**
   - POST `/api/auth/token`
   - Body: `username=testuser1&password=password123`
   - Returns JWT token

2. **Upload CV**
   - POST `/api/cv/upload`
   - Headers: `Authorization: Bearer <token>`
   - Body: File upload

3. **Get Profile**
   - GET `/api/cv/profile`
   - Headers: `Authorization: Bearer <token>`

4. **Search Jobs**
   - GET `/api/jobs`
   - Headers: `Authorization: Bearer <token>`

## Troubleshooting

### Backend won't start
- Check if port 8000 is available
- Verify .env file exists in backend folder
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

### Frontend won't start
- Check if port 5173 is available
- Run `npm install` again
- Clear node_modules: `rm -rf node_modules && npm install`

### Login fails
- Make sure backend is running
- Check browser console for errors
- Verify test users were created: `python scripts/create_test_users.py`

### Database errors
- Verify Supabase credentials in backend/.env
- Check Supabase project is active
- Ensure migrations were applied (already done)

## Project Structure

```
job-agent/
├── backend/              # FastAPI Python backend
│   ├── api/             # API endpoints
│   ├── models/          # Pydantic models
│   ├── services/        # Business logic (AI goes here)
│   ├── database/        # Database client
│   ├── scripts/         # Utility scripts
│   ├── main.py          # Entry point
│   └── requirements.txt # Python dependencies
│
├── src/                 # React frontend
│   ├── api/            # API client
│   ├── components/     # React components
│   ├── context/        # Auth context
│   ├── pages/          # Page components
│   └── App.tsx         # Main app
│
├── package.json        # Node dependencies
└── README.md          # Project overview
```

## Next Steps

The foundation is complete! Next phases:

1. **CV Parser** - Implement OCR and structured extraction
2. **Job Scraper** - Scrape jobs from JobsDB, LinkedIn, Indeed
3. **Matching Algorithm** - Build semantic matching with vector search
4. **RAG System** - Generate tailored resumes and cover letters
5. **Automation** - Semi-automated application filling

All the infrastructure is ready for AI integration!

## Notes

- Backend uses FastAPI for auto-generated API docs
- Frontend uses React Router for navigation
- Authentication uses JWT tokens
- Database uses Supabase PostgreSQL with pgvector
- All AI logic will go in `backend/services/` folder
- Current endpoints return placeholder data ready for AI integration
