# IBG E-2-E Failure Log

**Date:** 2026-05-17
**Sprint:** IBG E-2-E Functional Spine
**Status:** Active

---

## Summary

This log documents failures and classification mismatches from the IBG E-2-E functional spine validation run across 10 representative instruments.

| Metric | Count |
|--------|-------|
| Total instruments | 10 |
| Full pipeline success | 9 |
| Vectorizer failures | 1 |
| Classification mismatches | 9 |

---

## Critical Failures

### F-001: Fender Stratocaster Empty Vectorizer Response

**Source file:** `Fender-Stratocaster-62.pdf`
**Run ID:** `e2e_stratocaster_*`
**Stage failed:** Stage 1 (Vectorizer)

**Symptom:**
Vectorizer returned empty dimensions and no DXF artifacts.

```json
{
  "dimensions": null,
  "artifacts": {
    "dxf": null,
    "svg": null
  }
}
```

**Impact:**
- No BodyEvidence created
- No Body Grid analysis
- No IBG reconstruction
- No BOE package

**Root cause candidates:**
1. PDF structure not parseable by current vectorizer
2. Blueprint layout differs from expected format
3. Possible OCR/extraction issue in blueprint_reader pipeline

**Action required:**
- Investigate PDF structure manually
- Test with alternative Stratocaster blueprint
- Check vectorizer logs for specific error

**Priority:** HIGH — Stratocaster is a primary reference instrument

---

## Classification Mismatches

All 9 successful instruments were classified as `slab_body` instead of their expected morphology classes. This is documented behavior given current Body Grid limitations.

### M-001: Gibson Les Paul

**Source:** `Gibson-Les-Paul-59-Complete.pdf`
**Expected class:** `ROUNDED_SINGLE_CUT`
**Actual class:** `slab_body`
**Confidence:** 0.27

**Analysis:**
- Les Paul has a pronounced single cutaway with rounded horn
- Classification requires curvature-aware primitives
- Current Body Grid lacks horn detection logic

### M-002: Fender Telecaster

**Source:** `Fender-Telecaster-52.pdf`
**Expected class:** `SLAB_SINGLE_CUT` or `ROUNDED_SINGLE_CUT`
**Actual class:** `slab_body`
**Confidence:** 0.27

**Analysis:**
- Telecaster has a simpler cutaway than Les Paul
- Still requires cutaway detection logic

### M-003: Gibson SG

**Source:** `Gibson-SG-Standard.pdf`
**Expected class:** `DOUBLE_CUT_SYMMETRIC` or similar
**Actual class:** `slab_body`
**Confidence:** 0.27

**Analysis:**
- SG has aggressive double cutaway
- Requires symmetric cutaway detection

### M-004: Gibson ES-335

**Source:** `Gibson-ES-335.pdf`
**Expected class:** `SEMI_HOLLOW_DOUBLE_CUT`
**Actual class:** `slab_body`
**Confidence:** 0.28

**Analysis:**
- ES-335 has distinctive f-holes and double cutaway
- Requires hollow body detection logic

### M-005: PRS Custom 24

**Source:** `PRS-Custom-24.pdf`
**Expected class:** `ROUNDED_DOUBLE_CUT`
**Actual class:** `slab_body`
**Confidence:** 0.27

**Analysis:**
- PRS has smooth double cutaway with rounded horns
- Requires horn curvature analysis

### M-006: Gibson Explorer

**Source:** `Gibson-Explorer.pdf`
**Expected class:** `ASYMMETRIC_POINTED` or `EXPLORER_TYPE`
**Actual class:** `slab_body`
**Confidence:** 0.27

**Analysis:**
- Explorer has radical asymmetric pointed shape
- Requires asymmetry detection and pointed feature recognition

### M-007: Gibson Flying V

**Source:** `Gibson-Flying-V.pdf`
**Expected class:** `V_SHAPE` or `ASYMMETRIC_POINTED`
**Actual class:** `slab_body`
**Confidence:** 0.27

**Analysis:**
- Flying V has distinctive V-shaped body
- Requires V-pattern recognition

### M-008: Fender Jazz Bass

**Source:** `Fender-Jazz-Bass.pdf`
**Expected class:** `OFFSET_WAIST` or `J_BASS_TYPE`
**Actual class:** `slab_body`
**Confidence:** 0.27

**Analysis:**
- Jazz Bass has offset waist and distinctive curves
- Requires waist offset detection

### M-009: Martin D-28

**Source:** `Martin-D-28.pdf`
**Expected class:** `DREADNOUGHT` or `ACOUSTIC_STANDARD`
**Actual class:** `slab_body`
**Confidence:** 0.28

**Analysis:**
- D-28 is a dreadnought acoustic body
- Acoustic bodies have different morphology patterns than solid-body electrics

---

## Root Cause Analysis

### Why All Classifications Return slab_body

The current MorphologyAnalyzer in Body Grid uses a simplified classification approach that:

1. **Lacks curvature primitives** — Cannot distinguish rounded vs. pointed features
2. **Lacks cutaway detection** — Cannot identify single vs. double cutaway
3. **Lacks asymmetry metrics** — Cannot distinguish symmetric vs. offset designs
4. **Lacks horn analysis** — Cannot measure horn depth, angle, or curvature

The `slab_body` classification is the fallback when no distinctive features are detected. The low confidence (0.27-0.28) correctly indicates uncertainty.

### LandmarkPatternInferrer Gap

The `LandmarkPatternInferrer` (created in 1B-FIX sprint) was designed to address this gap by:

1. Detecting landmark patterns (horns, cutaways, waist points)
2. Inferring morphology class from landmark arrangement
3. Providing higher-confidence classification

**Current status:** Not integrated into E-2-E spine

---

## Remediation Plan

### Immediate (This Sprint)

1. **Investigate Stratocaster PDF** — Determine why vectorizer returned empty
2. **Document expected classes** — Create ground truth file for 10 instruments

### Next Sprint

1. **Integrate LandmarkPatternInferrer** — Wire into Body Grid analysis
2. **Add curvature primitives** — Implement arc/curve detection in morphology extraction
3. **Add cutaway detection** — Identify single/double cutaway patterns

### Future

1. **ML classifier** — Train on corpus of labeled instrument outlines
2. **Three-loop feedback** — Use BOE corrections to improve classification

---

## Metrics Tracking

| Run Date | Success Rate | Avg Confidence | Correct Classifications |
|----------|-------------|----------------|------------------------|
| 2026-05-17 | 90% (9/10) | 0.27 | 0/9 |

---

## References

- IBG_E2E_FUNCTIONAL_SPINE_REPORT.md — Sprint report
- IBG_E2E_REVIEW_PACKAGE_SCHEMA.md — BOE package schema
- body_grid_schema.py — BodyEvidence and MorphologyDescriptor definitions
- morphology_analyzer.py — Current classification logic
