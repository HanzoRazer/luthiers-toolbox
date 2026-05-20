# Vectorizer Ecosystem Developer Handoff

**Date:** 2026-05-13  
**Author:** Code Audit (Claude Opus 4.5)  
**Scope:** Blueprint Reader Vectorizer (LIVE) + Photo Vectorizer (SUSPENDED)

---

## Executive Summary

The Luthiers Toolbox contains **two distinct vectorizer systems** totaling **50,000+ lines of Python** with fundamentally different production states:

| System | Status | Lines | Modules | Tests | Maturity |
|--------|--------|-------|---------|-------|----------|
| **Blueprint Vectorizer** | LIVE OPERATIONAL | 25,000+ | 68 | 200+ | 8.0/10 |
| **Photo Vectorizer** | SUSPENDED R&D | 25,000+ | 45 | 277 | 4.0/10 |

**Critical Finding:** The blueprint vectorizer has **three complete subsystems that are NOT WIRED** into the production pipeline:
1. Calibration Pipeline (1,450 lines) - ready but never instantiated
2. FeedbackSystem class - defined but never called
3. TrainingDataCollector class - defined but never called

**Strategic Decision:** Photo vectorizer is formally superseded by InstrumentBodyGenerator (IBG). Only the blueprint path and `edge_to_dxf.py` remain production-viable.

---

## Part 1: Blueprint Reader Vectorizer (LIVE)

### 1.1 System Architecture

```
services/blueprint-import/
├── vectorizer_phase3.py          [4,149 lines] Core extraction engine
├── vectorizer_phase2.py          [1,684 lines] Legacy fallback
├── vectorizer_enhancements.py    [1,155 lines] Phase 3.7 optional modules
├── calibration/                  [1,450 lines] UNINTEGRATED calibration pipeline
│   ├── pixel_calibrator.py       [502 lines]  Multi-method scale detection
│   ├── scale_detector.py         [509 lines]  Reference feature recognition
│   └── dimension_extractor.py    [439 lines]  Real-world dimension calc
├── phase4/                       [2,500+ lines] Dimension linking
│   ├── pipeline.py               [271 lines]  End-to-end orchestrator
│   ├── dimension_linker.py       [348 lines]  OCR-to-geometry association
│   ├── arrow_detector.py         [827 lines]  Witness/leader line detection
│   └── leader_associator.py      [1,018 lines] Multi-factor ranking
├── classifiers/
│   ├── grid_zone/                [46 tests] Zone-based body detection
│   └── latin_american/           [33 tests] 6-instrument classifier
├── config/
│   └── processing_tiers.py       [330 lines] EXPRESS/STANDARD/PREMIUM/BATCH
└── tests/                        [200+ tests] Comprehensive test suite
```

### 1.2 Integration Flow

```
[API Request]
     │
     ▼
blueprint_async_router.py ─────► asyncio.to_thread()
     │
     ▼
BlueprintOrchestrator.process_file()
     │
     ▼
Phase3Vectorizer.extract() ─────► dual_pass_extraction()
     │                                   │
     │                                   ├── MLContourClassifier
     │                                   ├── PrimitiveDetector  
     │                                   └── OCR dimension extraction
     │
     ▼
export_to_dxf() ◄───── [MISSING: validate_scale_before_export()]
     │
     ▼
[DXF Output R12/R2000]
```

### 1.3 What Is Wired (Working)

| Component | Status | Location |
|-----------|--------|----------|
| Phase 3 Vectorizer | COMPLETE | `vectorizer_phase3.py` |
| Phase 4 Leader Lines | COMPLETE | `phase4/pipeline.py` (100 tests passing) |
| OCR Dimension Extraction | COMPLETE | `extract_dimensions.py` |
| DXF Export (R12/R2000) | COMPLETE | `dxf_compat.py` |
| ML Classification | COMPLETE | `MLContourClassifier` with sklearn |
| Processing Tiers | COMPLETE | EXPRESS/STANDARD/PREMIUM/BATCH |

### 1.4 What Exists But Is NOT Wired (Critical Gap)

| Component | Files | Problem | Impact |
|-----------|-------|---------|--------|
| **Calibration Pipeline** | `calibration/*.py` (1,450 lines) | Never instantiated in vectorizer flow | Scale detection relies on heuristics |
| **Scale Validation Gate** | `vectorizer_phase3.py:2327` | Function exists but NOT CALLED before export | 2.5x scale errors not prevented |
| **FeedbackSystem** | `vectorizer_phase3.py:1181` | Class defined, no caller | No user feedback collection |
| **TrainingDataCollector** | `vectorizer_phase3.py:1273` | Class defined, no caller | No model retraining |

