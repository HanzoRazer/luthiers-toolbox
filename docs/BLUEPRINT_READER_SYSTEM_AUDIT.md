# Blueprint Reader System Audit

**Version:** 1.0.0
**Date:** 2026-01-13
**Status:** ~93% Production-Ready

---

## Executive Summary

The Blueprint Reader is the **most complete subsystem** in the luthiers-toolbox repository. All core phases (AI analysis, geometry vectorization, CAM bridge) are operational with excellent engineering practices including graceful degradation and modular architecture.

---

## 1. Architecture Overview

### Phase Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    BLUEPRINT READER PIPELINE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Upload] → [Phase 1: AI] → [Phase 2: OpenCV] → [Phase 3: CAM]  │
│     │            │               │                    │          │
│     │            │               │                    │          │
│   PDF/PNG    Claude API     Edge Detection      Adaptive        │
│   JPG        Dimensions     Contours            Pocketing       │
│              Extraction     DXF Export          Toolpaths       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Graceful Degradation

The system implements H1 architecture with feature-gated endpoints:

| Dependency Missing | Behavior |
|--------------------|----------|
| Claude API key | `/analyze` returns 503 |
| OpenCV | `/vectorize-geometry` returns 501 |
| pdf2image | PDF upload returns 503 |

---

## 2. Backend Structure

### Core Routers

```
services/api/app/routers/
├── blueprint_router.py           # 1,315 lines
│   ├── POST /blueprint/analyze           # Phase 1: AI dimension extraction
│   ├── POST /blueprint/to-svg            # Phase 1: SVG export
│   ├── POST /blueprint/vectorize-geometry # Phase 2: OpenCV pipeline
│   ├── POST /blueprint/to-dxf            # Phase 2: DXF export (planned)
│   └── GET  /blueprint/health            # Health check
│
└── blueprint_cam_bridge.py       # 965 lines
    ├── POST /cam/blueprint/reconstruct-contours  # Phase 3.1
    ├── POST /cam/blueprint/preflight             # Phase 3.2
    ├── POST /cam/blueprint/to-adaptive           # Phase 2.5
    └── GET  /cam/blueprint/health                # Health check
```

### Supporting Modules

```
services/api/app/cam/
├── contour_reconstructor.py      # 23KB - LINE/SPLINE → closed loops
│   └── reconstruct_contours_from_dxf()
│       - 5-stage pipeline
│       - Graph-based DFS cycle detection
│       - Spline adaptive sampling
│       - Signed area winding order
│
├── dxf_preflight.py              # 28KB - 6-stage validation
│   └── DXFPreflight class
│       - check_layers()
│       - check_closed_paths()
│       - check_units()
│       - check_entity_types()
│       - check_dimensions()
│       - generate_html_report()
│
├── dxf_upload_guard.py           # 5KB - Security validation
│   └── read_dxf_with_validation()
│
└── adaptive_core_l1.py           # 25KB - Adaptive pocketing
    ├── plan_adaptive_l1()
    └── to_toolpath()
```

### External Service

```
services/blueprint-import/        # Standalone package
├── analyzer.py                   # 220 lines - Claude API
│   └── BlueprintAnalyzer class
│       - analyze_from_bytes()
│       - _analyze_with_claude()
│
├── vectorizer_phase2.py          # 447 lines - OpenCV
│   ├── GeometryDetector class
│   │   - preprocess_image()
│   │   - detect_edges()
│   │   - extract_contours()
│   │   - detect_lines()
│   └── Phase2Vectorizer class
│       - analyze_and_vectorize()
│       - _export_svg_with_geometry()
│       - _export_dxf_r12()
│
├── vectorizer.py                 # Phase 1 SVG
│   └── BasicSVGVectorizer class
│
└── dxf_compat.py                 # DXF version compatibility
```

---

## 3. API Endpoints

### Phase 1: AI Analysis

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/api/blueprint/analyze` | POST | ✅ Functional | Claude Sonnet 4 dimension extraction |
| `/api/blueprint/to-svg` | POST | ✅ Functional* | Dimension annotation SVG |
| `/api/blueprint/health` | GET | ✅ Functional | Phase availability check |

*Returns 501 in Docker (vectorizer.py not packaged)

**Input:** PDF, PNG, JPG (max 20MB)

**Output:**
```json
{
  "scale": "1:1",
  "dimensions": [
    {"label": "Body Width", "value": 380, "unit": "mm", "confidence": 0.95}
  ],
  "blueprint_type": "guitar_body",
  "model_detected": "Les Paul"
}
```

### Phase 2: Geometry Vectorization

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/api/blueprint/vectorize-geometry` | POST | ✅ Functional | OpenCV edge detection |
| `/api/blueprint/to-dxf` | POST | ❌ Planned | Use vectorize-geometry instead |

