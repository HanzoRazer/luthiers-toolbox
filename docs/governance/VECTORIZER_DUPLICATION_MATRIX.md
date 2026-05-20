# Vectorizer Duplication Matrix

**Date:** 2026-05-20  
**Status:** ARCHAEOLOGY_COMPLETE  
**Sprint:** Vectorizer Technical Debt Archaeology

---

## Overview

This document maps duplicate or parallel implementations across the vectorizer ecosystem.

---

## Code Duplication

### Contour Hierarchy Logic

| Location A | Location B | Duplication | Risk |
|------------|------------|-------------|------|
| `photo-vectorizer/edge_to_dxf.py:419` | `api/services/contour_hierarchy.py` | Full duplication | **High** |

**Evidence:** TODO comment at line 419:
```python
# TODO: Consolidate with services/api/app/services/contour_hierarchy.py
```

**Recommendation:** Extract shared contour hierarchy module.

### ExtractedShape / BodyIsolationResult

| Location A | Location B | Duplication | Risk |
|------------|------------|-------------|------|
| `photo-vectorizer/photo_vectorizer_v2.py` | `photo-vectorizer/_experimental/ai_photo_path/ai_extractor.py` | `ExtractedShape` copied | Low |

**Assessment:** Experimental code duplicates production data structure. Low risk since experimental is not wired.

### Cognitive Extractors

| Location A | Location B | Duplication | Risk |
|------------|------------|-------------|------|
| `photo-vectorizer/cognitive_extractor.py` | `photo-vectorizer/cognitive_extraction_engine.py` | Parallel implementations | **High** |

**Assessment:** Two 1400+ LOC files with similar purposes. Both orphaned (never imported). High dead code risk.

---

## Version Proliferation

### Extract Body Grid (5 versions)

| Version | File | Status | Differences |
|---------|------|--------|-------------|
| v1 | `extract_body_grid.py` | Abandoned | Original |
| v2 | `extract_body_grid_v2.py` | Abandoned | Unknown |
| v3 | `extract_body_grid_v3.py` | Abandoned | Unknown |
| v4 | `extract_body_grid_v4.py` | Abandoned | Unknown |
| v5 | `extract_body_grid_v5.py` | Abandoned | Soundhole fill |

**Assessment:** 5 abandoned iterations. None wired to production. Should be archived.

### Geometry Coach (2 versions)

| Version | File | Status | Usage |
|---------|------|--------|-------|
| v1 | `geometry_coach.py` | Superseded | Rarely used |
| v2 | `geometry_coach_v2.py` | Canonical | Active |

**Assessment:** v2 is canonical. v1 should be deprecated explicitly or removed.

### Photo Vectorizer Naming

| Name | Version | Status |
|------|---------|--------|
| `photo_vectorizer_v2.py` | Docstring says "v3.0" | **Canonical** |

**Assessment:** File named v2 but docstring says v3.0. Misleading.

---

## Overlapping Systems

### Border Detection

| System | Location | Scope |
|--------|----------|-------|
| Extraction-stage border removal | `edge_to_dxf.py` | Photo pipeline |
| Cleanup-stage border removal | `blueprint_clean.py:352` | Blueprint pipeline |
| Contour plausibility border check | `contour_plausibility.py` | Photo pipeline |

**Assessment:** Border detection implemented at multiple stages. Intentional redundancy for defense-in-depth.

### Scale Detection

| System | Location | Method |
|--------|----------|--------|
| `ScaleCalibrator` | vectorizer_enhancements.py | Rule-based |
| `pixel_calibrator.py` | blueprint-import/calibration/ | Multi-method |
| `scale_detector.py` | blueprint-import/calibration/ | Feature detection |
| `BlueprintAnalyzer` | blueprint-import/analyzer.py | Claude vision |

**Assessment:** Multiple scale detection methods. `calibration_integration.py` is **PARTIAL** (calibration API routes only; not on main `BlueprintOrchestrator` vectorize). See `VECTORIZER_COMPONENT_LIFECYCLE.md`.

### DXF Output

| System | Location | Format | Scope |
|--------|----------|--------|-------|
| `dxf_compat.py` | blueprint-import | R12/R2000 | **Canonical** |
| `export_to_dxf()` | vectorizer_phase3.py | Uses dxf_compat | Phase 3 |
| `EdgeToDXF` export | edge_to_dxf.py | Uses dxf_compat | Photo |
| `dxf_postprocessor.py` | blueprint-import | Post-processing | Optional |

**Assessment:** All DXF generation correctly routes through `dxf_compat.py`. No duplication.

---

## Service Boundary Overlap

### services/blueprint-import vs services/photo-vectorizer

| Capability | blueprint-import | photo-vectorizer |
|------------|------------------|------------------|
| PDF extraction | `vectorizer_phase3.py` (fitz) | N/A |
| Edge detection | Canny in phase3 | Multi-scale Canny in edge_to_dxf |
| ML classification | Optional sklearn | N/A |
| Body isolation | N/A | `body_isolation_stage.py` |
| DXF generation | `dxf_compat.py` | Uses blueprint-import's dxf_compat |
| Coaching/retry | N/A | `geometry_coach_v2.py` |

**Assessment:** Services have distinct responsibilities but share `dxf_compat.py` via sys.path manipulation.

### API Services vs Vectorizer Services

| Capability | api/services/ | vectorizer services |
|------------|---------------|---------------------|
| Contour scoring | `contour_scoring.py` | `contour_plausibility.py` |
| Recommendation | `contour_recommendation.py` | N/A |
| Orchestration | `blueprint_orchestrator.py` | N/A |
| Cleanup | `blueprint_clean.py` | N/A |

**Assessment:** API layer orchestrates, vectorizer services extract. Clean separation.

---

## Duplication Risk Summary

| Duplication | Files Involved | Risk | Action |
|-------------|----------------|------|--------|
| Contour hierarchy | edge_to_dxf.py, contour_hierarchy.py | **High** | Extract shared module |
| Cognitive extractors | cognitive_extractor.py, cognitive_extraction_engine.py | **High** | Archive both |
| Grid extraction | 5 versions | Medium | Archive all |
| Geometry coach | v1, v2 | Low | Deprecate v1 |

---

## Recommendations

1. **CRITICAL:** Extract contour hierarchy logic to shared module used by both `edge_to_dxf.py` and `contour_hierarchy.py`.

2. **HIGH:** Archive or delete `cognitive_extractor.py` and `cognitive_extraction_engine.py` — both are 1400+ LOC orphaned files.

3. **MEDIUM:** Archive `extract_body_grid_v*.py` (5 files) — none wired, all abandoned.

4. **LOW:** Explicitly deprecate `geometry_coach.py` v1 in favor of v2.

5. **LOW:** Rename `photo_vectorizer_v2.py` to match its actual version (v3) or update docstring.

---

*Vectorizer Duplication Matrix — Archaeology Complete — 2026-05-20*
