param(
  [string]$Root = "Luthiers_Tool_Box_Full",
  [string]$ZipName = "Luthiers_Tool_Box_Full_GitHubReady_Ultra.zip",
  [string]$GitRemote = "",            # e.g. https://github.com/you/luthiers-tool-box.git
  [string]$Tag = "v0.1.0"
)

$ErrorActionPreference = "Stop"
$ZipPath = Join-Path $PWD $ZipName

function Ensure-Dir($Path) {
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
}
function Write-File($Path, $Content) {
  Ensure-Dir $Path
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}
function Have-Git { try { git --version *> $null; return $true } catch { return $false } }

# Clean slate
if (Test-Path $Root) { Remove-Item $Root -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Root | Out-Null

# -------------------- SERVER (FastAPI) --------------------
Write-File "$Root\server\requirements.txt" @"
fastapi
uvicorn[standard]
pydantic
shapely
ezdxf
python-multipart
"@

Write-File "$Root\server\Dockerfile" @"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]
"@

Write-File "$Root\server\app.py" @"
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import os, json, asyncio, ezdxf
from shapely.geometry import Polygon
from shapely.ops import unary_union

app = FastAPI(title="Luthier's Tool Box API")
STORAGE = os.path.abspath("./storage")
os.makedirs(STORAGE, exist_ok=True)

DB: Dict[str, dict] = {"projects": {}, "documents": {}, "versions": {}, "exports": {}}

class NewProject(BaseModel): name: str
class NewDocument(BaseModel): project_id: str; name: str
class SaveVersion(BaseModel):
    document_id: str
    author: str = "anon"
    payload_json: Dict[str, Any]
    is_snapshot: bool = True
class ExportReq(BaseModel):
    document_id: str
    version_no: Optional[int] = None
    kind: str = "dxf"
    notes: Optional[str] = None

@app.post("/projects")
def create_project(req: NewProject):
    pid = str(uuid4())
    DB["projects"][pid] = {"id": pid, "name": req.name, "created_at": datetime.utcnow().isoformat()}
    return DB["projects"][pid]

@app.post("/documents")
def create_document(req: NewDocument):
    if req.project_id not in DB["projects"]: raise HTTPException(404, "project not found")
    did = str(uuid4())
    DB["documents"][did] = {"id": did, "project_id": req.project_id, "name": req.name, "head_version": 0}
    DB["versions"][did] = []
    return DB["documents"][did]

@app.post("/versions/save")
def save_version(req: SaveVersion):
    doc = DB["documents"].get(req.document_id)
    if not doc: raise HTTPException(404, "document not found")
    if (req.payload_json or {}).get("units","mm") != "mm":
        raise HTTPException(400, "units must be 'mm'")
    new_no = doc["head_version"] + 1
    DB["versions"][req.document_id].append({
        "version_no": new_no,
        "is_snapshot": req.is_snapshot,
        "payload_json": req.payload_json,
        "created_at": datetime.utcnow().isoformat(),
        "author": req.author,
    })
    doc["head_version"] = new_no
    return {"ok": True, "version_no": new_no}

@app.get("/versions/{document_id}")
def list_versions(document_id: str):
    return DB["versions"].get(document_id, [])

@app.post("/exports/queue")
def queue_export(req: ExportReq):
    doc = DB["documents"].get(req.document_id)
    if not doc: raise HTTPException(404, "document not found")
    vno = req.version_no or doc["head_version"]
    if vno < 1: raise HTTPException(400, "no versions available")
    exp_id = str(uuid4())
    out_dir = os.path.join(STORAGE, "exports")
    os.makedirs(out_dir, exist_ok=True)
    file_path = os.path.join(out_dir, f"export_{exp_id}.{req.kind}")
    DB["exports"][exp_id] = {
        "id": exp_id, "document_id": req.document_id, "version_no": vno,
        "kind": req.kind, "status": "queued", "file_path": file_path
    }
    asyncio.create_task(_process_export(exp_id))
    return DB["exports"][exp_id]

@app.get("/exports/list")
def list_exports(status: Optional[str] = None, kind: Optional[str] = None):
    items = list(DB["exports"].values())
    if status: items = [e for e in items if e["status"] == status]
    if kind:   items = [e for e in items if e["kind"] == kind]
    return items

@app.get("/files/{export_id}")
def get_export_file(export_id: str):
    exp = DB["exports"].get(export_id)
    if not exp or exp["status"] != "ready" or not os.path.exists(exp["file_path"]):
        raise HTTPException(404, "file not ready")
    return FileResponse(exp["file_path"], filename=os.path.basename(exp["file_path"]))

async def _process_export(export_id: str):
    exp = DB["exports"][export_id]
    exp["status"] = "processing"
    try:
        versions = DB["versions"][exp["document_id"]]
        payload = next(v for v in versions if v["version_no"] == exp["version_no"])["payload_json"]
        polylines = payload.get("polylines", [])
        doc = ezdxf.new("R12")  # R12 LWPolylines (mm)
        msp = doc.modelspace()
        for ring in polylines:
            if not ring: continue
            if ring[0] != ring[-1]: ring = ring + [ring[0]]
            msp.add_lwpolyline(ring, format="xy", dxfattribs={"layer":"OUTLINE","closed":True})
        os.makedirs(os.path.dirname(file_path := exp["file_path"]), exist_ok=True)
        doc.saveas(file_path)
        exp["status"] = "ready"
    except Exception as e:
        exp["status"] = "error"; exp["notes"]=str(e)
"@

# -------------------- CLIENT (Vue 3 + Vite) --------------------
Write-File "$Root\client\Dockerfile" @"
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN npm i || true
COPY . .
RUN npm run build
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
"@

Write-File "$Root\client\package.json" @"
{
  "name": "luthiers-tool-box-client",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "echo Skipping lint (add ESLint later)"
  },
  "dependencies": { "vue": "^3.4.0" },
  "devDependencies": { "vite": "^5.0.0", "@vitejs/plugin-vue": "^5.0.0" }
}
"@