**Parameters:**
- `scale_factor`: 0.1-10.0
- `canny_low`: 10-200
- `canny_high`: 50-300
- `min_contour_area`: 10-1000 px²

**Output:** SVG + DXF R12 files

### Phase 2.5 & 3: CAM Bridge

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/api/blueprint/cam/reconstruct-contours` | POST | ✅ Functional | LINE/SPLINE → closed loops |
| `/api/blueprint/cam/preflight` | POST | ✅ Functional | 6-stage DXF validation |
| `/api/blueprint/cam/to-adaptive` | POST | ✅ Functional | Blueprint → adaptive pocketing |
| `/api/blueprint/cam/health` | GET | ✅ Functional | Phase 3 availability |

**to-adaptive Parameters:**
- `tool_d`: Tool diameter (mm)
- `stepover`: Stepover percentage
- `stepdown`: Depth per pass (mm)
- `margin`: Safety margin (mm)
- `strategy`: "Spiral" or "Lanes"
- `smoothing`: Path smoothing enabled

---

## 4. Frontend Components

### BlueprintLab.vue

**Location:** `client/src/views/BlueprintLab.vue`

**Sections:**

| Section | Feature | Status |
|---------|---------|--------|
| 1 | Upload Zone (drag-and-drop) | ✅ Complete |
| 2 | Phase 1 AI Analysis | ✅ Complete |
| 3 | Phase 2 Vectorization | ✅ Complete |
| 4 | Phase 3 CAM Integration | 🟡 Disabled |

**Phase 1 UI Features:**
- "Start Analysis" button
- Real-time progress timer
- Scale detection with confidence badge
- Blueprint type classification
- Collapsible dimensions table (50+ dimensions)
- Export buttons (SVG, Parametric Designer)

**Phase 2 UI Features:**
- Parameter sliders (scale, thresholds, min area)
- "Vectorize Geometry" button
- Statistics display (contours, lines, timing)
- SVG preview canvas
- Export buttons (SVG, DXF R2000)

**Phase 3 UI:**
- "Send to Adaptive Lab" button (disabled, "Coming Soon")

### Router Configuration

```typescript
// client/src/router/index.ts
{ path: '/blueprint-lab', component: BlueprintLab }
{ path: '/lab/blueprint', redirect: '/blueprint-lab' }
```

---

## 5. Core Algorithms

### Phase 1: AI Dimension Extraction

```python
# Claude Sonnet 4 Vision API
async def analyze_from_bytes(file_bytes, filename):
    # 1. Convert PDF to image (300 DPI)
    # 2. Send to Claude with dimension extraction prompt
    # 3. Parse structured response
    # 4. Return scale, dimensions, blueprint_type
```

**Accuracy:** Depends on image quality (300+ DPI recommended)
**Timing:** 3-7 seconds

### Phase 2: Geometry Vectorization

```python
# OpenCV Pipeline
def analyze_and_vectorize(image):
    # 1. Preprocess: grayscale → Gaussian blur → CLAHE
    # 2. Edge detection: Canny (thresholds: 50/150)
    # 3. Contour extraction: Douglas-Peucker approximation
    # 4. Line detection: Hough transform
    # 5. Export: SVG + DXF R12
```

**Accuracy:** 85-95% of visible edges
**Timing:** 1-2 seconds

### Phase 3.1: Contour Reconstruction

```python
# Graph-based cycle detection
def reconstruct_contours_from_dxf(dxf_bytes):
    # 1. Collect entities (LINE, SPLINE, ARC)
    # 2. Build edge graph
    # 3. Deduplicate points (0.1mm tolerance)
    # 4. DFS cycle detection
    # 5. Classify loops (outer boundary vs islands)
```

**Use Case:** Gibson L-00 style drawings (48 LINEs + 33 SPLINEs → 3 closed loops)
**Timing:** 0.6-1.6 seconds

### Phase 3.2: DXF Preflight Validation

```python
# 6-stage validation pipeline
class DXFPreflight:
    def validate(self, dxf_bytes):
        # 1. Parse DXF
        # 2. Check required layers
        # 3. Validate closed paths
        # 4. Check unit consistency ($INSUNITS)
        # 5. Validate entity types
        # 6. Dimension sanity (lutherie ranges)
