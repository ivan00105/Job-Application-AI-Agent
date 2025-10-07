# Development Guide - Quick Reference

Quick reference for making changes to the Job Application Agent project.

## 📚 Documentation Index

- **First Time Setup**: [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md) - Complete setup instructions
- **Project Overview**: [README.md](README.md) - What this project does
- **Backend API Reference**: [backend/README.md](backend/README.md) - Backend-specific details
- **Feature Roadmap**: [FEATURE_IDEAS.md](FEATURE_IDEAS.md) - Planned features and ideas

---

## 🎯 Common Development Tasks

### Adding a New Frontend Page

1. **Create page component** in `src/pages/YourPage.tsx`
2. **Import dependencies**: React hooks, Tailwind CSS, Lucide icons
3. **Add route** in `src/App.tsx` inside the `<Routes>` section
4. **Wrap with `<ProtectedRoute>`** if authentication required
5. **Add navigation link** in `src/components/Layout.tsx` sidebar
6. **Use existing components** from `src/components/` when possible

**Example route:**
```tsx
<Route path="/your-page" element={<ProtectedRoute><YourPage /></ProtectedRoute>} />
```

---

### Creating New Backend API Endpoints

1. **Create/modify file** in `backend/api/` (e.g., `backend/api/bookmarks.py`)
2. **Define Pydantic models** in `backend/models/` for request/response validation
3. **Add business logic** in `backend/services/` if complex operations needed
4. **Write database queries** using Supabase client from `database/supabase_client.py`
5. **Include router** in `backend/main.py` if creating new API module
6. **Test endpoints** at http://localhost:8000/docs

**Example endpoint:**
```python
@router.post("/bookmarks")
async def create_bookmark(job_id: str, current_user: dict = Depends(get_current_user)):
    # Your logic here
    return {"status": "success"}
```

---

### Modifying Database Schema

1. **Create migration file** in `supabase/migrations/` with timestamp prefix: `YYYYMMDDHHMMSS_description.sql`
2. **Write SQL statements** with proper comments explaining changes
3. **Include indexes** for frequently queried columns
4. **Add foreign keys** if linking to other tables
5. **Apply migration** via Supabase dashboard SQL Editor or CLI
6. **Update backend models** in `backend/models/` to match new schema
7. **Handle existing data** carefully if modifying populated tables

**Migration file template:**
```sql
/*
  # Description of changes

  1. Tables modified
  2. Columns added/changed
  3. Security policies
*/

CREATE TABLE IF NOT EXISTS bookmarks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id) NOT NULL,
  job_id uuid REFERENCES jobs(id) NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
```

---

### Connecting to Commercial AI APIs

1. **Add API key** to `backend/.env` (e.g., `OPENAI_API_KEY=sk-...`)
2. **Install package** in `backend/requirements.txt` then run `pip install -r requirements.txt`
3. **Create service file** in `backend/services/` for AI logic
4. **Build prompt templates** with proper context
5. **Implement error handling** and fallback mechanisms
6. **Use async operations** to avoid blocking

**Example:**
```python
# backend/services/ai_service.py
import openai
from config import get_settings

settings = get_settings()
openai.api_key = settings.OPENAI_API_KEY

async def analyze_text(text: str):
    response = await openai.ChatCompletion.acreate(...)
    return response
```

---

### Integrating Open Source Models

1. **Choose model** from Hugging Face or set up Ollama for local inference
2. **Add to requirements.txt**: `transformers`, `torch`, `sentence-transformers`, etc.
3. **Run** `pip install -r requirements.txt` in backend venv
4. **Create service wrapper** in `backend/services/` to handle model loading
5. **Implement caching** to avoid reloading models on every request
6. **Consider memory requirements** and optimize batch processing
7. **Add configuration** to switch between local and cloud models

**Example:**
```python
# backend/services/local_model_service.py
from transformers import pipeline

model = None

def load_model():
    global model
    if model is None:
        model = pipeline("sentiment-analysis")
    return model
```

---

### Managing Environment Variables

