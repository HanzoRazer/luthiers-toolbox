# Photo Vectorizer Architecture — Annotated Executive Summary

**Date:** 2026-04-11  
**Location:** `services/photo-vectorizer/`  
**Lines of Code:** ~27,500 (excluding tests)  
**Test Files:** 33 test modules  

---

## 1. System Purpose

The Photo Vectorizer is a standalone service that converts photographs and AI-generated images of guitars/instruments into clean SVG and DXF vector outlines. It is designed for:

- Hobbyist luthiers who have concept photos but no CAD drawings
- Importing AI-generated guitar renders (DALL-E, Midjourney) into CAM workflows
- Digitizing blueprint PDFs and scanned drawings
- Creating reference outlines from photographs for manual tracing

---

## 2. Chronological Build Progression

### Phase 1: Foundation (March 9–14, 2026)

**Commit:** `94d90243` — "Photo Vectorizer V2 — standalone photo-to-SVG/DXF extractor"

| Component | Lines | Purpose |
|-----------|-------|---------|
| `photo_vectorizer_v2.py` | 5,350 | Main extraction pipeline (12 stages) |
| `grid_classify.py` | 420 | Photo grid classification |
| `material_bom.py` | 370 | Bill of materials generation |
| `__init__.py` | 1 | Package marker |

**Technical Attributes:**
- 12-stage extraction pipeline (background removal → export)
- GrabCut / rembg / SAM background removal options
- Canny + Sobel + Laplacian edge fusion
- Reference object detection (coins, rulers)
- EXIF DPI extraction for scale calibration
- SVG/DXF/JSON export formats

---

### Phase 2: Patch Series 14/13/15/17 (March 14–17, 2026)

**Commit:** `752d5dd2` — "deploy patches 14+13+15 — gated closer, family classifier, feature-scale calibration"  
**Commit:** `6eb43121` — "Patch 17: ContourMerger + X-extent guard + coin position filter"

| Component | Lines | Purpose |
|-----------|-------|---------|
| `contour_plausibility.py` | 360 | Contour scoring with ownership |
| `contour_election.py` | 60 | Body contour election with threshold |
| `test_patches_14_13_15.py` | 340 | Patch validation tests |
| `test_patch_17.py` | 380 | Merger + guard tests |

**Technical Attributes:**
- **Patch 14:** GatedAdaptiveCloser — exterior-ring-gated morphological close
- **Patch 13A:** InstrumentFamilyClassifier — scale-independent family detection
- **Patch 13B:** FeatureScaleCalibrator — calibration from feature sizes
- **Patch 13C:** BatchCalibrationSmoother — median z-score outlier correction
- **Patch 15:** compute_rough_mpp — pre-calibration mpp for adaptive kernels
- **Patch 17:** ContourMerger — fills fragmented contours, morphological close
- **X-extent guard:** Rejects contours wider than 1.3× body region
- **Coin filter:** Rejects coin candidates inside foreground mask

**Test Results:** 127/127 pass

---

### Phase 3: Contour Stage Extraction (March 17–18, 2026)

**Commit:** `ebc28864` — "extract Stage 8 into ContourStage + GeometryCoachV1"  
**Commit:** `739664ff` — "contour plausibility scorer + typed stage result"

| Component | Lines | Purpose |
|-----------|-------|---------|
| `contour_stage.py` | 588 | Extracted Stage 8 pipeline module |
| `geometry_coach.py` | 260 | V1 coaching for retry decisions |
| `test_contour_stage.py` | 889 | Stage isolation tests |

**Technical Attributes:**
- Extracted contour assembly from monolithic pipeline
- ContourStageResult dataclass with typed fields
- ContourPlausibilityScorer with 6-signal breakdown
- Pre/post merge scoring comparison
- Export blocking with enriched diagnostics
- Seam for GeometryCoach inspection

---

### Phase 4: Body Isolation & Geometry Coach V2 (March 17–18, 2026)

**Commit:** `190adf66` — "V2 body-isolation coaching pipeline + geometry authority"

| Component | Lines | Purpose |
|-----------|-------|---------|
| `geometry_coach_v2.py` | 878 | V2 coaching with body+contour retry |
| `body_isolation_stage.py` | 593 | Body isolation with save/restore |
| `body_isolation_result.py` | 270 | Typed result with 6-signal breakdown |
| `geometry_authority.py` | 200 | Family priors, dimension fit scoring |

**Technical Attributes:**
- **Rules A-D:** Coaching decision rules
- **Rule A:** Body isolation score < 0.45 → retry body isolation
- **Rule B:** Contour score < 0.80 → retry contour stage
- **Rule C:** Ownership < 0.60 → retry body isolation
- **Rule D:** Border penalty > 0.5 → retry with border suppression
- Monotonic improvement gate (min 0.03 improvement)
- Max 2 retries before manual review
- Named retry profiles (lower_bout_recovery, border_suppression, etc.)

**Test Results:** 198 passed, 1 pre-existing failure

---

### Phase 5: Replay Framework (March 18, 2026)