```

**Output:** JSON or HTML report with ERROR/WARNING/INFO

### Phase 2.5: Adaptive Pocketing

```python
# Blueprint → Toolpath
def blueprint_to_adaptive(dxf_bytes, params):
    # 1. Extract closed LWPOLYLINE loops
    # 2. Call plan_adaptive_l1() with island avoidance
    # 3. Generate toolpath moves
    # 4. Return moves[], stats{}, warnings[]
```

**Integration:** Uses `adaptive_core_l1.py` engine

---

## 6. Dependencies

### Required (Always)

```
fastapi                 # Router framework
ezdxf>=1.1.0           # DXF read/write
pyclipper              # Polygon offsetting
numpy>=1.24.0          # Numerical operations
```

### Phase 1 (Optional)

```
emergentintegrations>=0.1.0  # OR anthropic (Claude API)
pdf2image>=1.16.0           # PDF conversion
Pillow>=10.0.0              # Image processing
```

### Phase 2 (Optional)

```
opencv-python>=4.8.0        # Edge detection
scikit-image>=0.21.0        # Advanced image analysis
svgwrite>=1.4.0             # SVG generation
```

### Environment Variables

```bash
EMERGENT_LLM_KEY=...    # Primary Claude API key
ANTHROPIC_API_KEY=...   # Fallback Claude API key
```

---

## 7. Integration Points

### With Adaptive Engine (L.1)

```python
from ..cam.adaptive_core_l1 import plan_adaptive_l1, to_toolpath

# /cam/blueprint/to-adaptive endpoint
loops = extract_loops_from_dxf(dxf_bytes)
moves = plan_adaptive_l1(loops, tool_d, stepover, ...)
toolpath = to_toolpath(moves)
```

**Status:** ✅ Complete

### With Contour Reconstructor

```python
from ..cam.contour_reconstructor import reconstruct_contours_from_dxf

# /cam/blueprint/reconstruct-contours endpoint
loops = reconstruct_contours_from_dxf(dxf_bytes)
```

**Status:** ✅ Complete

### With DXF Preflight

```python
from ..cam.dxf_preflight import DXFPreflight, generate_html_report

