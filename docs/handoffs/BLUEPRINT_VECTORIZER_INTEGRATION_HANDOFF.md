# Blueprint Vectorizer Integration - Developer Handoff

**Document Type:** Annotated Executive Summary
**Created:** 2026-03-06
**Status:** Ready for Implementation
**Priority:** High

---

## Executive Summary

The Production Shop has a 3-phase Blueprint Lab UI and backend infrastructure that is **80% complete**. The missing piece is the **pixel calibration module** (`services/blueprint-import/calibration/`) which extracts accurate real-world dimensions from blueprints. This module exists but is **not wired** into the web application.

**Goal:** Wire the calibration module into the existing Blueprint Lab workflow to solve the core pain point: *vendors sell garbage "CNC-ready" files with unknown scaling*.

---

## Current State Assessment

### What's Built (Frontend)

| Component | Path | Status |
|-----------|------|--------|
| BlueprintLab.vue | `packages/client/src/views/` | ✅ Complete |
| BlueprintUploadZone.vue | `components/blueprint/` | ✅ Complete |
| Phase1AnalysisPanel.vue | `components/blueprint/` | ✅ Complete |
| Phase2VectorizationPanel.vue | `components/blueprint/` | ✅ Complete |
| Phase3CamPanel.vue | `components/blueprint/` | ✅ Complete |
| useBlueprintWorkflow.ts | `composables/` | ✅ Complete |

> **Annotation:** The UI is fully functional. User can upload PDF/image, run AI analysis, vectorize, and send to CAM. The gap is calibration accuracy.

### What's Built (Backend)

| Component | Path | Status |
|-----------|------|--------|
| phase1_router.py | `app/routers/blueprint/` | ✅ Claude AI analysis |
| phase2_router.py | `app/routers/blueprint/` | ✅ Basic OpenCV |
| constants.py | `app/routers/blueprint/` | ✅ Adds blueprint-import to path |
| Feature registry | `app/core/features.py` | ⚠️ Path may be wrong |

> **Annotation:** Backend has Phase 1 (AI) and Phase 2 (OpenCV) endpoints. The `constants.py` already adds `services/blueprint-import/` to sys.path, so importing calibration modules should work.

### What's Built (Standalone - NOT WIRED)

| Component | Path | Purpose |
|-----------|------|---------|
| pixel_calibrator.py | `blueprint-import/calibration/` | Multi-method PPI detection |
| scale_detector.py | `blueprint-import/calibration/` | Scale length detection |
| dimension_extractor.py | `blueprint-import/calibration/` | Body/bout measurement |
| calibration_integration.py | `blueprint-import/` | Pipeline wrapper |
| grid_zone_classifier.py | `blueprint-import/classifiers/` | ML-based zone detection |
| vectorizer_phase3.py | `blueprint-import/` | Advanced vectorizer |

> **Annotation:** These modules are tested and working standalone (see `CALIBRATION_REPORT.md`). They need API endpoints and UI integration.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vue 3)                         │
├─────────────────────────────────────────────────────────────────┤
│  BlueprintLab.vue                                               │
│    ├── BlueprintUploadZone.vue    → POST /blueprint/analyze     │
│    ├── Phase1AnalysisPanel.vue    ← AI dimensions + scale       │
│    ├── [NEW] CalibrationPanel.vue → POST /blueprint/calibrate   │
│    ├── Phase2VectorizationPanel   → POST /blueprint/vectorize   │
│    └── Phase3CamPanel.vue         → POST /cam/adaptive          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                        │
├─────────────────────────────────────────────────────────────────┤
│  /api/blueprint/                                                │
│    ├── POST /analyze          → phase1_router.py (Claude AI)    │
│    ├── POST /calibrate [NEW]  → calibration_router.py           │
│    ├── POST /vectorize        → phase2_router.py (OpenCV)       │
│    └── GET  /dimensions [NEW] → dimension_extractor.py          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CALIBRATION MODULE (Python)                    │
├─────────────────────────────────────────────────────────────────┤
│  services/blueprint-import/calibration/                         │
│    ├── PixelCalibrator      → PPI from paper/ruler/body         │
│    ├── ScaleReferenceDetector → Nut-to-bridge detection         │
│    ├── CalibratedDimensionExtractor → Real-world measurements   │
│    └── EnhancedCalibrationPipeline  → Orchestration             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integration Tasks

