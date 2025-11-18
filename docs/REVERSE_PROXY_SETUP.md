# Reverse Proxy Setup Guide

This guide explains how to configure your Job Application AI Agent to work behind a reverse proxy, allowing remote machines to access the application.

## Overview

A reverse proxy sits between clients and your application server, forwarding requests and handling SSL termination, load balancing, and security. This setup enables:

- Remote access to your application
- SSL/TLS encryption (HTTPS)
- Better security and performance
- Domain-based access instead of IP:port

## Backend Configuration

The FastAPI backend has been configured to support reverse proxies. Key settings in `backend/config.py`:

### Environment Variables

Add these to your `.env` file:

```bash
# Reverse Proxy Configuration
TRUSTED_PROXY_HOSTS=*  # Or specific IPs: "127.0.0.1,192.168.1.1"
ROOT_PATH=  # Leave empty unless app is at a subpath like "/api"
ALLOWED_ORIGINS=http://localhost:5173,http://your-domain.com,https://your-domain.com
```

### Configuration Options

- **TRUSTED_PROXY_HOSTS**: Comma-separated list of proxy server IPs, or `*` to trust all
- **ROOT_PATH**: If your app is served at a subpath (e.g., `/api`), set this
- **ALLOWED_ORIGINS**: Comma-separated list of allowed CORS origins

## Nginx Setup

### 1. Install Nginx

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install nginx
```

**CentOS/RHEL:**
```bash
sudo yum install nginx
```

**macOS:**
```bash
brew install nginx
```

### 2. Configure Nginx

1. Copy the example configuration:
```bash
sudo cp nginx.conf.example /etc/nginx/sites-available/job-application-agent
# Or on CentOS/RHEL:
sudo cp nginx.conf.example /etc/nginx/conf.d/job-application-agent.conf
```

2. Edit the configuration file:
```bash
sudo nano /etc/nginx/sites-available/job-application-agent
```

3. Update the following:
   - Replace `your-domain.com` with your domain or IP
   - Update SSL certificate paths (if using HTTPS)
   - Adjust frontend build path if serving static files
   - Update backend port if different from 8000

4. Enable the site (Ubuntu/Debian):
```bash
sudo ln -s /etc/nginx/sites-available/job-application-agent /etc/nginx/sites-enabled/
```

5. Test configuration:
```bash
sudo nginx -t
```

6. Reload nginx:
```bash
sudo systemctl reload nginx
# Or: sudo service nginx reload
```

### 3. SSL Certificate (HTTPS)

**Using Let's Encrypt (Recommended):**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

**Manual SSL Setup:**

1. Obtain SSL certificates from your CA
2. Place certificates in `/etc/ssl/certs/` and `/etc/ssl/private/`
3. Update paths in nginx configuration

## Frontend Configuration

Update your frontend to use the reverse proxy URL:

### Environment Variable

Create or update `.env` in the project root:

```bash
VITE_API_URL=https://your-domain.com
# Or for HTTP: VITE_API_URL=http://your-domain.com
```

### Build and Deploy

1. Build the frontend:
```bash
npm run build
```

2. Option A: Serve via Nginx (recommended)
   - Copy `dist/` contents to `/var/www/job-application-agent/`
   - Update nginx config `root` path

3. Option B: Serve via separate server
   - Update `VITE_API_URL` to point to your backend domain
   - Deploy frontend separately

## Testing

1. **Backend Health Check:**
```bash
curl http://your-domain.com/health
```

2. **API Endpoint:**
```bash
curl http://your-domain.com/api/jobs
```

3. **Frontend Access:**
   - Open `https://your-domain.com` in a browser
   - Verify API calls work correctly

## Firewall Configuration

Ensure ports are open:

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Or for iptables:
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

## Troubleshooting

### Backend not accessible

1. Check backend is running:
```bash
curl http://localhost:8000/health
```

2. Verify nginx proxy_pass URL matches backend
3. Check nginx error logs:
```bash
sudo tail -f /var/log/nginx/error.log
```

### CORS Errors

1. Verify `ALLOWED_ORIGINS` includes your frontend URL
2. Check browser console for specific CORS errors
3. Ensure frontend `VITE_API_URL` matches backend domain

### SSL Certificate Issues

1. Verify certificate paths in nginx config
2. Check certificate permissions:
```bash
sudo chmod 644 /path/to/certificate.crt
sudo chmod 600 /path/to/private.key
```

3. Test SSL:
```bash
openssl s_client -connect your-domain.com:443
```

## Alternative: Caddy

Caddy provides automatic HTTPS. Example `Caddyfile`:

```
your-domain.com {
    reverse_proxy /api localhost:8000
    
    root * /path/to/frontend/dist
    try_files {path} /index.html
    file_server
}
```

## Alternative: Traefik

For Docker deployments, Traefik is a popular choice. See Docker documentation for Traefik labels.

## Security Considerations

1. **Restrict Proxy IPs**: Set `TRUSTED_PROXY_HOSTS` to specific IPs instead of `*`
2. **Use HTTPS**: Always use SSL/TLS in production
3. **Rate Limiting**: Consider adding rate limiting in nginx
4. **Firewall**: Only expose necessary ports (80, 443)
5. **Keep Updated**: Regularly update nginx and certificates

## Development vs Production

- **Development**: Use HTTP, allow all origins, trust all proxies
- **Production**: Use HTTPS, restrict origins, specify trusted proxy IPs