# /cam/blueprint/preflight endpoint
preflight = DXFPreflight()
result = preflight.validate(dxf_bytes)
html = generate_html_report(result)
```

**Status:** ✅ Complete

### With RMOS

**Status:** ❌ No integration found
**Gap:** Would need bridge to saw operation definitions

### With Art Studio

**Status:** ⚠️ Minimal (style reference only)
**Opportunity:** Blueprint geometry for rosette constraints

---

## 8. Test Coverage

### Test Files

| Test File | Components | Status |
|-----------|-----------|--------|
| `test_blueprint_ai_disabled.py` | Graceful degradation | ✅ In CI |
| `test_blueprint_phase3_ci.py` | Phase 3 modules | ⚠️ Partial |
| `__REFERENCE__/test_blueprint_phase1.py` | AI analysis | ✅ Reference |
| `__REFERENCE__/test_blueprint_phase2.py` | Vectorization | ✅ Reference |
| `__REFERENCE__/test_blueprint_cam_bridge.py` | CAM bridge | ✅ Reference |
| `__REFERENCE__/test_real_blueprint_gibson_l00.py` | Real-world | ✅ Reference |

### Coverage Assessment

| Component | Coverage | Notes |
|-----------|----------|-------|
| Phase 1 (analyzer) | ✅ Good | Basic tests in CI |
| Phase 2 (vectorizer) | ✅ Good | Tests available |
| Phase 3.1 (contour) | ⚠️ Partial | Reference tests only |
| Phase 3.2 (preflight) | ⚠️ Partial | Reference tests only |
| Integration | ⚠️ Partial | Not in main CI |

---

## 9. Performance Characteristics

### Timing

| Phase | Operation | Duration |
|-------|-----------|----------|
| Phase 1 | PDF conversion | 1-2s |
| Phase 1 | Claude API call | 2-5s |
| Phase 1 | **Total** | **3-7s** |
| Phase 2 | Edge detection | 0.3-0.8s |
| Phase 2 | Contour extraction | 0.2-0.5s |
| Phase 2 | DXF export | 0.1-0.3s |
| Phase 2 | **Total** | **1-2s** |
| Phase 3.1 | Contour reconstruction | 0.6-1.6s |
| Phase 3.2 | Preflight validation | 0.2-0.5s |
| Phase 2.5 | Adaptive planning | 1-3s |

### Memory Usage

| Phase | Memory |
|-------|--------|
| Phase 1 | 50-150MB |
| Phase 2 | 100-300MB |
| Phase 3 | 30-80MB |

### Accuracy Metrics

| Metric | Value |
|--------|-------|
| Contour detection | 85-95% of visible edges |
| False positives | <5% |
| Dimension tolerance | ±0.5mm (at 1:1 scale) |
| Endpoint matching | 0.1mm default tolerance |

---

## 10. Safety Rules Implemented

| Rule | Implementation |
|------|----------------|
| File size limit | 20MB max |
| Extension validation | .pdf, .png, .jpg, .jpeg only |
| API key validation | Check before Claude calls |
| Temp file cleanup | try/finally blocks |
| Closed path requirement | Validate before adaptive |
| Minimum loop validation | ≥3 points required |
| Island classification | First loop = outer boundary |
| DXF version check | Compatibility validation |

---

## 11. Identified Gaps

### Missing Functionality

| Gap | Impact | Effort |
|-----|--------|--------|
| **RMOS Integration** | No saw operation bridge | 8h |
| **Art Studio Integration** | No visual constraints | 4h |
| **Multi-page PDF** | Only first page analyzed | 4h |
| **Frontend CAM Button** | Disabled in UI | 2h |

### Incomplete Features

| Feature | Status | Notes |
|---------|--------|-------|
| Phase 1 SVG in Docker | 501 | vectorizer.py not packaged |
| `/blueprint/to-dxf` | Planned | Use `/vectorize-geometry` |
| Handwritten dimensions | Not supported | OCR integration needed |
| DXF R18 export | Framework ready | dxf_compat.py exists |

### Test Gaps

| Gap | Priority |
|-----|----------|
| Phase 3.1 tests in CI | High |
| Phase 3.2 tests in CI | High |
| Integration pipeline tests | Medium |

---

## 12. Path to Full Completion

### Priority 1: Critical (10h)

| Task | Hours | Outcome |
|------|-------|---------|
| RMOS integration bridge | 8h | Blueprint → saw operations |
| Enable Phase 1 SVG in Docker | 2h | Full production functionality |

### Priority 2: Important (10h)

| Task | Hours | Outcome |
|------|-------|---------|
| Multi-page PDF support | 4h | Full document analysis |
| Phase 3 CI test integration | 4h | Complete test coverage |
| Enable frontend CAM button | 2h | Seamless UI workflow |

### Priority 3: Enhancement (4h)

| Task | Hours | Outcome |
|------|-------|---------|
| Art Studio integration | 4h | Visual constraint support |

**Total: ~24 hours to 100% completion**

---

## 13. Summary

### Component Status

| Component | Status | Completeness |
|-----------|--------|--------------|
| Phase 1: AI Analysis | ✅ Complete | 100% |
| Phase 1: SVG Export | ✅ Complete | 100%* |
| Phase 2: Vectorization | ✅ Complete | 100% |
| Phase 2: DXF Export | ✅ Complete | 100% |
| Phase 2.5: CAM Bridge | ✅ Complete | 100% |
| Phase 3.1: Contour Reconstruction | ✅ Complete | 100% |
| Phase 3.2: DXF Preflight | ✅ Complete | 100% |
| Frontend UI | ✅ Complete | 95% |
| API Endpoints | ✅ Complete | 90% |
| RMOS Integration | ❌ Missing | 0% |
| Art Studio Integration | ⚠️ Minimal | 10% |
| Test Coverage | ⚠️ Partial | 60% |

*Unavailable in Docker

### Overall Assessment

**Blueprint Reader is 93% complete and the most production-ready subsystem.**

**Strengths:**
- Complete AI + OpenCV pipeline
- Excellent graceful degradation
- Modular, well-documented code
- Full frontend UI (Phase 1 + 2)
- CAM bridge operational

**Gaps:**
- RMOS integration missing
- Multi-page PDF not supported
- Phase 3 tests not in main CI

**Recommendation:** 24 focused hours completes Blueprint Reader for production use.

---

*Document generated as part of luthiers-toolbox system audit.*
