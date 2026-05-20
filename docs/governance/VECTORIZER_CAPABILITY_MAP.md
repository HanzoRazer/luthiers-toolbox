# Vectorizer Capability Map

**Date:** 2026-05-20  
**Status:** ARCHAEOLOGY_COMPLETE  
**Sprint:** Vectorizer Technical Debt Archaeology

---

## Vectorizer Modes Inventory

### CleanupMode Enum (API-Exposed Modes)

| Mode | Entrypoint | DXF Output | Topology Quality | Known Issues | Status |
|------|------------|------------|------------------|--------------|--------|
| `refined` | `extract_blueprint_to_dxf()` | R12 LINE | Good | Border fallback selection | **CANONICAL** |
| `baseline` | `clean_blueprint_dxf()` baseline | R12 LINE | Good | No 5-tier fallback | **CANONICAL** |
| `restored_baseline` | RETR_LIST extraction | R12 LINE | Variable | 189 layers vs 1 | CANONICAL |
| `v2_raw` | `Phase3Vectorizer._raw_extract()` | R12 LINE | Excellent | Text intact | **CANONICAL_RECOVERY** |
| `photo_v2` | `EdgeToDXF.convert_enhanced()` | R12 LINE | Good | Text masked out | **CANONICAL_RECOVERY** |
| `photo_refined` | `EdgeToDXF.convert()` kernel=0 | R12 LINE | Good | Higher entity count | CANONICAL_RECOVERY |
| `layered_dual_pass` | `extract_dual_pass()` | R12/R2000 | Variable | Pass B stub | EXPERIMENTAL |
| `enhanced` | `extract_blueprint_enhanced()` | R12 LINE | High detail | 50k-300k entities | PRODUCTION |
| `cam_ready_r2000` | `Phase3Vectorizer(R2000)` | R2000 LWPOLYLINE | CAM-ready | Auth required | PRODUCTION |

### ExtractionMode Enum (Phase3 Internal)

| Mode | Method | Behavior | Status |
|------|--------|----------|--------|
| `SMART` | `extract()` default | ML classification, OCR | Active |
| `SIMPLE` | `_simple_extraction()` | All contours, no ML | **BROKEN** (UNKNOWN excluded) |

---

## Subsystem Capabilities

### Body Isolation Systems

| System | Location | Canonical | Active | Tested | Risk |
|--------|----------|-----------|--------|--------|------|
| `BodyIsolationStage` | photo-vectorizer/body_isolation_stage.py | Yes | Yes | Yes | Low |
| `BodyIsolationResult` | photo-vectorizer/body_isolation_result.py | Yes | Yes | Yes | Low |
| `artifact_body_evidence_adapter.py` | api/ibg/morphology_harvest/ | Advisory | Yes | Yes | Medium |
| `ContourPlausibilityScorer` | photo-vectorizer/contour_plausibility.py | Yes | Yes | Yes | Low |

### Contour Reconstruction Systems

| System | Location | Canonical | Active | Tested | Risk |
|--------|----------|-----------|--------|--------|------|
| `arc_reconstructor.py` | api/ibg/ | Standalone | Yes | No | Medium |
| `contour_reconstruction.py` | api/routers/blueprint_cam/ | Yes | Yes | Yes | Low |
| `topology_recovery.py` | api/ibg/workflow/ | Yes | Yes | Yes | Low |
| Gap closing in `blueprint_clean.py` | api/services/ | Yes | Yes | Implicit | Low |

### DXF Generation Systems

| System | Location | Format | Canonical | Notes |
|--------|----------|--------|-----------|-------|
| `dxf_compat.py` | blueprint-import | R12/R2000 | **Yes** | All DXF MUST route here |
| `dxf_postprocessor.py` | blueprint-import | Any | Optional | CAM-ready post-processing |
| `unified_dxf_cleaner.py` | api/cam/ | Any | Downstream | Layer consolidation |
| `layer_consolidator.py` | api/cam/ | Any | Downstream | CAM workflow |

### Semantic Scoring Systems

| System | Location | Canonical | Active | Tested | Risk |
|--------|----------|-----------|--------|--------|------|
| `contour_scoring.py` | api/services/ | Yes | Yes | Yes | Low |
| `contour_plausibility.py` | photo-vectorizer | Yes | Yes | Yes | Low |
| `contour_election.py` | photo-vectorizer | Yes | Yes | Yes | Low |
| `contour_recommendation.py` | api/services/ | Yes | Yes | Yes | Low |

### Calibration Systems

| System | Location | Canonical | Active | Tested | Risk |
|--------|----------|-----------|--------|--------|------|
| `pixel_calibrator.py` | blueprint-import/calibration/ | Yes | Yes | Yes | Low |
| `scale_detector.py` | blueprint-import/calibration/ | Yes | Yes | No | Medium |
| `calibration_integration.py` | blueprint-import | **ORPHAN** | No | No | **High** |
| `ScaleCalibrator` | vectorizer_enhancements.py | Optional | Yes | No | Medium |

### Coaching / Retry Systems

| System | Location | Canonical | Active | Tested | Risk |
|--------|----------|-----------|--------|--------|------|
| `geometry_coach.py` | photo-vectorizer | Superseded | Rarely | Yes | Medium |
| `geometry_coach_v2.py` | photo-vectorizer | Yes | Yes | Yes | Low |
| Retry profiles | body_isolation_stage.py | Yes | Yes | Yes | Low |

---

## Operational Capability Audit

### Does It Actually Work?

| Subsystem | Works? | Conditions | Wired? | Tested? | Canonical? |
|-----------|--------|------------|--------|---------|------------|
| V2_RAW mode | **Yes** | PDF input | Yes | Yes | Yes |
| PHOTO_V2 mode | **Yes** | Image input | Yes | Yes | Yes |
| SIMPLE extraction | **No** | — | Partial | No | No |
| Phase 4 dimension linking | Unknown | Standalone | No | Yes | No |
| Feedback retraining | **No** | Never called | No | No | No |
| Calibration integration | **No** | Never called | No | No | No |
| Body isolation | **Yes** | Photo pipeline | Yes | Yes | Yes |
| Arc reconstruction | **Yes** | Gap bridging | Yes | Yes | Yes |
| IBG intake gate | **Yes** | Constitutional | Yes | Yes | Yes |

### Runtime Evidence

| Capability | Evidence Source | Date |
|------------|-----------------|------|
| V2_RAW produces clean DXF | User visual confirmation | 2026-05-12 |
| PHOTO_V2 generates DXF | Runtime test artifact | 2026-05-12 |
| Body isolation retry works | Test suite passes | Continuous |
| IBG gate blocks invalid | Constitutional tests | 2026-05-18 |

---

## Capability Gaps

| Gap | Impact | Priority |
|-----|--------|----------|
| `calibration_integration.py` not wired | Scale accuracy limited | Medium |
| `FeedbackSystem` not triggered | No learning from corrections | Low |
| `_simple_extraction()` broken | Non-guitar instruments fail | High |
| Phase 4 not integrated | Manual dimension annotation | Low |
| `cognitive_*` orphaned | Dead code risk | Medium |

---

*Vectorizer Capability Map — Archaeology Complete — 2026-05-20*
