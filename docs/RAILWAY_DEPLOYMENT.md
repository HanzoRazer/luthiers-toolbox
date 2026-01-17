# Railway Deployment Guide

This guide explains how to deploy Luthier's Tool Box to [Railway](https://railway.app).

## Overview

The project deploys as two services:
- **API** (`services/api`): FastAPI backend (Python 3.11)
- **Client** (`packages/client`): Vue 3 + Vite frontend (nginx)

## Quick Start

### Option 1: Deploy via Railway Dashboard (Recommended)

1. **Create a Railway Account**
   - Go to [railway.app](https://railway.app) and sign up
   - Link your GitHub account

2. **Create New Project**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `HanzoRazer/luthiers-toolbox`
   - Railway will detect the `railway.json` files automatically

3. **Configure Services**

   For the **API service**:
   - Root Directory: `services/api`
   - Add environment variables:
     - `SG_SPEC_TOKEN`: Your GitHub token for private sg-spec repo
     - `CORS_ORIGINS`: Will be auto-set to client URL
   - Add a volume for persistent SQLite storage (optional)

   For the **Client service**:
   - Root Directory: `packages/client`
   - Add environment variable:
     - `VITE_API_URL`: Set to the API service URL

4. **Generate Domain**
   - Click on each service → Settings → Generate Domain
   - Update `CORS_ORIGINS` on API with the client domain

### Option 2: Deploy via GitHub Actions

1. **Get Railway Token**
   - Go to Railway Dashboard → Account → Tokens
   - Create a new token

2. **Add GitHub Secret**
   - Go to your GitHub repo → Settings → Secrets → Actions
   - Add `RAILWAY_TOKEN` with your Railway token

3. **Push to main**
   - The workflow `.github/workflows/railway-deploy.yml` will auto-deploy

4. **Manual Deploy**
   - Go to Actions → Railway Deploy → Run workflow
   - Select which service to deploy

### Option 3: Deploy via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Deploy API
cd services/api
railway up --service api

# Deploy Client
cd packages/client
railway up --service client
```

## Environment Variables

### API Service

| Variable | Description | Required |
|----------|-------------|----------|
| `SG_SPEC_TOKEN` | GitHub token for private sg-spec repo | Yes (for build) |
| `CORS_ORIGINS` | Allowed CORS origins (client URL) | Yes |
| `ART_STUDIO_DB_PATH` | SQLite database path | No (defaults to /app/...) |
| `SERVER_PORT` | API server port | No (defaults to 8000) |

### Client Service

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_URL` | API backend URL | Yes |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│     Client      │────▶│       API       │
│   (Vue + nginx) │     │   (FastAPI)     │
│     Port 80     │     │    Port 8000    │
└─────────────────┘     └─────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         │              │   SQLite DB     │
         │              │   (Volume)      │
         │              └─────────────────┘
         ▼
    User Browser
```

## Volumes (Persistent Storage)

For production, attach a volume to the API service:
- Mount path: `/app/services/api/app/data`
- This persists the SQLite database across deployments

## Health Checks

Both services have health check endpoints:
- **API**: `GET /health`
- **Client**: `GET /health`

Railway monitors these automatically.

## Troubleshooting

### Build Fails: "Cannot find module sg-spec"
- Ensure `SG_SPEC_TOKEN` is set in Railway environment variables
- The token needs read access to the private sg-spec repository

### CORS Errors
- Update `CORS_ORIGINS` on the API service to include the client domain
- Format: `https://your-client.railway.app`

### Database Reset on Deploy
- Attach a volume to the API service to persist data
- Mount at `/app/services/api/app/data`

### Client Shows Blank Page
- Check browser console for errors
- Verify `VITE_API_URL` points to the correct API URL
- Ensure API is running and accessible

## Monitoring

Railway provides built-in monitoring:
- Logs: Click on service → Logs
- Metrics: Click on service → Metrics
- Deployments: Click on service → Deployments

## Cost Estimation

Railway pricing (as of 2025):
- Free tier: $5/month credit
- Usage-based: ~$0.000463/GB-minute for memory
- Typical cost for this project: $5-20/month depending on traffic
