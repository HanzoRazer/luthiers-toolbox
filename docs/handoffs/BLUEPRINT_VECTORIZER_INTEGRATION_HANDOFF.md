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

*Production Shop - Blueprint Vectorizer Integration Handoff*