### Task 1: Create Calibration Router (Backend)

**File:** `services/api/app/routers/blueprint/calibration_router.py`

```python
# Endpoints needed:
POST /calibrate          # Run auto-calibration, return PPI + confidence
POST /calibrate/manual   # User clicks two points, provides real measurement
GET  /calibration/{id}   # Retrieve calibration result
POST /dimensions         # Extract dimensions using calibration
```

**Dependencies:**
- Import from `calibration` module (already on sys.path via constants.py)
- Store calibration results in session or temp file

### Task 2: Register Router

**File:** `services/api/app/routers/blueprint/__init__.py`

```python
from .calibration_router import router as calibration_router
router.include_router(calibration_router)
```

### Task 3: Add Calibration UI Component (Frontend)

**File:** `packages/client/src/components/blueprint/CalibrationPanel.vue`

Features needed:
- Display auto-detected PPI and confidence
- Show calibration method used
- Manual override: click two points, enter dimension
- Brand/model dropdown for known scale lengths
- "Accept Calibration" button to proceed

### Task 4: Update Workflow Composable

**File:** `packages/client/src/composables/useBlueprintWorkflow.ts`

Add:
- `calibration` ref for calibration state
- `calibrate()` function to call API
- `manualCalibrate(point1, point2, dimension)` for user override

### Task 5: Wire CalibrationPanel into BlueprintLab

**File:** `packages/client/src/views/BlueprintLab.vue`

Insert between Phase1 and Phase2:
```vue
<CalibrationPanel
  v-if="analysis"
  :calibration="calibration"
  :is-calibrating="isCalibrating"
  @calibrate="runCalibration"
  @manual-calibrate="manualCalibrate"
  @accept="acceptCalibration"
/>
```

---

## API Contract

### POST /api/blueprint/calibrate

**Request:**
```json
{
  "image_data": "base64...",
  "known_scale_length": 25.5,        // optional
  "paper_size": "letter",            // optional
  "prefer_method": "auto"            // auto|paper|scale|body_heuristic
}
```

**Response:**
```json
{
  "calibration_id": "uuid",
  "method": "scale_length",
  "ppi": 150.0,
  "ppmm": 5.91,
  "confidence": 0.85,
  "reference_name": "scale_length",
  "reference_value_inches": 25.5,
  "notes": ["Scale length detected: 25.5\" = 3825px"]
}
```

### POST /api/blueprint/dimensions

**Request:**
```json
{
  "image_data": "base64...",
  "calibration_id": "uuid",
  "name": "Stratocaster"
}
```

**Response:**
```json
{
  "body_length_inches": 17.5,
  "body_width_inches": 13.2,
  "upper_bout_width_inches": 11.5,
  "lower_bout_width_inches": 12.8,
  "waist_width_inches": 9.2,
  "scale_length_inches": 25.5,
  "calibration_confidence": 0.85,
  "warnings": []
}
```

---

## Testing Checklist

- [ ] Calibration endpoint returns valid PPI for test image
- [ ] Manual calibration with two points calculates correct PPI
- [ ] Dimensions endpoint extracts reasonable body measurements
- [ ] UI displays calibration results with confidence indicator
- [ ] Low-confidence results trigger manual calibration prompt
- [ ] Calibration persists through vectorization step
- [ ] End-to-end: Upload PDF → Calibrate → Vectorize → Export DXF with correct scale

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Auto-calibration accuracy | >70% within 5% of true PPI |
| Manual calibration accuracy | >95% (user provides ground truth) |
| Dimension extraction | Body length within 0.5" of actual |
| UI response time | <3s for calibration step |

---

## References

- `docs/ORIGIN_STORY.md` - Why this matters (the pain point)
- `services/blueprint-import/CALIBRATION_REPORT.md` - Test results
- `services/blueprint-import/calibration_integration.py` - Pipeline wrapper
- `packages/client/src/views/BlueprintLab.vue` - Current UI

---

## Vectorizer Pipeline Process Path Gaps (2026-03-07)

A full audit of the blueprint-to-CNC pipeline was conducted during OM purfling G-code generation. The recovered DXF scan data (`om_000_body.dxf` BODY_POINTS layer) was found unusable as a CNC contour — 5,451 scattered vectorized segments, not an ordered perimeter — which exposed the deeper issue: **Phase 3 and Phase 4 are completely disconnected from the API and CAM pipeline.**

