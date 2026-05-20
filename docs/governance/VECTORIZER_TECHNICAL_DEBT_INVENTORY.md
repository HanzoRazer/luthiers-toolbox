# Vectorizer Technical Debt Inventory

**Date:** 2026-05-20  
**Status:** ARCHAEOLOGY_COMPLETE  
**Sprint:** Vectorizer Technical Debt Archaeology

---

## Overview

Structured inventory of technical debt in the vectorizer ecosystem, classified by severity and impact domain.

---

## Debt Severity Classification

| Severity | Definition |
|----------|------------|
| **CRITICAL** | Actively harmful or blocking production quality |
| **HIGH** | Significant risk or major maintenance burden |
| **MEDIUM** | Noticeable impact on reliability or velocity |
| **LOW** | Minor cleanup, cosmetic, or documentation |

## Impact Domains

| Domain | Description |
|--------|-------------|
| **topology** | Contour/geometry correctness |
| **semantic** | Classification and interpretation accuracy |
| **dxf_integrity** | DXF output validity |
| **performance** | Speed and resource usage |
| **maintainability** | Code clarity and future changes |
| **authority_risk** | Semantic authority contamination |
| **regression_risk** | Probability of breaking changes |

---

## CRITICAL Severity

| Debt Item | Location | Domain | Issue | Recommendation |
|-----------|----------|--------|-------|----------------|
| `_simple_extraction()` exports empty DXF | vectorizer_phase3.py:3766 | **topology** | UNKNOWN category excluded by export | Fix export to include UNKNOWN or add category |
| `submit_correction()` never called | vectorizer_phase3.py | **authority_risk** | User feedback intake path dead | Wire to API or remove |
| `TrainingDataCollector` never instantiated | vectorizer_phase3.py:1273 | **authority_risk** | ML model cannot learn from corrections | Wire to API or remove |

**Corrected (2026-05-20 verification):**
- `calibration_integration.py` — Downgraded to MEDIUM. Wired to calibration API routes (`calibration_router`, `phase2_router`), not main vectorize orchestrator.
- `FeedbackSystem.record_classification()` — Partially wired in SMART mode with `enable_feedback=True`. Only `submit_correction()` is dead.

---

## HIGH Severity

| Debt Item | Location | Domain | Issue | Recommendation |
|-----------|----------|--------|-------|----------------|
| Contour hierarchy duplication | edge_to_dxf.py:419 | **maintainability** | Duplicates contour_hierarchy.py | Extract shared module |
| `cognitive_extractor.py` orphaned | photo-vectorizer/ | **regression_risk** | 1400+ LOC dead code | Archive |
| `cognitive_extraction_engine.py` orphaned | photo-vectorizer/ | **regression_risk** | 1400+ LOC dead code | Archive |
| edge_to_dxf grouping fallback silent | edge_to_dxf.py:1294 | **topology** | Falls back to deprecated method on any exception | Add telemetry, fix exceptions |
| 5 abandoned grid extractors | photo-vectorizer/ | **maintainability** | extract_body_grid_v1-v5 never wired | Archive all |
| Phase 4 standalone | blueprint-import/phase4/ | **semantic** | Complete but not integrated | Integrate or document as future work |

---

## MEDIUM Severity

| Debt Item | Location | Domain | Issue | Recommendation |
|-----------|----------|--------|-------|----------------|
| `calibration_integration.py` partial wiring | blueprint-import/ | **semantic** | Wired to calibration routes only, not main vectorize orchestrator | Wire to main pipeline or document scope |
| Contour plausibility import fallback | contour_plausibility.py:10 | **semantic** | Border detection disabled silently | Add warning log |
| CleanupMode invalid input default | vectorize_router.py:195 | **maintainability** | Silent default to REFINED | Log warning |
| `geometry_coach.py` v1 not deprecated | photo-vectorizer/ | **maintainability** | v2 is canonical but v1 still exists | Deprecate v1 |
| `photo_vectorizer_v2.py` version mismatch | photo-vectorizer/ | **maintainability** | File says v2, docstring says v3.0 | Align naming |
| `vectorizer_phase2.py` superseded | blueprint-import/ | **maintainability** | No API wiring | Deprecate or archive |
| `light_line_body_extractor.py` unknown | photo-vectorizer/ | **regression_risk** | Status unknown, no imports found | Investigate and classify |
| `photo_silhouette_extractor.py` unknown | photo-vectorizer/ | **regression_risk** | Status unknown, no imports found | Investigate and classify |
| Scale detection fragmentation | Multiple files | **semantic** | 4+ scale detection systems | Consolidate via calibration_integration |

---

## LOW Severity

