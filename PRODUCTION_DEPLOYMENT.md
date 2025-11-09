# 🚀 Production Deployment Guide

## Overview

This guide covers deploying the Luthier's Tool Box with:
- **Nginx front proxy** (routes `/api` → FastAPI, serves Vue SPA)
- **GitHub Container Registry** (GHCR) image publishing
- **Multi-stage builds** (Vue app built with Vite, served with nginx)
- **Production-ready configuration** (health checks, security headers, caching)

---

## 📦 Architecture

### Production Stack

```
Internet
    │
    ↓
[Nginx Proxy :80]
    │
    ├─ /api/* ────────→ [FastAPI :8000] (internal network)
    │                      │
    │                      └─ SQLite DB (persistent volume)
    │
    └─ /* ────────────→ [Static Assets] (Vue dist/)
                           (served by nginx)
```

### Container Flow

```
1. Client Request → Nginx :80
2. Route Analysis:
   - /api/cam/simulate → proxy_pass to api:8000
   - /docs → proxy_pass to api:8000/docs
   - /health → proxy_pass to api:8000/health
   - /assets/app.js → serve from /usr/share/nginx/html
   - / → serve index.html (Vue SPA)
```

### Image Publishing

```
Push to main/tags
    ↓
GitHub Actions
    ↓
Build 3 images (multi-platform):
    ├─ ghcr.io/yourorg/luthiers-toolbox-api:latest
    ├─ ghcr.io/yourorg/luthiers-toolbox-client:latest
    └─ ghcr.io/yourorg/luthiers-toolbox-nginx:latest
    ↓
Push to GHCR (GitHub Container Registry)
    ↓
Available for deployment
```

---

## 🏗️ Files Created

### Docker Configuration (5 files)

1. **`docker/nginx/Dockerfile`** - Nginx proxy image
2. **`docker/nginx/nginx.conf`** - Main nginx config
3. **`docker/nginx/default.conf`** - Server block with routing rules
4. **`docker/client/Dockerfile.production`** - Multi-stage Vue build
5. **`docker-compose.production.yml`** - Production orchestration

### CI/CD (1 file)

6. **`.github/workflows/publish-images.yml`** - Automated image publishing

### Documentation (1 file)

7. **`PRODUCTION_DEPLOYMENT.md`** - This file

---

## 🚀 Quick Start (Local Test)

### 1. Build Production Images Locally

```powershell
# Build all images
docker compose -f docker-compose.production.yml build

# Or build individually
docker build -f docker/api/Dockerfile -t toolbox-api:local .
docker build -f docker/client/Dockerfile.production -t toolbox-client:local .
docker build -f docker/nginx/Dockerfile -t toolbox-nginx:local .
```

### 2. Launch Stack

```powershell
# Create .env for local testing
cat > .env.production << EOF
API_IMAGE=toolbox-api:local
CLIENT_IMAGE=toolbox-client:local
NGINX_IMAGE=toolbox-nginx:local
NGINX_PORT=80
EOF

# Launch
docker compose -f docker-compose.production.yml --env-file .env.production up -d

# Watch logs
docker compose -f docker-compose.production.yml logs -f
```

### 3. Test

```powershell
# Health check
curl http://localhost/health

# API via proxy
curl http://localhost/api/health

# API docs
Start-Process http://localhost/docs

# Vue SPA
Start-Process http://localhost
```

### 4. Stop

```powershell
docker compose -f docker-compose.production.yml down -v
```

---

## 📤 Publishing to GHCR

### Setup (One-Time)

1. **Enable GHCR for your repo**:
   - Go to GitHub repo → Settings → Actions → General
   - Scroll to "Workflow permissions"
   - Select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"

2. **Update image names** in `.github/workflows/publish-images.yml`:
   ```yaml
   env:
     REGISTRY: ghcr.io
     IMAGE_PREFIX: YOUR_GITHUB_USERNAME/luthiers-toolbox
   ```

3. **Update `docker-compose.production.yml`**:
   ```yaml
   services:
     api:
       image: ghcr.io/YOUR_USERNAME/luthiers-toolbox-api:latest
     client:
       image: ghcr.io/YOUR_USERNAME/luthiers-toolbox-client:latest
     nginx:
       image: ghcr.io/YOUR_USERNAME/luthiers-toolbox-nginx:latest
   ```