### Pipeline Map

```
                    ┌──────────────────────────────────────────────────┐
                    │              CONNECTED (working)                 │
 Image ──→ Phase 1 ──→ /analyze ──→ AI dims + scale                  │
   │         (Claude)      │                   │                      │
   │                       ↓                   ↓                      │
   │               /to-svg (SVG)          (NOT passed to P3)  ← GAP  │
   │                                                                  │
   ├──→ Calibration ──→ /calibrate ──→ PPI ──→ Phase 2 scale fix     │
   │                                                                  │
   ├──→ Phase 2 ──→ /vectorize-geometry ──→ DXF ──→ CAM bridge ──→ G │
   │    (OpenCV)         ✅ endpoint            ✅ /to-adaptive       │
   │                                                                  │
   │              ┌──────────────────────────────────────────────────┐ │
   │              │              DISCONNECTED                       │ │
   ├──→ Phase 3.6 ──→ ❌ no endpoint ──→ DXF (never reaches CAM)  │ │
   │    (ML+OCR+                                                    │ │
   │     prims)   ──→ OCR dims ──→ ❌ dead end                     │ │
   │              ──→ primitives ──→ ❌ dead end                    │ │
   │                                                                │ │
   └──→ Phase 4 ──→ ❌ CLI only ──→ PipelineResult ──→ ❌ dead end │ │
        (dimension       (run_phase4.py)                            │ │
         linking)                                                    │ │
                  └──────────────────────────────────────────────────┘ │
 Frontend                                                             │
   └──→ BlueprintImporter.vue ──→ /analyze only ← GAP (no P2/P3 UI) │
   └──→ BlueprintLab.vue ──→ Phase 1 + Phase 2 panels (no Phase 3)  │
                    └─────────────────────────────────────────────────┘
```

### Gap Registry

| ID | Component | Issue | Severity |
|----|-----------|-------|----------|
| VEC-GAP-01 | Phase 3.6 API | `Phase3Vectorizer` (ML classification, OCR, geometric primitives, scale detection) in `vectorizer_phase3.py` has **zero HTTP endpoints**. Not imported in `constants.py`. Only accessible via direct Python or Phase 4 CLI. | Critical |
| VEC-GAP-02 | Phase 4 API | `phase4/pipeline.py` orchestrator exists but only exposed via `run_phase4.py` CLI script. No `/api/blueprint/phase4` or `/api/blueprint/link-dimensions` route. | High |
| VEC-GAP-03 | Phase 4 sink | `PipelineResult` (arrow detection, dimension-to-feature linking) has **no downstream consumer**. Nothing in CAM, frontend, or any other module reads this output. | High |
| VEC-GAP-04 | Phase 3 → CAM | CAM bridge (`blueprint_cam/extraction.py`) parses LWPOLYLINE on "GEOMETRY" layer. Phase 3 also writes to "GEOMETRY", so compatibility is likely — but no integration test exists to confirm. | Medium |
| VEC-GAP-05 | Phase 1 → Phase 3 | Phase 1 (Claude AI) returns scale factor + instrument dimensions. Phase 3 has independent `ScaleDetector`. No code passes Phase 1's AI-detected scale into Phase 3 as a calibration seed, causing redundant computation and potential disagreement. | Medium |
| VEC-GAP-06 | Frontend gaps | `BlueprintImporter.vue` calls `/analyze` only (Phase 1). `BlueprintLab.vue` has Phase 1 + Phase 2 panels but no Phase 3 panel. No UI for Phase 3 ML-classified features, OCR dimensions, or geometric primitives. | Medium |
| VEC-GAP-07 | constants.py | `app/routers/blueprint/constants.py` has `ANALYZER_AVAILABLE`, `VECTORIZER_AVAILABLE`, `PHASE2_AVAILABLE`, `CALIBRATION_AVAILABLE` — but no `PHASE3_AVAILABLE` flag or `Phase3Vectorizer` import. | Medium |
| VEC-GAP-08 | OCR dead end | Phase 3.6 OCR extracts dimension text into `ExtractionResult.ocr_dimensions` and `ocr_raw_texts`. No downstream consumer processes these values for calibration, validation, or display. | Low |

