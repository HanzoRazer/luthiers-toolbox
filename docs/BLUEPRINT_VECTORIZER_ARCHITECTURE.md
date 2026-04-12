# Blueprint Vectorizer Architecture

> **Developer Reference Document**  
> **Last Updated:** 2026-04-09  
> **Scope:** Frontend-Backend schema relationship for the Blueprint Reader tool

---

## 1. System Overview

The Blueprint Reader (`blueprint-reader.html`) is a browser-based tool that connects to two distinct backend vectorization pipelines deployed on Railway:

| Mode | Backend Module | API Endpoint | Use Case |
|------|----------------|--------------|----------|
| **Blueprint** | `vectorizer_phase3.py` | `POST /api/blueprint/edge-to-dxf/convert` | PDF/image blueprints with edge detection |
| **Photo** | `photo_vectorizer_v2.py` | `POST /api/vectorizer/extract` | Photographs and AI-generated images |

Both backends are deployed as part of the same FastAPI application at:
```
https://luthiers-toolbox-production.up.railway.app
```

---

## 2. File Tree

```
luthiers-toolbox/
├── hostinger/
│   └── blueprint-reader.html          # [FRONTEND] Production UI (deployed to Hostinger)
│
├── tools/
│   └── blueprint-reader.html          # [FRONTEND] Development copy (synced with hostinger/)
│
├── services/
│   ├── api/                            # [BACKEND] FastAPI application
│   │   ├── app/
│   │   │   ├── main.py                 # Application entry point, router registration
│   │   │   │
│   │   │   ├── router_registry/        # Centralized router loading system
│   │   │   │   ├── __init__.py         # load_all_routers() entry point
│   │   │   │   ├── loader.py           # Dynamic router import logic
│   │   │   │   ├── models.py           # RouterSpec dataclass
│   │   │   │   └── manifests/
│   │   │   │       └── business_manifest.py  # Registers vectorizer + blueprint routers
│   │   │   │
│   │   │   └── routers/
│   │   │       ├── photo_vectorizer_router.py   # [ROUTER] Photo/AI mode API
│   │   │       │
│   │   │       └── blueprint/                   # Blueprint mode routers
│   │   │           ├── __init__.py              # Aggregates all blueprint sub-routers
│   │   │           ├── edge_to_dxf_router.py    # [ROUTER] Edge-to-DXF conversion
│   │   │           ├── phase2_router.py         # OpenCV geometry vectorization
│   │   │           ├── phase3_router.py         # ML classification vectorization
│   │   │           ├── phase4_router.py         # Dimension linking
│   │   │           ├── calibration_router.py    # Scale calibration
│   │   │           └── clean_router.py          # Cleanup endpoints
│   │   │
│   │   └── docker/                     # Railway deployment config
│   │
│   ├── blueprint-import/               # [VECTORIZER] Blueprint processing
│   │   └── vectorizer_phase3.py        # Phase 3.6 vectorizer (4,149 lines)
│   │                                   #   - ML contour classification
│   │                                   #   - Grid zone analysis
│   │                                   #   - OCR dimension extraction
│   │                                   #   - DXF R12 export
│   │
│   └── photo-vectorizer/               # [VECTORIZER] Photo/AI processing
│       ├── photo_vectorizer_v2.py      # Photo Vectorizer v3.0 (5,351 lines)
│       │                               #   - 12-stage photo pipeline
│       │                               #   - Background removal (rembg, GrabCut, SAM)
│       │                               #   - Body isolation + plausibility scoring
│       │                               #   - Scale calibration from specs
│       │
│       └── edge_to_dxf.py              # Multi-scale edge fusion converter
│
└── docs/
    └── BLUEPRINT_VECTORIZER_ARCHITECTURE.md  # (this document)
```

---

## 3. API Endpoint Schema

### 3.1 Photo/AI Mode: `/api/vectorizer/extract`

**Router:** `services/api/app/routers/photo_vectorizer_router.py`  
**Backend:** `services/photo-vectorizer/photo_vectorizer_v2.py`

#### Request Schema (JSON body)

