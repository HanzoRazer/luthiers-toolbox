# Vision Image Display Fix — Complete

## Issue Summary
AI-generated images were not displaying in the UI because:
1. Backend returned `sha256` but no browser-loadable `url`
2. Frontend expected `image.url` for `<img :src="image.url">`
3. No blob download endpoint existed to serve CAS-stored bytes

## Root Cause of "advisory is not defined" Error

**The bug was a `*/` sequence inside a JSDoc comment that prematurely closed the comment block.**

In `packages/client/src/features/ai_images/api/visionApi.ts`, line 4:
```
* Calls the canonical /api/vision/* and /api/rmos/runs/*/advisory/* endpoints.
```

The `*/` in `runs/*/advisory` was interpreted as closing the JSDoc comment, leaving `advisory/*` as actual JavaScript code:
- `advisory` was evaluated as a variable (undefined) → `ReferenceError`
- `/*` started a new comment

**Fix:** Changed `runs/*/advisory/*` to `runs/{id}/advisory/*` to avoid the `*/` sequence.

---

## All Patches Applied

### Backend

| File | Change |
|------|--------|
| `services/api/app/vision/schemas.py` | Added `url` field to VisionAsset |
| `services/api/app/vision/router.py` | Added `_blob_download_url()`, populate `url` field |
| `services/api/app/advisory/blob_router.py` | **NEW** — blob download endpoint |
| `services/api/app/main.py` | Import + mount blob_router |

### Frontend

| File | Change |
|------|--------|
| `packages/client/src/main.ts` | Added Pinia initialization (was missing!) |
| `packages/client/src/features/ai_images/api/visionApi.ts` | Fixed JSDoc comment `*/` bug |
| `packages/client/src/features/ai_images/VisionAttachToRunWidget.vue` | Fixed image src to use `asset.url` |
| `packages/client/src/views/VisionAttachTestView.vue` | **NEW** — test page |
| `packages/client/src/router/index.ts` | Added `/dev/vision-attach` route |

---

## Architecture

```
Frontend (Vite)                           Backend (FastAPI :8000)
───────────────                           ───────────────────────
POST /api/vision/generate
        │
        └──► Vision Router generates images
             │
             └──► Returns VisionAsset[] with:
                  - sha256: content hash
                  - url: "/api/advisory/blobs/{sha}/download"

<img :src="asset.url">
        │
        └──► GET /api/advisory/blobs/{sha}/download
             │
             └──► Blob Router serves raw bytes from CAS
```

---

## How to Test

1. **Start backend:**
   ```powershell
   cd services\api
   $env:OPENAI_API_KEY="sk-proj-..."
   .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
   ```

2. **Start frontend:**
   ```powershell
   cd packages\client
   npm run dev
   ```

3. **Test the widget:**
   - Navigate to: `http://localhost:5173/dev/vision-attach`
   - Select "stub" provider (or "openai" if package installed)
   - Enter prompt, click Generate
   - Image should display in grid
   - Select image, select run, click Attach

---

## Lessons Learned

1. **JSDoc comments with URL patterns containing `*/` will break** — the `*/` closes the comment prematurely
2. **Sourcemaps can be misleading** — disabling them revealed the true bundled output
3. **Always check the compiled JS** — `curl http://localhost:PORT/src/file.ts` shows what Vite actually serves
4. **Pinia must be initialized** — `app.use(pinia)` before `app.use(router)` in main.ts
