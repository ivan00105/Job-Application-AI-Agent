# Browser Testing Guide

## 🧪 Quick Browser Test

### Step 1: Open Frontend

**Development:**
- Open: http://localhost:5173

**Production:**
- Open: https://aijobsfinder.groture.com

### Step 2: Open Browser DevTools

Press `F12` or right-click → "Inspect"

### Step 3: Check Console Tab

**✅ CORRECT Configuration:**
You should see:
```
🔗 API Base URL: https://api-aijobsfinder.groture.com
📡 Full API URL: https://api-aijobsfinder.groture.com/api
```

**❌ WRONG Configuration:**
If you see:
```
⚠️ VITE_API_URL not set in .env file, using default: http://localhost:8000
🔗 API Base URL: http://localhost:8000
```

**Fix:** Restart frontend dev server after updating `.env`

### Step 4: Check Network Tab

1. Go to **Network** tab in DevTools
2. Try to login or make any API call
3. Look at the request URL

**✅ CORRECT:**
- Request URL should be: `https://api-aijobsfinder.groture.com/api/...`

**❌ WRONG:**
- Request URL shows: `http://localhost:8000/api/...`

### Step 5: Test API Call

**In Browser Console, run:**
```javascript
// Check environment variable
console.log('API URL:', import.meta.env.VITE_API_URL)

// Test API call
fetch('https://api-aijobsfinder.groture.com/health')
  .then(r => r.json())
  .then(data => console.log('✅ Backend response:', data))
  .catch(err => console.error('❌ Error:', err))
```

**Expected output:**
```
API URL: https://api-aijobsfinder.groture.com
✅ Backend response: {status: "healthy"}
```

## 🔍 Verification Checklist

- [ ] Console shows correct API URL (not localhost:8000)
- [ ] Network tab shows requests to `api-aijobsfinder.groture.com`
- [ ] No CORS errors in console
- [ ] API calls return successful responses
- [ ] Login/authentication works

## 🐛 Common Issues

### Issue: Still seeing localhost:8000 in console

**Solution:**
1. Stop frontend dev server (Ctrl+C)
2. Verify `.env` file has `VITE_API_URL=https://api-aijobsfinder.groture.com`
3. Restart: `npm run dev`
4. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)

### Issue: CORS Error

**Error message:**
```
Access to fetch at 'https://api-aijobsfinder.groture.com/api/...' 
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**Solution:**
1. Check `backend/.env` has `ALLOWED_ORIGINS` including your frontend URL
2. Restart backend after changing CORS settings

### Issue: Network Error / Connection Refused

**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Check nginx is running (if using reverse proxy)
3. Verify SSL certificates are valid

## 📊 Test Results

After testing, you should have:

✅ **Console:** Shows correct API URL  
✅ **Network:** Requests go to external URL  
✅ **Functionality:** Login and API calls work  
✅ **No Errors:** No CORS or connection errors  

## 🎯 Quick Test Commands

**In Browser Console:**
```javascript
// 1. Check API URL
import.meta.env.VITE_API_URL

// 2. Test health endpoint
fetch('https://api-aijobsfinder.groture.com/health')
  .then(r => r.json())
  .then(console.log)

// 3. Check if API client is configured
console.log('API Base:', import.meta.env.VITE_API_URL)
```

