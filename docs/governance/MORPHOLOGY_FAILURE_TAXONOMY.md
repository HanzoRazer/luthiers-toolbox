# Morphology Failure Taxonomy

**Date:** 2026-05-17
**Sprint:** IBG Corpus Ingestion & Morphology Validation 1B
**Status:** ACTIVE — Updated during validation

---

## Purpose

Tracks failure modes discovered during morphology validation.
This taxonomy is essential for vectorizer robustness improvements.

---

## Failure Summary

| Severity | Count |
|----------|-------|
| Critical | 7 |
| Major | 3 |
| Minor | 1 |
| Observation | 0 |

---

## Failures by Category

### Morphology Classification

| Type | Instrument | Severity | Description |
|------|------------|----------|-------------|
| classification_mismatch | les_paul_59 | major | Expected ROUNDED_SINGLE_CUT, got ROUNDED_ACOUSTIC |
| low_confidence | les_paul_59 | minor | Classification confidence only 0.00 |

### PDF/Image Extraction

| Type | Instrument | Severity | Description |
|------|------------|----------|-------------|
| harvest_failed | sg_complete | major | No morphology data extracted from PDF |
| harvest_exception | stratocaster_62 | critical | Object of type ContourCategory is not JSON serializable |
| harvest_failed | jazzmaster_62 | major | No morphology data extracted from PDF |
| harvest_exception | explorer_complete | critical | Object of type ContourCategory is not JSON serializable |
| harvest_exception | dreadnought | critical | Object of type ContourCategory is not JSON serializable |
| harvest_exception | classical_santos | critical | Object of type ContourCategory is not JSON serializable |
| harvest_exception | es335_complete | critical | Object of type ContourCategory is not JSON serializable |
| harvest_exception | klein_ergonomic | critical | Object of type ContourCategory is not JSON serializable |
| harvest_exception | cuatro_pr | critical | Object of type ContourCategory is not JSON serializable |

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

1. **Critical** — Blocks further processing, must fix
2. **Major** — Significant impact on morphology quality
3. **Minor** — Affects accuracy but doesn't block
4. **Observation** — Noted for future improvement
