# Vectorizer Technical Debt Inventory

**Date:** 2026-05-20  
**Status:** ARCHAEOLOGY_COMPLETE — reconciled 2026-10-11  
**Sprint:** Vectorizer Technical Debt Archaeology  
**Lifecycle authority:** `docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md` (component states, ACTIVE promotion, SIMPLE gate)

---

## Overview

Structured inventory of technical debt in the vectorizer ecosystem, classified by severity and impact domain.

Non-canonical or unwired systems must use lifecycle states in `VECTORIZER_COMPONENT_LIFECYCLE.md` — **`ACTIVE` requires explicit sign-off**, not export-only fixes.

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
| relocated `cognitive_extractor.py` | `vectorizer-sandbox/src/semantic/` | **regression_risk** | Research-only; no longer in runtime spine | Preserve externally; production re-import remains gated |
| relocated `cognitive_extraction_engine.py` | `vectorizer-sandbox/src/semantic/` | **regression_risk** | Research-only; no longer in runtime spine | Preserve externally; production re-import remains gated |
| edge_to_dxf grouping fallback silent | edge_to_dxf.py:1294 | **topology** | Falls back to deprecated method on any exception | Add telemetry, fix exceptions |
| relocated grid extractors v1–v5 | `vectorizer-sandbox/src/archaeology/` | **maintainability** | Research-only; no longer in runtime spine | Preserve externally; harvest concepts only through research |
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
| relocated `vectorizer_phase2.py` | `vectorizer-sandbox/src/archaeology/vectorizer_phase2_runtime_spine.py` | **maintainability** | Removed from runtime spine; dev route is relocation stub | Preserve externally; no production re-import |
| `light_line_body_extractor.py` unknown | photo-vectorizer/ | **regression_risk** | Status unknown, no imports found | Investigate and classify |
| `photo_silhouette_extractor.py` unknown | photo-vectorizer/ | **regression_risk** | Status unknown, no imports found | Investigate and classify |
| Scale detection fragmentation | Multiple files | **semantic** | 4+ scale detection systems | Consolidate via calibration_integration |

---

## LOW Severity

| Debt Item | Location | Domain | Issue | Recommendation |
|-----------|----------|--------|-------|----------------|
| Neural network boost TODO | classifiers/latin_american/classifier.py:503 | **semantic** | Incomplete feature | Complete or remove TODO |
| DEPRECATED comment | edge_to_dxf.py:261 | **maintainability** | Method marked deprecated but kept | Remove or document why kept |
| Optional dep print statements | `vectorizer-sandbox/src/semantic/cognitive_extraction_engine.py` | **maintainability** | Research-only implementation detail | Address only in sandbox research work |
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
| `calibration_integration.py` not on main vectorize | MEDIUM | blueprint-import (PARTIAL — calibration API only) |
| Phase 4 standalone | HIGH | blueprint-import/phase4 |
| Contour plausibility import fallback | MEDIUM | contour_plausibility.py |
| Scale detection fragmentation | MEDIUM | Multiple |

### Authority Risk Impact (2 items)

| Item | Severity | Location |
|------|----------|----------|
| `submit_correction()` never called | CRITICAL | vectorizer_phase3.py (DEAD — PR-3 gate) |
| `TrainingDataCollector` never instantiated | CRITICAL | vectorizer_phase3.py (DEAD) |
| `record_classification()` narrow use | MEDIUM | vectorizer_phase3.py (PARTIAL) |

### Maintainability Impact (10 items)

| Item | Severity | Location |
|------|----------|----------|
| Contour hierarchy duplication | HIGH | edge_to_dxf.py |
| relocated cognitive_extractor.py | LOW | vectorizer-sandbox (research-only) |
| relocated cognitive_extraction_engine.py | LOW | vectorizer-sandbox (research-only) |
| 5 grid extractors v1–v5 (archaeological) | MEDIUM | photo-vectorizer |
| geometry_coach v1 not deprecated | MEDIUM | photo-vectorizer |
| photo_vectorizer_v2.py version mismatch | MEDIUM | photo-vectorizer |
| relocated vectorizer_phase2.py | LOW | vectorizer-sandbox (research-only) |
| CleanupMode invalid default | MEDIUM | vectorize_router.py |
| March pipeline restore orphaned | LOW | photo-vectorizer |
| DEPRECATED comment kept | LOW | edge_to_dxf.py |