#### Backend Configuration
- **Add variables** to `backend/.env`
- **Access in code**: Use `get_settings()` function from `backend/config.py`
- **Example**: `DATABASE_URL`, `OPENAI_API_KEY`, `SECRET_KEY`

#### Frontend Configuration
- **Add variables** to root `.env` with `VITE_` prefix
- **Access in code**: `import.meta.env.VITE_VARIABLE_NAME`
- **Example**: `VITE_SUPABASE_URL`, `VITE_API_URL`

**Important:**
- Never commit `.env` files to version control
- Update `.env.example` files with placeholder values
- Restart servers after changing environment variables

---

### Installing New Dependencies

#### Frontend (React/TypeScript)
```bash
npm install package-name
# Dependencies automatically added to package.json
```

#### Backend (Python/FastAPI)
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install package-name
pip freeze > requirements.txt  # Update requirements file
```

**Always verify** new packages don't conflict with existing dependencies.

---

## 🚀 Quick Commands

### Start Development Servers

```bash
# Backend (Terminal 1)
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py

# Frontend (Terminal 2)
npm run dev
```

### Access Points
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Testing & Building
```bash
# Test backend endpoint
curl http://localhost:8000/api/auth/me -H "Authorization: Bearer YOUR_TOKEN"

# Build frontend
npm run build

# Type check
npm run typecheck
```

---

## 📁 Project Structure Quick Reference

```
project/
├── backend/              # Python FastAPI backend
│   ├── api/             # API endpoints (add new routes here)
│   ├── models/          # Pydantic models (data validation)
│   ├── services/        # Business logic & AI (add AI code here)
│   ├── database/        # Database client (Supabase)
│   ├── scripts/         # Utility scripts
│   └── main.py          # Entry point
│
├── src/                 # React TypeScript frontend
│   ├── api/            # API client functions (add API calls here)
│   ├── components/     # Reusable components (add shared UI here)
│   ├── context/        # React context (state management)
│   ├── pages/          # Page components (add new pages here)
│   └── App.tsx         # Main app with routes
│
├── supabase/migrations/ # Database migrations (add schema changes here)
└── .env                # Environment variables (frontend)
```

---

## 🐛 Quick Troubleshooting

**Backend won't start:**
- Check virtual environment is activated (`source venv/bin/activate`)
- Verify `backend/.env` file exists with Supabase credentials
- Check port 8000 is not in use

**Frontend errors:**
- Ensure backend is running on http://localhost:8000
- Check browser console for specific errors
- Verify `.env` has correct `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`

**Database errors:**
- Verify Supabase credentials in `backend/.env`
- Check Supabase project is active in dashboard
- Ensure migrations were applied

**Import errors:**
- Frontend: Run `npm install`
- Backend: Activate venv and run `pip install -r requirements.txt`

---

## 🔐 Security Best Practices

- Never commit `.env` files or API keys to git
- Use Row Level Security (RLS) policies for all Supabase tables
- Validate all user inputs with Pydantic models
- Use JWT tokens for authentication (already implemented)
- Sanitize data before database queries

---

## 📝 Code Style Guidelines

- **Frontend**: Use TypeScript, Tailwind CSS classes, Lucide icons
- **Backend**: Use type hints, async/await, Pydantic models
- **Components**: Build reusable components with composition pattern
- **API**: Follow REST conventions, return proper status codes
- **Database**: Always use parameterized queries, never string concatenation

---

## 🌐 Self-Hosting Notes

**Current Setup**: Using Supabase managed database (PostgreSQL + pgvector)

**Future Self-Hosting**: Possible but requires:
- Self-hosted PostgreSQL with pgvector extension
- Configuration changes in `backend/.env`
- Manual database backups and management
- Connection pooling setup for production

For now, Supabase managed database is recommended for simplicity.

---

## 📞 Need Help?

1. **Check API docs**: http://localhost:8000/docs
2. **Review existing code**: Look at similar features for patterns
3. **Check Supabase dashboard**: Verify data and schema
4. **Console logs**: Use browser console (frontend) and terminal (backend)
5. **Read error messages**: They usually tell you exactly what's wrong

---

**Happy coding! 🚀**