**Commit:** `bf65f46f` — "photo vectorizer regression replay + body isolation"  
**Commit:** `2659f590` — "add replay framework + type configs + smoke tests"

| Component | Lines | Purpose |
|-----------|-------|---------|
| `replay_execution.py` | 170 | Replay runner for regression testing |
| `replay_fixture_loader.py` | 80 | Load regression fixtures |
| `replay_objects.py` | 75 | Typed replay objects |
| `replay_summary.py` | 100 | Generate replay summaries |
| `fixtures/*.json` | — | Regression test fixtures |

**Technical Attributes:**
- JSON fixture format for reproducible tests
- Ownership score tracking across retries
- Retry attempt recording with diagnostics
- Regression detection (archtop, benedetto, smart_guitar fixtures)

---

### Phase 6: Spec-Prior Contour Election — Diff 3 (March 18–21, 2026)

**Commit:** `e9fcb385` — "Diff 3 — spec-prior contour election"

| Component | Lines | Purpose |
|-----------|-------|---------|
| `body_model.py` | 85 | BodyModel dataclass |
| `landmark_extractor.py` | 340 | Landmark detection |
| `body_dimension_reference.json` | — | 16 guitar specs |

**Technical Attributes:**
- BodyModel with dimensional landmarks (upper_bout, waist, lower_bout)
- Hausdorff distance for contour-vs-spec comparison
- Expected outline generation from instrument specs
- elect_body_contour_against_expected_outline() function
- Specs: stratocaster, telecaster, les_paul, es335, dreadnought, jumbo, etc.

---

### Phase 7: AI Pipeline V3 (March 24 – April 2, 2026)

**Commit:** `d62584a7` — "v3 AI extraction path"  
**Commit:** `1fc94780` — "add cognitive extraction engine with document improvements"  
**Commit:** `b6b17739` — "add ai_render_extractor for AI-generated renders"

| Component | Lines | Purpose |
|-----------|-------|---------|
| `ai_render_extractor.py` | 462 | AI image feature detection |
| `cognitive_extraction_engine.py` | 1,503 | Agentic parallel extraction |
| `cognitive_extractor.py` | 1,470 | Cognitive pipeline wrapper |
| `photo_silhouette_extractor.py` | 370 | Silhouette extraction |
| `light_line_body_extractor.py` | 578 | Light-line body detection |

**Technical Attributes:**
- **Dual-path architecture:** Photo pipeline (12-stage) + AI pipeline (4-stage)
- **AI detection:** _detect_ai_image() identifies AI-generated renders
- **Cognitive engine:** Parallel extraction methods + fusion + agentic refinement
- **Cell types:** body, neck, headstock, background, hole, edge, uncertain
- **Extraction methods:** Otsu, Canny, color, grid, edge_flow, watershed, adaptive_thresh
- AI-optimized path extraction with clean backgrounds

---

### Phase 8: Multi-View Blueprint Support (April 1, 2026)

**Commit:** `3034b5d0` — "add blueprint view segmenter for multi-view blueprints"  
**Commit:** `38159c9b` — "add multi-view blueprint support to geometry coach"

| Component | Lines | Purpose |
|-----------|-------|---------|
| `blueprint_view_segmenter.py` | 830 | Multi-view detection & segmentation |
| `multi_view_reconstructor.py` | 928 | 3D reconstruction from views |
| `calibrate_carlos_jumbo.py` | 460 | Calibration for Carlos Jumbo guitar |

**Technical Attributes:**
- DetectedView dataclass (front, side, top, back views)
- View scoring and ranking
- Multi-view minimum area ratio (5%)
- Max 6 views per blueprint
- Carlos Jumbo calibration from 1:1 blueprint
- Soundhole-based scale calibration

---

### Phase 9: Edge-to-DXF & Topology Fix (April 1–9, 2026)

**Commit:** `9417fd9b` — "add edge_to_dxf high-fidelity exporter"  
**Commit:** `bee3e601` — "use contour tracing instead of row-major pixel sorting"

| Component | Lines | Purpose |
|-----------|-------|---------|
| `edge_to_dxf.py` | 468 | High-fidelity edge→DXF export |

**Technical Attributes:**
- DXF R12 format for Fusion 360 compatibility
- LINE entities (not LWPOLYLINE)
- cv2.findContours() for proper topology (fixed row-major sorting bug)
- Configurable scale (default: body height = 500mm)
- Stage timing instrumentation
- 50K–300K LINE entities for archival fidelity

---

### Phase 10: Production Hardening (April 9–11, 2026)

**Commit:** `57d9fce0` — "triage implementation with timing + diagnostics"  
**Commit:** `5cb5112e` — "cache rembg U2Net model between requests"

**Technical Attributes:**
- rembg session caching (255MB model loaded once)
- Stage timing with StageTimer utility
- Memory diagnostics for Railway deployment
- Benedetto 17" spec added to body_dimension_reference.json

---

## 3. File Structure Summary