### Trigger Publishing

#### Option 1: Push to Main

```bash
git add .
git commit -m "Add production deployment"
git push origin main

# GitHub Actions automatically:
# - Builds 3 images (linux/amd64, linux/arm64)
# - Tags with 'latest' and 'main-<sha>'
# - Pushes to ghcr.io
```

#### Option 2: Create Version Tag

```bash
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions automatically:
# - Builds images
# - Tags with 'v1.0.0', '1.0', '1', 'latest'
# - Creates GitHub Release
# - Pushes to ghcr.io
```

#### Option 3: Manual Trigger

- Go to GitHub repo → Actions → "Publish Docker Images"
- Click "Run workflow"
- Select branch/tag
- Click "Run workflow"

### Verify Published Images

```bash
# View on GitHub
# https://github.com/YOUR_USERNAME?tab=packages

# Pull images
docker pull ghcr.io/YOUR_USERNAME/luthiers-toolbox-api:latest
docker pull ghcr.io/YOUR_USERNAME/luthiers-toolbox-client:latest
docker pull ghcr.io/YOUR_USERNAME/luthiers-toolbox-nginx:latest
```

---

## 🌐 Production Deployment

### Option 1: VPS/Cloud VM (AWS EC2, DigitalOcean, etc.)

#### Prerequisites

- Ubuntu 22.04+ or similar Linux
- Docker + Docker Compose installed
- Domain name pointed to server IP (optional)
- Port 80 (HTTP) open in firewall

#### Deployment Steps

```bash
# 1. SSH into server
ssh user@your-server-ip

# 2. Install Docker (if needed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# 3. Clone repo or copy files
git clone https://github.com/YOUR_USERNAME/luthiers-toolbox.git
cd luthiers-toolbox

# 4. Create production .env
cat > .env << EOF
API_IMAGE=ghcr.io/YOUR_USERNAME/luthiers-toolbox-api:latest
CLIENT_IMAGE=ghcr.io/YOUR_USERNAME/luthiers-toolbox-client:latest
NGINX_IMAGE=ghcr.io/YOUR_USERNAME/luthiers-toolbox-nginx:latest
NGINX_PORT=80
EOF

# 5. Login to GHCR (if images are private)
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# 6. Pull and launch
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d

# 7. Verify
curl http://localhost/health
docker compose -f docker-compose.production.yml ps
```

#### Access

- **HTTP**: `http://your-server-ip`
- **API Docs**: `http://your-server-ip/docs`

### Option 2: Add HTTPS with Let's Encrypt

```bash
# 1. Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# 2. Stop nginx container temporarily
docker compose -f docker-compose.production.yml stop nginx

# 3. Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 4. Update docker-compose.production.yml
services:
  nginx:
    ports:
      - "80:80"
      - "443:443"  # Add HTTPS
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro

# 5. Update docker/nginx/default.conf (add SSL server block)
# See "HTTPS Configuration" section below

# 6. Restart
docker compose -f docker-compose.production.yml up -d
```

### Option 3: Docker Swarm (Multi-Node)

```bash
# Initialize swarm on manager node
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.production.yml toolbox

# Scale services
docker service scale toolbox_api=3
docker service scale toolbox_nginx=2

# View services
docker service ls
docker service logs toolbox_nginx
```

### Option 4: Kubernetes (Advanced)

See `kubernetes/` directory (to be created if needed).

---

## 🔒 HTTPS Configuration

Add this to `docker/nginx/default.conf`:

```nginx
# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # ... rest of config (API proxy, static files, etc.) ...
}
```

---

## 📊 Monitoring

### Health Checks

```bash
# Nginx health
curl http://localhost/health

# API health (via proxy)
curl http://localhost/api/health

# Container health
docker compose -f docker-compose.production.yml ps
```

### Logs

```bash
# All services
docker compose -f docker-compose.production.yml logs -f

# Specific service
docker compose -f docker-compose.production.yml logs -f nginx
docker compose -f docker-compose.production.yml logs -f api

# Last 100 lines
docker compose -f docker-compose.production.yml logs --tail=100
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Volume inspection
docker volume ls
docker volume inspect luthiers-toolbox_api_data
```

---

## 🔄 Updates

### Update to Latest Images

```bash
# Pull latest
docker compose -f docker-compose.production.yml pull

# Recreate containers
docker compose -f docker-compose.production.yml up -d

# Remove old images
docker image prune -a
```