| Debt Item | Location | Domain | Issue | Recommendation |
|-----------|----------|--------|-------|----------------|
| Neural network boost TODO | classifiers/latin_american/classifier.py:503 | **semantic** | Incomplete feature | Complete or remove TODO |
| DEPRECATED comment | edge_to_dxf.py:261 | **maintainability** | Method marked deprecated but kept | Remove or document why kept |
| Optional dep print statements | cognitive_extraction_engine.py:1491 | **maintainability** | Uses print() instead of logger | Convert to logger.info |
| March pipeline restore orphaned | march_pipeline_restore.py | **maintainability** | Restoration script never integrated | Archive |
| Archive references in specs | gibson_sg.json, gibson_explorer.json | **maintainability** | Reference archived files | Update paths or document |

---

## Debt by Impact Domain

### Topology Impact (3 items)

| Item | Severity | Location |
|------|----------|----------|
| `_simple_extraction()` broken export | CRITICAL | vectorizer_phase3.py |
| edge_to_dxf grouping fallback | HIGH | edge_to_dxf.py |
| Body isolation best-effort return | MEDIUM | body_isolation_stage.py |

### Semantic Interpretation Impact (4 items)

| Item | Severity | Location |
|------|----------|----------|
| `calibration_integration.py` orphaned | CRITICAL | blueprint-import |
| Phase 4 standalone | HIGH | blueprint-import/phase4 |
| Contour plausibility import fallback | MEDIUM | contour_plausibility.py |
| Scale detection fragmentation | MEDIUM | Multiple |

### Authority Risk Impact (2 items)

| Item | Severity | Location |
|------|----------|----------|
| `FeedbackSystem` never triggered | CRITICAL | vectorizer_phase3.py |
| `TrainingDataCollector` never triggered | CRITICAL | vectorizer_phase3.py |

### Maintainability Impact (10 items)

| Item | Severity | Location |
|------|----------|----------|
| Contour hierarchy duplication | HIGH | edge_to_dxf.py |
| cognitive_extractor.py orphaned | HIGH | photo-vectorizer |
| cognitive_extraction_engine.py orphaned | HIGH | photo-vectorizer |
| 5 abandoned grid extractors | HIGH | photo-vectorizer |
| geometry_coach v1 not deprecated | MEDIUM | photo-vectorizer |
| photo_vectorizer_v2.py version mismatch | MEDIUM | photo-vectorizer |
| vectorizer_phase2.py superseded | MEDIUM | blueprint-import |
| CleanupMode invalid default | MEDIUM | vectorize_router.py |
| March pipeline restore orphaned | LOW | photo-vectorizer |
| DEPRECATED comment kept | LOW | edge_to_dxf.py |

### Regression Risk Impact (4 items)

| Item | Severity | Location |
|------|----------|----------|
| cognitive_extractor.py orphaned | HIGH | photo-vectorizer |
| cognitive_extraction_engine.py orphaned | HIGH | photo-vectorizer |
| light_line_body_extractor.py unknown | MEDIUM | photo-vectorizer |
| photo_silhouette_extractor.py unknown | MEDIUM | photo-vectorizer |

---

## Dead Code Inventory

| File | LOC | Status | Action |
|------|-----|--------|--------|
| `cognitive_extractor.py` | 1455 | Orphan | Archive |
| `cognitive_extraction_engine.py` | 1492 | Orphan | Archive |
| `extract_body_grid.py` | ~200 | Abandoned | Archive |
| `extract_body_grid_v2.py` | ~200 | Abandoned | Archive |
| `extract_body_grid_v3.py` | ~200 | Abandoned | Archive |
| `extract_body_grid_v4.py` | ~200 | Abandoned | Archive |
| `extract_body_grid_v5.py` | ~200 | Abandoned | Archive |
| `march_pipeline_restore.py` | ~100 | Orphan | Archive |
| `vectorizer_phase2.py` | 1684 | Superseded | Deprecate |

**Total Dead/Superseded Code:** ~5,800+ LOC

---

## Priority Matrix

| Priority | Severity | Count | Next Action |
|----------|----------|-------|-------------|
| P0 | CRITICAL | 4 | Fix `_simple_extraction()`, wire feedback systems |
| P1 | HIGH | 6 | Archive dead code, fix grouping fallback |
| P2 | MEDIUM | 8 | Consolidate, deprecate, document |
| P3 | LOW | 5 | Cleanup when convenient |

---

## Architectural Question

> Can the vectorizer layer become a trustworthy semantic evidence generator?

**Assessment:** Yes, with targeted fixes:

1. **Topology reliability:** V2_RAW and PHOTO_V2 modes produce clean output. SIMPLE mode needs fix.

2. **Semantic fidelity:** Feedback loop disconnection is the primary authority risk. Wiring FeedbackSystem would enable learning.

3. **Hidden fallbacks:** Most fallbacks are logged. edge_to_dxf grouping fallback needs telemetry.

4. **Dead code:** ~5,800 LOC should be archived to reduce surface area.

**Conclusion:** The vectorizer CAN be trustworthy if:
- CRITICAL items (4) are addressed
- HIGH dead code (5,800 LOC) is archived
- Fallback telemetry is added

---

*Vectorizer Technical Debt Inventory — Archaeology Complete — 2026-05-20*
