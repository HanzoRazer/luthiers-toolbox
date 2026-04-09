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

- [ ] All 5 test cases pass
- [ ] `ok: true` only when both SVG and DXF present
- [ ] Failures include `stage` and `error` fields
- [ ] No streaming downloads (base64 only)
- [ ] Railway timeout set to 180s
- [ ] Frontend shows error when artifacts missing
