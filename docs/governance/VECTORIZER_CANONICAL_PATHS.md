# Vectorizer Canonical Paths

**Date:** 2026-05-20  
**Status:** ARCHAEOLOGY_COMPLETE  
**Sprint:** Vectorizer Technical Debt Archaeology

---

## Overview

This document identifies the TRUE production intake paths for the vectorizer ecosystem.
Paths are classified as:

- **CANONICAL_PRODUCTION** — Active production path, user-facing
- **CANONICAL_RECOVERY** — Protected experimental recovery modes (MRP-1C)
- **DEVELOPMENT_ONLY** — Dev/staging environment only
- **DEBUG_TOOL** — Manual debugging, not production
- **ORPHAN** — Code exists but never wired
- **ABANDONED** — Superseded or broken

---

## Frontend Intake Points

| Path | Classification | API Endpoint | Modes |
|------|----------------|--------------|-------|
| `hostinger/blueprint-reader.html` | **CANONICAL_PRODUCTION** | `/api/blueprint/vectorize/async` | v2_raw, refined, baseline |
| `hostinger/blueprint-reader.html` | **CANONICAL_PRODUCTION** | `/api/vectorizer/extract` | photo_v2, auto, ai, photo, blueprint |
| `packages/client/src/composables/useBlueprintWorkflow.ts` | DEVELOPMENT_ONLY | Multiple (phase2, phase3, silhouette) | Various |
| `hostinger/body-outline-editor.html` | DEBUG_TOOL | None (manual editing) | N/A |

---

## API Endpoint Paths

### Primary Vectorize Endpoint

```
POST /api/blueprint/vectorize
```

**Router:** `services/api/app/routers/blueprint/vectorize_router.py`  
**Orchestrator:** `services/api/app/services/blueprint_orchestrator.py`  
**Classification:** CANONICAL_PRODUCTION

**Mode Routing:**

| Mode Parameter | Orchestrator Route | Extraction Path | Status |
|----------------|-------------------|-----------------|--------|
| `refined` (default) | `extract_blueprint_to_dxf()` | Blueprint Reader pipeline | CANONICAL_PRODUCTION |
| `baseline` | `clean_blueprint_dxf()` baseline branch | Simpler pre-grouping | CANONICAL_PRODUCTION |
| `restored_baseline` | `extract_blueprint_to_dxf()` RETR_LIST | Historical 86c49526 behavior | CANONICAL_PRODUCTION |
| `v2_raw` | `Phase3Vectorizer._raw_extract()` | March 2026 fidelity | **CANONICAL_RECOVERY** |
| `photo_v2` | `EdgeToDXF.convert_enhanced()` | Multi-scale Canny | **CANONICAL_RECOVERY** |
| `photo_refined` | `EdgeToDXF.convert()` morph_close_kernel=0 | Text-preserving photo | **CANONICAL_RECOVERY** |
| `layered_dual_pass` | `extract_dual_pass()` | Phase 4 layer building | EXPERIMENTAL |
| `enhanced` | `extract_blueprint_enhanced()` | Multi-scale fusion (50k-300k entities) | PRODUCTION |
| `cam_ready_r2000` | `Phase3Vectorizer(dxf_version='R2000')` | Paid tier LWPOLYLINE | PRODUCTION (auth required) |

### Photo Vectorizer Endpoint

```
POST /api/vectorizer/extract
```

**Router:** `services/api/app/routers/photo_vectorizer_router.py`  
**Orchestrator:** `services/api/app/services/photo_orchestrator.py`  
**Source:** `services/photo-vectorizer/photo_vectorizer_v2.py`  
**Classification:** CANONICAL_PRODUCTION

**Source Type Routing:**

| source_type | Pipeline | Status |
|-------------|----------|--------|
| `auto` | Auto-detect photo vs AI | CANONICAL_PRODUCTION |
| `photo` | 12-stage photo pipeline | CANONICAL_PRODUCTION |
| `ai` | 4-stage AI render pipeline | CANONICAL_PRODUCTION |
| `blueprint` | Gap closing + edge detection | CANONICAL_PRODUCTION |
| `silhouette` | Silhouette extraction | CANONICAL_PRODUCTION |

---

## Backend Extraction Systems

### services/blueprint-import/

