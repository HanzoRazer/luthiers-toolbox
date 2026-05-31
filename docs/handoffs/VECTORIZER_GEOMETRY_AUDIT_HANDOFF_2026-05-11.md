# Vectorizer & Geometry Systems Audit Handoff

**Date:** 2026-05-11  
**Audit Scope:** Vectorizer pipeline, geometry generators, DXF compliance  
**Status:** AUDIT COMPLETE — Remediation Required

> **CONFLATION CORRECTION (2026-05-30).** This audit quotes the CLAUDE.md three-loop / AGE
> mandate ("requested by Ross in multiple sessions… must be built"; "APPROVED DESIGN") as if it
> were owed runtime work. Per ground truth from Ross (2026-05-30), that mandate was conflation:
> the three-loop architecture + AGE were **experimental, never approved, and never implemented**
> here — now **sandboxed into `vectorizer-sandbox`**. Treat any "approved/owed" framing in this
> doc as superseded. The shipped **scale-validation gate** is real and unaffected. See
> `docs/handoffs/DEV_HANDOFF_2026-05-30_THREE_LOOP_CONFLATION_REMOVAL.md` (+ `_CORRECTIONS.md`).
>
> **Live-code carve-out:** "never implemented" means the *named, unified* architecture only.
> `GeometryCoachV2` (photo-vectorizer) is real, **API-reachable** runtime code — its "Loop 1" name
> is retrospective labeling, NOT the approved architecture. Do NOT delete or sandbox it; deletion
> degrades a live endpoint path. See handoff §2 + §9b.

---

## Executive Summary

The vectorizer has **strong individual components** (scale validation, dxf_compat, feedback infrastructure) but **lacks the integrated three-loop feedback architecture** approved in CLAUDE.md (2026-04-02). The gap is particularly acute for Loop 2 (learning) and AGE (AI guidance), which do not exist at all.

The geometry systems have a robust dxf_compat framework but **21 files bypass it**, indicating enforcement gaps rather than technical limitations.

---

## Implementation Status Matrix

| Component | CLAUDE.md Requirement | Actual Status | Integration |
|-----------|----------------------|---------------|-------------|
| Scale Validation Gate | IMMEDIATE | ✅ Complete | Wired at line 3559 |
| Loop 1: Intra-Frame Validation | REQUIRED | ⚠️ Partial | Scale gate only, no fallback retry |
| Loop 2: Cross-Image Learning | REQUIRED | ❌ None | No strategy cache, no learning |
| Loop 3: User Corrections | REQUIRED | ⚠️ Orphaned | FeedbackSystem exists, no API |
| AGE Integration | APPROVED DESIGN | ❌ None | Never built |
| dxf_compat System | STANDARD | ✅ Complete | Both locations ready |
| dxf_writer.py (Central) | Was BLOCKING | ✅ Complete | Mature, integrated |
| calibration_integration.py | REFERENCE | ⚠️ Orphaned | Never imported |
| Segmentation-First (Sprint B) | HIGH PRIORITY | ❌ None | Not started |

---

## 1. Vectorizer Pipeline Gaps

### 1.1 Loop 1: Intra-Frame Validation (INCOMPLETE)

**What IS implemented:**
- `validate_scale_before_export()` at `vectorizer_phase3.py:2327-2425`
- Validates body dimensions against spec (0.8–1.2× tolerance)
- Applies geometric mean correction when validation fails
- Called in extract() pipeline before export_to_dxf()

**What IS MISSING:**
- No `extract_with_self_check()` wrapper with automated retry
- No multi-factor validation (has_reasonable_size, has_continuous_boundary, has_no_spikes, aspect_ratio_plausible, scale_plausible)
- No fallback strategy selection when validation fails
- No automatic retry with alternative extraction methods

**Gap:** Scale validation checks dimensions but doesn't trigger alternative extractions.

---

### 1.2 Loop 2: Cross-Image Learning (NOT IMPLEMENTED)

**CLAUDE.md specifies:**
```python
class AdaptiveExtractor:
    def __init__(self):
        self.strategy_cache = {}  # image_signature → winning_strategy
```

**What ACTUALLY exists:**
- ❌ No `strategy_cache` attribute
- ❌ No `get_image_signature()` method
- ❌ No `try_all_strategies()` method
- ❌ No `pick_best()` method

**Gap:** Same extraction strategy always followed. No cross-run learning.

---

### 1.3 Loop 3: User Correction Retraining (ORPHANED)

**What exists:**
- `FeedbackSystem` class (lines 1181–1267)
- `TrainingDataCollector` class (lines 1273–1330)
- Instantiated when `enable_feedback=True`
- Recording happens once per extraction (low confidence samples)

**What IS MISSING:**
- ❌ No API endpoint for user corrections
- ❌ `submit_correction()` never called
- ❌ `TrainingDataCollector` instantiated but never used
- ❌ No retraining pipeline

