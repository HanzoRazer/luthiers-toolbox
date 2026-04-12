# Vectorizer Pipeline Handoff
**Date:** 2025-04-09  
**Status:** Production Regression  
**Priority:** HIGH  

---

## 1. Executive Summary

The blueprint/photo vectorizer pipeline works in isolation but fails inconsistently in production deployment. Users upload images expecting both SVG preview and DXF download. They get:

- SVG only (no DXF)
- DXF only (no SVG)  
- Empty DXF (595K entities → 0 contours)
- Silent failures (dimensions shown, no artifacts)

**Root issue:** No unified artifact contract. Backend returns partial results as "success."

**Target state:** Success requires BOTH artifacts present and valid. Otherwise, fail loudly with stage + reason.

---

## 2. Observed Failures (Real Test Cases)

### Case A: Benedetto 17" Archtop Blueprint (PDF)

| Field | Value | Expected |
|-------|-------|----------|
| `ok` | true | — |
| `body_width_mm` | 323.1 | 431.8 |
| `body_height_mm` | 499.5 | 482.6 |
| `svg_content` | missing | present |
| `svg_path_d` | present | — |
| `dxf_base64` | missing | present |

**Problem:** Elected wrong contour (ES-335 instead of jumbo_archtop). SVG path exists but DXF missing.

### Case B: Blueprint Edge-to-DXF → Clean

| Stage | Input | Output |
|-------|-------|--------|
| edge-to-dxf | 1600x1135 image | 595,000 LINE entities |
| clean/filter | 595K LINEs | **0 contours** |

**Problem:** Chain detection fails. Raw DXF exists but cleaned DXF is empty.

### Case C: Photo Mode (Archtop Photo)

| Field | Value |
|-------|-------|
| `ok` | true |
| `elapsed` | 77.9s |
| `svg_path_d` | 55,704 chars (3 paths) |
| `dxf_path` | present |
| `dxf_base64` | missing |

**Problem:** DXF file exists on server but not returned inline. Streaming download fails on Railway.

---

## 3. Root Causes

### A. Contract Mismatch

Frontend expects:
```javascript
if (data.svg_content && data.dxf_base64) → success
```

Backend returns:
```python
return {"ok": True, "svg_path_d": "...", "dxf_path": "/tmp/..."}
# Missing: svg_content, dxf_base64
```

**Result:** Frontend receives `ok: true` but has no usable artifacts.

### B. Topology Failure (Critical)

The `unified_dxf_cleaner.py` chain detection expects LINE endpoints to connect within 0.1mm.

But `edge_to_dxf.py` creates LINEs by iterating **row-major sorted pixels**, not contour paths:

```python
# edge_to_dxf.py lines 207-231
sorted_indices = np.lexsort((edge_points[:, 1], edge_points[:, 0]))  # Sort by (y, x)
for i in range(len(sorted_points) - 1):
    y1, x1 = sorted_points[i]
    y2, x2 = sorted_points[i + 1]
    if dist_sq <= threshold_sq:  # 3px adjacency
        msp.add_line(...)
```

**Result:** LINEs jump between rows. No continuous chains form. 595K LINEs → 0 closed contours.

### C. Export Inconsistency

| Path | SVG Export | DXF Export |
|------|------------|------------|
| Photo → AI | ✓ `_write_ai_svg()` | ✗ Not called |
| Photo → Standard | ✓ via potrace | ✓ via `write_dxf()` |
| Blueprint → Phase3 | ✓ `export_to_svg()` | ✓ `export_to_dxf()` |
| Blueprint → Edge | ✗ None | ✓ LINE entities |

**Result:** AI path generates SVG but skips DXF.

### D. Stateless Deployment Issue

```python
# clean_router.py
_output_file_registry[filename] = str(output_path)  # In-memory dict
```

Railway runs multiple workers. Registry doesn't persist across requests.

**Result:** `/clean/download/{filename}` returns 404.

**Mitigation (already applied):** Return `dxf_b64` inline for files <10MB.

---

## 4. Target System Contract

### Success Criteria

```
Success = ALL of:
  1. SVG content is present AND renderable (>100 chars)
  2. DXF content is present AND contains >0 entities
  3. Body dimensions are plausible for instrument spec
```

### Response Schema (Target)

```json
{
  "ok": true,
  "stage": "complete",
  "artifacts": {
    "svg": {
      "present": true,
      "content": "<svg>...</svg>",
      "path_count": 3
    },
    "dxf": {
      "present": true,
      "base64": "...",
      "entity_count": 1247
    }
  },
  "dimensions": {
    "width_mm": 431.8,
    "height_mm": 482.6,
    "spec_match": "jumbo_archtop",
    "confidence": 0.92
  },
  "warnings": []
}
```

### Failure Response

```json
{
  "ok": false,
  "stage": "contour_detection",
  "error": "No closed contours found after chain assembly",
  "artifacts": {
    "svg": { "present": false },
    "dxf": { "present": false }
  },
  "debug": {
    "line_count": 595000,
    "chain_count": 12847,
    "chains_above_100mm": 0
  }
}
```

---

## 5. Required Backend Changes

### 5.1 Photo Pipeline (`photo_vectorizer_v2.py`)

**Current:** AI path calls `_write_ai_svg()` but not DXF export.

**Required:**
- After SVG generation, call DXF export with same contour
- Validate both outputs before returning `ok: true`

**Invariant:**
```python
if export_svg and export_dxf:
    assert result.output_svg and Path(result.output_svg).exists()
    assert result.output_dxf and Path(result.output_dxf).exists()
```

### 5.2 Photo Router (`photo_vectorizer_router.py`)

**Current:** Returns `svg_path_d` and `dxf_path` (file paths).

**Required:**
- Read SVG file, return as `svg_content`
- Read DXF file, return as `dxf_base64`
- Fail if either missing