### Closure Plan (Priority Order)

1. **Phase 3 router** — Create `app/routers/blueprint/phase3_router.py` wrapping `Phase3Vectorizer.extract()` as `POST /extract-advanced`. Add `PHASE3_AVAILABLE` flag to `constants.py`. Register in `__init__.py`.
2. **Phase 1 → Phase 3 scale bridge** — Pass AI-detected scale factor from `/analyze` response into Phase 3 as initial `mm_per_px` hint, eliminating redundant scale detection.
3. **Phase 3 → CAM integration test** — Confirm Phase 3 DXF output parses correctly through `extract_loops_from_dxf()`. Add integration test to `services/api/tests/`.
4. **Phase 4 router** — Create `app/routers/blueprint/phase4_router.py` wrapping `BlueprintPipeline.process()` as `POST /link-dimensions`.
5. **Phase 4 → CAM consumer** — Feed linked dimensions (e.g., auto-detected neck pocket width) into toolpath planning parameters.
6. **Frontend Phase 3 panel** — Add `Phase3ExtractionPanel.vue` to `BlueprintLab.vue` showing ML-classified contours, OCR dimensions, and detected primitives.
7. **OCR pipeline** — Route `ocr_dimensions` into calibration validation (cross-check OCR-read "25.5 inch" against Phase 1 AI scale detection).

### Evidence: OM Purfling Case Study

The OM purfling binding work (see `docs/handoffs/OM_PURFLING_CNC_HANDOFF.md`) demonstrated the gap concretely:
- `om_000_body.dxf` BODY_POINTS layer: 5,451 scattered scan segments (not a usable contour)
- `om_000_body.dxf` BODY_OUTLINE layer: 10-point bounding polygon (too coarse for CNC)
- **Workaround required:** Parametric Bézier outline generated from `martin_om28.json` spec dimensions
- **If pipeline were connected:** Phase 3 ML classification → clean closed BODY_OUTLINE polyline → offset toolpath → G-code

---

## Recovered DXF Assets (2026-03-07)

During the WP-3 store decomposition refactor (commit `543f7401`), **19 vectorized body outline DXF files** were accidentally deleted from `services/api/app/instrument_geometry/body/dxf/`. These files were originally committed in `8d06e1ab` (Dec 14, 2025) as part of the instrument geometry recovery.

All 19 files have been **recovered from git history** and restored to both their original working location and an archive copy.

### Archive Location

```
Guitar Plans/Recovered_DXF_Assets_2026-03-07/
├── acoustic/          (9 files, ~1.7 MB)
│   ├── J45_body_outline.dxf
│   ├── J45_body_outline_dense.dxf
│   ├── Jumbo_body.dxf
│   ├── classical_body.dxf
│   ├── dreadnought_body.dxf
│   ├── gibson_l_00_body.dxf
│   ├── om_000_body.dxf
│   ├── orchestra_model_body_view.dxf
│   └── orchestra_model_clean.dxf
├── electric/          (7 files, ~276 KB)
│   ├── JS1000_body.dxf
│   ├── LesPaul_body.dxf
│   ├── Stratocaster_body.dxf
│   ├── flying_v_body.dxf
│   ├── flying_v_full.dxf
│   ├── gibson_explorer_body.dxf
│   └── harmony_h44_body.dxf
└── other/             (3 files, ~118 KB)
    ├── concert_ukulele_body.dxf
    ├── octave_mandolin_body.dxf
    └── soprano_ukulele_body.dxf
```

### Working Location (Restored)

All files also restored to their original paths under:
```
services/api/app/instrument_geometry/body/dxf/{acoustic,electric,other}/
```

### Format Note

These DXFs are **AC1024 (AutoCAD 2010)** format, not the project-standard AC1009 (R12). They are fully readable by `ezdxf` and usable for CNC toolpath generation. If strict R12 compliance is needed, the Vectorizer Phase 2 pipeline can re-export them from the source DWGs in the Guitar Plans archive.

### Available for Re-vectorization

If any recovered file is found to be incomplete or needs refinement, the source DWGs and PDFs remain available in `Guitar Plans/` for re-processing through the Blueprint Vectorizer pipeline (Phase 2: OpenCV + DXF export).

---

*Production Shop - Blueprint Vectorizer Integration Handoff*
