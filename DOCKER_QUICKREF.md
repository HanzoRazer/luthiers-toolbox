# 🐳 Docker Quick Reference

## 🚀 Essential Commands

### Start
```powershell
.\docker-start.ps1                    # Automated start
# OR
docker compose up -d                  # Manual start
```

### Test
```powershell
.\docker-test.ps1                     # Run 8 automated tests
```

### Stop
```powershell
docker compose down                   # Stop and remove containers
docker compose down -v                # Also remove volumes
```

---

## 📊 Status & Logs

```powershell
docker compose ps                     # List running containers
docker compose logs -f                # Follow all logs
docker compose logs -f api            # Follow API logs only
docker compose logs -f client         # Follow client logs only
docker compose logs --tail=50 api     # Last 50 lines
```

---

## 🔄 Rebuild & Restart

```powershell
# Rebuild specific service
docker compose build api
docker compose up -d api

# Rebuild all
docker compose build
docker compose up -d

# Rebuild without cache
docker compose build --no-cache
```

---

## 🧪 Test Endpoints

```powershell
# Health check
curl http://localhost:8000/health

# Arc simulation
curl -X POST http://localhost:8000/cam/simulate_gcode `
  -H "Content-Type: application/json" `
  -d '{"gcode":"G21 G90 G17 F1200\nG2 X60 Y40 I30 J20"}'

# Post-processors
curl http://localhost:8000/tooling/posts | ConvertFrom-Json

# Via client proxy
curl http://localhost:8080/health
```

---

## 🐚 Container Shell Access

```powershell
# API container
docker compose exec api /bin/bash

# Client container
docker compose exec client /bin/sh

# Run one-off command
docker compose exec api python -c "import sys; print(sys.version)"
```

---

## 📦 Images & Cleanup

```powershell
# List images
docker images | Select-String toolbox

# Remove unused images
docker image prune

# Remove specific image
docker rmi toolbox/api:local

# Clean everything (BE CAREFUL!)
docker system prune -a --volumes
```

---

## 🔍 Debugging

```powershell
# Inspect container
docker compose exec api env              # Check environment vars
docker compose exec api curl localhost:8000/health  # Test from inside

# Check network
docker network ls
docker network inspect toolbox_default

# Check volumes
docker volume ls
docker volume inspect toolbox_data
```

---

## 🎯 Common Workflows

### Fresh Start
```powershell
docker compose down -v
docker compose build --no-cache
docker compose up -d
.\docker-test.ps1
```

### Quick Restart
```powershell
docker compose restart
```

### Update Code & Restart
```powershell
# Make changes to services/api/...
docker compose build api
docker compose up -d api
docker compose logs -f api
```

---

## 📈 Resource Monitoring

```powershell
# Real-time stats
docker stats

# Disk usage
docker system df

# Container resource limits
docker compose exec api cat /sys/fs/cgroup/memory/memory.limit_in_bytes
```

---

## 🔧 Environment

```powershell
# Use different env file
docker compose --env-file .env.prod up -d

# Override port
$env:SERVER_PORT="9000"; docker compose up -d

# Check loaded config
docker compose config
```

---

## 🚢 Production

### Push to Registry
```powershell
# Tag
docker tag toolbox/api:local ghcr.io/yourorg/api:v1.0.0

# Login
docker login ghcr.io -u USERNAME -p TOKEN

# Push
docker push ghcr.io/yourorg/api:v1.0.0
```

### Pull on Server
```powershell
docker pull ghcr.io/yourorg/api:v1.0.0
docker compose up -d
```

---

## URLs

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | Direct API access |
| API Docs | http://localhost:8000/docs | Swagger UI |
| OpenAPI | http://localhost:8000/openapi.json | API spec |
| Client | http://localhost:8080 | Nginx frontend |
| Client Proxy | http://localhost:8080/cam/... | Proxied API |

---

## File Structure

```
docker/
├── api/
│   └── Dockerfile              # FastAPI container
└── client/
    ├── Dockerfile              # Nginx container
    ├── index.html              # Static site
    └── client.nginx.conf       # Proxy config

docker-compose.yml              # Orchestration
.env.example                    # Config template
docker-start.ps1                # Start script
docker-test.ps1                 # Test script
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port in use | Change `SERVER_PORT` in `.env` |
| Build fails | `docker compose build --no-cache` |
| Health check fails | `docker compose logs api` |
| Can't connect | Check `docker compose ps` |
| Out of space | `docker system prune -a` |

---

**Full docs**: See `DOCKER_SETUP.md`
