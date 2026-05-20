# IBG Morphology Validation 1B Report

**Date:** 2026-05-19
**Corpus:** C:\Users\thepr\Downloads\luthiers-toolbox\Guitar Plans

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total instruments | 10 |
| Successful harvests | 0 (0%) |
| Classification matches | 0 (0%) |
| Failures recorded | 10 |

---

## Per-Instrument Results

### les_paul_59 (single_cut)

**File:** `Gibson-Les-Paul-59-Complete.pdf`
**Status:** FAIL

**Errors:**
- Harvest failed: no data extracted
- Harvest error: Blueprint extraction error: Submit failed: 404 - {"status":"error","code":404,"message":"Application not found","request_id":"DXaA8-01S9mdokBso3UVLg"}

**Attention points:**
- carved top detection
- asymmetry handling

---

### sg_complete (double_cut)

**File:** `01-Gibson-SG-Complete-Template.pdf`
**Status:** FAIL

**Errors:**
- Harvest failed: no data extracted
- Harvest error: Blueprint extraction error: Submit failed: 404 - {"status":"error","code":404,"message":"Application not found","request_id":"B2ju1a-nRKaMBCEUH4GxDA"}

**Attention points:**
- horn detection
- cutaway symmetry

---

### stratocaster_62 (slab_body)

**File:** `Fender-Stratocaster-62.pdf`
**Status:** FAIL

**Errors:**
- Harvest failed: no data extracted
- Harvest error: Blueprint extraction error: Submit failed: 404 - {"status":"error","code":404,"message":"Application not found","request_id":"8ffwiJJVS6anc7H_c9o55Q"}

**Attention points:**
- contour detection
- waist offset

---

### jazzmaster_62 (offset)

**File:** `Fender-Jazzmaster-62-Body.pdf`
**Status:** FAIL

**Errors:**
- Harvest failed: no data extracted
- Harvest error: Blueprint extraction error: Submit failed: 404 - {"status":"error","code":404,"message":"Application not found","request_id":"KMJRnZdrTX2E910eFFmdQQ"}

**Attention points:**
- asymmetry handling
- offset detection
- waist behavior

---

### explorer_complete (angular)

**File:** `Gibson-Explorer-05-Complete-Plans.pdf`
**Status:** FAIL

**Errors:**
- Harvest failed: no data extracted
- Harvest error: Blueprint extraction error: Submit failed: 404 - {"status":"error","code":404,"message":"Application not found","request_id":"HmsJ7OBZTNO84nkHAax-fw"}

**Attention points:**
- angular primitive detection
- suppressed waist
- non-traditional zones

---

### dreadnought (acoustic_dread)

**File:** `A003-Dreadnought-MM.pdf`
**Status:** FAIL

**Errors:**
- Harvest failed: no data extracted
- Harvest error: Blueprint extraction error: Submit failed: 404 - {"status":"error","code":404,"message":"Application not found","request_id":"mkZNNbH2SpmBwP_VyCLmYg"}

**Attention points:**
- bout ratios
- waist detection
- symmetry

---

### classical_santos (classical)

**File:** `Classical-Santos-Hernandez-MM.pdf`
**Status:** FAIL

**Errors:**
- Harvest failed: no data extracted
- Harvest error: Blueprint extraction error: Submit failed: 404 - {"status":"error","code":404,"message":"Application not found","request_id":"bmArS1_KRri5B3-_woOzXw"}

**Attention points:**
- bout proportions
- waist position
- classical vs acoustic

---

### es335_complete (semi_hollow)

**File:** `Gibson-335/Gibson-335-Dot-Complete.pdf`
**Status:** FAIL

**Errors:**
- Harvest failed: no data extracted
- Harvest error: Blueprint extraction error: Submit failed: 404 - {"status":"error","code":404,"message":"Application not found","request_id":"6WWpxqQ2Rg2keUkjyCLmYg"}

**Attention points:**
- f-hole detection
- hollow body handling
- cutaway behavior

---

### klein_ergonomic (ergonomic)

**File:** `Klein-Guitar-Plan.pdf`
**Status:** FAIL

**Errors:**
- Harvest failed: no data extracted
- Harvest error: Blueprint extraction error: Submit failed: 404 - {"status":"error","code":404,"message":"Application not found","request_id":"TmcFTewlRYef-GX0ozsQ6Q"}

**Attention points:**
- non-canonical morphology
- zone mapping failure
- hybrid detection

---

### cuatro_pr (latin_folk)

**File:** `El Cuatro/cuatro puertoriqueño.pdf`
**Status:** FAIL

**Errors:**
- Harvest failed: no data extracted
- Harvest error: Blueprint extraction error: Submit failed: 404 - {"status":"error","code":404,"message":"Application not found","request_id":"MOGnenkgQYa1pGRSc9o55Q"}

**Attention points:**
- scale assumptions
- non-guitar morphology
- size handling

---

## Key Observations

### Classification Accuracy

No instruments correctly classified.

### Failure Summary

Total failures recorded: 10

See `docs/governance/MORPHOLOGY_FAILURE_TAXONOMY.md` for details.