**Gap:** Feedback plumbing exists but is not wired to API layer.

---

### 1.4 AGE Integration (NOT IMPLEMENTED)

**CLAUDE.md line 408:**
> "DO NOT drop the AGE integration from scope again. It was requested by Ross in multiple sessions. It must be built."

**Status:** Not in codebase.

**Required implementation:**
```python
class VectorizerAGE:
    def evaluate_extraction(self, result, spec_name, image_path):
        # Ask Claude to evaluate extraction plausibility
        # Returns: (is_plausible, recommended_strategy, reasoning)
```

**Gap:** AI-driven evaluation of extraction quality completely absent.

---

### 1.5 Segmentation-First Extraction (SPRINT B - NOT STARTED)

**Root cause confirmed:** 148 open endpoints from edge detection gaps
- 88 gaps <0.5mm (noise)
- 34 gaps >5mm (maximum 27.25mm) — genuine discontinuities

**Required implementation:**
- `extract_body_by_segmentation()` using flood fill from image center
- `fg_mask` priority path for foreground mask
- Edge detection as fallback only

**File:** `services/blueprint-import/vectorizer_phase3.py`

---

## 2. DXF Compliance Violations

### 2.1 Requirement (from CLAUDE.md)

All DXF generators must use `dxf_compat.create_document()` and `dxf_compat.add_polyline()`. Direct `ezdxf.new()` calls are forbidden outside the wrapper.

### 2.2 Violations Found (21 files)

| Category | Files | Count |
|----------|-------|-------|
| Routers | neck_profile_export.py, headstock_transition_export.py, dxf_export.py, curve_export_router.py, export.py | 5 |
| Blueprint CAM | dxf_preprocessor.py, contour_reconstruction.py | 2 |
| CAM Generators | archtop_saddle_generator.py, archtop_bridge_generator.py, archtop_contour_generator.py, layer_consolidator.py, dxf_consolidator.py, unified_dxf_cleaner.py, archtop_surface_tools.py | 7 |
| Smart Guitar | smart_guitar_dxf.py, smart_guitar_dxf_router.py | 2 |
| Validation/Export | dxf_advanced_validation.py, inlay_export.py, dxf_preflight_router.py, inlay_calc.py | 4 |
| Util | dxf_compat.py (wrapper, acceptable) | 1 |

### 2.3 Refactoring Pattern

```python
# Current (violates standard):
import ezdxf
doc = ezdxf.new("R2010")

# Replace with:
from app.util.dxf_compat import create_document
doc = create_document(version='R2010')
```

---

## 3. Orphaned Components

### 3.1 calibration_integration.py

**File:** `services/blueprint-import/calibration_integration.py`

**Status:** Exists but never imported anywhere.

**Contains:**
- `EnhancedCalibrationPipeline` class
- Multi-method calibration: user reference → scale length → ruler → paper size → body heuristic
- `extract_dimensions()` for guitar dimension extraction

**Decision required:**
1. **Integrate:** Migrate into main pipeline
2. **Archive:** Document why superseded
3. **Remove:** Delete if obsolete

---

## 4. Remediation Plan

### Phase 1: DXF Compliance (Priority: HIGH)

**Effort:** 8–12 hours

| Task | File(s) | Action |
|------|---------|--------|
| 1.1 | 20 violation files | Replace `ezdxf.new()` with `dxf_compat.create_document()` |
| 1.2 | Pre-commit config | Add hook to catch future `ezdxf.new()` calls |
| 1.3 | CI pipeline | Add linter rule for dxf_compat enforcement |

### Phase 2: Loop 1 Completion (Priority: HIGH)

**Effort:** 12–16 hours

| Task | File | Action |
|------|------|--------|
| 2.1 | vectorizer_phase3.py | Add `extract_with_self_check()` wrapper |
| 2.2 | vectorizer_phase3.py | Implement 5-check voting system |
| 2.3 | vectorizer_phase3.py | Add fallback strategy retry logic |
| 2.4 | tests/ | Add unit tests for validation and retry |

### Phase 3: Loop 2 Implementation (Priority: MEDIUM)

**Effort:** 16–20 hours

| Task | File | Action |
|------|------|--------|
| 3.1 | vectorizer_phase3.py | Add `strategy_cache` attribute |
| 3.2 | vectorizer_phase3.py | Implement `get_image_signature()` |
| 3.3 | vectorizer_phase3.py | Implement `try_all_strategies()` |
| 3.4 | vectorizer_phase3.py | Implement `pick_best()` |
| 3.5 | vectorizer_phase3.py | Add cache persistence (JSON) |

### Phase 4: Loop 3 Wiring (Priority: MEDIUM)

**Effort:** 8–12 hours

| Task | File | Action |
|------|------|--------|
| 4.1 | routers/ | Create `/api/blueprint/correction` endpoint |
| 4.2 | endpoint | Wire to `feedback.submit_correction()` |
| 4.3 | scheduler | Add weekly retraining task |
| 4.4 | docs | Document feedback flow |