Write-File "$Root\client\vite.config.ts" @"
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig({
  plugins:[vue()],
  server:{
    port:5173,
    proxy:{ '/api': { target:'http://localhost:8000', changeOrigin:true, rewrite:p=>p.replace(/^\\/api/,'') } }
  },
  build:{ outDir:'dist', emptyOutDir:true }
})
"@

Write-File "$Root\client\index.html" @"
<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Luthier’s Tool Box</title></head>
<body><div id='app'></div><script type='module' src='/src/main.ts'></script></body></html>
"@

Write-File "$Root\client\src\main.ts" @"
import { createApp } from 'vue'
import App from './App.vue'
createApp(App).mount('#app')
"@

Write-File "$Root\client\src\App.vue" @"
<template>
  <div style='font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; padding:16px'>
    <h2>Luthier’s Tool Box (Vue 3 + Vite, mm)</h2>
    <button @click='queue'>Queue Demo DXF</button>
    <pre>{{ status }}</pre>
  </div>
</template>
<script setup>
import { ref } from 'vue'
const status = ref('Idle')
async function queue(){
  const p = await fetch('/api/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Demo'})}).then(r=>r.json())
  const d = await fetch('/api/documents',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project_id:p.id,name:'Top'})}).then(r=>r.json())
  const polylines = [[[0,0],[300,0],[300,200],[0,200]]]
  const sv = await fetch('/api/versions/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({document_id:d.id,author:'toolbox',is_snapshot:true,payload_json:{polylines,units:'mm'}})}).then(r=>r.json())
  const exp = await fetch('/api/exports/queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({document_id:d.id,version_no:sv.version_no,kind:'dxf',notes:'demo rectangle'})}).then(r=>r.json())
  status.value = JSON.stringify(exp,null,2)
}
</script>
"@

# -------------------- Docker Compose --------------------
Write-File "$Root\docker-compose.yml" @"
version: '3.9'
services:
  api:
    build: ./server
    container_name: ltb-api
    ports: ['8000:8000']
    volumes:
      - ./server/storage:/app/storage
  client:
    build: ./client
    container_name: ltb-client
    depends_on: [api]
    ports: ['8080:80']
"@

# -------------------- GitHub Actions (CI + Release/GHCR) --------------------
New-Item -ItemType Directory -Force -Path "$Root\.github\workflows" | Out-Null

Write-File "$Root\.github\workflows\ci.yml" @"
name: CI
on: [push, pull_request]
jobs:
  build-and-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Server deps check
        run: |
          cd server
          python -m venv .venv
          . .venv/bin/activate
          pip install -r requirements.txt
          python - << 'PY'
import importlib
for m in ('fastapi','uvicorn','pydantic','shapely','ezdxf'):
    importlib.import_module(m)
print('Server deps OK')
PY
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - name: Client build
        run: |
          cd client
          npm ci || npm i
          npm run build
"@

Write-File "$Root\.github\workflows\release.yml" @"
name: Release
on:
  push:
    tags: ['v*']
permissions:
  contents: read
  packages: write
jobs:
  build-artifacts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - name: Build client
        run: |
          cd client
          npm ci || npm i
          npm run build
          tar -czf ../client-dist.tgz -C dist .
      - uses: actions/upload-artifact@v4
        with: { name: client-dist, path: client-dist.tgz }
  docker-publish:
    needs: build-artifacts
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: \${{ github.repository_owner }}
          password: \${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: ./server
          push: true
          tags: |
            ghcr.io/\${{ github.repository_owner }}/luthiers-tool-box-api:latest
            ghcr.io/\${{ github.repository_owner }}/luthiers-tool-box-api:\${{ github.ref_name }}
      - uses: docker/build-push-action@v5
        with:
          context: ./client
          push: true
          tags: |
            ghcr.io/\${{ github.repository_owner }}/luthiers-tool-box-client:latest
            ghcr.io/\${{ github.repository_owner }}/luthiers-tool-box-client:\${{ github.ref_name }}
"@

# -------------------- Repo meta --------------------
Write-File "$Root\.gitignore" @"
node_modules/
dist/
.vite/
.cache/
*.log
__pycache__/
*.py[cod]
.venv/
.DS_Store
Thumbs.db
server/storage/
"@

Write-File "$Root\LICENSE" @"
MIT License

Copyright (c) 2025
Permission is hereby granted, free of charge, to any person obtaining a copy of this software...
"@

Write-File "$Root\README.md" @"
# Luthier’s Tool Box – Vue 3 + Vite (mm) + FastAPI (DXF R12)

## Run locally
### API
\`\`\`bash
cd server
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
\`\`\`

### Client
\`\`\`bash
cd client
npm i
npm run dev
# open http://localhost:5173
\`\`\`

## Docker Compose
\`\`\`bash
docker compose up --build -d
# Client: http://localhost:8080 | API: http://localhost:8000
\`\`\`

## CI
- \`.github/workflows/ci.yml\`: builds server deps + client on push/PR
- \`.github/workflows/release.yml\`: tag \`vX.Y.Z\` → builds client artifact and publishes Docker images to GHCR
"@

# -------------------- ZIP --------------------
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path "$Root\*" -DestinationPath $ZipPath -Force
Write-Host "`n📦 Created ZIP:" (Resolve-Path $ZipPath)

# -------------------- Git init / first commit / optional push+tag --------------------
if (-not (Have-Git)) {
  Write-Warning "Git is not installed or not on PATH — skipping repo init/push."
  return
}

Push-Location $Root
git init | Out-Null
git add . | Out-Null
git commit -m "feat: Luthier’s Tool Box MVP (Vue 3 + FastAPI, mm, DXF R12, Docker, CI)" | Out-Null
git branch -M main | Out-Null

if ($GitRemote) {
  git remote add origin $GitRemote | Out-Null
  git push -u origin main
  if ($Tag) {
    git tag -a $Tag -m "Release $Tag"
    git push origin $Tag
  }
  Write-Host "`n✅ Repo pushed to:" $GitRemote
} else {
  Write-Host "`nℹ️  Skipped push (no -GitRemote provided)."
}

Pop-Location
Write-Host "`n✅ Done. Client/dev: http://localhost:5173  | API: http://localhost:8000"