```
services/photo-vectorizer/
├── photo_vectorizer_v2.py      # Main pipeline (5,350 lines)
├── contour_stage.py            # Stage 8 extraction (588 lines)
├── geometry_coach_v2.py        # V2 coaching (878 lines)
├── body_isolation_stage.py     # Body isolation (593 lines)
├── cognitive_extraction_engine.py  # Agentic extraction (1,503 lines)
├── cognitive_extractor.py      # Cognitive wrapper (1,470 lines)
├── multi_view_reconstructor.py # 3D reconstruction (928 lines)
├── blueprint_view_segmenter.py # Multi-view detection (830 lines)
├── edge_to_dxf.py              # High-fidelity DXF (468 lines)
├── ai_render_extractor.py      # AI image features (462 lines)
├── light_line_body_extractor.py # Light-line detection (578 lines)
├── contour_plausibility.py     # Scoring (360 lines)
├── body_isolation_result.py    # Typed result (270 lines)
├── geometry_authority.py       # Family priors (200 lines)
├── landmark_extractor.py       # Landmark detection (340 lines)
├── grid_classify.py            # Grid classification (420 lines)
├── geometry_coach.py           # V1 coach (260 lines)
├── body_model.py               # BodyModel (85 lines)
├── contour_election.py         # Election gate (60 lines)
├── replay_*.py                 # Replay framework (~400 lines)
├── body_dimension_reference.json  # 16 guitar specs
├── fixtures/                   # Regression fixtures
└── test_*.py                   # 33 test modules
```

---

## 4. Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **Dual-path architecture** | Photos need 12-stage cleanup; AI images need 4-stage extraction |
| **Ownership threshold 0.60** | Prevents false positives from guitar stands, backgrounds |
| **Spec-prior election (Diff 3)** | Hausdorff distance prevents wrong-shape election |
| **cv2.findContours() fix** | Row-major sorting broke topology; contour tracing preserves connectivity |
| **DXF R12 format** | Maximum compatibility with Fusion 360, AutoCAD |
| **LINE entities** | LWPOLYLINE causes Fusion freeze; LINE is universal |
| **rembg session caching** | Avoids 255MB allocation per request |
| **Max 2 retries** | Prevents infinite loops; forces manual review |

---

## 5. Current State (April 11, 2026)

### Working

- Photo pipeline (12-stage) — production ready
- AI pipeline (4-stage) — production ready
- Blueprint edge-to-DXF — production ready
- Geometry coaching with retries — production ready
- Multi-view blueprint detection — production ready

### Known Issues

- Photo pipeline still uses ownership threshold 0.60 as hard gate
- Blueprint pipeline uses unified scoring (10% ownership weight)
- Pipelines are not at parity — intentional scope boundary

### Test Coverage

- 33 test modules
- ~200 test cases
- Regression fixtures for archtop, benedetto, smart_guitar

---

## 6. Integration Points

| Consumer | Endpoint | Protocol |
|----------|----------|----------|
| API Router | `PhotoVectorizerV2.extract()` | Direct import |
| PhotoOrchestrator | `PhotoVectorizerV2.extract()` | Orchestration wrapper |
| Blueprint Pipeline | `edge_to_dxf.EdgeToDXF.convert()` | Direct import |
| Frontend | `/api/vectorizer/extract` | HTTP POST |

---

## 7. Dependencies

### Required

```
opencv-python-headless>=4.8
numpy
ezdxf>=1.0
```

### Optional

```
rembg>=2.0          # Better background removal
PyMuPDF (fitz)      # PDF support
segment-anything    # SAM background removal
Pillow              # EXIF extraction
scipy               # Hausdorff distance
```

---

## 8. Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `VECTORIZER_DEBUG` | `0` | Enable debug diagnostics |
| `REMBG_SESSION_CACHE` | enabled | Cache U2Net model |

### Body Dimension Reference

`body_dimension_reference.json` contains 16 guitar specs:
- stratocaster, telecaster, les_paul, es335
- dreadnought, om_000, jumbo, classical, j45
- flying_v, bass_4string, gibson_sg
- smart_guitar, jumbo_archtop, benedetto_17

---

## 9. Evolution Summary

| Phase | Date | Focus | Key Files Added |
|-------|------|-------|-----------------|
| 1 | Mar 9–14 | Foundation | photo_vectorizer_v2.py |
| 2 | Mar 14–17 | Patches 14/13/15/17 | contour_plausibility.py |
| 3 | Mar 17–18 | Stage extraction | contour_stage.py |
| 4 | Mar 17–18 | Geometry Coach V2 | geometry_coach_v2.py |
| 5 | Mar 18 | Replay framework | replay_*.py |
| 6 | Mar 18–21 | Spec-prior election | body_model.py, landmarks |
| 7 | Mar 24–Apr 2 | AI pipeline | cognitive_*.py |
| 8 | Apr 1 | Multi-view | blueprint_view_segmenter.py |
| 9 | Apr 1–9 | Edge-to-DXF | edge_to_dxf.py |
| 10 | Apr 9–11 | Production | timing, caching |

**Total evolution:** ~5 weeks from initial commit to production hardening.