| System | Entry Point | Classification | Notes |
|--------|-------------|----------------|-------|
| `vectorizer_phase3.py` | `Phase3Vectorizer.extract()` | **CANONICAL** | Primary blueprint extraction |
| `vectorizer_phase3.py:_raw_extract()` | Line 2838 | **CANONICAL_RECOVERY** | V2_RAW mode source |
| `vectorizer_phase3.py:_simple_extraction()` | Line 3766 | BROKEN | Exports empty (UNKNOWN excluded) |
| `vectorizer_phase2.py` | `VectorizerPhase2` | SUPERSEDED | No API wiring |
| `vectorizer_enhancements.py` | Optional import by phase3 | ACTIVE | Phase 3.7 features |
| `dxf_compat.py` | All DXF creation | **CANONICAL** | R12/R2000 abstraction |
| `phase4/` | Dimension linking | STANDALONE | Not integrated |
| `calibration_integration.py` | `EnhancedCalibrationPipeline` | PARTIAL | Wired to calibration routes, not main vectorize |

### services/photo-vectorizer/

| System | Entry Point | Classification | Notes |
|--------|-------------|----------------|-------|
| `photo_vectorizer_v2.py` | `PhotoVectorizerV2.extract()` | **CANONICAL** | Main photo extraction |
| `edge_to_dxf.py` | `EdgeToDXF.convert_enhanced()` | **CANONICAL** | PHOTO_V2 mode source |
| `body_isolation_stage.py` | `BodyIsolationStage` | **CANONICAL** | Stage 4.5 body isolation |
| `geometry_coach_v2.py` | `GeometryCoachV2` | ACTIVE | Retry logic |
| `cognitive_extractor.py` | Never imported | **ORPHAN** | High risk |
| `cognitive_extraction_engine.py` | Never imported | **ORPHAN** | High risk |
| `extract_body_grid_v*.py` (5 files) | None | **ABANDONED** | Never wired |

---

## Canonical Path Trace

### Blueprint PDF Intake (Production)

```
blueprint-reader.html
    ↓ POST /api/blueprint/vectorize/async (mode=v2_raw)
    ↓
vectorize_router.py → BlueprintOrchestrator.process_file()
    ↓ CleanupMode.V2_RAW branch
    ↓
Phase3Vectorizer._raw_extract()
    ↓ CHAIN_APPROX_NONE, no classification
    ↓
dxf_compat.create_document() → R12 DXF
    ↓
Response: { artifacts: { dxf: { base64: "..." } } }
```

### Photo Image Intake (Production)

```
blueprint-reader.html (Photo mode toggle)
    ↓ POST /api/vectorizer/extract (source_type=auto)
    ↓
photo_vectorizer_router.py → PhotoOrchestrator.process()
    ↓
PhotoVectorizerV2.extract()
    ↓ 12-stage pipeline or 4-stage AI pipeline
    ↓
Response: { artifacts: { svg: {...}, dxf: {...} } }
```

---

## Not Wired / Orphan Systems

| System | Location | Reason |
|--------|----------|--------|
| `calibration_integration.py` | blueprint-import | Wired to calibration routes only (not main vectorize) |
| `FeedbackSystem.record_classification` | vectorizer_phase3.py:1181 | Called in SMART mode with enable_feedback=True |
| `FeedbackSystem.submit_correction` | vectorizer_phase3.py | **NEVER CALLED** — user feedback intake dead |
| `TrainingDataCollector` | vectorizer_phase3.py:1273 | Never instantiated |
| `phase4/` directory | blueprint-import | Complete but standalone |
| `cognitive_extractor.py` | photo-vectorizer | Never imported |
| `cognitive_extraction_engine.py` | photo-vectorizer | Never imported |
| `extract_body_grid_v*.py` | photo-vectorizer | 5 abandoned versions |

---

## Verification Evidence

| Path | Verified Method | Date |
|------|-----------------|------|
| V2_RAW mode | Runtime test + visual inspection | 2026-05-12 |
| PHOTO_V2 mode | Runtime test (DXF generated) | 2026-05-12 |
| blueprint-reader.html | Static analysis + API trace | 2026-05-20 |
| OrphanSystems | Grep for imports (0 found) | 2026-05-20 |

---

*Vectorizer Canonical Paths Inventory — Archaeology Complete — 2026-05-20*