```typescript
interface VectorizeRequest {
  image_b64: string;              // Base64-encoded image (JPEG/PNG)
  media_type?: string;            // Default: "image/jpeg"
  known_width_mm?: number | null; // Reference dimension if known
  correct_perspective?: boolean;  // Default: true
  export_svg?: boolean;           // Default: true
  export_dxf?: boolean;           // Default: false
  label?: string;                 // Default: "photo-extract"
  source_type?: string;           // "auto" | "ai" | "photo" | "blueprint" | "silhouette"
  gap_closing_level?: string;     // "normal" | "aggressive" | "extreme"
  spec_name?: string | null;      // Instrument spec for AI pipeline scaling
}
```

#### Response Schema

```typescript
interface VectorizeResponse {
  ok: boolean;                    // Success flag
  svg_path_d: string;             // SVG path data for ImportView
  svg_path: string;               // File path (Blueprint workflow)
  dxf_path: string;               // File path (Blueprint workflow)
  contour_count: number;          // Number of contours extracted
  line_count: number;             // LINE entities in DXF
  body_width_mm: number;          // Extracted body width
  body_height_mm: number;         // Extracted body height
  body_width_in: number;          // Width in inches
  body_height_in: number;         // Height in inches
  scale_source: string;           // "spec" | "reference" | "estimated"
  bg_method: string;              // Background removal method used
  perspective_corrected: boolean; // Whether perspective was corrected
  warnings: string[];             // Processing warnings
  processing_ms: number;          // Processing time in milliseconds
  export_blocked: boolean;        // Whether export was blocked
  export_block_reason: string;    // Reason for blocking
  error: string;                  // Error message if failed
}
```

---

### 3.2 Blueprint Mode: `/api/blueprint/edge-to-dxf/convert`

**Router:** `services/api/app/routers/blueprint/edge_to_dxf_router.py`  
**Backend:** `services/photo-vectorizer/edge_to_dxf.py`

#### Request Schema (multipart/form-data)

```typescript
interface EdgeToDXFRequest {
  file: File;                     // Image or PDF file (required)
  target_height_mm?: number;      // Default: 500.0
  canny_low?: number;             // Range: 1-255, default: 50
  canny_high?: number;            // Range: 1-255, default: 150
  adjacency?: number;             // Range: 1.0-10.0, default: 3.0
  return_file?: boolean;          // Default: false (returns JSON metadata)
}
```

#### Response Schema

```typescript
interface EdgeToDXFResponse {
  success: boolean;
  dxf_path: string | null;        // Path to generated DXF
  line_count: number;             // LINE entities in output
  edge_pixel_count: number;       // Edge pixels detected
  image_size_px: [number, number];// [width, height] in pixels
  output_size_mm: [number, number];// [width, height] in mm
  mm_per_px: number;              // Scale factor
  processing_time_ms: number;
  file_size_mb: number;
  method: string;                 // "standard" | "enhanced"
  error: string | null;
}
```

---

### 3.3 Enhanced Edge Fusion: `/api/blueprint/edge-to-dxf/enhanced`

Same router as 3.2, uses multi-scale edge fusion (30/100, 50/150, 80/200 thresholds).

Produces 50,000-300,000+ LINE entities for archival-quality DXF files.

---

## 4. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (blueprint-reader.html)                   │
│                                                                             │
│   ┌───────────────────────┐         ┌───────────────────────┐               │
│   │     Blueprint Mode    │         │      Photo Mode       │               │
│   │   (FormData upload)   │         │  (JSON base64 upload) │               │
│   └───────────┬───────────┘         └───────────┬───────────┘               │
│               │                                 │                           │
│               ▼                                 ▼                           │
│   ┌───────────────────────────────────────────────────────────┐             │
│   │  const API_BASE = 'https://luthiers-toolbox-production... │             │
│   └───────────────────────────────────────────────────────────┘             │
└───────────────┬─────────────────────────────────┬───────────────────────────┘
                │                                 │
                │ POST multipart/form-data        │ POST application/json
                │ /api/blueprint/edge-to-dxf/     │ /api/vectorizer/extract
                │ convert                         │
                ▼                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RAILWAY (FastAPI Backend)                              │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        main.py                                      │   │