**Key change:**
```python
# Before returning success
has_svg = bool(svg_content) and len(svg_content) > 100
has_dxf = bool(dxf_base64) and len(dxf_base64) > 100
if not (has_svg and has_dxf):
    return {"ok": False, "stage": "artifact_validation", "error": "..."}
```

### 5.3 Edge-to-DXF (`edge_to_dxf.py`)

**Current:** Creates LINEs from row-major sorted pixels.

**Required:** Create LINEs by tracing actual contours.

**Option A (Recommended):** Use `cv2.findContours()` instead of pixel sorting:
```python
contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
for contour in contours:
    for i in range(len(contour) - 1):
        p1 = contour[i][0]
        p2 = contour[i + 1][0]
        msp.add_line(...)
```

**Option B:** Increase cleaner tolerance to 5mm and lower min_length to 10mm (band-aid).

### 5.4 Clean Router (`clean_router.py`)

**Current:** Returns `download_filename` for streaming.

**Required:** Always return `dxf_b64` inline. Already partially implemented.

**Validation:**
```python
if result.contours_found == 0:
    return {"success": False, "error": "No contours survived filtering", ...}
```

### 5.5 Contour Detection (`photo_vectorizer_v2.py`)

**Current:** Single threshold method fails on AI images.

**Required:** Multi-method fallback:
1. Otsu threshold
2. Adaptive threshold (if #1 fails)
3. Canny edge detection (if #2 fails)

---

## 6. Required Frontend Changes

### 6.1 Artifact Detection (`blueprint-reader.html`)

**Current:**
```javascript
svgContent = data.svg_content || buildSvgFromPath(data.svg_path_d);
hasDxf = !!(data.dxf_base64 || data.dxf_content || data.dxf_path);
```

**Required:** Consume normalized `artifacts` object:
```javascript
const svg = data.artifacts?.svg;
const dxf = data.artifacts?.dxf;

if (!svg?.present || !dxf?.present) {
    showError(`Missing: SVG=${svg?.present ? '✓' : '✗'}, DXF=${dxf?.present ? '✓' : '✗'}`);
    return;
}
```

### 6.2 Download Handler

**Current:** Tries streaming endpoint, falls back to base64.

**Required:** Use base64 only (streaming unreliable on Railway):
```javascript
function downloadDxf() {
    const dxf = extractedData.artifacts?.dxf;
    if (!dxf?.base64) {
        showError('DXF not available');
        return;
    }
    const blob = base64ToBlob(dxf.base64, 'application/dxf');
    downloadBlob(blob, getOutputName('.dxf'));
}
```

---

## 7. Deployment Constraints

### Railway Configuration

| Setting | Current | Required |
|---------|---------|----------|
| Plan | Pro (1GB RAM) | ✓ Sufficient |
| Gateway timeout | 60s default | **Set to 180s in dashboard** |
| Workers | 1 | ✓ |

**Dashboard path:** Railway → api service → Settings → Networking → Request Timeout

### Memory Profile (Measured)

| Stage | Memory |
|-------|--------|
| Baseline | 357 MB |
| After rembg init | 380 MB (+23 MB with caching) |
| Peak extraction | 520 MB |
| After GC | 392 MB |

**Conclusion:** 1GB is sufficient. rembg model caching is active.

### Dependencies

```
# Required in services/api/requirements.txt
opencv-python-headless>=4.8
ezdxf>=1.0
rembg>=2.0  # Optional but recommended
```

### Stateless File Issue

**Problem:** `/tmp` files don't persist across Railway workers.

**Solution:** Return artifacts as base64 in response body, not file paths.

---

## 8. Test Matrix

| Test Case | Mode | Spec | Expected |
|-----------|------|------|----------|
| Benedetto Front.jpg | Blueprint | jumbo_archtop | SVG + DXF, 432×483mm |
| AI guitar render | Photo | auto | SVG + DXF or fail loudly |
| Low-contrast AI | Photo | stratocaster | Fallback detection, fail if no contour |
| Cuatro PDF | Blueprint | None | SVG + DXF, closed contours |
| Sunburst photo | Photo | es335 | SVG + DXF, ~375×500mm |

### Success Criteria Per Test

```
✓ ok: true only if both artifacts present
✓ Dimensions within 20% of spec
✓ SVG renders in browser
✓ DXF opens in CAD software
✓ No silent failures (error message if failed)
```

---

## 9. File Reference

### Backend (services/api/app/)

| File | Role | Change Needed |
|------|------|---------------|
| `routers/photo_vectorizer_router.py` | Photo extraction endpoint | Return inline artifacts |
| `routers/blueprint/edge_to_dxf_router.py` | Raw edge extraction | None (upstream fix) |
| `routers/blueprint/clean_router.py` | DXF filtering | Validate contour count |
| `cam/unified_dxf_cleaner.py` | Chain detection | Increase tolerance OR fix upstream |

### Photo Vectorizer (services/photo-vectorizer/)

| File | Role | Change Needed |
|------|------|---------------|
| `photo_vectorizer_v2.py` | Main extraction logic | Add DXF to AI path, multi-threshold |
| `edge_to_dxf.py` | Pixel→LINE conversion | Use contour tracing, not row-sort |
| `body_dimension_reference.json` | Spec dimensions | ✓ benedetto_17 added |

### Blueprint Import (services/blueprint-import/)

| File | Role | Change Needed |
|------|------|---------------|
| `vectorizer_phase3.py` | Blueprint vectorization | Verify DXF export |
| `dxf_compat.py` | DXF version handling | None |

### Frontend (hostinger/)

| File | Role | Change Needed |
|------|------|---------------|
| `blueprint-reader.html` | Upload + preview UI | Consume normalized artifacts |

---

## 10. Diagnostic Commands

### Check Railway Logs
```bash
railway logs --environment production --limit 200 | grep -E "VECTORIZER_|SVG_|BODY_"
```

### Verify Entity Types in DXF
```python
import ezdxf
doc = ezdxf.readfile("path/to/file.dxf")
msp = doc.modelspace()
types = {}
for e in msp:
    t = e.dxftype()
    types[t] = types.get(t, 0) + 1
print(types)  # Expected: {'LINE': 595000} or {'LWPOLYLINE': 12}
```

### Test Chain Detection Locally
```bash
cd services/api
python -c "
from app.cam.unified_dxf_cleaner import DXFCleaner
cleaner = DXFCleaner(min_contour_length_mm=50, endpoint_tolerance=1.0)
result = cleaner.clean_file('input.dxf', 'output.dxf')
print(f'Chains: {result.chains_found}, Contours: {result.contours_found}')
"
```

---

## 11. Definition of Done

- [x] All 5 test cases pass
- [x] `ok: true` only when both SVG and DXF present
- [x] Failures include `stage` and `error` fields
- [x] No streaming downloads (base64 only)
- [x] Railway timeout set to 180s
- [x] Frontend shows error when artifacts missing

---

## 12. Blueprint Pipeline Refactor Completion

**Date:** 2025-04-10  
**Status:** COMPLETE

### Overview

The blueprint processing pipeline (`/api/blueprint/vectorize`) has been fully refactored into a unified, production-ready architecture. This refactor consolidates extraction, cleanup, contour selection, artifact generation, and job orchestration into a single coherent system.

The pipeline now operates as a **deterministic, observable decision system** rather than a threshold-based filter chain.

### Key Architectural Changes

| Component | Change |
|-----------|--------|
| `BlueprintOrchestrator` | Single coordination layer for all blueprint processing |
| `blueprint_extract.py` | Extraction service (image load, edge detection, raw DXF) |
| `blueprint_clean.py` | Cleanup service (contour scoring, filtering, SVG generation) |
| `blueprint_orchestrator.py` | Orchestration (composes services, validates artifacts) |
| `blueprint_limits.py` | Input guardrails (upload size, DPI caps, auto-downscale) |
| `StageTimer` | Per-stage timing diagnostics |
| `/api/blueprint/vectorize` | Single-entry endpoint (replaces multi-stage flow) |

### Contour Selection Refactor (Core Change)

Contour selection has been fundamentally redesigned.

#### Before

Binary threshold-based filtering:
- Length thresholds
- Closure checks
- Ownership threshold (0.60 hard gate)

**Failure mode:** No contour passed thresholds → hard fail.

#### After

Unified scoring-based selection:

| Signal | Weight | Description |
|--------|--------|-------------|
| Area ratio | 25% | Contour area vs image area |
| Closure quality | 20% | How well contour closes |
| Aspect ratio | 15% | Guitar-like proportions |
| Solidity | 15% | Fill ratio of convex hull |
| Continuity | 15% | Gap-free perimeter |
| Ownership | 10% | Foreground pixel coverage |

**Decision model:**
- All candidates are scored and ranked
- Best contour is selected deterministically
- Fallback to best available if all scores are low
- Confidence score (0.0–1.0) is emitted with result

#### Ownership Handling

| Before | After |
|--------|-------|
| Hard gate at 0.60 | Weighted signal (10%) |
| Binary pass/fail | Contributes to composite score |
| Standalone rejection | No standalone rejection |

### Decision Model

The pipeline now follows a three-tier outcome model:

| Outcome | Condition | Response |
|---------|-----------|----------|
| **Fail** | No usable contour found | `ok: false`, stage indicates where |
| **Warn** | Usable contour, low confidence | `ok: true`, warnings included |
| **Pass** | Strong contour | `ok: true`, no warnings |

Artifact validation (SVG/DXF both present and valid) still overrides confidence.

### Observability

Each run now provides:

| Field | Description |
|-------|-------------|
| `contour_confidence` | 0.0–1.0 confidence in selected contour |
| `warnings` | Downscale, DPI cap, low confidence notices |
| `stage_timings` | Per-stage milliseconds (debug mode) |
| `debug` | Full diagnostic payload (when enabled) |

### Input Guardrails

| Guardrail | Limit | Behavior |
|-----------|-------|----------|
| Upload size | 25 MB | Reject with 413 |
| Raster dimensions | 8192×8192 px | Auto-downscale with warning |
| PDF DPI | 300 | Cap and warn |

---

## 13. Scope Boundary: Blueprint vs Photo

> **IMPORTANT:** This refactor applies only to the blueprint pipeline.

### What Changed (Blueprint)

| Item | Status |
|------|--------|
| `/api/blueprint/vectorize` | ✅ New unified endpoint |
| `BlueprintOrchestrator` | ✅ Central coordination |
| Unified contour scoring | ✅ Scoring-based selection |
| Ownership as weighted signal | ✅ 10% weight, no hard gate |
| Low-confidence with warnings | ✅ Returns result + warning |
| Stage timing diagnostics | ✅ `StageTimer` utility |

### What Did NOT Change (Photo)

| Item | Status |
|------|--------|
| `/api/vectorizer/extract` | ❌ Unchanged |
| `photo_vectorizer_v2.py` | ❌ Unchanged |
| Ownership threshold (0.60) | ❌ Still hard gate |
| Hard fail on low ownership | ❌ Still fails |
| Contour election logic | ❌ Unchanged |

### Behavioral Difference

| Scenario | Blueprint | Photo |
|----------|-----------|-------|
| Ownership = 0.55 | Returns with warning | Hard fails |
| Noisy input | Best-effort + confidence | May reject entirely |
| AI-generated image | Likely succeeds | May fail ownership gate |

### Implication for Testing

- **Do not** test photo mode against blueprint expectations
- **Do not** assume photo failures are regressions from this refactor
- Photo pipeline needs separate follow-up refactor for parity

---

## 14. Current Production Architecture

### Blueprint Pipeline (Refactored)

```
POST /api/blueprint/vectorize
    │
    ├─► BlueprintOrchestrator.process_file()
    │       │
    │       ├─► extract_blueprint_to_dxf() ─► raw DXF
    │       │
    │       ├─► clean_blueprint_dxf() ─► scored contours
    │       │       │
    │       │       └─► UnifiedContourScorer ─► confidence
    │       │
    │       ├─► validate_artifacts() ─► SVG + DXF present?
    │       │
    │       └─► BlueprintResult ─► canonical response
    │
    └─► Response: ok, stage, artifacts, dimensions, warnings
```

### Photo Pipeline (Unchanged)

```
POST /api/vectorizer/extract
    │
    ├─► PhotoVectorizerV2.extract()
    │       │
    │       ├─► body_isolation() ─► foreground mask
    │       │
    │       ├─► contour_stage() ─► candidates
    │       │       │
    │       │       └─► ownership_threshold = 0.60 ─► HARD GATE
    │       │
    │       ├─► export_blocked? ─► fail if ownership < 0.60
    │       │
    │       └─► VectorizerResult
    │
    └─► Response: ok, artifacts, dimensions, warnings
```

---

## 15. Open Follow-ups

| Item | Priority | Notes |
|------|----------|-------|
| Photo pipeline refactor | HIGH | Bring parity with blueprint scoring model |
| Frontend confidence display | MEDIUM | Surface `contour_confidence` to users |
| Scoring weight tuning | LOW | Adjust weights based on production data |
| Warning UX | MEDIUM | Show downscale/low-confidence warnings clearly |

---

## 16. Summary

The blueprint vectorizer has been transformed from a fragile, threshold-based filter chain into a robust, scoring-based decision system. The key improvements are:

1. **No more silent partial failures** — artifacts are validated before success
2. **No more binary threshold rejections** — low-confidence results return with warnings
3. **Observable decision process** — confidence scores and stage timings available
4. **Unified architecture** — single orchestrator, single endpoint, single contract

The photo pipeline remains unchanged and requires separate follow-up work.

---

## 17. Photo Pipeline Refactor — COMPLETE

**Date:** 2026-04-11  
**Status:** COMPLETE (structural refactor)  
**Next:** Geometry deduplication

### Overview

The photo pipeline (`/api/vectorizer/extract`) has been refactored to match the blueprint architecture pattern. Business logic moved from router to orchestrator. Confidence is now sourced from real scorer output (not fabricated).

### What Changed

| Component | Before | After |
|-----------|--------|-------|
| `photo_vectorizer_router.py` | 528 lines, owns business logic | 370 lines, thin HTTP wrapper |
| `photo_orchestrator.py` | Did not exist | 310 lines, owns orchestration |
| Confidence value | Fabricated (0.9 or 0.0) | Real scorer: `result.contour_stage.ownership_score` |
| Artifact encoding | In router | In orchestrator |
| Validation gates | Scattered | Centralized in orchestrator |

### PhotoOrchestrator Responsibilities

```
PhotoOrchestrator.process_image()
    │
    ├─► Validate input (empty check)
    │
    ├─► Import PhotoVectorizerV2 (graceful failure)
    │
    ├─► Create temp directory (orchestrator owns)
    │
    ├─► Call vectorizer.extract()
    │
    ├─► Source confidence from result.contour_stage.ownership_score
    │
    ├─► Encode SVG artifact (read file, validate content)
    │
    ├─► Encode DXF artifact (read file, base64, count entities)
    │
    ├─► Validate artifacts (SVG_MIN_CHARS, DXF_MIN_BYTES)
    │
    └─► Return PhotoResult (canonical schema)
```

### Router Now Thin Wrapper

```python
# photo_vectorizer_router.py — simplified flow
result = _orchestrator.process_image(
    image_bytes=img_bytes,
    filename=filename,
    spec_name=req.spec_name,
    ...
)

# Map to response with legacy fields
return VectorizeResponse(
    ok=result.ok,
    stage=result.stage,
    artifacts=artifacts,       # Canonical
    dimensions=dimensions,     # Canonical
    svg_path_d=svg_path_d,     # Legacy
    body_width_mm=...,         # Legacy
    ...
)
```

### Confidence Fix (Critical)

**Before:** Confidence was hardcoded based on export_blocked flag:
```python
confidence = 0.0 if export_blocked else 0.9  # FABRICATED
```

**After:** Confidence sourced from real scorer:
```python
confidence = 0.0
contour_stage = getattr(result, "contour_stage", None)
if contour_stage is not None:
    ownership_score = getattr(contour_stage, "ownership_score", None)
    if ownership_score is not None:
        confidence = float(ownership_score)
```

### Test Results

```
=== RESULT ===
ok: True
stage: complete
dimensions: 222x329mm
confidence: 0.710  ← Real scorer output (was 0.9 fabricated)
artifacts.svg.present: True
```

### Files Modified

| File | Change |
|------|--------|
| `app/services/photo_orchestrator.py` | NEW — 310 lines |
| `app/routers/photo_vectorizer_router.py` | Refactored — 528→370 lines |

### Behavioral Note

The photo pipeline ownership threshold (0.60 hard gate) was NOT changed. This refactor is structural only:
- Router is now thin
- Orchestrator owns logic
- Confidence is real signal

Behavioral changes to threshold/decision model are a separate follow-up.

---

## 18. Frontend Canonical Schema Integration — COMPLETE

**Date:** 2026-04-11  
**Status:** COMPLETE

### Problem

Frontend photo mode validated against legacy fields:
```javascript
const dxfAvailable = !!(data.dxf_base64 || data.dxf_content || data.dxf_path);
```

But backend now returns canonical schema:
```json
{
  "artifacts": {
    "dxf": { "present": true, "base64": "..." }
  }
}
```

Result: `requireBothArtifacts()` threw "DXF must be generated" even though DXF was present.

### Solution

Frontend updated to check canonical schema first, with legacy fallback.

### Changes to `tools/blueprint-reader.html`

#### 1. `getArtifacts()` Function (lines 643-653)

```javascript
if (mode === 'photo') {
  // Canonical first, then legacy fallback
  const widthMm = data?.dimensions?.width_mm || data.body_width_mm || 500;
  const heightMm = data?.dimensions?.height_mm || data.body_height_mm || 500;
  
  svgContent = data?.artifacts?.svg?.content || 
               data.svg_content || 
               buildSvgFromPath(data.svg_path_d, widthMm, heightMm);
  
  hasDxf = !!(
    (data?.artifacts?.dxf?.present && 
     (data?.artifacts?.dxf?.base64 || data?.artifacts?.dxf?.entity_count > 0)) ||
    data.dxf_base64 || data.dxf_content || data.dxf_path
  );
}
```

#### 2. Photo Mode Validation (lines 1186-1213)

```javascript
// Canonical success check
const canonicalSuccess = !!(
  data?.ok === true &&
  data?.artifacts?.svg?.present &&
  data?.artifacts?.dxf?.present
);

// Contour count is informational when canonical artifacts present
if (Number(contourCount) <= 0 && !canonicalSuccess) {
  throw new Error('No contours detected...');
}

// Skip requireBothArtifacts when canonical artifacts present
if (!canonicalSuccess) {
  requireBothArtifacts(artifacts, artifacts.hasDxf, 'Extraction');
}
```

#### 3. Download Handler (line 1371)

```javascript
// Canonical first, then legacy
const dxfBase64 = extractedData?.artifacts?.dxf?.base64 || extractedData.dxf_base64;
```

### Success Rule

```javascript
if (data?.ok === true &&
    data?.artifacts?.svg?.present &&
    data?.artifacts?.dxf?.present) {
  // Treat as success — skip legacy validation paths
}
```

---

## 19. Remaining Issue: Geometry Duplication

**Date:** 2026-04-11  
**Status:** OPEN  
**Priority:** HIGH  
**Type:** Geometry integrity failure (not runtime failure)

### Problem

DXF output contains duplicate/overlapping paths:
- Identical contours at same location
- Overlapping LINE segments
- Coincident nodes

This causes:
- CAD software slowdown (processing redundant geometry)
- Fabrication issues (double-cut, over-etching)
- Visual artifacts in preview

### Evidence

From retest artifact analysis:
- Multiple paths overlap at body outline
- Near-identical contours (tolerance ~0.01-0.05mm)
- Both construction + final geometry exported

### Required Fix

Add geometry deduplication pass before DXF export:

```python
def deduplicate_geometry(chains: List[Chain], tolerance_mm: float = 0.05) -> List[Chain]:
    """
    Remove duplicate/overlapping paths from chain list.
    
    Operations:
    1. Merge identical contours (within tolerance)
    2. Remove overlapping LINE segments
    3. Collapse coincident nodes
    4. Enforce winding + closed path validation
    """
    ...
```

### Location Options

| Option | File | Pros | Cons |
|--------|------|------|------|
| A | `unified_dxf_cleaner.py` | Already has chain logic | Adds complexity to cleaner |
| B | New `geometry_dedup.py` | Clean separation | New file to maintain |
| C | `write_selected_chains()` | Single export point | Mixes concerns |

**Recommendation:** Option A — add `deduplicate_chains()` method to `DXFCleaner` class.

### Algorithm Outline

```python
def deduplicate_chains(self, chains: List[Chain], tolerance: float = 0.05) -> List[Chain]:
    """
    1. Build spatial index (KD-tree or grid)
    2. For each chain:
       a. Hash by centroid + bounding box
       b. If hash collision, compare point-by-point within tolerance
       c. If duplicate, mark for removal
    3. Segment overlap detection:
       a. For each LINE segment, check if another segment overlaps
       b. If overlap > 80%, keep only one
    4. Node collapse:
       a. If two nodes within tolerance, merge to single point
    5. Return deduplicated chains
    """
```

### Validation

After deduplication:
- No two chains should have same centroid within tolerance
- No LINE segment should overlap another by >80%
- All exported contours should be closed (start == end within tolerance)

### Test Case

Use existing retest artifact. Before/after should show:
- Reduced entity count (duplicates removed)
- Same visual output (no missing geometry)
- DXF opens without slowdown in Fusion 360

---

## 20. Canonical Response Schema (Production Contract)

### Photo Vectorizer Response

```json
{
  "ok": true,
  "stage": "complete",
  "artifacts": {
    "svg": {
      "present": true,
      "content": "<svg>...</svg>",
      "path_count": 3
    },
    "dxf": {
      "present": true,
      "base64": "...",
      "entity_count": 1247,
      "closed_contours": 3
    }
  },
  "dimensions": {
    "width_mm": 350.5,
    "height_mm": 482.6,
    "width_in": 13.8,
    "height_in": 19.0,
    "spec_match": "jumbo_archtop",
    "confidence": 0.715
  },
  "svg_path_d": "M...",           // Legacy
  "body_width_mm": 350.5,         // Legacy
  "body_height_mm": 482.6,        // Legacy
  "scale_source": "spec_match",
  "bg_method": "rembg",
  "perspective_corrected": false,
  "warnings": [],
  "processing_ms": 4523.1,
  "export_blocked": false,
  "export_block_reason": "",
  "error": "",
  "debug": null
}
```

### Blueprint Vectorizer Response

```json
{
  "ok": true,
  "stage": "complete",
  "artifacts": {
    "svg": {
      "present": true,
      "content": "<svg>...</svg>",
      "path_count": 6
    },
    "dxf": {
      "present": true,
      "base64": "...",
      "entity_count": 847,
      "closed_contours": 6
    }
  },
  "dimensions": {
    "width_mm": 289.8,
    "height_mm": 375.0
  },
  "metrics": {
    "original_entities": 595000,
    "chains_found": 12847,
    "contours_found": 6,
    "best_confidence": 0.535
  },
  "warnings": [
    "PDF render DPI capped from 300 to 150 for web processing.",
    "Low confidence contour selection (0.54). Review output before fabrication."
  ],
  "error": ""
}
```

---

## 21. File Reference (Updated)

### Backend — Services/API

| File | Role | Status |
|------|------|--------|
| `app/services/photo_orchestrator.py` | Photo orchestration | NEW |
| `app/services/blueprint_orchestrator.py` | Blueprint orchestration | UPDATED |
| `app/routers/photo_vectorizer_router.py` | Photo HTTP wrapper | REFACTORED |
| `app/routers/blueprint/vectorize_router.py` | Blueprint HTTP wrapper | STABLE |
| `app/services/blueprint_extract.py` | Edge extraction | STABLE |
| `app/services/blueprint_clean.py` | Contour scoring/cleanup | STABLE |
| `app/services/contour_scoring.py` | Unified scorer | STABLE |
| `app/cam/unified_dxf_cleaner.py` | Chain assembly | NEEDS: dedup |

### Photo Vectorizer — Services/photo-vectorizer

| File | Role | Status |
|------|------|--------|
| `photo_vectorizer_v2.py` | Main extraction | STABLE |
| `contour_plausibility.py` | Ownership scoring | STABLE |
| `edge_to_dxf.py` | Contour→DXF | STABLE |

### Frontend

| File | Role | Status |
|------|------|--------|
| `tools/blueprint-reader.html` | Upload/preview UI | UPDATED |

---

## 22. Definition of Done (Updated)

### Completed ✓

- [x] Blueprint orchestrator refactor
- [x] Photo orchestrator refactor
- [x] Confidence sourced from real scorer
- [x] Frontend canonical schema integration
- [x] Legacy field fallback in frontend
- [x] `ok: true` only when both artifacts present
- [x] Canonical success bypasses legacy validation

### Remaining

- [ ] Geometry deduplication (`unified_dxf_cleaner.py`)
- [ ] Validate no duplicate paths in output
- [ ] Photo threshold/decision model alignment (optional)
- [ ] Frontend confidence display (optional)

---

## 23. Next Developer Actions

### Immediate: Geometry Deduplication

1. Add `deduplicate_chains()` to `unified_dxf_cleaner.py`
2. Call before `write_selected_chains()`
3. Test with retest artifact — verify reduced entity count
4. Verify DXF opens cleanly in Fusion 360

### Acceptance Test

```bash
# Before dedup
python -c "import ezdxf; doc=ezdxf.readfile('before.dxf'); print(len(list(doc.modelspace())))"
# Output: 1247

# After dedup  
python -c "import ezdxf; doc=ezdxf.readfile('after.dxf'); print(len(list(doc.modelspace())))"
# Output: 623  # ~50% reduction expected
```

### Visual Validation

- Open DXF in Fusion 360
- No duplicate outlines visible
- Single closed contour for body
- No performance lag on import

---

## 24. Recommendation Layer Architecture — COMPLETE

**Date:** 2026-04-12  
**Status:** PRODUCTION

### Overview

The vectorizer pipelines now include a unified **recommendation layer** that separates:
- **Scoring** (which contour is best?) — `contour_scoring.py`
- **Acceptance** (is it good enough?) — `contour_recommendation.py`

This enables mode-specific thresholds without duplicating scoring logic.

### New File: `contour_recommendation.py`

Location: `services/api/app/services/contour_recommendation.py` (~411 lines)

```python
class RecommendationAction(Enum):
    ACCEPT = "accept"   # High confidence, artifacts valid
    REVIEW = "review"   # Moderate confidence, manual review suggested
    REJECT = "reject"   # Low confidence or missing artifacts

class ProcessingMode(Enum):
    BLUEPRINT = "blueprint"  # More permissive (ownership = weighted signal)
    PHOTO = "photo"          # Stricter (ownership = hard gate)

@dataclass
class SelectionResult:
    candidate_count: int
    selected_index: Optional[int]
    selection_score: float      # Best candidate score
    runner_up_score: float      # Second-best score
    winner_margin: float        # Separation from runner-up
    reasons: list[str]

@dataclass
class Recommendation:
    action: RecommendationAction
    confidence: float           # 0.0-1.0
    reasons: list[str]          # Human-readable explanation
```

### Threshold Configuration

| Mode | Accept Score | Accept Margin | Accept Ownership | Review Score |
|------|--------------|---------------|------------------|--------------|
| Blueprint | 0.70 | 0.12 | N/A | 0.45 |
| Photo | 0.75 | 0.15 | 0.75 | 0.55 |

### Hard-Fail Detection

The recommendation layer detects structural failures that override score:

| Hard-Fail | Description |
|-----------|-------------|
| `no_artifacts` | No valid SVG or DXF produced |
| `page_span` | Contour spans full page (annotation, not body) |
| `page_border` | Best candidate is the page border |
| `extreme_aspect` | Aspect ratio wildly wrong for instrument |
| `extreme_fragmentation` | Too many disconnected pieces |
| `multi_path_ambiguity` | Multiple peer contours, can't choose |
| `spec_forced_rescue` | Spec override used with low quality |
| `mode_mismatch` | AI/photo classifier disagrees with source_type |

### Integration Points

```
BlueprintOrchestrator
    └─► clean_blueprint_dxf()
        └─► score_contours() → SelectionResult
    └─► recommend() → Recommendation
    └─► ok = (recommendation.action == ACCEPT)

PhotoOrchestrator
    └─► PhotoVectorizerV2.extract()
        └─► contour_stage.ownership_score
    └─► recommend() → Recommendation
    └─► ok = (recommendation.action == ACCEPT)
```

### Data Flow

```
Contours → score_contours() → SelectionResult
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │   RecommendationInput        │
                     │   - selection: SelectionResult
                     │   - mode: BLUEPRINT | PHOTO  
                     │   - svg_valid: bool          
                     │   - dxf_valid: bool          
                     │   - ownership_score: float   
                     │   - warnings: list[str]      
                     └──────────────────────────────┘
                                    │
                                    ▼
                            recommend()
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │   Recommendation             │
                     │   - action: ACCEPT|REVIEW|REJECT
                     │   - confidence: 0.0-1.0     
                     │   - reasons: list[str]      
                     └──────────────────────────────┘
```

---

## 25. Complete File Reference (2026-04-12)

### API Services Layer (`services/api/app/services/`)

| File | Lines | Role | Dependencies |
|------|-------|------|--------------|
| `photo_orchestrator.py` | 413 | Photo pipeline coordination | `photo_vectorizer_v2`, `contour_recommendation` |
| `blueprint_orchestrator.py` | 413 | Blueprint pipeline coordination | `blueprint_extract`, `blueprint_clean`, `contour_recommendation` |
| `blueprint_extract.py` | 356 | Edge extraction service | `edge_to_dxf`, `fitz` (PDF) |
| `blueprint_clean.py` | 418 | Cleanup + contour scoring | `unified_dxf_cleaner`, `contour_scoring` |
| `blueprint_limits.py` | ~100 | Input guardrails (size, DPI) | — |
| `contour_scoring.py` | 775 | Multi-signal contour ranking | `numpy`, `cv2` |
| `contour_recommendation.py` | 411 | Accept/review/reject decisions | `contour_scoring` |

### API Routers (`services/api/app/routers/`)

| File | Lines | Endpoint | Handler |
|------|-------|----------|---------|
| `photo_vectorizer_router.py` | 371 | `POST /api/vectorizer/extract` | `PhotoOrchestrator.process_image()` |
| `blueprint/vectorize_router.py` | 174 | `POST /api/blueprint/vectorize` | `BlueprintOrchestrator.process_file()` |
| `blueprint_async_router.py` | 237 | `POST /api/blueprint/vectorize/async` | Background job wrapper |

### CAM Utilities (`services/api/app/cam/`)

| File | Lines | Role |
|------|-------|------|
| `unified_dxf_cleaner.py` | ~600 | Chain detection, DXF read/write |
| `dxf_compat.py` | ~200 | DXF version compatibility |

### Photo Vectorizer Core (`services/photo-vectorizer/`)

| File | Lines | Role |
|------|-------|------|
| `photo_vectorizer_v2.py` | 5,366 | Main 12-stage pipeline |
| `contour_stage.py` | 588 | Stage 8 extraction |
| `body_isolation_stage.py` | 593 | Body region isolation |
| `geometry_coach_v2.py` | 878 | Agentic retry loop |
| `geometry_coach.py` | 259 | V1 retry logic |
| `contour_plausibility.py` | 379 | Ownership scoring |
| `contour_election.py` | 61 | Body election gate |
| `cognitive_extraction_engine.py` | 1,503 | Agentic parallel extraction |
| `cognitive_extractor.py` | 1,470 | Cognitive wrapper |
| `edge_to_dxf.py` | 733 | High-fidelity DXF export |
| `blueprint_view_segmenter.py` | 830 | Multi-view detection |
| `multi_view_reconstructor.py` | 928 | 3D reconstruction |
| `ai_render_extractor.py` | 462 | AI image features |
| `light_line_body_extractor.py` | 578 | Light-line extraction |
| `grid_classify.py` | 420 | Grid zone classification |
| `body_model.py` | 85 | Instrument body constraints |
| `landmark_extractor.py` | 340 | Landmark detection |
| `body_isolation_result.py` | 270 | Typed result dataclass |
| `geometry_authority.py` | 200 | Family priors, dimension fit |
| `body_dimension_reference.json` | — | 16 guitar specs |

### Blueprint Import (`services/blueprint-import/`)

| File | Lines | Role |
|------|-------|------|
| `vectorizer_phase3.py` | 4,148 | Phase 3.6 blueprint extraction |
| `dxf_compat.py` | ~200 | DXF version handling |

### Frontend (`hostinger/`, `tools/`)

| File | Role |
|------|------|
| `hostinger/blueprint-reader.html` | Production upload UI |
| `tools/blueprint-reader.html` | Development copy |

### Async Job System (`services/api/app/jobs/`)

| File | Role |
|------|------|
| `__init__.py` | Package marker |
| `models.py` | Job status dataclasses |
| `store.py` | In-memory + Redis job store |

### Documentation (`docs/`)

| File | Purpose |
|------|---------|
| `PHOTO_VECTORIZER_ARCHITECTURE.md` | Executive summary of photo-vectorizer |
| `BLUEPRINT_VECTORIZER_ARCHITECTURE.md` | Blueprint pipeline architecture |
| `handoffs/VECTORIZER_PIPELINE_HANDOFF.md` | This file |

---

## 26. Onboarding Guide for New Engineers

### Prerequisites

```bash
# Python 3.11+
python --version

# Required packages
pip install opencv-python-headless numpy ezdxf rembg PyMuPDF

# Optional (for SAM background removal)
pip install segment-anything torch
```

### Local Development Setup

```bash
# Clone repo
git clone https://github.com/HanzoRazer/luthiers-toolbox.git
cd luthiers-toolbox

# Set up API
cd services/api
pip install -r requirements.txt

# Add photo-vectorizer to path
export PYTHONPATH="$PWD/../photo-vectorizer:$PYTHONPATH"

# Run API
uvicorn app.main:app --reload --port 8000
```

### Key Concepts to Understand

#### 1. Dual Pipeline Architecture

```
Photo Pipeline (12-stage):
  - Input: JPEG/PNG photo or AI render
  - Hard gate: ownership_score >= 0.60
  - Output: SVG + DXF via PhotoOrchestrator

Blueprint Pipeline (4-stage):
  - Input: PDF or image of technical drawing
  - No hard gate: ownership is weighted signal
  - Output: SVG + DXF via BlueprintOrchestrator
```

#### 2. Orchestrator Pattern

Both pipelines use orchestrators that:
- Own temp directory lifecycle
- Delegate to specialized services
- Aggregate warnings
- Source confidence from real scorer
- Validate artifacts before success
- Return canonical response schema

#### 3. Recommendation Layer

```python
# Scoring (deterministic ranking)
result = score_contours(contours, width, height)

# Acceptance (mode-specific thresholds)
recommendation = recommend(RecommendationInput(
    selection=result,
    mode=ProcessingMode.PHOTO,
    svg_valid=True,
    dxf_valid=True,
))

# ok = True only when action == ACCEPT
ok = recommendation.action == RecommendationAction.ACCEPT
```

#### 4. Canonical Response Schema

Both pipelines return the same structure:

```json
{
  "ok": true,
  "stage": "complete",
  "artifacts": {
    "svg": { "present": true, "content": "...", "path_count": 3 },
    "dxf": { "present": true, "base64": "...", "entity_count": 847 }
  },
  "dimensions": { "width_mm": 350.5, "height_mm": 482.6 },
  "selection": { "candidate_count": 12, "selection_score": 0.78 },
  "recommendation": { "action": "accept", "confidence": 0.82 },
  "warnings": []
}
```

### Common Tasks

#### Add a new instrument spec

Edit `services/photo-vectorizer/body_dimension_reference.json`:

```json
{
  "my_new_guitar": {
    "body_width_mm": 350,
    "body_height_mm": 450,
    "lower_bout_mm": 350,
    "upper_bout_mm": 280,
    "waist_mm": 230
  }
}
```

#### Adjust contour scoring weights

Edit `services/api/app/services/contour_scoring.py`:

```python
# Weight configuration (must sum to 1.0)
WEIGHT_AREA = 0.25
WEIGHT_CLOSURE = 0.20
WEIGHT_ASPECT = 0.15
WEIGHT_SOLIDITY = 0.15
WEIGHT_CONTINUITY = 0.15
WEIGHT_OWNERSHIP = 0.10
```

#### Adjust recommendation thresholds

Edit `services/api/app/services/contour_recommendation.py`:

```python
# Blueprint mode (more permissive)
BLUEPRINT_ACCEPT_SCORE = 0.70
BLUEPRINT_ACCEPT_MARGIN = 0.12
BLUEPRINT_REVIEW_SCORE = 0.45

# Photo mode (stricter)
PHOTO_ACCEPT_SCORE = 0.75
PHOTO_ACCEPT_MARGIN = 0.15
PHOTO_ACCEPT_OWNERSHIP = 0.75
```

### Testing

```bash
# Run all vectorizer tests
cd services/photo-vectorizer
pytest test_*.py -v

# Run API tests
cd services/api
pytest tests/test_vectorizer*.py -v

# Test specific endpoint
curl -X POST http://localhost:8000/api/vectorizer/extract \
  -H "Content-Type: application/json" \
  -d '{"image_b64": "...", "spec_name": "stratocaster"}'
```

### Debugging

#### Enable debug mode

```bash
export VECTORIZER_DEBUG=1
```

Then add `"debug": true` to request payload.

#### Check Railway logs

```bash
railway logs --environment production --limit 200 | grep "VECTORIZER\|BLUEPRINT\|PHOTO"
```

#### Inspect DXF entities

```python
import ezdxf
doc = ezdxf.readfile("output.dxf")
msp = doc.modelspace()
types = {}
for e in msp:
    t = e.dxftype()
    types[t] = types.get(t, 0) + 1
print(types)  # Expected: {'LINE': N}
```

---

## 27. Architecture Decision Records

### ADR-001: Separate Scoring from Acceptance

**Context:** Original pipeline used hard thresholds scattered across code.

**Decision:** Create `contour_scoring.py` for deterministic ranking, `contour_recommendation.py` for mode-specific acceptance.

**Consequences:** 
- Scoring is testable in isolation
- Thresholds configurable per mode
- Clear separation of concerns

### ADR-002: Orchestrator Pattern

**Context:** Business logic was scattered across routers, making testing difficult.

**Decision:** Create `PhotoOrchestrator` and `BlueprintOrchestrator` that own:
- Temp directory lifecycle
- Warning aggregation
- Artifact validation
- Response construction

**Consequences:**
- Routers are thin HTTP wrappers
- Orchestrators are unit-testable
- Single source of truth per pipeline

### ADR-003: Canonical Response Schema

**Context:** Frontend checked multiple legacy field combinations.

**Decision:** Define canonical `artifacts` and `dimensions` schema. Keep legacy fields for backward compatibility.

**Consequences:**
- Frontend can migrate incrementally
- New code uses canonical fields
- Clear contract documentation

### ADR-004: Blueprint vs Photo Scope Boundary

**Context:** Blueprint refactor risked breaking photo pipeline.

**Decision:** Explicitly scope ownership behavior:
- Blueprint: ownership is 10% weighted signal
- Photo: ownership is hard gate at 0.60

**Consequences:**
- No behavioral changes to photo pipeline
- Blueprint tolerates low-ownership better
- Clear documentation prevents confusion

---

## 28. Glossary

| Term | Definition |
|------|------------|
| **Ownership score** | Ratio of contour area to foreground mask area (0.0-1.0) |
| **Selection score** | Composite score from all signals (area, closure, aspect, etc.) |
| **Winner margin** | Difference between best and second-best candidate scores |
| **Hard gate** | Binary pass/fail threshold (photo: 0.60 ownership) |
| **Weighted signal** | Contributes to composite score (blueprint: 10% ownership) |
| **Orchestrator** | Business logic coordinator that delegates to services |
| **Recommendation** | Accept/review/reject decision based on mode and signals |
| **Stage** | Processing phase (upload, edge_extraction, cleanup, validation, complete) |
| **Canonical schema** | Normalized response structure (`artifacts`, `dimensions`) |
| **Legacy fields** | Old response fields kept for backward compatibility |

---

## 29. Change Log

| Date | Section | Change |
|------|---------|--------|
| 2026-04-09 | 1-11 | Initial handoff document |
| 2026-04-10 | 12-16 | Blueprint refactor completion |
| 2026-04-11 | 17-22 | Photo refactor + frontend integration |
| 2026-04-12 | 24-28 | Recommendation layer + complete file reference + onboarding guide |
