# Testing Guide - AI Jobs Finder Configuration

## ✅ Configuration Test Results

Your configuration has been verified:
- ✅ Frontend `.env` configured correctly
- ✅ Backend `.env` configured correctly  
- ✅ Backend is running and accessible
- ✅ Frontend dev server is running

## 🧪 Step-by-Step Testing

### Step 1: Verify Backend is Running

**Check backend status:**
```bash
curl http://localhost:8000/health
```

**Expected output:**
```json
{"status":"healthy"}
```

**If backend is not running:**
```bash
cd backend
python main.py
```

You should see:
```
Starting Job Application Agent API on 0.0.0.0:8000
External URL: https://api-aijobsfinder.groture.com
```

### Step 2: Verify Frontend is Running

**Check frontend status:**
```bash
curl http://localhost:5173
```

**If frontend is not running:**
```bash
npm run dev
```

### Step 3: Test Frontend Configuration in Browser

1. **Open the frontend:**
   - Development: http://localhost:5173
   - Production: https://aijobsfinder.groture.com

2. **Open Browser DevTools (F12)**

3. **Check Console Tab:**
   You should see:
   ```
   🔗 API Base URL: https://api-aijobsfinder.groture.com
   📡 Full API URL: https://api-aijobsfinder.groture.com/api
   ```

4. **If you see a warning:**
   ```
   ⚠️ VITE_API_URL not set in .env file, using default: http://localhost:8000
   ```
   This means the frontend dev server needs to be restarted.

### Step 4: Test API Calls

1. **Open Network Tab in DevTools (F12)**

2. **Try to login or make any API call**

3. **Check the request URL:**
   - ✅ Should show: `https://api-aijobsfinder.groture.com/api/...`
   - ❌ Should NOT show: `http://localhost:8000/api/...`

### Step 5: Test Backend API Directly

**Test health endpoint:**
```bash
curl https://api-aijobsfinder.groture.com/health
```

**Test API endpoint (if authenticated):**
```bash
curl https://api-aijobsfinder.groture.com/api/jobs \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔄 Restarting Servers

### Restart Backend

```bash
# Stop current backend (Ctrl+C in terminal running backend)
# Then start:
cd backend
python main.py
```

### Restart Frontend

```bash
# Stop current frontend dev server (Ctrl+C in terminal running frontend)
# Then start:
npm run dev
```

**Important:** Always restart after changing `.env` files!

## 🧪 Automated Testing

### Run Test Script

**Linux/Mac:**
```bash
./test-configuration.sh
```

**Windows:**
```bash
test-configuration.bat
```

## ✅ Verification Checklist

- [ ] Backend is running on `localhost:8000`
- [ ] Frontend is running on `localhost:5173`
- [ ] Browser console shows correct API URL
- [ ] Network tab shows API calls to `api-aijobsfinder.groture.com`
- [ ] No CORS errors in browser console
- [ ] API calls are successful

## 🐛 Troubleshooting

### Issue: Frontend still shows localhost:8000

**Solution:**
1. Verify `.env` file exists in project root
2. Check `VITE_API_URL=https://api-aijobsfinder.groture.com` in `.env`
3. **Restart frontend dev server** (this is critical!)

### Issue: CORS Errors

**Solution:**
1. Check `backend/.env` has frontend domain in `ALLOWED_ORIGINS`
2. Restart backend after changing CORS settings

### Issue: Connection Refused

**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Check nginx is running (if using reverse proxy): `sudo systemctl status nginx`
3. Check firewall allows port 8000

### Issue: SSL Certificate Errors

**Solution:**
1. For development, you can use `-k` flag with curl to ignore SSL
2. For production, ensure SSL certificates are properly configured in nginx

## 📊 Test Results Template

```
✅ Backend Health: PASS
✅ Frontend Config: PASS
✅ API URL in Console: PASS
✅ Network Requests: PASS
✅ CORS: PASS
```

## 🎯 Quick Test Commands

```bash
# Test backend locally
curl http://localhost:8000/health

# Test backend externally
curl https://api-aijobsfinder.groture.com/health

# Test frontend
curl http://localhost:5173

# Check environment variables
cat .env | grep VITE_API_URL
cat backend/.env | grep EXTERNAL_URL
```