### 1.5 Approved Architecture Not Implemented

Per CLAUDE.md (lines 218-556), the following architecture was approved but not built:

**Three-Loop Feedback Architecture:**

| Loop | Purpose | Status |
|------|---------|--------|
| **Loop 1** | Intra-frame validation (retry with fallback strategies) | PARTIAL - gate exists, not wired |
| **Loop 2** | Cross-image strategy caching (image_signature → strategy) | NOT STARTED |
| **Loop 3** | User correction retraining (FeedbackSystem + TrainingDataCollector) | NOT STARTED |

**AGE Integration (Agentic Guidance Engine):**
- Pattern exists in `tap_tone_pi/tap_tone/analyzer_guidance_engine.py`
- Should sit above Loop 1 for Claude API-driven strategy selection
- NOT STARTED

### 1.6 Current Blocking Issues

| Issue | Root Cause | Solution | Effort |
|-------|-----------|----------|--------|
| **2.5x Scale Errors** | `validate_scale_before_export()` not called | Wire into orchestrator before `export_to_dxf()` | 30 min |
| **148 Open Endpoints** | Edge detection noise + genuine discontinuities | Implement segmentation-first extraction (flood fill) | 4 hours |
| **Calibration Unused** | Pipeline never instantiated | Create `VectorizerWithCalibration` wrapper | 2 hours |
| **No Feedback Loop** | Classes exist, no wiring | Wire FeedbackSystem to correction endpoint | 2 hours |

### 1.7 Key Entry Points

**Standalone Python:**
```python
from services.blueprint_import.vectorizer_phase3 import Phase3Vectorizer
vectorizer = Phase3Vectorizer()
result = vectorizer.extract("blueprint.pdf", target_height_mm=500)
vectorizer.export_to_dxf(result.contours, "output.dxf")
```

**Via API:**
```bash
curl -X POST http://localhost:8000/api/blueprint/vectorize/async \
  -F "file=@blueprint.pdf" \
  -F "target_height_mm=500"
```

**Testing:**
```bash
pytest services/blueprint-import/tests/ -v
pytest services/api/tests/test_blueprint*.py -v
```

### 1.8 Priority Actions (Blueprint Vectorizer)

| Priority | Action | Impact | Effort |
|----------|--------|--------|--------|
| **P1** | Wire scale validation gate | Prevents 2.5x errors | 30 min |
| **P2** | Integrate calibration pipeline | Auto-corrects scale | 2 hours |
| **P3** | Implement Loop 2 (strategy caching) | Faster repeat processing | 1 hour |
| **P4** | Wire feedback loop (Loop 3) | Enables model improvement | 2 hours |
| **P5** | Segmentation-first extraction | Closes 148 open endpoints | 4 hours |
| **P6** | AGE integration | AI-driven strategy selection | 4 hours |

---

## Part 2: Photo Vectorizer (SUSPENDED)

### 2.1 Suspension Status

**Formal Decision:** Sprint 4 (April 16, 2026)  
**Document:** `docs/audits/SUPERSESSION_AND_ORPHAN_AUDIT_RESULTS.md`  
**Verdict:** "Photo vectorizer is set aside. **InstrumentBodyGenerator is the forward path.**"

### 2.2 System Architecture

```
services/photo-vectorizer/
├── photo_vectorizer_v2.py        [4,606 lines] Main orchestrator (SUPERSEDED)
├── edge_to_dxf.py                [2,350 lines] Edge-to-DXF converter (ACTIVE)
├── light_line_body_extractor.py  [522 lines]  Blueprint extraction (LIVE)
├── cognitive_extraction_engine.py [1,223 lines] AI pipeline (SUSPENDED)
├── cognitive_extractor.py        [1,424 lines] AI extraction (SUSPENDED)
├── contour_stage.py              [522 lines]  Contour extraction (SUSPENDED)
├── contour_plausibility.py       [329 lines]  Body ownership scoring (SUSPENDED)
├── geometry_coach_v2.py          [759 lines]  ML coaching (SCAFFOLDED for IBG)
└── tests/                        [277 tests]  Comprehensive but suspended
```

### 2.3 Path Status

| Path | Status | Notes |
|------|--------|-------|
| **Blueprint Path** | LIVE | `light_line_body_extractor.py` remains operational |
| **Photo Path** | SUSPENDED | Poor results on L-1 images, 52% dimensional errors |
| **AI Path** | SUSPENDED | Poor results on DALL-E/Midjourney renders |

### 2.4 What Remains Production-Viable

**edge_to_dxf.py** (2,350 lines):
- High-fidelity edge-to-DXF converter
- R12 format for maximum compatibility
- Entity caps: 5M per image, 12M aggregate batch
- CLI tool + API integration complete
- **Status:** ACTIVE and production-ready

