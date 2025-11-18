# Fix for Mixed Content Error (HTTP/HTTPS)

## Problem
The frontend is loaded over HTTPS (`https://aijobsfinder.groture.com`), but it's trying to make API requests to HTTP (`http://api-aijobsfinder.groture.com`). Browsers block this for security reasons.

## Solution

### Step 1: Update Frontend `.env` File

Create or update `.env` file in the **project root** (same directory as `package.json`):

```bash
VITE_API_URL=https://api-aijobsfinder.groture.com
```

**Important:** Use `https://` not `http://`

### Step 2: Rebuild Frontend

After updating `.env`, you must rebuild the frontend:

```bash
# Stop the current build process (if running)
# Then rebuild:
npm run build
```

### Step 3: Verify Nginx Configuration

Your nginx configuration should already be correct (from `docs/nginx-aijobsfinder.conf`):

- ✅ Frontend: `https://aijobsfinder.groture.com` (HTTPS)
- ✅ Backend API: `https://api-aijobsfinder.groture.com` (HTTPS)
- ✅ HTTP to HTTPS redirects are configured

### Step 4: Test

1. Clear browser cache or use incognito mode
2. Visit `https://aijobsfinder.groture.com/jobs`
3. Open browser DevTools (F12) → Network tab
4. Check API requests - they should now go to `https://api-aijobsfinder.groture.com`
5. No more mixed content errors!

## Verification

### Check API URL in Browser Console

Open browser console (F12) and run:

```javascript
console.log(import.meta.env.VITE_API_URL)
```

Should show: `https://api-aijobsfinder.groture.com`

### Check Network Requests

1. Open DevTools (F12) → Network tab
2. Make a request (e.g., search for jobs)
3. Look for API calls - they should all use `https://`

## Common Issues

### Issue: Still seeing HTTP requests

**Fix:**
1. Make sure `.env` file is in project root (not in `src/` or `backend/`)
2. Rebuild frontend: `npm run build`
3. Clear browser cache
4. Restart nginx: `sudo systemctl reload nginx`

### Issue: SSL certificate errors

**Fix:**
- Make sure SSL certificates are properly configured in nginx
- Check certificate paths in `/etc/nginx/sites-available/aijobsfinder`
- Verify certificates are valid: `sudo certbot certificates`

### Issue: CORS errors

**Fix:**
Update `backend/.env`:

```bash
ALLOWED_ORIGINS=https://aijobsfinder.groture.com,https://api-aijobsfinder.groture.com
```

Then restart backend.

## Summary

**Frontend `.env` (project root):**
```bash
VITE_API_URL=https://api-aijobsfinder.groture.com
```

**Backend `.env` (`backend/.env`):**
```bash
EXTERNAL_URL=https://api-aijobsfinder.groture.com
ALLOWED_ORIGINS=https://aijobsfinder.groture.com,https://api-aijobsfinder.groture.com
```

**Key Points:**
- ✅ Always use `https://` in production
- ✅ Rebuild frontend after changing `.env`
- ✅ Nginx handles SSL termination (backend runs on HTTP internally)
- ✅ Both frontend and API must use HTTPS

