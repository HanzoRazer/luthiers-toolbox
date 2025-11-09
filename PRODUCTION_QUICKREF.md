# 🚀 Production Patch - Quick Reference

## What's Included

✅ **Nginx Front Proxy** - Routes `/api` → FastAPI, serves Vue SPA  
✅ **Production Client Build** - Multi-stage Dockerfile (Vite → nginx)  
✅ **GHCR Publishing** - Automated image builds on push/tags  
✅ **Production Compose** - 3-service orchestration  

---

## Files Created (7 files)

### Docker Configuration
1. `docker/nginx/Dockerfile` - Nginx proxy image
2. `docker/nginx/nginx.conf` - Main nginx config
3. `docker/nginx/default.conf` - Routing rules (API proxy + SPA)
4. `docker/client/Dockerfile.production` - Multi-stage Vue build
5. `docker-compose.production.yml` - Production stack

### CI/CD
6. `.github/workflows/publish-images.yml` - Automated GHCR publishing

### Documentation
7. `PRODUCTION_DEPLOYMENT.md` - Complete deployment guide

---

## Quick Test

```powershell
# Build production images locally
docker compose -f docker-compose.production.yml build

# Launch stack
docker compose -f docker-compose.production.yml up -d

# Test
curl http://localhost/health          # Nginx health
curl http://localhost/api/health      # API via proxy
Start-Process http://localhost        # Vue SPA
Start-Process http://localhost/docs   # API docs

# Stop
docker compose -f docker-compose.production.yml down -v
```

---

## Publish to GHCR

### 1. Update GitHub Username

Edit `.github/workflows/publish-images.yml`:
```yaml
env:
  IMAGE_PREFIX: YOUR_GITHUB_USERNAME/luthiers-toolbox
```

Edit `docker-compose.production.yml`:
```yaml
services:
  api:
    image: ghcr.io/YOUR_USERNAME/luthiers-toolbox-api:latest
  client:
    image: ghcr.io/YOUR_USERNAME/luthiers-toolbox-client:latest
  nginx:
    image: ghcr.io/YOUR_USERNAME/luthiers-toolbox-nginx:latest
```

### 2. Enable GHCR Permissions

- GitHub repo → Settings → Actions → General
- Workflow permissions → "Read and write permissions"
- Enable "Allow GitHub Actions to create and approve pull requests"

### 3. Push to Trigger Build

```bash
git add .
git commit -m "Add production deployment with nginx proxy"
git push origin main
```

**GitHub Actions will**:
- Build 3 images (API, Client, Nginx)
- Tag with `latest` and `main-<sha>`
- Push to ghcr.io/YOUR_USERNAME/luthiers-toolbox-*
- Support linux/amd64 + linux/arm64

### 4. Deploy on Server

```bash
# On your server
docker login ghcr.io -u YOUR_USERNAME -p YOUR_GITHUB_TOKEN

# Create .env
cat > .env << EOF
API_IMAGE=ghcr.io/YOUR_USERNAME/luthiers-toolbox-api:latest
CLIENT_IMAGE=ghcr.io/YOUR_USERNAME/luthiers-toolbox-client:latest
NGINX_IMAGE=ghcr.io/YOUR_USERNAME/luthiers-toolbox-nginx:latest
NGINX_PORT=80
EOF

# Pull and launch
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d
```

---

## Architecture

```
Browser
    │
    ↓
[Nginx :80]
    │
    ├─ /api/* ────→ [FastAPI :8000] (internal)
    │                   │
    │                   └─ SQLite (persistent)
    │
    └─ /* ─────────→ [Vue SPA] (static files)
```

### Routing Rules

| Path | Destination | Purpose |
|------|-------------|---------|
| `/api/*` | FastAPI backend | API calls |
| `/health` | FastAPI health | Health check |
| `/docs` | FastAPI docs | API documentation |
| `/assets/*` | Nginx static | Vue app JS/CSS |
| `/` | Nginx index.html | Vue SPA entry |
| `/<any>` | Nginx index.html | Vue Router fallback |

---

## Production Features

### Security
- ✅ X-Frame-Options, X-Content-Type-Options headers
- ✅ XSS Protection
- ✅ Hidden file access denied (/.git, etc.)
- ✅ Non-root containers

### Performance
- ✅ Gzip compression (text, JS, CSS, JSON)
- ✅ Static asset caching (1 year)
- ✅ No caching for index.html (always fresh)
- ✅ Multi-stage builds (small images)

### Reliability
- ✅ Health checks on all containers
- ✅ Auto-restart on failure
- ✅ Graceful shutdown
- ✅ Persistent data volumes

---

## Version Tagging

### Create Release

```bash
# Tag version
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions will:
# - Build images
# - Tag with v1.0.0, 1.0, 1, latest
# - Create GitHub Release
# - Push to GHCR
```

### Use Specific Version

```bash
# In .env
API_IMAGE=ghcr.io/YOUR_USERNAME/luthiers-toolbox-api:v1.0.0
```

---

## Troubleshooting

### Nginx 502 Bad Gateway
```bash
# Check API health
docker compose -f docker-compose.production.yml logs api

# Restart API
docker compose -f docker-compose.production.yml restart api
```

### Vue App Blank Page
```bash
# Check build
docker compose -f docker-compose.production.yml logs client

# Rebuild
docker compose -f docker-compose.production.yml build --no-cache client
```

### /api Routes 404
```bash
# Test nginx config
docker compose -f docker-compose.production.yml exec nginx nginx -t

# Reload nginx
docker compose -f docker-compose.production.yml exec nginx nginx -s reload
```

---

## Monitoring

```bash
# Logs
docker compose -f docker-compose.production.yml logs -f

# Resource usage
docker stats

# Health status
curl http://localhost/health
curl http://localhost/api/health
```

---

## Updates

```bash
# Pull latest
docker compose -f docker-compose.production.yml pull

# Recreate
docker compose -f docker-compose.production.yml up -d

# Clean old images
docker image prune -a
```

---

## Key Commands

```powershell
# Local build and test
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d
curl http://localhost/health

# Push to trigger GHCR publish
git push origin main

# Deploy on server
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d

# Stop
docker compose -f docker-compose.production.yml down -v
```

---

## Summary

**What You Get**:
- 🌐 Single-port deployment (nginx :80)
- 🔀 Automatic API routing
- 📦 Published images on GHCR
- 🚀 Production-ready configuration
- 🔄 CI/CD automation
- 📱 Multi-platform support (amd64, arm64)

**Next Step**: See `PRODUCTION_DEPLOYMENT.md` for complete deployment guide.

---

**Status**: 🟢 **READY TO DEPLOY**
