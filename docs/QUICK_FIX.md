# Quick Fix: "Refuse to Connect" Error

## Immediate Steps

### 1. Configure Backend External URL

**Create or update `backend/.env`:**

```bash
# For local development
EXTERNAL_URL=http://localhost:8000

# For remote access (direct, no reverse proxy)
EXTERNAL_URL=http://YOUR_SERVER_IP:8000

# For remote access (with reverse proxy)
# EXTERNAL_URL=https://your-domain.com
```

### 2. Configure Frontend API URL

**Create `.env` file in project root** (if it doesn't exist):

```bash
# Must match backend EXTERNAL_URL
# For local development
VITE_API_URL=http://localhost:8000

# For remote access (replace with your server IP/domain)
# VITE_API_URL=http://YOUR_SERVER_IP:8000
# OR if using reverse proxy:
# VITE_API_URL=https://your-domain.com
```

### 3. Update CORS Settings

**In `backend/.env`, add your frontend URL:**

```bash
ALLOWED_ORIGINS=http://localhost:5173,http://YOUR_SERVER_IP:5173,https://your-domain.com
```

### 4. Check Backend is Running
```bash
# In backend directory
cd backend
python main.py
```

You should see:
```
Starting Job Application Agent API on 0.0.0.0:8000
External URL: http://YOUR_SERVER_IP:8000
```

### 5. Test Backend Locally
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

### 6. Restart Both Servers

**After creating/updating `.env` files:**

```bash
# Backend (stop with Ctrl+C, then restart)
cd backend
python main.py

# Frontend (in project root, stop with Ctrl+C, then restart)
npm run dev
```

**Important:** Always restart servers after changing environment variables!

## Common Issues

### Issue: Frontend can't reach backend from remote machine

**Solution A: Direct Access**
1. Backend must be running on `0.0.0.0:8000` (already configured)
2. Set `VITE_API_URL=http://YOUR_SERVER_IP:8000` in frontend `.env`
3. Add frontend origin to backend `ALLOWED_ORIGINS`
4. Open firewall port 8000

**Solution B: Use Reverse Proxy (Recommended)**
1. Set up nginx/Caddy (see `REVERSE_PROXY_SETUP.md`)
2. Set `VITE_API_URL=https://your-domain.com` in frontend `.env`
3. Backend runs on localhost:8000 (only via proxy)

### Issue: CORS errors in browser console

**Fix:** Update `backend/.env`:
```bash
ALLOWED_ORIGINS=http://localhost:5173,http://YOUR_FRONTEND_URL
```

### Issue: Environment variable not working

**Fix:** 
- Ensure `.env` is in project root (not in `src/` or `backend/`)
- Restart dev server after changing `.env`
- Check variable name starts with `VITE_`

## Verify Setup

1. **Backend accessible:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Frontend can reach backend:**
   - Open browser DevTools (F12)
   - Check Network tab for API calls
   - Should see successful requests to your API URL

3. **Check API URL in browser console:**
   ```javascript
   console.log(import.meta.env.VITE_API_URL)
   ```

## Configuration Summary

**Backend `backend/.env`:**
```bash
EXTERNAL_URL=http://YOUR_SERVER_IP:8000
ALLOWED_ORIGINS=http://localhost:5173,http://YOUR_SERVER_IP:5173
```

**Frontend `.env` (project root):**
```bash
VITE_API_URL=http://YOUR_SERVER_IP:8000
```

**Key Points:**
- `EXTERNAL_URL` and `VITE_API_URL` must match
- Add frontend URL to `ALLOWED_ORIGINS`
- Restart both servers after changes

## Still Not Working?

- See `BACKEND_URL_SETUP.md` for detailed configuration guide
- See `TROUBLESHOOTING.md` for detailed troubleshooting steps

