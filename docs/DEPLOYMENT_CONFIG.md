# Deployment Configuration for AI Jobs Finder

## Domain Configuration

- **Frontend:** https://aijobsfinder.groture.com
- **Backend API:** https://api-aijobsfinder.groture.com

## Configuration Summary

### Frontend Configuration (`.env` in project root)

```bash
VITE_API_URL=https://api-aijobsfinder.groture.com
```

### Backend Configuration (`backend/.env`)

```bash
# Reverse Proxy Configuration
EXTERNAL_URL=https://api-aijobsfinder.groture.com
ALLOWED_ORIGINS=https://aijobsfinder.groture.com,http://aijobsfinder.groture.com,https://api-aijobsfinder.groture.com,http://localhost:5173,http://127.0.0.1:5173
TRUSTED_PROXY_HOSTS=127.0.0.1
ROOT_PATH=
```

## Nginx Setup

### 1. Install Nginx

```bash
sudo apt update
sudo apt install nginx
```

### 2. Copy Configuration

```bash
sudo cp nginx-aijobsfinder.conf /etc/nginx/sites-available/aijobsfinder
sudo ln -s /etc/nginx/sites-available/aijobsfinder /etc/nginx/sites-enabled/
```

### 3. Update SSL Certificate Paths

Edit `/etc/nginx/sites-available/aijobsfinder` and update:

```nginx
ssl_certificate /etc/ssl/certs/aijobsfinder.groture.com.crt;
ssl_certificate_key /etc/ssl/private/aijobsfinder.groture.com.key;
```

And for the API server:

```nginx
ssl_certificate /etc/ssl/certs/api-aijobsfinder.groture.com.crt;
ssl_certificate_key /etc/ssl/private/api-aijobsfinder.groture.com.key;
```

### 4. Update Frontend Build Path

Edit `/etc/nginx/sites-available/aijobsfinder` and update:

```nginx
root /var/www/aijobsfinder.groture.com/dist;
```

Replace with your actual frontend build directory.

### 5. Test and Reload Nginx

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate Setup

### Option 1: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificates for both domains
sudo certbot --nginx -d aijobsfinder.groture.com
sudo certbot --nginx -d api-aijobsfinder.groture.com
```

Certbot will automatically update the nginx configuration.

### Option 2: Manual SSL Certificates

1. Obtain SSL certificates from your CA
2. Place certificates in:
   - `/etc/ssl/certs/aijobsfinder.groture.com.crt`
   - `/etc/ssl/private/aijobsfinder.groture.com.key`
   - `/etc/ssl/certs/api-aijobsfinder.groture.com.crt`
   - `/etc/ssl/private/api-aijobsfinder.groture.com.key`
3. Set proper permissions:
   ```bash
   sudo chmod 644 /etc/ssl/certs/*.crt
   sudo chmod 600 /etc/ssl/private/*.key
   ```

## Frontend Build and Deploy

### 1. Build Frontend

```bash
npm run build
```

This creates a `dist/` directory with the production build.

### 2. Deploy Frontend Files

```bash
# Create directory
sudo mkdir -p /var/www/aijobsfinder.groture.com

# Copy build files
sudo cp -r dist/* /var/www/aijobsfinder.groture.com/

# Set permissions
sudo chown -R www-data:www-data /var/www/aijobsfinder.groture.com
sudo chmod -R 755 /var/www/aijobsfinder.groture.com
```

## Backend Deployment

### 1. Ensure Backend is Running

```bash
cd backend
python main.py
```

Or use a process manager like systemd or supervisor.

### 2. Verify Backend is Accessible

```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

### 3. Verify Through Proxy

```bash
curl https://api-aijobsfinder.groture.com/health
```

Should return: `{"status":"healthy"}`

## Verification Checklist

- [ ] Frontend `.env` has `VITE_API_URL=https://api-aijobsfinder.groture.com`
- [ ] Backend `.env` has `EXTERNAL_URL=https://api-aijobsfinder.groture.com`
- [ ] Backend `.env` has frontend domain in `ALLOWED_ORIGINS`
- [ ] Nginx configuration is installed and enabled
- [ ] SSL certificates are configured
- [ ] Frontend build is deployed to `/var/www/aijobsfinder.groture.com/dist`
- [ ] Backend is running on `localhost:8000`
- [ ] Firewall allows ports 80 and 443
- [ ] DNS records point to server IP

## Testing

### Test Frontend
```bash
curl -I https://aijobsfinder.groture.com
```

### Test Backend API
```bash
curl https://api-aijobsfinder.groture.com/health
```

### Test from Browser
1. Open https://aijobsfinder.groture.com
2. Open DevTools (F12)
3. Check Console - should see: `🔗 API Base URL: https://api-aijobsfinder.groture.com`
4. Check Network tab - API calls should go to `api-aijobsfinder.groture.com`

## Troubleshooting

### Frontend shows "Connection Refused"

1. Check backend is running: `curl http://localhost:8000/health`
2. Check nginx is running: `sudo systemctl status nginx`
3. Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
4. Verify `.env` file has correct `VITE_API_URL`

### CORS Errors

1. Verify `ALLOWED_ORIGINS` in `backend/.env` includes `https://aijobsfinder.groture.com`
2. Restart backend after changing CORS settings
3. Check browser console for specific CORS error

### SSL Certificate Errors

1. Verify certificate paths in nginx config
2. Check certificate permissions
3. Test SSL: `openssl s_client -connect api-aijobsfinder.groture.com:443`

## DNS Configuration

Ensure your DNS records are set up:

```
A record: aijobsfinder.groture.com -> YOUR_SERVER_IP
A record: api-aijobsfinder.groture.com -> YOUR_SERVER_IP
```

Or use CNAME if using a load balancer:

```
CNAME: aijobsfinder.groture.com -> your-load-balancer
CNAME: api-aijobsfinder.groture.com -> your-load-balancer
```