### Update to Specific Version

```bash
# Edit .env
API_IMAGE=ghcr.io/YOUR_USERNAME/luthiers-toolbox-api:v1.2.0
CLIENT_IMAGE=ghcr.io/YOUR_USERNAME/luthiers-toolbox-client:v1.2.0
NGINX_IMAGE=ghcr.io/YOUR_USERNAME/luthiers-toolbox-nginx:v1.2.0

# Deploy
docker compose -f docker-compose.production.yml up -d
```

### Rollback

```bash
# Use previous version tag
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d

# Or use commit SHA tags
API_IMAGE=ghcr.io/YOUR_USERNAME/luthiers-toolbox-api:main-abc1234
```

---

## 🛠️ Troubleshooting

### Issue: Nginx 502 Bad Gateway

**Cause**: API container not healthy or network issue

**Solution**:
```bash
# Check API health
docker compose -f docker-compose.production.yml logs api

# Verify network
docker network inspect luthiers-toolbox_toolbox_network

# Restart API
docker compose -f docker-compose.production.yml restart api
```

### Issue: Vue App Shows Blank Page

**Cause**: Build failed or assets not copied

**Solution**:
```bash
# Check build logs
docker compose -f docker-compose.production.yml logs client

# Rebuild with no cache
docker compose -f docker-compose.production.yml build --no-cache client

# Verify files in container
docker compose -f docker-compose.production.yml exec nginx ls -la /usr/share/nginx/html
```

### Issue: /api Routes Return 404

**Cause**: Nginx routing misconfigured

**Solution**:
```bash
# Check nginx config
docker compose -f docker-compose.production.yml exec nginx cat /etc/nginx/conf.d/default.conf

# Test nginx config
docker compose -f docker-compose.production.yml exec nginx nginx -t

# Reload nginx
docker compose -f docker-compose.production.yml exec nginx nginx -s reload
```

### Issue: CORS Errors

**Cause**: Client making direct requests to api:8000 instead of via proxy

**Solution**: Update Vue app to use `/api` prefix:

```typescript
// src/utils/api.ts
const BASE_URL = '/api';  // Use proxy, not http://localhost:8000
```

---

## 📈 Performance Tuning

### Nginx Caching

Add to `docker/nginx/default.conf`:

```nginx
# Cache static assets
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    add_header X-Cache-Status $upstream_cache_status;
    # ... rest of proxy config ...
}
```

### API Performance

```bash
# Increase uvicorn workers
# docker/api/Dockerfile
CMD ["python","-m","uvicorn","services.api.app.main:app",\
     "--host","0.0.0.0","--port","8000",\
     "--workers","4"]  # Add workers
```

### Database Optimization

```bash
# Use volume for better I/O
volumes:
  api_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/fast-disk/api_data
```

---

## 🎯 Summary

### What You Have Now

✅ **Nginx front proxy** - Routes `/api` to FastAPI, serves Vue SPA  
✅ **Production client build** - Multi-stage Dockerfile (Vite build → nginx)  
✅ **GHCR publishing** - Automated image builds on push/tags  
✅ **Multi-platform images** - linux/amd64 + linux/arm64  
✅ **Production compose** - 3-service stack (api, client via nginx proxy, nginx)  
✅ **Health checks** - All containers monitored  
✅ **Security headers** - X-Frame-Options, CSP-ready  
✅ **Static asset caching** - 1-year cache for JS/CSS  
✅ **SPA routing** - Vue Router fallback  
✅ **CI/CD** - Automated builds + smoke tests  

### Deployment Checklist

- [ ] Update GitHub username in workflow
- [ ] Enable GHCR permissions
- [ ] Push to trigger image build
- [ ] Pull images on server
- [ ] Create production .env
- [ ] Launch stack
- [ ] Test endpoints
- [ ] Configure domain/HTTPS (optional)
- [ ] Setup monitoring (optional)

### Next Steps

1. **Test locally**: `docker compose -f docker-compose.production.yml up -d`
2. **Commit changes**: `git add . && git commit -m "Add production deployment"`
3. **Push to trigger CI**: `git push origin main`
4. **Deploy to server**: Follow VPS deployment steps

---

**Total Files**: 7 files created  
**Status**: 🟢 **PRODUCTION READY**

