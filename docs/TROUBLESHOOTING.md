# Troubleshooting: "Refuse to Connect" Error

If your frontend shows "refuse to connect" errors, follow these steps:

## Quick Checklist

1. ✅ **Backend is running** - Check if backend server is active
2. ✅ **Correct API URL** - Frontend must point to the right backend URL
3. ✅ **CORS configured** - Backend must allow your frontend origin
4. ✅ **Network accessible** - Backend must be reachable from frontend location
5. ✅ **Firewall/Ports** - Required ports must be open

## Step-by-Step Troubleshooting

### 1. Verify Backend is Running

**Check if backend is accessible locally:**
```bash
# Test backend health endpoint
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

**If backend is not running:**
```bash
cd backend
python main.py
# Or: uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Configure Frontend API URL

**For Local Development:**
Create or update `.env` in the project root:
```bash
VITE_API_URL=http://localhost:8000
```

**For Remote Access (via Reverse Proxy):**
```bash
# If using domain
VITE_API_URL=https://your-domain.com

# If using IP address
VITE_API_URL=http://YOUR_SERVER_IP

# If using IP with port (no reverse proxy)
VITE_API_URL=http://YOUR_SERVER_IP:8000
```

**Important:** After changing `.env`, restart the frontend dev server:
```bash
# Stop the dev server (Ctrl+C) and restart
npm run dev
```

### 3. Check CORS Configuration

**Backend must allow your frontend origin.**

Update `backend/.env`:
```bash
ALLOWED_ORIGINS=http://localhost:5173,http://YOUR_FRONTEND_URL
```

**For remote access, include:**
```bash
ALLOWED_ORIGINS=http://localhost:5173,http://YOUR_SERVER_IP,https://your-domain.com
```

**Restart backend after changing CORS settings.**

### 4. Network Accessibility

**If accessing from a remote machine:**

**Option A: Direct Backend Access (No Reverse Proxy)**
- Backend must bind to `0.0.0.0` (already configured)
- Frontend must use server IP: `VITE_API_URL=http://YOUR_SERVER_IP:8000`
- Firewall must allow port 8000

**Option B: Via Reverse Proxy (Recommended)**
- Set up nginx/Caddy as reverse proxy
- Frontend uses: `VITE_API_URL=http://your-domain.com` or `https://your-domain.com`
- Backend runs on localhost:8000 (only accessible via proxy)

### 5. Firewall Configuration

**Allow backend port (if accessing directly):**
```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp

# CentOS/RHEL
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload

# Windows Firewall
# Add inbound rule for port 8000
```

**For reverse proxy, allow ports 80/443:**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 6. Browser Console Debugging

**Open browser DevTools (F12) and check:**

1. **Network Tab:**
   - Look for failed requests
   - Check the exact URL being called
   - Note the error message (CORS, connection refused, timeout)

2. **Console Tab:**
   - Look for error messages
   - Check if `VITE_API_URL` is being read correctly

**Test API URL in console:**
```javascript
// In browser console
console.log(import.meta.env.VITE_API_URL)
// Should show your configured API URL
```

### 7. Common Scenarios

#### Scenario A: Local Development
```bash
# Backend: http://localhost:8000
# Frontend: http://localhost:5173

# .env file:
VITE_API_URL=http://localhost:8000

# Backend .env:
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

#### Scenario B: Remote Access (Direct)
```bash
# Backend: http://YOUR_SERVER_IP:8000
# Frontend: http://YOUR_SERVER_IP:5173 (or remote machine)

# .env file:
VITE_API_URL=http://YOUR_SERVER_IP:8000

# Backend .env:
ALLOWED_ORIGINS=http://YOUR_SERVER_IP:5173,http://YOUR_SERVER_IP:3000
```

#### Scenario C: Remote Access (Reverse Proxy)
```bash
# Backend: http://localhost:8000 (only accessible via proxy)
# Frontend: https://your-domain.com

# .env file:
VITE_API_URL=https://your-domain.com

# Backend .env:
ALLOWED_ORIGINS=https://your-domain.com,http://your-domain.com
```

### 8. Vite Dev Server Network Access

**If frontend dev server needs to be accessible remotely:**

Update `vite.config.ts`:
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // Allow external connections
    port: 5173,
  },
  // ... rest of config
})
```

Then access from remote machine:
```
http://YOUR_SERVER_IP:5173
```

### 9. Test Backend Connectivity

**From the machine running the frontend:**

```bash
# Test if backend is reachable
curl http://YOUR_BACKEND_URL/health

# Test API endpoint
curl http://YOUR_BACKEND_URL/api/jobs
```

**If curl fails:**
- Backend is not running
- Network/firewall blocking
- Wrong URL

### 10. Verify Environment Variables

**Check if Vite is reading the .env file:**

```bash
# In project root, verify .env exists
cat .env

# Should contain:
VITE_API_URL=http://your-backend-url
```

**Note:** Vite only reads `.env` files at build/dev server start. Restart after changes.

## Quick Fix Commands

```bash
# 1. Check backend is running
curl http://localhost:8000/health

# 2. Check frontend can reach backend
curl http://YOUR_BACKEND_URL/health

# 3. Restart backend
cd backend
python main.py

# 4. Restart frontend (after updating .env)
npm run dev
```

## Still Having Issues?

1. **Check browser console** for specific error messages
2. **Check backend logs** for connection attempts
3. **Verify network connectivity** between frontend and backend
4. **Test with curl/Postman** to isolate frontend vs backend issues
5. **Check if using HTTPS** - mixed HTTP/HTTPS can cause issues

## Common Error Messages

- **"Connection refused"**: Backend not running or wrong port
- **"CORS error"**: Backend doesn't allow your origin
- **"Network error"**: Firewall blocking or wrong URL
- **"Mixed content"**: HTTPS frontend trying to access HTTP backend

