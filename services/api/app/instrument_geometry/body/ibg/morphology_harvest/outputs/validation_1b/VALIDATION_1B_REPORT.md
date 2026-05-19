# IBG Morphology Validation 1B Report

**Date:** 2026-05-17
**Corpus:** C:\Users\thepr\Downloads\luthiers-toolbox\Guitar Plans

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total instruments | 10 |
| Successful harvests | 8 (80%) |
| Classification matches | 0 (0%) |
| Failures recorded | 11 |

---

## Per-Instrument Results

### les_paul_59 (single_cut)

**File:** `Gibson-Les-Paul-59-Complete.pdf`
**Status:** PARTIAL

| Metric | Value |
|--------|-------|
| Expected class | ROUNDED_SINGLE_CUT |
| Actual class | ROUNDED_ACOUSTIC |
| Classification confidence | 0.00 |
| Centerline confidence | 0.60 |
| Asymmetry score | 0.00 |
| Primitives detected | 0 |

**Warnings:**
- Low classification confidence: 0.00
- Missing regions: lower_bout, waist, upper_bout, butt_end

**Ambiguities:**
- Classification mismatch: expected ROUNDED_SINGLE_CUT, got ROUNDED_ACOUSTIC (conf: 0.00)

**Attention points:**
- carved top detection
- asymmetry handling

---

### sg_complete (double_cut)

**File:** `01-Gibson-SG-Complete-Template.pdf`
**Status:** FAIL

**Errors:**
- Harvest failed: no data extracted

**Attention points:**
- horn detection
- cutaway symmetry

---

### stratocaster_62 (slab_body)

**File:** `Fender-Stratocaster-62.pdf`
**Status:** PARTIAL

| Metric | Value |
|--------|-------|
| Expected class | SLAB_BODY |
| Actual class | N/A |
| Classification confidence | 0.00 |
| Centerline confidence | 0.00 |
| Asymmetry score | 0.00 |
| Primitives detected | 0 |

**Errors:**
- Harvest exception: Object of type ContourCategory is not JSON serializable

**Attention points:**
- contour detection
- waist offset

---

### jazzmaster_62 (offset)

**File:** `Fender-Jazzmaster-62-Body.pdf`
**Status:** FAIL

**Errors:**
- Harvest failed: no data extracted

**Attention points:**
- asymmetry handling
- offset detection
- waist behavior

---

### explorer_complete (angular)

**File:** `Gibson-Explorer-05-Complete-Plans.pdf`
**Status:** PARTIAL

| Metric | Value |
|--------|-------|
| Expected class | ANGULAR_WEDGE |
| Actual class | N/A |
| Classification confidence | 0.00 |
| Centerline confidence | 0.00 |
| Asymmetry score | 0.00 |
| Primitives detected | 0 |

**Errors:**
- Harvest exception: Object of type ContourCategory is not JSON serializable

**Attention points:**
- angular primitive detection
- suppressed waist
- non-traditional zones

---

### dreadnought (acoustic_dread)

**File:** `A003-Dreadnought-MM.pdf`
**Status:** PARTIAL

| Metric | Value |
|--------|-------|
| Expected class | ROUNDED_ACOUSTIC |
| Actual class | N/A |
| Classification confidence | 0.00 |
| Centerline confidence | 0.00 |
| Asymmetry score | 0.00 |
| Primitives detected | 0 |

**Errors:**
- Harvest exception: Object of type ContourCategory is not JSON serializable

**Attention points:**
- bout ratios
- waist detection
- symmetry

---

### classical_santos (classical)

**File:** `Classical-Santos-Hernandez-MM.pdf`
**Status:** PARTIAL

| Metric | Value |
|--------|-------|
| Expected class | CLASSICAL_FIGURE_8 |
| Actual class | N/A |
| Classification confidence | 0.00 |
| Centerline confidence | 0.00 |
| Asymmetry score | 0.00 |
| Primitives detected | 0 |

**Errors:**
- Harvest exception: Object of type ContourCategory is not JSON serializable

**Attention points:**
- bout proportions
- waist position
- classical vs acoustic

---

### es335_complete (semi_hollow)

**File:** `Gibson-335/Gibson-335-Dot-Complete.pdf`
**Status:** PARTIAL

| Metric | Value |
|--------|-------|
| Expected class | ROUNDED_DOUBLE_CUT |
| Actual class | N/A |
| Classification confidence | 0.00 |
| Centerline confidence | 0.00 |
| Asymmetry score | 0.00 |
| Primitives detected | 0 |

**Errors:**
- Harvest exception: Object of type ContourCategory is not JSON serializable

**Attention points:**
- f-hole detection
- hollow body handling
- cutaway behavior

---

### klein_ergonomic (ergonomic)

**File:** `Klein-Guitar-Plan.pdf`
**Status:** PARTIAL

| Metric | Value |
|--------|-------|
| Expected class | HYBRID_FORM |
| Actual class | N/A |
| Classification confidence | 0.00 |
| Centerline confidence | 0.00 |
| Asymmetry score | 0.00 |
| Primitives detected | 0 |

**Errors:**
- Harvest exception: Object of type ContourCategory is not JSON serializable

**Attention points:**
- non-canonical morphology
- zone mapping failure
- hybrid detection

---

### cuatro_pr (latin_folk)

**File:** `El Cuatro/cuatro puertoriqueño.pdf`
**Status:** PARTIAL

| Metric | Value |
|--------|-------|
| Expected class | ROUNDED_ACOUSTIC |
| Actual class | N/A |
| Classification confidence | 0.00 |
| Centerline confidence | 0.00 |
| Asymmetry score | 0.00 |
| Primitives detected | 0 |

**Errors:**
- Harvest exception: Object of type ContourCategory is not JSON serializable

**Attention points:**
- scale assumptions
- non-guitar morphology
- size handling

---

## Key Observations

### Classification Accuracy

No instruments correctly classified.

### Classification Mismatches

- **les_paul_59**: Expected ROUNDED_SINGLE_CUT, got ROUNDED_ACOUSTIC
- **stratocaster_62**: Expected SLAB_BODY, got None
- **explorer_complete**: Expected ANGULAR_WEDGE, got None
- **dreadnought**: Expected ROUNDED_ACOUSTIC, got None
- **classical_santos**: Expected CLASSICAL_FIGURE_8, got None
- **es335_complete**: Expected ROUNDED_DOUBLE_CUT, got None
- **klein_ergonomic**: Expected HYBRID_FORM, got None
- **cuatro_pr**: Expected ROUNDED_ACOUSTIC, got None

### Failure Summary

Total failures recorded: 11

See `docs/governance/MORPHOLOGY_FAILURE_TAXONOMY.md` for details.
