# Blueprint Reader Photo-Vectorizer Integration State

**Date:** 2026-04-28  
**Scope:** Investigation only — no code changes

---

## 1. What endpoints does blueprint-reader.html currently call?

**Blueprint mode:**
- `POST /api/blueprint/vectorize/async` — submit job (FormData: file, target_height_mm, min_contour_length_mm, close_gaps_mm, debug)
- `GET /api/blueprint/vectorize/status/{jobId}` — poll for completion
- `POST /api/blueprint/clean` — filter contours (JSON: dxf_path, min_contour_length_mm)
- `GET /api/blueprint/clean/download/{filename}` — legacy streaming fallback

**Photo mode:**
- `POST /api/vectorizer/extract` — JSON body with image_b64, source_type, export_svg, export_dxf, spec_name

Both hostinger/ and tools/ versions are identical.

---

## 2. Are any photo-vectorizer endpoints among those calls?

**No.** The frontend does NOT call:
- `/api/blueprint/edge-to-dxf/` (any path)
- `/api/photo-vectorizer/` (any path)

The comment on line 588 ("90s for edge-to-dxf") is stale. Git history (commit ad285944) shows the frontend was migrated FROM `/api/blueprint/edge-to-dxf/convert` TO `/api/blueprint/vectorize/async`.

Photo mode calls `/api/vectorizer/extract`, which is the photo-vectorizer service but at a different route prefix than documentation suggests.

---

## 3. Evidence of partial integration work?

**None in frontend.** Searched for:
- Commented-out photo-vectorizer calls — none found
- Unused JS variables (pvUrl, callPhotoVectorizer) — none found
- TODO/FIXME comments — none found

**Stash `stash@{2}: photo-vectorizer WIP`** contains backend code only (geometry_coach_v2.py and tests), not frontend integration.

**Documentation mismatch:** BLUEPRINT_VECTORIZER_ARCHITECTURE.md and EDGE_TO_DXF_API_MIGRATION_HANDOFF.md describe edge-to-dxf as the current path. The frontend disagrees — it was already migrated.

---

## 4. UI surface and what each element triggers

| Element | Triggers |
|---------|----------|
| Upload zone | handleFile() — sets selectedFile, auto-detects mode |
| Source Type dropdown | Stored in requestBody for photo mode only |
| Instrument Spec dropdown | Sent as spec_name to photo mode only |
| Mode badge (Blueprint/Photo) | Toggles routeMode variable, syncs sourceType |
| Extract Outline button | Branches on routeMode: blueprint→async job, photo→vectorizer/extract |
| Retry button | Re-clicks Extract button with backoff |
| Download SVG | Builds from artifacts.svg.content or svg_path_d |
| Download DXF | Uses artifacts.dxf.base64 or streaming fallback |

**No orphan UI.** All elements have wired handlers.

---

## 5. Call chain: upload to DXF

**Blueprint mode:**
1. User drops file → handleFile() sets routeMode='blueprint'
2. Click Extract → POST /api/blueprint/vectorize/async with FormData
3. Poll /api/blueprint/vectorize/status/{jobId} every 5s
4. On complete: extractedData = pollResult
5. getArtifacts() reads artifacts.svg.content, artifacts.dxf.base64
6. renderSvgPreview() displays SVG
7. Click Download DXF → atob(artifacts.dxf.base64) → Blob → download

**Photo mode:**
1. User drops JPG/PNG → handleFile() sets routeMode='photo'
2. Click Extract → resizeImageIfNeeded() → base64
3. POST /api/vectorizer/extract with JSON body
4. extractedData = response JSON
5. getArtifacts() reads svg_content or svg_path_d, dxf_base64
6. renderSvgPreview() displays SVG
7. Click Download DXF → atob(dxf_base64) → Blob → download

---

## Key Findings

1. **Frontend already migrated from edge-to-dxf.** The async vectorize endpoints are in use; edge-to-dxf is not called.
2. **Documentation is stale.** Handoffs describe edge-to-dxf as current; code shows migration complete.
3. **No partial integration remnants.** The migration was clean — no commented code, no orphan UI.
4. **Photo mode uses /api/vectorizer/extract,** not /api/photo-vectorizer/ paths.
5. **Stale comment on line 588** says "edge-to-dxf" but the endpoint changed.