│   │  app.include_router(router, prefix="/api", tags=["Blueprint"])      │   │
│   │  app.include_router(router, prefix="/api/vectorizer", ...)          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                         │                                │                  │
│                         ▼                                ▼                  │
│   ┌───────────────────────────────┐   ┌───────────────────────────────┐     │
│   │   edge_to_dxf_router.py       │   │ photo_vectorizer_router.py    │     │
│   │                               │   │                               │     │
│   │  @router.post("/convert")     │   │  @router.post("/extract")     │     │
│   │  async def convert_edges(...) │   │  async def extract_from_photo │     │
│   └───────────┬───────────────────┘   └───────────┬───────────────────┘     │
│               │                                   │                         │
│               │ from edge_to_dxf import ...       │ from photo_vectorizer_v2│
│               │                                   │ import PhotoVectorizerV2│
│               ▼                                   ▼                         │
│   ┌───────────────────────────────┐   ┌───────────────────────────────┐     │
│   │      edge_to_dxf.py           │   │   photo_vectorizer_v2.py      │     │
│   │  (services/photo-vectorizer/) │   │  (services/photo-vectorizer/) │     │
│   │                               │   │                               │     │
│   │  - Canny edge detection       │   │  - 12-stage photo pipeline    │     │
│   │  - Multi-scale fusion         │   │  - Background removal         │     │
│   │  - LINE entity export         │   │  - Body isolation             │     │
│   │  - DXF R12 format             │   │  - Contour assembly           │     │
│   └───────────────────────────────┘   │  - Scale calibration          │     │
│                                       │  - SVG + DXF export           │     │
│                                       └───────────────────────────────┘     │
│                                                                             │
│   Also available (via phase3_router.py):                                    │
│   ┌───────────────────────────────┐                                         │
│   │   vectorizer_phase3.py        │                                         │
│   │  (services/blueprint-import/) │                                         │
│   │                               │                                         │
│   │  - ML contour classification  │                                         │
│   │  - Grid zone analysis         │                                         │
│   │  - OCR dimension extraction   │                                         │
│   │  - Dual-pass extraction       │                                         │
│   └───────────────────────────────┘                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                │                                 │
                ▼                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RESPONSE                                         │
│                                                                             │
│   Blueprint Mode:                        Photo Mode:                        │
│   - dxf_path (file on server)            - svg_path_d (inline SVG path)     │
│   - line_count, edge_pixel_count         - body_width_mm, body_height_mm    │
│   - mm_per_px scale factor               - scale_source, bg_method          │
│   - processing_time_ms                   - warnings[], processing_ms        │
│                                                                             │
│   Frontend renders SVG preview and/or triggers DXF download                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Frontend Implementation Details

### 5.1 API Base Configuration

```javascript
// blueprint-reader.html line ~50
const API_BASE = 'https://luthiers-toolbox-production.up.railway.app';
```

### 5.2 Blueprint Mode Request

```javascript
// Uses FormData for file upload
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('target_height_mm', targetHeight);
formData.append('canny_low', cannyLow);
formData.append('canny_high', cannyHigh);

const response = await fetch(`${API_BASE}/api/blueprint/edge-to-dxf/convert`, {
    method: 'POST',
    body: formData
});
```

### 5.3 Photo Mode Request