### Regression Risk Impact (4 items)

| Item | Severity | Location |
|------|----------|----------|
| cognitive_extractor.py unwired (archaeological) | MEDIUM | photo-vectorizer |
| cognitive_extraction_engine.py unwired (archaeological) | MEDIUM | photo-vectorizer |
| light_line_body_extractor.py unknown | MEDIUM | photo-vectorizer |
| photo_silhouette_extractor.py unknown | MEDIUM | photo-vectorizer |

---

## Archaeological research inventory (preserve — do not delete in remediation sprint)

| File | LOC | Lifecycle state | Action |
|------|-----|-----------------|--------|
| former `cognitive_extractor.py` | ~1470 | **RELOCATED_EXTERNAL / RETAIN_RESEARCH_ONLY** | Preserved in `vectorizer-sandbox/src/semantic/` |
| former `cognitive_extraction_engine.py` | ~1503 | **RELOCATED_EXTERNAL / RETAIN_RESEARCH_ONLY** | Preserved in `vectorizer-sandbox/src/semantic/` |
| former `extract_body_grid.py` v1–v5 | ~1,640 total | **RELOCATED_EXTERNAL / RETAIN_RESEARCH_ONLY** | Preserved in `vectorizer-sandbox/src/archaeology/` |
| `march_pipeline_restore.py` | ~100 | **PARTIAL / Tier B** | Remains separately coupled; not part of completed Tier A disposition |

**Policy:** Unwired ≠ worthless. Harvest semantic/topology ideas before any deletion. See `VECTORIZER_COMPONENT_LIFECYCLE.md`.

## Superseded operational code

| File | LOC | Status | Action |
|------|-----|--------|--------|
| former `vectorizer_phase2.py` | 1684 | **RELOCATED_EXTERNAL / RETAIN_RESEARCH_ONLY** | Preserved in `vectorizer-sandbox/src/archaeology/vectorizer_phase2_runtime_spine.py` |

**~5,800 LOC** cognitive/grid: **research artifacts**, not janitorial delete target for PR-1–3.

---

## Priority Matrix

| Priority | Severity | Count | Next Action |
|----------|----------|-------|-------------|
| P0-live | HIGH/telemetry | 1 | PR-2 grouping fallback visibility on `refined` path |
| P0-code | CRITICAL | 3 | PR-1 SIMPLE export; PR-3 gate DEAD feedback paths |
| P1 | HIGH | 6 | **Tier A complete:** relocated to `vectorizer-sandbox`, research-only, grep-gated against production re-import; Tier B remains separate |
| P2 | MEDIUM | 8 | Calibration on main vectorize (optional), consolidate scale |
| P3 | LOW | 5 | Cleanup when convenient |

---

## Architectural Question

> Can the vectorizer layer become a trustworthy semantic evidence generator?

**Assessment:** Yes, with targeted fixes:

1. **Topology reliability:** Canonical `refined` path needs grouping fallback telemetry (PR-2). V2_RAW / PHOTO_V2 recovery modes are SANDBOX.

2. **Semantic fidelity:** `submit_correction` and `TrainingDataCollector` are DEAD — classify and gate (PR-3), do not imply learning. `record_classification` is PARTIAL only.

3. **SIMPLE:** Export fix (PR-1) → **EXPORT_SAFE** only; commercial ACTIVE requires `VECTORIZER_COMPONENT_LIFECYCLE.md` gate + sign-off.

4. **Relocated research lineage:** cognitive/grid/Phase-2 assets are **RELOCATED_EXTERNAL / RETAIN_RESEARCH_ONLY** in `vectorizer-sandbox`; preserve and harvest concepts there, with the existing grep gate preventing production re-import.

**Conclusion:** Trustworthiness on the **live** path requires PR-2 observability on `refined`, constitutional IBG intake, and golden `refined` stability — not enabling Phase 3 SIMPLE for MVP.

---

*Vectorizer Technical Debt Inventory — Archaeology Complete — 2026-05-20*
