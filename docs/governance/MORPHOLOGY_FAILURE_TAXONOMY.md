# Morphology Failure Taxonomy

**Date:** 2026-05-16
**Sprint:** IBG Corpus Ingestion & Morphology Validation 1B
**Status:** ACTIVE — Updated during validation
**Governance:** MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md

---

## Purpose

Tracks failure modes discovered during morphology validation.
This taxonomy is essential for vectorizer robustness improvements.

---

## Root Cause Analysis

### Primary Failure: Phase 4 Not Wired

All 10 representative instruments failed with the same root cause:
**Phase 4 (dimension extraction) is not wired in 1A.**

The morphology harvest coordinator is a **thin coordination layer** that delegates:
- Dimension extraction → Phase 4 pipeline
- Scale calibration → Calibration pipeline  
- Morphology classification → Body Grid

**System Status at Validation Time:**
```
phase4: not_wired_in_1A (reason: Phase 4 wiring deferred to 1B)
calibration: not_wired_in_1A (reason: Calibration wiring deferred to 1B)
body_grid: available
```

**Dependency Chain:**
```
PDF → Phase 4 (dimensions) → body_data.observed → Body Grid (classification)
                ↑
        BLOCKED HERE
```

Body Grid is available but cannot classify without body_data.observed being True,
which requires Phase 4 to have extracted dimensions. This is correct behavior —
the harvest layer should not attempt to extract dimensions itself.

### Architectural Validation

This failure confirms the architecture is sound:
1. HarvestCoordinator correctly delegates extraction (does not parse PDFs directly)
2. Body Grid correctly waits for observed data (does not hallucinate landmarks)
3. Failure is clean and traceable (not silent or partial)

### Remediation Path

Phase 1B must wire:
1. `services/blueprint-import/phase4/` → `morphology_harvest/adapters.py`
2. `services/blueprint-import/calibration/` → `morphology_harvest/adapters.py`

Until Phase 4 is wired, all corpus validation will fail at the extraction step.

---

## Failure Summary

| Severity | Count |
|----------|-------|
| Critical | 1 (upstream dependency) |
| Major | 10 (blocked instruments) |
| Minor | 0 |
| Observation | 0 |

---

## Failures by Category

### Upstream Dependency (CRITICAL)

| Type | Component | Severity | Description |
|------|-----------|----------|-------------|
| upstream_unmet | phase4_adapter | critical | Phase 4 dimension extraction not wired, blocks all harvest |
| upstream_unmet | calibration_adapter | critical | Calibration pipeline not wired, blocks scale detection |

### PDF/Image Extraction (Blocked by Above)

| Type | Instrument | Severity | Description |
|------|------------|----------|-------------|
| harvest_blocked | les_paul_59 | major | Blocked: Phase 4 not wired |
| harvest_blocked | sg_complete | major | Blocked: Phase 4 not wired |
| harvest_blocked | stratocaster_62 | major | Blocked: Phase 4 not wired |
| harvest_blocked | jazzmaster_62 | major | Blocked: Phase 4 not wired |
| harvest_blocked | explorer_complete | major | Blocked: Phase 4 not wired |
| harvest_blocked | dreadnought | major | Blocked: Phase 4 not wired |
| harvest_blocked | classical_santos | major | Blocked: Phase 4 not wired |
| harvest_blocked | es335_complete | major | Blocked: Phase 4 not wired |
| harvest_blocked | klein_ergonomic | major | Blocked: Phase 4 not wired |
| harvest_blocked | cuatro_pr | major | Blocked: Phase 4 not wired |

---

## Downstream Validation: Body Grid Classification

### Synthetic Test Results (2026-05-16)

Tested Body Grid classification with synthetic BodyEvidence containing only landmark points.

| Instrument | Expected | Actual | Status |
|------------|----------|--------|--------|
| les_paul_synthetic | rounded_single_cut | slab_body | MISMATCH |
| sg_synthetic | double_cut | slab_body | MISMATCH |
| stratocaster_synthetic | slab_body | slab_body | MATCH |
| dreadnought_synthetic | rounded_acoustic | slab_body | MISMATCH |
| classical_synthetic | rounded_acoustic | slab_body | MISMATCH |
| explorer_synthetic | angular_wedge | slab_body | MISMATCH |

**Accuracy:** 1/6 (16%)

### Root Cause: Insufficient Evidence for Grammar

The variant grammar defaults to SLAB_BODY when given only landmark points. To distinguish morphology classes, the grammar needs:

1. **Contour segments** — not just point landmarks
2. **Horn detection primitives** — cutaway/horn presence and type
3. **Curvature primitives** — rounded vs angular transitions
4. **Waist behavior** — suppressed, offset, or standard

**Observations:**
- All asymmetry scores were 0.0 (symmetric landmarks were fed)
- Only 6 primitives detected per instrument (minimal)
- High confidence (0.94) on default classification = overconfident fallback

### Architectural Analysis

The variant grammar requires specific **primitive types** to classify bodies:

| Grammar Rule | Required Primitives |
|--------------|---------------------|
| rounded_single_cut | CONVEX_BOUT, CONCAVE_WAIST, CUTAWAY_INTRUSION |
| rounded_acoustic | CONVEX_BOUT, CONCAVE_WAIST, BUTT_TERMINATION |
| double_cut_horns | HORN_PROJECTION |
| angular_wedge | LINE_SEGMENT, DIAGONAL_SEGMENT |
| slab_body | ARC_SEGMENT (default rule, least restrictive) |

**Evidence Flow Gap:**
```
PDF → Phase 4 → dimensions → HarvestRecord → landmarks → BodyEvidence
                                                          ↓
                                                  PrimitiveDetector
                                                          ↓
                                                  ???  (insufficient)
                                                          ↓
                                                  VariantGrammar → SLAB_BODY default
```

**Root Cause:** Landmarks alone cannot provide:
- Curvature class (CONVEX vs CONCAVE vs LINE)
- Geometry type (ARC vs LINE vs SPLINE)
- Horn/cutaway presence (requires contour analysis)

**Remediation Path:**

1. **Contour extraction** — Phase 4 or vectorizer must provide contour segments, not just dimensions
2. **Curvature analysis** — PrimitiveDetector needs point sequences to compute curvature
3. **OR landmark inference** — PrimitiveDetector could infer primitives from landmark patterns
   - e.g., lower_bout_max + waist_min + upper_bout_max pattern → infer CONVEX_BOUT + CONCAVE_WAIST

**Option B (Landmark Pattern Inference)** is lower-effort and could work for basic classification:
- Lower bout wider than upper → acoustic pattern
- Waist significantly narrower → pronounced waist primitive
- Asymmetric upper bout landmarks → cutaway inference

This would require enhancing PrimitiveDetector to work with sparse landmarks.

---

## Pending Discovery (Once Phase 4 Wired)

These instruments have attention points flagged for morphology edge case discovery:

| Instrument | Expected Class | Attention Points |
|------------|---------------|------------------|
| jazzmaster_62 | OFFSET_DOUBLE_CUT | asymmetry handling, offset detection, waist behavior |
| explorer_complete | ANGULAR_WEDGE | angular primitive detection, suppressed waist, non-traditional zones |
| klein_ergonomic | HYBRID_FORM | non-canonical morphology, zone mapping failure, hybrid detection |
| es335_complete | ROUNDED_DOUBLE_CUT | f-hole detection, hollow body handling, cutaway behavior |
| cuatro_pr | ROUNDED_ACOUSTIC | scale assumptions, non-guitar morphology, size handling |

**Expected Failure Categories (Phase 4 Wired):**
- Asymmetry breakdown (Jazzmaster offset, Klein ergonomic)
- Zone mapping failure (Explorer angular zones, Klein non-canonical)
- Primitive detection gaps (Explorer angular, 335 f-holes)
- Scale/size assumptions (Cuatro non-standard, Klein headless)
- Topology collapse (Explorer wedge, Klein curved-arm)

---

## Expected Failure Categories (Reference)

These categories should be tracked during morphology validation:

| Category | Description |
|----------|-------------|
| OCR failures | Text detection issues in scanned plans |
| Contour fragmentation | Incomplete or broken contour detection |
| Centerline ambiguity | Cannot determine body centerline |
| Zone misclassification | Wrong zone assigned to region |
| Asymmetry breakdown | Asymmetry detection fails or misbehaves |
| False primitive detection | Primitives detected that don't exist |
| Missing primitive detection | Real primitives not detected |
| Dimension ambiguity | Cannot associate dimensions with geometry |
| Raster degradation | Quality loss in scanned/raster plans |
| Scan skew | Rotated or skewed scan affects geometry |
| Topology collapse | Unusual shape breaks zone/primitive model |
| Scale mismatch | Extracted dimensions don't match expected |

---

## Remediation Priority

1. **Critical** � Blocks further processing, must fix
2. **Major** � Significant impact on morphology quality
3. **Minor** � Affects accuracy but doesn't block
4. **Observation** � Noted for future improvement