```bash
# CLI usage
python edge_to_dxf.py "image.jpg" -o output.dxf --height 500

# API endpoint
POST /api/blueprint/edge-to-dxf
```

### 2.5 Blocking Issues (If Resuming)

| Priority | Issue | Impact | Effort |
|----------|-------|--------|--------|
| **1** | Scale calibration broken | Every output has wrong dimensions | Small |
| **2** | Reference object false positives | Knobs trigger coin detection | Small |
| **3** | Contour deduplication missing | Inner/outer edge traces duplicated | Small |
| **4** | FeatureClassifier too simplistic | Overlapping size ranges cause misclassification | Medium |

### 2.6 Recommendation

**Do NOT resume photo vectorizer development** unless:
1. IBG forward path proves insufficient for the use case
2. All 4 blocking issues are addressed
3. Clear product requirement for photo-to-vector workflow

**Instead:** Focus on IBG (InstrumentBodyGenerator) which is the architectural successor.

---

## Part 3: Development Sandboxes

### 3.1 Sandbox Inventory

| Sandbox | Location | Items | Purpose | Status |
|---------|----------|-------|---------|--------|
| **Arc Reconstructor** | `sandbox/arc_reconstructor/` | 71 | Gap bridging R&D | Active research |
| **Text Geometry Eval** | `services/blueprint-import/sandbox/text_geometry_eval/` | 64 | Phase 2 verification | Active testing |
| **Photo Live Test** | `services/photo-vectorizer/live_test_output/` | 249 | Photo vectorizer tests | Suspended |
| **Benchmark Outputs** | `benchmark_outputs/` | 28 | Gap closure params | Reference |
| **Phase 4 Output** | `phase4_output/` | 95 | Historical | Archive |
| **API Comparisons** | `services/api/test_temp/sandbox_vs_engineer_comparison/` | 30 | Validation | Active |

**Total:** 672 items across 12 directories

### 3.2 Arc Reconstructor (Research Highlight)

**Location:** `sandbox/arc_reconstructor/`  
**Achievement:** Demonstrated Tier 0 reference bridging + 56.7% arc promotion

**Key Files:**
- `arc_reconstructor.py` - Core gap-bridging engine
- `reference_outline_bridge.py` - Tier 0 solver using body_outlines.json
- `SESSION_AUDITS.md` - **CRITICAL:** 485-line development audit trail

**Four-Tier Gap Bridging:**
| Tier | Method | Source |
|------|--------|--------|
| 0 | Reference outline | body_outlines.json waypoints |
| 1 | Measured radius | Adjacent chain curvature |
| 2 | Spherical arch formula | arch_radius_mm + body_height_mm |
| 3 | Zone lookup table | Fallback |

**Status:** Sandbox-only, NOT production. Integration decision pending.

### 3.3 Text Geometry Evaluation (Decision Quality)

**Location:** `services/blueprint-import/sandbox/text_geometry_eval/`  
**Purpose:** Verify Phase 2 vectorizer meets 95% text legibility threshold

**Success Criteria:**
- Text legibility: >= 95% word recovery rate (OCR comparison)
- Geometry score: >= 2/3 checks pass (closure, aspect ratio, continuity)

**Pipeline Variants Under Test:**
| Runner | Pipeline | Status |
|--------|----------|--------|
| `run_phase2_dark_lines.py` | Phase 2 auto_threshold | **Expected winner** |
| `run_phase2_simple.py` | Phase 2 simple mode | Baseline |
| `run_phase3_smart.py` | Phase 3 ML classifier | Reference |
| `run_edge_to_dxf_refined.py` | EdgeToDXF REFINED | Production default |

### 3.4 Artifacts to Preserve

| Artifact | Location | Reason |
|----------|----------|--------|
| `SESSION_AUDITS.md` | sandbox/arc_reconstructor/ | Complete development audit trail |
| `text_geometry_eval/` | services/blueprint-import/sandbox/ | Decision-quality corpus |
| `DEVELOPER_HANDOFF.md` | services/photo-vectorizer/ | Architecture + blocking issues |
| `live_test_output/` | services/photo-vectorizer/ | 30 test cases, 249 items |
| `evaluation_results.json` | text_geometry_eval/outputs/ | 95% legibility decision data |

---

## Part 4: Dependencies & Configuration

### 4.1 External Libraries