```javascript
// Uses JSON with base64 encoding
const reader = new FileReader();
reader.onload = async () => {
    const base64 = reader.result.split(',')[1];
    
    const response = await fetch(`${API_BASE}/api/vectorizer/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            image_b64: base64,
            media_type: file.type,
            source_type: 'photo',
            spec_name: selectedSpec,
            known_width_mm: referenceWidth
        })
    });
};
reader.readAsDataURL(file);
```

---

## 6. Backend Pipeline Details

### 6.1 Photo Vectorizer v3.0 (12-Stage Pipeline)

Location: `services/photo-vectorizer/photo_vectorizer_v2.py`

```
Stage 1:  Load image
Stage 2:  Perspective correction (if enabled)
Stage 3:  Background removal (rembg → GrabCut → threshold fallback)
Stage 4:  Edge detection (Canny)
Stage 5:  Contour extraction
Stage 6:  Body isolation (largest plausible contour)
Stage 7:  Contour assembly (connect gaps)
Stage 8:  Plausibility scoring
Stage 9:  Scale calibration (from spec / reference / estimated)
Stage 10: SVG generation
Stage 11: DXF export (R12 format)
Stage 12: Cleanup + response
```

**AI-Generated Image Mode** (`AIToCADExtractor`):
- 4-stage simplified pipeline
- No background removal needed (clean silhouettes)
- Direct contour extraction from alpha channel

### 6.2 Vectorizer Phase 3.6 (Blueprint Pipeline)

Location: `services/blueprint-import/vectorizer_phase3.py`

```
Phase 1:  PDF/image load + optional page selection
Phase 2:  Dual-pass edge detection (coarse + fine)
Phase 3:  Contour extraction + ML classification
Phase 4:  Grid zone analysis (body, neck, headstock regions)
Phase 5:  OCR dimension extraction
Phase 6:  Scale calibration from detected dimensions
Phase 7:  Geometry primitives detection (circles, lines, arcs)
Phase 8:  DXF R12 export with layer separation
```

---

## 7. Router Registration Chain

```python
# main.py
from .router_registry import load_all_routers

for router, prefix, tags in load_all_routers():
    app.include_router(router, prefix=prefix, tags=tags)

# router_registry/manifests/business_manifest.py
BUSINESS_ROUTERS = [
    RouterSpec(
        module="app.routers.blueprint",        # Loads blueprint/__init__.py
        prefix="/api",                          # → /api/blueprint/...
        tags=["Blueprint"],
    ),
    RouterSpec(
        module="app.routers.photo_vectorizer_router",
        prefix="/api/vectorizer",              # → /api/vectorizer/...
        tags=["Vectorizer", "Photo Import"],
    ),
]

# routers/blueprint/__init__.py
router = APIRouter(prefix="/blueprint", tags=["blueprint"])
router.include_router(edge_to_dxf_router)  # → /api/blueprint/edge-to-dxf/...
router.include_router(phase3_router)        # → /api/blueprint/phase3/...
```

---

## 8. DXF Output Standards

Per `CLAUDE.md` blocking infrastructure note:

| Property | Standard |
|----------|----------|
| Format | R12 (AC1009) |
| Entities | LINE only (no LWPOLYLINE) |
| Coordinates | ≤3 decimal places |
| EXTMIN/EXTMAX | Sentinel values (1e+20) |
| Units | INSUNITS=4 (mm), MEASUREMENT=1 (metric) |

**Rationale:** LWPOLYLINE causes Fusion 360 to freeze. R12 LINE entities have universal CAM compatibility.

---

## 9. Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | Claude API for AI analysis (Phase 1) | Required |
| `OPENAI_API_KEY` | DALL-E image generation | Optional |
| `RMOS_STRICT_STARTUP` | Fail fast on missing deps | `1` |
| `ENABLE_ROUTE_ANALYTICS` | Router usage metrics | `0` |

---

## 10. Deployment Topology

```
┌─────────────────────────────────────────────────────────┐
│                    HOSTINGER                            │
│  blueprint-reader.html (static HTML/JS)                 │
│  *.productionshop.io                                    │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    RAILWAY                              │
│  luthiers-toolbox-production.up.railway.app             │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │              FastAPI Application                   │  │
│  │  - CORS: allow_origins=["*"]                       │  │
│  │  - Rate limiting enabled                           │  │
│  │  - Request ID middleware                           │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ photo-vectorizer│  │ blueprint-import│              │
│  │ (cv2, rembg,    │  │ (cv2, ezdxf,    │              │
│  │  potrace)       │  │  pytesseract)   │              │
│  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

---

## 11. Error Handling

### 11.1 Vectorizer Unavailable (503)

```json
{
  "detail": "Photo vectorizer unavailable: <import_error>. Ensure services/photo-vectorizer is on PYTHONPATH and deps installed: pip install opencv-python rembg"
}
```

**Cause:** Heavy dependencies (cv2, rembg) not installed in container.

### 11.2 Invalid Base64 (422)