### Phase 5: AGE Integration (Priority: MEDIUM-HIGH)

**Effort:** 12–16 hours

| Task | File | Action |
|------|------|--------|
| 5.1 | vectorizer_phase3.py | Create `VectorizerAGE` class |
| 5.2 | VectorizerAGE | Implement `evaluate_extraction()` |
| 5.3 | VectorizerAGE | Add Claude API integration |
| 5.4 | VectorizerAGE | Add silent fallback when API unavailable |
| 5.5 | vectorizer_phase3.py | Wire AGE above Loop 1 |

### Phase 6: Segmentation-First (Priority: HIGH)

**Effort:** 8–12 hours

| Task | File | Action |
|------|------|--------|
| 6.1 | vectorizer_phase3.py | Add `extract_body_by_segmentation()` |
| 6.2 | vectorizer_phase3.py | Implement flood fill from center |
| 6.3 | vectorizer_phase3.py | Add `fg_mask` priority path |
| 6.4 | vectorizer_phase3.py | Edge detection as fallback |

---

## 5. Remediation Checklist

```
DXF Compliance (REMEDIATED via VECTOR-1A — see VECTOR_1A_DXF_COMPLIANCE_CLOSEOUT.md)
[x] Refactor 19 violating files to use dxf_compat
[x] Add pre-commit hook to prevent future violations
[x] Add enforcement script (scripts/check_dxf_compat.py)
[x] Document exemptions (docs/architecture/DXF_COMPAT_EXEMPTIONS.md)
[x] Add R12 compliance tests (test_dxf_compat_r12_compliance.py)
[x] Add semantic determinism tests
[-] Smart Guitar excluded (EXCLUDED_EXTERNAL_ECOSYSTEM)
[-] Photo Vectorizer excluded (EXCLUDED_R_AND_D_SANDBOX)

Loop 1: Intra-Frame Validation
[ ] Add extract_with_self_check() with 5-check voting
[ ] Implement fallback retry mechanism
[ ] Add unit tests for validation

Loop 2: Cross-Image Learning
[ ] Add strategy_cache to Phase3Vectorizer
[ ] Implement get_image_signature()
[ ] Implement try_all_strategies()
[ ] Implement pick_best()
[ ] Add cache persistence

Loop 3: User Corrections
[ ] Create API endpoint for corrections
[ ] Wire FeedbackSystem to endpoint
[ ] Set up retraining scheduler
[ ] Document feedback API

AGE Integration
[ ] Implement VectorizerAGE class
[ ] Add Claude API evaluation
[ ] Add silent fallback
[ ] Wire above Loop 1

Segmentation-First
[ ] Implement extract_body_by_segmentation()
[ ] Add flood fill approach
[ ] Add fg_mask priority path
[ ] Make edge detection fallback only

Cleanup
[ ] Audit calibration_integration.py
[ ] Archive or integrate orphaned modules
```

---

## 6. File Reference

| File | Location | Purpose |
|------|----------|---------|
| vectorizer_phase3.py | services/blueprint-import/ | Main vectorizer, needs all loops |
| dxf_compat.py | services/api/app/util/ | DXF compatibility layer |
| dxf_compat.py | services/blueprint-import/ | Blueprint import DXF compat |
| dxf_writer.py | services/api/app/cam/ | Central DXF writer |
| calibration_integration.py | services/blueprint-import/ | Orphaned calibration module |
| FeedbackSystem | vectorizer_phase3.py:1181 | User correction collection |
| TrainingDataCollector | vectorizer_phase3.py:1273 | ML training data collector |

---

## 7. Estimated Total Effort

| Phase | Hours |
|-------|-------|
| Phase 1: DXF Compliance | 8–12 |
| Phase 2: Loop 1 Completion | 12–16 |
| Phase 3: Loop 2 Implementation | 16–20 |
| Phase 4: Loop 3 Wiring | 8–12 |
| Phase 5: AGE Integration | 12–16 |
| Phase 6: Segmentation-First | 8–12 |
| **Total** | **64–88 hours** |

---

## 8. Critical Quotes from CLAUDE.md

### On AGE (line 408):
> "DO NOT drop the AGE integration from scope again. It was requested by Ross in multiple sessions. It must be built."

### On Loop Architecture (line 415):
> "The feedback loop architecture is APPROVED. Point fixes to epsilon values, simplification tolerances, or version strings are NOT substitutes for implementing the approved architecture."

### On DXF Compliance:
> "No new DXF generator may be built until dxf_writer.py exists and existing generators are refactored to use it."

**Note:** dxf_writer.py now exists. The blocking status has changed to: "21 existing generators still bypass it."

---

*Audit completed: 2026-05-11*  
*No code changes made — audit only*  
*Ready for remediation planning*
