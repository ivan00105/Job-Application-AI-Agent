# Configuration Summary for AI Jobs Finder

## ✅ Configuration Complete

Your application has been configured for:
- **Frontend:** https://aijobsfinder.groture.com
- **Backend API:** https://api-aijobsfinder.groture.com

## 📋 Configuration Files

### Frontend (`.env` in project root)
```bash
VITE_API_URL=https://api-aijobsfinder.groture.com
```

### Backend (`backend/.env`)
```bash
EXTERNAL_URL=https://api-aijobsfinder.groture.com
ALLOWED_ORIGINS=https://aijobsfinder.groture.com,http://aijobsfinder.groture.com,https://api-aijobsfinder.groture.com,http://localhost:5173,http://127.0.0.1:5173
TRUSTED_PROXY_HOSTS=127.0.0.1
ROOT_PATH=
```

## 🚀 Next Steps

### 1. Restart Both Servers

**Backend:**
```bash
cd backend
python main.py
```

You should see:
```
Starting Job Application Agent API on 0.0.0.0:8000
External URL: https://api-aijobsfinder.groture.com
```

**Frontend:**
```bash
# Stop current dev server (Ctrl+C)
npm run dev
```

### 2. Verify Configuration

**Check Frontend Console:**
1. Open https://aijobsfinder.groture.com (or http://localhost:5173 in dev)
2. Open DevTools (F12)
3. Check Console - should see:
   ```
   🔗 API Base URL: https://api-aijobsfinder.groture.com
   📡 Full API URL: https://api-aijobsfinder.groture.com/api
   ```

**Test Backend:**
```bash
curl https://api-aijobsfinder.groture.com/health
```

Should return: `{"status":"healthy"}`

### 3. Set Up Nginx (Production)

See `nginx-aijobsfinder.conf` for the complete nginx configuration.

**Quick Setup:**
```bash
sudo cp nginx-aijobsfinder.conf /etc/nginx/sites-available/aijobsfinder
sudo ln -s /etc/nginx/sites-available/aijobsfinder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. SSL Certificates

**Using Let's Encrypt:**
```bash
sudo certbot --nginx -d aijobsfinder.groture.com
sudo certbot --nginx -d api-aijobsfinder.groture.com
```

## 📝 Important Notes

1. **Environment Variables:** Always restart servers after changing `.env` files
2. **CORS:** Backend must allow frontend origin in `ALLOWED_ORIGINS`
3. **Proxy:** Backend runs on `localhost:8000`, nginx proxies to `api-aijobsfinder.groture.com`
4. **Frontend Build:** Deploy built files to `/var/www/aijobsfinder.groture.com/dist`

## 🔍 Troubleshooting

### Frontend still calling localhost:8000
- ✅ Check `.env` file exists in project root
- ✅ Verify `VITE_API_URL=https://api-aijobsfinder.groture.com`
- ✅ Restart frontend dev server

### CORS Errors
- ✅ Verify `ALLOWED_ORIGINS` includes `https://aijobsfinder.groture.com`
- ✅ Restart backend after changing CORS

### Connection Refused
- ✅ Check backend is running: `curl http://localhost:8000/health`
- ✅ Check nginx is running: `sudo systemctl status nginx`
- ✅ Check nginx logs: `sudo tail -f /var/log/nginx/error.log`

## 📚 Documentation

- `DEPLOYMENT_CONFIG.md` - Complete deployment guide
- `nginx-aijobsfinder.conf` - Nginx configuration file
- `REVERSE_PROXY_SETUP.md` - General reverse proxy guide
- `BACKEND_URL_SETUP.md` - Backend URL configuration guide

