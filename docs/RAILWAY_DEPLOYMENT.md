# Railway Deployment Guide

## Overview

Luthier's ToolBox is deployed on Railway as two services:

| Service | URL | Description |
|---------|-----|-------------|
| **API** | `luthiers-toolbox-production.up.railway.app` | FastAPI backend |
| **Client** | `luthiers-toolbox-production-635e.up.railway.app` | Vue 3 frontend |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│     Client      │────▶│      API        │
│  (Vue 3/Vite)   │     │   (FastAPI)     │
│     nginx       │     │    uvicorn      │
└─────────────────┘     └─────────────────┘
   packages/client        services/api
```

## Service Configuration

### API Service (`services/api`)

- **Builder**: Dockerfile
- **Root Directory**: `services/api`
- **Dockerfile**: `services/api/Dockerfile`
- **Health Check**: `/health`
- **Port**: Dynamic (uses Railway's `PORT` env var, defaults to 8000)

**Environment Variables**:
- `PORT` - Set automatically by Railway
- `SG_SPEC_TOKEN` - GitHub token for private repo access (if needed)
- `CORS_ORIGINS` - Allowed CORS origins (set to client URL)

### Client Service (`packages/client`)

- **Builder**: Dockerfile
- **Root Directory**: `packages/client`
- **Dockerfile**: `packages/client/Dockerfile`
- **Health Check**: `/health`
- **Port**: Dynamic (uses Railway's `PORT` env var)

**Environment Variables**:
- `PORT` - Set automatically by Railway
- `VITE_API_URL` - API base URL (e.g., `https://luthiers-toolbox-production.up.railway.app`)

**Note**: `VITE_*` variables are baked in at build time. Changes require a redeploy.

## Configuration Files

### `packages/client/railway.json`
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "startCommand": "/bin/sh /start.sh",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 60
  }
}
```

### `services/api/railway.json`
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "healthcheckPath": "/health",
    "healthcheckTimeout": 120
  }
}
```

## Auto-Deploy

Both services auto-deploy on push to `main` branch.

## Troubleshooting

### "Dockerfile does not exist"
- Check `railway.json` has correct `dockerfilePath`
- Verify Root Directory is set correctly in Railway dashboard

### "pnpm not found" or wrong start command
- Add `startCommand` in `railway.json` to override stuck dashboard settings

### 502 Bad Gateway
- Check deployment logs for errors
- Verify PORT env var is being used correctly

### Client shows JSON errors
- Set `VITE_API_URL` environment variable
- Redeploy (Vite vars are baked at build time)

## Useful Commands

```bash
# Check API health
curl https://luthiers-toolbox-production.up.railway.app/health

# Check client health  
curl https://luthiers-toolbox-production-635e.up.railway.app/health

# View API docs
open https://luthiers-toolbox-production.up.railway.app/docs
```