```json
{
  "detail": "Invalid base64: <decode_error>"
}
```

**Cause:** Corrupt or truncated image data in request.

### 11.3 Export Blocked

```json
{
  "ok": false,
  "export_blocked": true,
  "export_block_reason": "Body dimensions implausible: 524mm x 951mm exceeds spec range"
}
```

**Cause:** Scale validation failed. See CLAUDE.md vectorizer architecture for Loop 1 validation.

---

## 12. Testing Endpoints

### Health Check

```bash
curl https://luthiers-toolbox-production.up.railway.app/api/vectorizer/status
```

```json
{
  "available": true,
  "error": "",
  "note": "POST /extract with base64 image when available=true"
}
```

### Edge-to-DXF Status

```bash
curl https://luthiers-toolbox-production.up.railway.app/api/blueprint/edge-to-dxf/status
```

```json
{
  "available": true,
  "pdf_support": true,
  "error": null
}
```

---

## 13. Related Documentation

| Document | Location | Content |
|----------|----------|---------|
| Project CLAUDE.md | `CLAUDE.md` | Blocking infrastructure, DXF standards, vectorizer architecture |
| Vectorizer Sprint B | `CLAUDE.md` | Segmentation-first extraction plan |
| AGE Integration | `CLAUDE.md` | Agentic Guidance Engine pattern for Loop 1 |

---

## Appendix A: Complete Endpoint Reference

| Endpoint | Method | Mode | Router |
|----------|--------|------|--------|
| `/api/vectorizer/status` | GET | Photo | photo_vectorizer_router.py |
| `/api/vectorizer/extract` | POST | Photo | photo_vectorizer_router.py |
| `/api/blueprint/edge-to-dxf/status` | GET | Blueprint | edge_to_dxf_router.py |
| `/api/blueprint/edge-to-dxf/convert` | POST | Blueprint | edge_to_dxf_router.py |
| `/api/blueprint/edge-to-dxf/enhanced` | POST | Blueprint | edge_to_dxf_router.py |
| `/api/blueprint/vectorize-geometry` | POST | Blueprint | phase2_router.py |
| `/api/blueprint/phase3/vectorize` | POST | Blueprint | phase3_router.py |
| `/api/blueprint/phase4/link-dimensions` | POST | Blueprint | phase4_router.py |
| `/api/blueprint/calibration/...` | * | Blueprint | calibration_router.py |

---

## Appendix B: Schema Type Definitions (Pydantic)

### VectorizeRequest (photo_vectorizer_router.py:113)

```python
class VectorizeRequest(BaseModel):
    image_b64:          str
    media_type:         str = "image/jpeg"
    known_width_mm:     Optional[float] = None
    correct_perspective:bool = True
    export_svg:         bool = True
    export_dxf:         bool = False
    label:              str  = "photo-extract"
    source_type:        str  = "auto"
    gap_closing_level:  str  = "normal"
    spec_name:          Optional[str] = None
```

### VectorizeResponse (photo_vectorizer_router.py:125)

```python
class VectorizeResponse(BaseModel):
    ok:                 bool
    svg_path_d:         str   = ""
    svg_path:           str   = ""
    dxf_path:           str   = ""
    contour_count:      int   = 0
    line_count:         int   = 0
    body_width_mm:      float = 0.0
    body_height_mm:     float = 0.0
    body_width_in:      float = 0.0
    body_height_in:     float = 0.0
    scale_source:       str   = ""
    bg_method:          str   = ""
    perspective_corrected: bool = False
    warnings:           list[str] = []
    processing_ms:      float = 0.0
    export_blocked:     bool  = False
    export_block_reason:str   = ""
    error:              str   = ""
```

### EdgeToDXFResponse (edge_to_dxf_router.py:80)

```python
class EdgeToDXFResponse(BaseModel):
    success: bool
    dxf_path: Optional[str] = None
    line_count: int = 0
    edge_pixel_count: int = 0
    image_size_px: list = []
    output_size_mm: list = []
    mm_per_px: float = 0.0
    processing_time_ms: float = 0.0
    file_size_mb: float = 0.0
    method: str = ""
    error: Optional[str] = None
```
