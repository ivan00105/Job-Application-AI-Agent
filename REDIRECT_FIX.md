# 307 Redirect Fix

## Issue Identified

The backend was returning a `307 Temporary Redirect` because:
1. The frontend was calling `/api/jobs` (without trailing slash)
2. The backend route is defined as `@router.get("/")` which expects `/api/jobs/` (with trailing slash)
3. FastAPI automatically redirects `/api/jobs` → `/api/jobs/` with a 307 redirect

If the initial request was HTTP (due to cached code or misconfiguration), the browser blocks the redirect as mixed content.

## Changes Made

1. **Updated `src/api/client.ts`**: Changed `/jobs` to `/jobs/` in the `jobsAPI.search` function to match the backend route and avoid the redirect.

## Root Cause

The 307 redirect itself is not the problem - it's a normal FastAPI behavior. The real issue was:
- The frontend making HTTP requests (due to old cached build)
- The browser blocking HTTP→HTTPS redirects as mixed content

## Solution

1. **Frontend fix**: Use trailing slash in API calls to match backend routes
2. **Backend CORS**: Already fixed to allow production frontend domain
3. **HTTPS enforcement**: Code now auto-upgrades HTTP to HTTPS

## Next Steps

1. **Rebuild and redeploy frontend** to include the trailing slash fix
2. **Restart backend** to apply CORS changes
3. **Clear browser cache** or do a hard refresh (Ctrl+Shift+R)

After these steps, the 307 redirect should no longer occur, and all requests should go directly to HTTPS endpoints.

