# Frontend Environment Setup Guide

## Problem: Frontend Still Calling localhost:8000

If your frontend is still calling `localhost:8000` instead of your external URL, you need to create/update the `.env` file.

## Quick Fix

### Step 1: Create/Update `.env` File

**Location:** Create `.env` file in the **project root** (same directory as `package.json`)

**Content:**
```bash
VITE_API_URL=http://YOUR_SERVER_IP:8000
```

**Replace `YOUR_SERVER_IP` with:**
- Your server's IP address (e.g., `192.168.1.100`)
- Or your domain (e.g., `https://api.yourdomain.com`)

### Step 2: Find Your Server IP

**On Linux/Mac:**
```bash
hostname -I
# or
ip addr show
```

**On Windows:**
```bash
ipconfig
# Look for IPv4 Address
```

**From another machine:**
- Use the IP address that other machines can reach
- Usually starts with `192.168.x.x` or `10.x.x.x` for local networks
- Or use your public IP if accessing from internet

### Step 3: Update `.env` File

**Example for remote access:**
```bash
VITE_API_URL=http://192.168.1.100:8000
```

**Example for reverse proxy:**
```bash
VITE_API_URL=https://your-domain.com
```

### Step 4: Restart Frontend Dev Server

**⚠️ CRITICAL:** You MUST restart the dev server after creating/updating `.env`!

```bash
# Stop the current dev server (Ctrl+C)
# Then restart:
npm run dev
```

## Verification

### Check Browser Console

1. Open your frontend in browser
2. Open DevTools (F12)
3. Check Console tab
4. You should see:
   ```
   🔗 API Base URL: http://YOUR_SERVER_IP:8000
   📡 Full API URL: http://YOUR_SERVER_IP:8000/api
   ```

### Check Network Tab

1. Open DevTools (F12)
2. Go to Network tab
3. Make an API call (e.g., login)
4. Check the request URL - it should show your external URL, not `localhost:8000`

### Test API URL in Console

In browser console, run:
```javascript
console.log(import.meta.env.VITE_API_URL)
```

Should show your configured URL.

## Common Issues

### Issue: Still seeing localhost:8000

**Causes:**
1. `.env` file not in project root
2. Dev server not restarted after creating `.env`
3. Wrong variable name (must be `VITE_API_URL`, not `API_URL`)
4. `.env` file has syntax errors

**Fix:**
1. Verify `.env` is in project root (same level as `package.json`)
2. Stop and restart `npm run dev`
3. Check variable name is exactly `VITE_API_URL`
4. Ensure no quotes around the URL in `.env`

### Issue: Environment variable not loading

**Check:**
- File must be named exactly `.env` (not `.env.local`, `.env.production`, etc.)
- No spaces around `=` sign: `VITE_API_URL=http://...` (not `VITE_API_URL = http://...`)
- No quotes needed: `VITE_API_URL=http://192.168.1.100:8000`

### Issue: CORS errors after fixing URL

**Fix:** Update `backend/.env`:
```bash
ALLOWED_ORIGINS=http://localhost:5173,http://YOUR_SERVER_IP:5173
```

Then restart backend.

## Using Setup Scripts

### Windows:
```bash
setup-frontend-env.bat
```

### Linux/Mac:
```bash
chmod +x setup-frontend-env.sh
./setup-frontend-env.sh
```

## Example Configurations

### Local Development
```bash
# .env
VITE_API_URL=http://localhost:8000
```

### Remote Access (Same Network)
```bash
# .env
VITE_API_URL=http://192.168.1.100:8000
```

### Remote Access (Reverse Proxy)
```bash
# .env
VITE_API_URL=https://api.yourdomain.com
```

### Remote Access (Public IP)
```bash
# .env
VITE_API_URL=http://YOUR_PUBLIC_IP:8000
```

## Complete Setup Checklist

- [ ] Created `.env` file in project root
- [ ] Set `VITE_API_URL` to your backend external URL
- [ ] Verified URL is correct (no typos)
- [ ] Restarted frontend dev server
- [ ] Checked browser console for API URL log
- [ ] Verified Network tab shows correct URL
- [ ] Updated backend `ALLOWED_ORIGINS` if needed
- [ ] Restarted backend if CORS changed

## Still Having Issues?

1. **Check browser console** - Look for the API URL log message
2. **Check Network tab** - See what URL is actually being called
3. **Verify .env location** - Must be in project root
4. **Restart dev server** - Changes only apply after restart
5. **Check for typos** - URL must be exact

See `BACKEND_URL_SETUP.md` for backend configuration.