| Library | Version | Use Case |
|---------|---------|----------|
| `opencv-python` | Latest | Edge detection, contour extraction |
| `numpy` | Latest | Numerical operations |
| `ezdxf` | Latest | DXF generation |
| `scikit-learn` | Latest | ML classifier (optional, graceful fallback) |
| `pytesseract` / `easyocr` | Latest | OCR dimension extraction |
| `pdf2image` / `PyMuPDF` | Latest | PDF rasterization |
| `rembg` | Latest | Background removal (optional) |
| `anthropic` | Latest | Claude API for analysis |

### 4.2 Configuration Files

| File | Purpose |
|------|---------|
| `config/processing_tiers.py` | EXPRESS/STANDARD/PREMIUM/BATCH definitions |
| `data_registry/edition/cnc_blueprints/blueprint_standards.json` | Instrument specs |
| `classifiers/grid_zone/zones.py` | Grid zone configurations |
| `classifiers/latin_american/instruments.py` | Latin American instruments |

### 4.3 DXF Format Configuration

| Tier | Format | Entities | Verified |
|------|--------|----------|----------|
| Free | R12 (AC1009) | LINE only | Yes |
| Paid | R2000 (AC1015) | LWPOLYLINE | DWG TrueView 2026 + GRBL pipeline |

---

## Part 5: Governance & Documentation

### 5.1 Master Documents

| Document | Location | Purpose |
|----------|----------|---------|
| **CLAUDE.md** | repo root | Vectorizer architecture decisions (lines 218-556) |
| **VECTORIZER_UPGRADE_PLAN.md** | docs/ | Roadmap + 8.0/10 maturity rating |
| **BLUEPRINT_READER_PROTECTION_RULES.md** | docs/governance/ | Governance policy |
| **THREE_LOOP_ARCHITECTURE_REFRAMED.md** | docs/governance/ | Loop architecture |
| **SUPERSESSION_AND_ORPHAN_AUDIT_RESULTS.md** | docs/audits/ | Photo vectorizer suspension |

### 5.2 Related Handoffs

| Document | Date | Content |
|----------|------|---------|
| `EDGE_TO_DXF_API_MIGRATION_HANDOFF.md` | 2026-04 | edge_to_dxf integration |
| `VECTOR_1A_DXF_COMPLIANCE_CLOSEOUT.md` | 2026-04 | R&D sandbox status |
| `VECTOR_1B_LOOP2_PROVENANCE_AUDIT.md` | 2026-04 | Photo vectorizer classification |

---

## Part 6: Quick Reference

### 6.1 Where to Find Key Logic

| Logic | Location |
|-------|----------|
| **Scale Detection** | `vectorizer_phase3.py:1071` (ScaleDetector class) |
| **Scale Validation** | `vectorizer_phase3.py:2327` (validate_scale_before_export) |
| **ML Classification** | `vectorizer_phase3.py:773` (MLContourClassifier) |
| **OCR Dimensions** | `extract_dimensions.py` |
| **Leader Lines** | `phase4/arrow_detector.py` + `leader_associator.py` |
| **Calibration** | `calibration/pixel_calibrator.py` (UNINTEGRATED) |
| **Feedback Loop** | `vectorizer_phase3.py:1181` (FeedbackSystem, NEVER CALLED) |

### 6.2 Test Commands

```bash
# Blueprint vectorizer tests
pytest services/blueprint-import/tests/ -v

# Phase 4 dimension linking tests
pytest services/blueprint-import/tests/test_arrow_detector.py -v  # 33 tests
pytest services/blueprint-import/tests/test_leader_associator.py -v  # 35 tests

# API integration tests
pytest services/api/tests/test_blueprint*.py -v

# Photo vectorizer tests (SUSPENDED)
pytest services/photo-vectorizer/tests/ -v  # 277 tests
```

### 6.3 Development Priority Matrix

| Effort | Impact | Action |
|--------|--------|--------|
| Small | High | Wire scale validation gate |
| Small | High | Integrate calibration pipeline |
| Small | Medium | Implement strategy caching (Loop 2) |
| Medium | Medium | Wire feedback loop (Loop 3) |
| Medium | High | Segmentation-first extraction |
| Large | High | AGE integration |

---

## Handoff Checklist

- [x] Blueprint vectorizer architecture documented (68 modules, 25,000 lines)
- [x] Photo vectorizer suspension status confirmed
- [x] Unintegrated subsystems identified (calibration, feedback, training)
- [x] Critical issues documented (scale validation, 148 open endpoints)
- [x] Approved architecture gaps noted (3-loop feedback, AGE)
- [x] Sandbox inventory completed (672 items, 12 directories)
- [x] Test coverage mapped (200+ blueprint, 277 photo)
- [x] Priority actions ranked
- [x] Key file locations indexed
- [x] Governance documents referenced

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2026-05-13 | Code Audit | Initial comprehensive handoff document |

---

**End of Document**
