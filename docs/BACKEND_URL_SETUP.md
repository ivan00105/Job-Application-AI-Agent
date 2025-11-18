# Backend External URL Configuration Guide

This guide explains how to configure the backend external URL so that API calls from the frontend are successful.

## Quick Setup

### Step 1: Configure Backend External URL

Create or update `backend/.env`:

```bash
# Option A: Direct access (no reverse proxy)
EXTERNAL_URL=http://YOUR_SERVER_IP:8000

# Option B: Reverse proxy with domain
EXTERNAL_URL=https://your-domain.com

# Option C: Local development
EXTERNAL_URL=http://localhost:8000
```

### Step 2: Configure Frontend API URL

Create or update `.env` in the project root (same level as `package.json`):

```bash
# Must match the backend EXTERNAL_URL
VITE_API_URL=http://YOUR_SERVER_IP:8000
# OR
VITE_API_URL=https://your-domain.com
```

### Step 3: Update CORS Origins

In `backend/.env`, add your frontend URL to allowed origins:

```bash
ALLOWED_ORIGINS=http://localhost:5173,http://YOUR_SERVER_IP:5173,https://your-domain.com
```

### Step 4: Restart Both Servers

```bash
# Backend
cd backend
python main.py

# Frontend (in project root)
npm run dev
```

## Configuration Examples

### Example 1: Local Development

**Backend `backend/.env`:**
```bash
EXTERNAL_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

**Frontend `.env`:**
```bash
VITE_API_URL=http://localhost:8000
```

### Example 2: Remote Access (Direct, No Reverse Proxy)

**Backend `backend/.env`:**
```bash
EXTERNAL_URL=http://192.168.1.100:8000
ALLOWED_ORIGINS=http://localhost:5173,http://192.168.1.100:5173,http://192.168.1.100:3000
```

**Frontend `.env`:**
```bash
VITE_API_URL=http://192.168.1.100:8000
```

**Important:** 
- Replace `192.168.1.100` with your actual server IP
- Ensure firewall allows port 8000
- Backend must bind to `0.0.0.0` (already configured)

### Example 3: Remote Access (With Reverse Proxy)

**Backend `backend/.env`:**
```bash
EXTERNAL_URL=https://api.yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,http://yourdomain.com
ROOT_PATH=
TRUSTED_PROXY_HOSTS=127.0.0.1
```

**Frontend `.env`:**
```bash
VITE_API_URL=https://api.yourdomain.com
```

**Nginx Configuration:**
- Backend runs on `localhost:8000`
- Nginx proxies `https://api.yourdomain.com` → `http://localhost:8000`
- Frontend is served from `https://yourdomain.com`

### Example 4: Same Domain (Frontend and Backend)

**Backend `backend/.env`:**
```bash
EXTERNAL_URL=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,http://yourdomain.com
ROOT_PATH=
TRUSTED_PROXY_HOSTS=127.0.0.1
```

**Frontend `.env`:**
```bash
VITE_API_URL=https://yourdomain.com
```

**Nginx Configuration:**
- Frontend: `https://yourdomain.com/` → serves static files
- Backend API: `https://yourdomain.com/api` → proxies to `http://localhost:8000/api`

## How It Works

1. **Backend `EXTERNAL_URL`**: 
   - Tells the backend what URL clients should use
   - Used in logs and documentation links
   - Helps with URL generation in responses

2. **Frontend `VITE_API_URL`**:
   - Tells the frontend where to send API requests
   - Must match `EXTERNAL_URL` (or the URL clients actually use)

3. **CORS `ALLOWED_ORIGINS`**:
   - Backend allows requests from these origins
   - Must include your frontend URL(s)

## Verification

### 1. Check Backend Startup

When you start the backend, you should see:
```
Starting Job Application Agent API on 0.0.0.0:8000
External URL: http://YOUR_SERVER_IP:8000
API docs: http://YOUR_SERVER_IP:8000/docs
```

### 2. Test Backend Directly

```bash
# From any machine that can reach the server
curl http://YOUR_SERVER_IP:8000/health
# Should return: {"status":"healthy"}
```

### 3. Test from Frontend

1. Open browser DevTools (F12)
2. Go to Network tab
3. Try to use the frontend
4. Check if API calls are successful
5. Look for CORS errors in Console tab

### 4. Check API URL in Browser Console

```javascript
// In browser console
console.log(import.meta.env.VITE_API_URL)
// Should show your configured API URL
```

## Troubleshooting

### Issue: "Connection Refused"

**Causes:**
- Backend not running
- Wrong IP/port in `VITE_API_URL`
- Firewall blocking port 8000

**Fix:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `VITE_API_URL` matches backend `EXTERNAL_URL`
3. Open firewall port 8000

### Issue: CORS Errors

**Causes:**
- Frontend URL not in `ALLOWED_ORIGINS`
- Protocol mismatch (HTTP vs HTTPS)

**Fix:**
1. Add frontend URL to `ALLOWED_ORIGINS` in `backend/.env`
2. Ensure protocol matches (both HTTP or both HTTPS)
3. Restart backend after changing CORS

### Issue: Wrong API URL in Requests

**Causes:**
- `.env` file not in correct location
- Dev server not restarted after changing `.env`
- Environment variable not prefixed with `VITE_`

**Fix:**
1. Ensure `.env` is in project root (not in `src/` or `backend/`)
2. Restart frontend dev server after changing `.env`
3. Verify variable name is `VITE_API_URL` (not `API_URL`)

## Environment Variables Summary

### Backend (`backend/.env`)
```bash
# Required for remote access
EXTERNAL_URL=http://YOUR_SERVER_IP:8000
ALLOWED_ORIGINS=http://localhost:5173,http://YOUR_SERVER_IP:5173

# Optional (for reverse proxy)
ROOT_PATH=
TRUSTED_PROXY_HOSTS=127.0.0.1
```

### Frontend (`.env` in project root)
```bash
# Required - must match backend EXTERNAL_URL
VITE_API_URL=http://YOUR_SERVER_IP:8000
```

## Next Steps

- See `REVERSE_PROXY_SETUP.md` for setting up nginx/Caddy
- See `TROUBLESHOOTING.md` for detailed troubleshooting
- See `QUICK_FIX.md` for immediate fixes

