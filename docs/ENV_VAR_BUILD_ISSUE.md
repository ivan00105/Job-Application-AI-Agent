# Environment Variable Not Taking Effect - Build Time Issue

## Problem

After updating the `.env` file with `VITE_API_URL=https://api-aijobsfinder.groture.com`, the frontend is still using the old HTTP URL.

## Root Cause

**Vite embeds environment variables at BUILD TIME**, not at runtime. This means:

1. When you run `npm run build`, Vite reads the `.env` file
2. It embeds the environment variable values directly into the JavaScript bundle
3. If you update `.env` AFTER building, the old values are still in the built files
4. You must rebuild the frontend after changing `.env`

## Solution

### Step 1: Verify `.env` File

Check that `.env` file exists in the **project root** (same directory as `package.json`) and contains:

```bash
VITE_API_URL=https://api-aijobsfinder.groture.com
```

**Important:**
- No quotes around the URL
- No spaces around `=`
- Must use `https://` (not `http://`)

### Step 2: Rebuild Frontend

After updating `.env`, you MUST rebuild:

```bash
# In project root
npm run build
```

This will:
- Read the updated `.env` file
- Embed the new `VITE_API_URL` value into the build
- Generate new files in `dist/` directory

### Step 3: Deploy New Build

Copy the new `dist/` directory to your server:

```bash
# Example: Copy to nginx directory
sudo cp -r dist/* /var/www/aijobsfinder.groture.com/dist/
```

Or if using a deployment script, run your deployment process.

### Step 4: Verify

1. Clear browser cache or use incognito mode
2. Visit `https://aijobsfinder.groture.com/jobs`
3. Open browser console (F12)
4. Look for these log messages:
   ```
   🔗 API Base URL: https://api-aijobsfinder.groture.com
   📡 Full API URL: https://api-aijobsfinder.groture.com/api
   🌍 Environment: production
   📦 VITE_API_URL from env: https://api-aijobsfinder.groture.com
   ```

If you see `http://` instead of `https://`, the build still has the old value.

## Debugging

### Check What URL is Actually Being Used

The updated code now logs the API URL to the console. Check browser console (F12) to see:
- What URL is actually being used
- Whether the environment variable is being read
- If there's an HTTPS/HTTP mismatch

### Common Mistakes

1. **Updated `.env` but didn't rebuild**
   - Fix: Run `npm run build` after updating `.env`

2. **`.env` file in wrong location**
   - Must be in project root (same level as `package.json`)
   - Not in `src/`, not in `backend/`

3. **Wrong variable name**
   - Must be exactly `VITE_API_URL` (not `API_URL` or `REACT_APP_API_URL`)

4. **Syntax error in `.env`**
   - No quotes: `VITE_API_URL=https://api-aijobsfinder.groture.com` ✅
   - Not: `VITE_API_URL="https://api-aijobsfinder.groture.com"` ❌
   - No spaces: `VITE_API_URL=https://...` ✅
   - Not: `VITE_API_URL = https://...` ❌

5. **Deployed old build**
   - Make sure you're deploying the NEW `dist/` folder after rebuilding

## Production Build Process

```bash
# 1. Update .env file
echo "VITE_API_URL=https://api-aijobsfinder.groture.com" > .env

# 2. Build frontend (this reads .env and embeds values)
npm run build

# 3. Deploy dist/ folder to server
# (Copy to nginx directory or run your deployment script)

# 4. Restart nginx (if needed)
sudo systemctl reload nginx
```

## Quick Verification Script

After rebuilding, you can verify the build contains the correct URL:

```bash
# Search for the API URL in the built files
grep -r "api-aijobsfinder.groture.com" dist/

# Should show https:// (not http://)
```

## Summary

**Key Point:** Environment variables in Vite are embedded at BUILD TIME, not runtime.

- ✅ Update `.env` file
- ✅ Run `npm run build` (this reads `.env` and embeds values)
- ✅ Deploy new `dist/` folder
- ✅ Clear browser cache and test

The new logging in `src/api/client.ts` will help you verify the URL is correct after rebuilding.

