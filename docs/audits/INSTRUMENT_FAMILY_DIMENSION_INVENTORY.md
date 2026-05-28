# Instrument Family Dimension Data-Integrity Inventory

**Date:** 2026-05-27  
**Scope:** Read-only audit of all instrument family dimension sources across the repository  
**Status:** Audit complete, divergences documented, CI guard created

---

## Section 1: Source Registry

| # | File Path | Line | Categories | Schema Fields |
|---|-----------|------|------------|---------------|
| 1 | `services/api/app/instrument_geometry/body/ibg/body_contour_solver.py` | 163 | Acoustic, Electric (4 families: dreadnought, cuatro_venezolano, stratocaster, jumbo) | lower_bout_mm, upper_bout_mm, waist_mm, body_length_mm, waist_y_norm |
| 1b | `services/api/app/instrument_geometry/body/ibg/instrument_body_generator.py` | 78 | Per-instrument (jumbo, etc.) | expected_dimensions: body_length_mm, lower_bout_mm, upper_bout_mm, waist_mm |
| 2 | `services/api/app/instrument_geometry/instrument_specs.py` | 61 | Acoustic, Electric, Archtop, Bass | body_length_mm, upper_bout_width_mm, waist_width_mm, lower_bout_width_mm, waist_y_norm |
| 3 | `services/photo-vectorizer/body_dimension_reference.json` | 11 | Acoustic, Electric, Archtop, Bass | body_length_mm, upper_bout_width_mm, waist_width_mm, lower_bout_width_mm, waist_y_norm |
| 4 | `hostinger/body-outline-editor.html` | 2834 | Acoustic, Electric | bodyLength, lowerBout, upperBout, waist, waistYNorm |
| 5 | `services/api/app/data_registry/system/instruments/body_templates.json` | 8 | Acoustic, Electric | lower_bout_mm, upper_bout_mm, waist_mm, length_mm |
| 6 | `services/api/app/data_registry/edition/parametric/guitar_templates.json` | 53 | Acoustic | lower_bout, upper_bout, waist (constraints) |
| 7 | `services/api/app/instrument_geometry/instrument_model_registry.json` | varies | All | body_dimensions_mm (sparse) |
| 8 | `services/api/app/generators/bezier_body.py` | 77+ | Acoustic | body_length, lower_bout_width, upper_bout_width, waist_width (inches) |
| 9 | `services/api/app/instrument_geometry/guitars/*.py` | varies | Individual models | MODEL_INFO dicts (body_width_mm, body_length_mm) |
| 10 | `services/api/app/instrument_geometry/body/catalog.json` | 11 | DXF metadata | dimensions_mm: width, height (bounding box - excluded) |

**Notes:**
- Source 3 (body_dimension_reference.json) appears to be a copy of Source 2 (instrument_specs.py BODY_DIMENSIONS)
- Source 10 (catalog.json) contains DXF bounding boxes, not body landmark dimensions - excluded from comparison
- Source 8 (bezier_body.py) uses inches, not mm - conversion required for comparison

---

## Section 2: Per-Category Comparison Tables

### Acoustic Flat-Top - Dreadnought

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| IBG FAMILY_DEFAULTS | 381.0 | 292.0 | 241.0 | 520.0 | 0.44 |
| instrument_specs.py | 381 | 292 | 241 | 520 | 0.43 |
| body_dimension_reference.json | 381 | 292 | 241 | 520 | 0.43 |
| body-outline-editor.html | **394** | **286** | **254** | **508** | 0.44 |
| body_templates.json | **396** | **286** | **279** | **508** | - |
| guitar_templates.json | **396** | **286** | **279** | - | - |
| guitars/dreadnought.py | **400** (body_width) | - | - | **510** | - |

**Divergences:**
- body-outline-editor.html: +13mm lower_bout, -6mm upper_bout, +13mm waist, -12mm body_length
- body_templates.json: +15mm lower_bout, -6mm upper_bout, +38mm waist, -12mm body_length
- guitars/dreadnought.py: uses different schema (body_width_mm=400, no bout breakdown)

---

### Acoustic Flat-Top - Jumbo

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| IBG FAMILY_DEFAULTS | 432.0 | 305.0 | 254.0 | 530.0 | 0.44 |
| INSTRUMENT_SPECS (instrument_body_generator.py) | 432.0 | 305.0 | 254.0 | 530.0 | - |
| jumbo_j200.py | 432.0 | 305.0 | 254.0 | 530.0 | - |
| registry: jumbo_j200 | 432.0 | 305.0 | 254.0 | 530.0 | - |
| body-outline-editor.html | 432 | 305 | 254 | 530 | 0.44 |
| instrument_specs.py | **419** | **320** | **272** | **521** | **0.43** |
| body_dimension_reference.json | **419** | **320** | **272** | **521** | **0.43** |
| body_templates.json | 432 | **318** | **279** | **533** | - |

**Divergences:**
- instrument_specs.py / body_dimension_reference.json: -13mm lower_bout, +15mm upper_bout, +18mm waist, -9mm body_length
- body_templates.json: +13mm upper_bout, +25mm waist, +3mm body_length

---

### Acoustic Flat-Top - OM/000

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| instrument_specs.py | 341 | 274 | 228 | 476 | 0.44 |
| body_dimension_reference.json | 341 | 274 | 228 | 476 | 0.44 |
| body-outline-editor.html | **380** | **280** | **254** | **482** | 0.44 |
| guitars/om_000.py | **380** (body_width) | - | - | **490** | - |

**Divergences:**
- body-outline-editor.html: +39mm lower_bout, +6mm upper_bout, +26mm waist, +6mm body_length
- guitars/om_000.py: different schema (body_width_mm only)

---

### Acoustic Flat-Top - Classical

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| instrument_specs.py | 365 | 280 | 225 | 481 | 0.45 |
| body_dimension_reference.json | 365 | 280 | 225 | 481 | 0.45 |
| body-outline-editor.html | **362** | 280 | **242** | **482** | **0.43** |
| guitars/classical.py | **370** (body_width) | - | - | **480** | - |

**Divergences:**
- body-outline-editor.html: -3mm lower_bout, +17mm waist, +1mm body_length
- guitars/classical.py: different schema

---

### Acoustic Flat-Top - Parlor

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| body-outline-editor.html | 304 | 228 | 204 | 400 | 0.42 |

**Note:** Parlor only exists in body-outline-editor.html. No other source defines it.

---

### Acoustic Flat-Top - J-45

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| instrument_specs.py | 394 | 295 | 248 | 506 | 0.44 |
| body_dimension_reference.json | 394 | 295 | 248 | 506 | 0.44 |
| body_templates.json | **412** | **292** | **267** | **504.8** | - |

**Divergences:**
- body_templates.json: +18mm lower_bout, -3mm upper_bout, +19mm waist, -1.2mm body_length

---

### Electric Solid-Body - Stratocaster

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| IBG FAMILY_DEFAULTS | 332.0 | 311.0 | 250.0 | 406.0 | 0.47 |
| instrument_specs.py | **408** | 311 | **308** | 406 | 0.47 |
| body_dimension_reference.json | **408** | 311 | **308** | 406 | 0.47 |
| body-outline-editor.html | **318** | **166** | **220** | **400** | 0.47 |
| body_templates.json | - | - | - | **396** | - |

**Divergences:**
- MAJOR: instrument_specs.py has lower_bout=408 vs FAMILY_DEFAULTS=332 (76mm difference!)
- body-outline-editor.html: significantly different all dimensions
- The Stratocaster schema differs fundamentally - upper_bout/lower_bout don't map cleanly to acoustic guitars

---

### Electric Solid-Body - Les Paul

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| instrument_specs.py | 340 | 283 | 266 | 450 | 0.44 |
| body_dimension_reference.json | 340 | 283 | 266 | 450 | 0.44 |
| body-outline-editor.html | **342** | **166** | **230** | **400** | **0.46** |
| body_templates.json | - | - | - | **444** | - |
| guitars/les_paul.py | **330** (body_width) | - | - | **444** | - |

**Divergences:**
- body-outline-editor.html: +2mm lower_bout, -117mm upper_bout (!), -36mm waist, -50mm body_length

---

### Electric Solid-Body - Telecaster

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| instrument_specs.py | 398 | 311 | 310 | 406 | 0.46 |
| body_dimension_reference.json | 398 | 311 | 310 | 406 | 0.46 |
| body-outline-editor.html | **318** | **204** | **240** | **394** | **0.45** |

**Divergences:**
- body-outline-editor.html: -80mm lower_bout, -107mm upper_bout, -70mm waist, -12mm body_length

---

### Electric Solid-Body - SG

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| instrument_specs.py | 330 | 330 | 180 | 444 | 0.35 |
| body_dimension_reference.json | 330 | 330 | 180 | 444 | 0.35 |
| body_templates.json | - | - | - | 394 | - |

**Divergences:**
- body_templates.json body length differs by 50mm

---

### Electric Solid-Body - Flying V

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| instrument_specs.py | 410 | 380 | 200 | 450 | 0.52 |
| body_dimension_reference.json | 410 | 380 | 200 | 450 | 0.52 |

**Note:** Consistent across known sources.

---

### Electric Solid-Body - Explorer

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| instrument_specs.py | 475 | 410 | 200 | 460 | 0.50 |
| body_dimension_reference.json | 475 | 410 | 200 | 460 | 0.50 |

**Note:** Consistent across known sources.

---

### Semi-Hollow - ES-335

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| instrument_specs.py | 420 | 375 | 295 | 500 | 0.43 |
| body_dimension_reference.json | 420 | 375 | 295 | 500 | 0.43 |
| guitars/es_335.py | - | - | - | - | - |

**Note:** es_335.py has no body dimensions, only neck/scale specifications.

---

### Archtop - Benedetto 17"

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| instrument_specs.py | 431.8 | 279.4 | 228.6 | 482.6 | 0.42 |
| body_dimension_reference.json | 431.8 | 279.4 | 228.6 | 482.6 | 0.42 |

**Note:** Consistent across known sources.

---

### Archtop - Jumbo Archtop

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| instrument_specs.py | 432 | 340 | 248 | 520 | 0.42 |
| body_dimension_reference.json | 432 | 340 | 248 | 520 | 0.42 |

**Note:** Consistent across known sources.

---

### Bass - 4-String (Generic)

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| instrument_specs.py | 370 | 310 | 280 | 430 | 0.45 |
| body_dimension_reference.json | 370 | 310 | 280 | 430 | 0.45 |
| guitars/jazz_bass.py | 340 (body_width) | - | - | 480 | - |

**Divergences:**
- jazz_bass.py uses different schema and different dimensions

---

### Ukulele - Soprano

| Source | lower_bout | upper_bout | waist | body_length |
|--------|------------|------------|-------|-------------|
| guitars/ukulele.py | 200 (body_width) | - | - | 280 |

**Note:** Only one source with limited dimension schema. No concert/tenor/baritone sizes defined.

---

### Cuatro - Venezolano

| Source | lower_bout | upper_bout | waist | body_length | waist_y_norm |
|--------|------------|------------|-------|-------------|--------------|
| IBG FAMILY_DEFAULTS | 250.1 | 156.9 | 130.0 | 350.0 | 0.43 |
| instrument_specs.py | **260** | **180** | **155** | **375** | 0.44 |
| body_dimension_reference.json | **260** | **180** | **155** | **375** | 0.44 |

**Divergences:**
- instrument_specs.py: +10mm lower_bout, +23mm upper_bout, +25mm waist, +25mm body_length

---

## Section 3: Divergences Summary

### Critical Divergences (>10mm difference)

1. **Dreadnought lower_bout:** 381mm (IBG) vs 394-396mm (BOE/templates) - 13-15mm
2. **Dreadnought waist:** 241mm (IBG) vs 254-279mm (BOE/templates) - 13-38mm
3. **Jumbo in instrument_specs.py:** Completely different dimensions than IBG canonical (lower_bout 419 vs 432)
4. **Stratocaster lower_bout:** 332mm (IBG) vs 408mm (instrument_specs.py) - 76mm!
5. **Cuatro venezolano:** All dimensions diverge by 10-25mm between IBG and instrument_specs.py
6. **Electric guitars in body-outline-editor.html:** Upper bout values (~166mm) don't match any other source

### Schema Inconsistencies

1. **guitars/*.py MODEL_INFO** uses `body_width_mm` (single value) instead of `lower_bout_mm/upper_bout_mm`
2. **body_templates.json** uses `length_mm` instead of `body_length_mm`
3. **bezier_body.py** uses inches, not millimeters
4. **body-outline-editor.html** uses camelCase (`lowerBout`) instead of snake_case

### Apples-vs-Oranges Cases (Excluded from Comparison)

1. **catalog.json** - Contains DXF bounding boxes, not body landmark dimensions
2. **Electric guitar bout terminology** - "lower_bout" and "upper_bout" don't map cleanly to solid-body guitars the way they do for acoustic guitars

---

## Section 4: Coverage Gaps

### Families in FAMILY_DEFAULTS vs Other Sources

| Family | IBG FAMILY_DEFAULTS | instrument_specs.py | body-outline-editor.html | body_templates.json |
|--------|---------------------|---------------------|--------------------------|---------------------|
| dreadnought | Yes | Yes | Yes | Yes |
| jumbo | Yes | Yes | Yes | Yes |
| stratocaster | Yes | Yes | Yes | Partial |
| cuatro_venezolano | Yes | Yes (as "cuatro") | No | No |
| om_000 | No | Yes | Yes | No |
| classical | No | Yes | Yes | No |
| parlor | No | No | Yes | No |
| les_paul | No | Yes | Yes | Yes |
| telecaster | No | Yes | Yes | Yes |
| es335 | No | Yes | No | Yes |
| flying_v | No | Yes | No | Yes |
| gibson_sg | No | Yes | No | Yes |
| gibson_explorer | No | Yes | No | No |
| bass_4string | No | Yes | No | No |
| benedetto_17 | No | Yes | No | No |
| j45 | No | Yes | No | Yes |
| archtop | No | Yes | No | Yes |

### Categories Entirely Missing from FAMILY_DEFAULTS

- **All archtop guitars** (ES-335, Benedetto, Jumbo Archtop, L-5, Super 400)
- **All hollow-body electrics**
- **All bass guitars** (P-Bass, J-Bass, short-scale)
- **All ukulele sizes** (soprano, concert, tenor, baritone)
- **All mandolin family** (A-style, F-style, mandola, octave mandolin)
- **Most electric solid-bodies** (Les Paul, Telecaster, SG, Flying V, Explorer, etc.)

### Missing Dimension Fields by Source

| Source | Has lower_bout | Has upper_bout | Has waist | Has body_length | Has depth |
|--------|----------------|----------------|-----------|-----------------|-----------|
| IBG FAMILY_DEFAULTS | Yes | Yes | Yes | Yes | Yes |
| instrument_specs.py | Yes | Yes | Yes | Yes | No |
| body-outline-editor.html | Yes | Yes | Yes | Yes | No |
| body_templates.json | Partial | Partial | Partial | Yes | Partial |
| guitars/*.py | No (uses body_width) | No | No | Yes | Partial |

---

## Section 5: Recommended Canonical Sources per Category

### Acoustic Flat-Top Guitars

**Recommended canonical:** IBG FAMILY_DEFAULTS (`body_contour_solver.py`)

**Reasoning:** This is the source used by the actual body geometry generator (IBG). The body-outline-editor.html and body_templates.json values appear to be older or Martin-specific variants. The instrument_specs.py values for jumbo diverge significantly and may represent a different "jumbo" reference guitar.

**Action needed:** Reconcile instrument_specs.py jumbo dimensions with IBG canonical, or document them as representing different reference instruments.

### Electric Solid-Body Guitars

**No clear canonical source.** 

**Reasoning:** 
- IBG FAMILY_DEFAULTS only has stratocaster
- instrument_specs.py has more entries but the lower_bout/upper_bout terminology doesn't fit solid bodies well
- The 76mm stratocaster lower_bout discrepancy between IBG (332mm) and instrument_specs.py (408mm) needs investigation - these may be measuring different aspects of the body

**Action needed:** Define what "lower_bout" and "upper_bout" mean for solid-body guitars. Current sources appear to interpret this differently.

### Archtop Guitars

**Recommended canonical:** instrument_specs.py BODY_DIMENSIONS

**Reasoning:** Only source with archtop entries. FAMILY_DEFAULTS has no archtop families.

**Action needed:** Add archtop families to FAMILY_DEFAULTS if IBG needs to generate archtop bodies.

### Bass Guitars

**Recommended canonical:** instrument_specs.py BODY_DIMENSIONS

**Reasoning:** Only source with bass entries. FAMILY_DEFAULTS has no bass families.

### Ukuleles

**No canonical source.**

**Reasoning:** Only guitars/ukulele.py exists with minimal dimensions for soprano only. No concert, tenor, or baritone sizes.

**Action needed:** Create ukulele family definitions if ukulele support is planned.

### Mandolin Family

**No source exists.**

**Reasoning:** No mandolin dimension data found anywhere in the repository.

---

## Section 6: Out-of-Scope Findings

These issues were encountered during the audit but are not family-dimension divergences:

1. **Scale length inconsistencies:** Some sources use 25.4" (645.16mm), others use 25.5" (647.7mm) for dreadnought
2. **Neck dimension divergences:** Multiple sources define neck profiles with different depths
3. **Fret count variations:** Some strat specs say 21, others 22, others 24 frets
4. **Soundhole diameter data:** Inconsistent across sources (100mm, 101.6mm, 102mm for jumbo)
5. **Body depth data:** Some sources include depth, others don't
6. **Bracing specifications:** Scattered across multiple files with no single source of truth

---

## Section 7: Family Taxonomy Gaps

1. **"Jumbo" ambiguity:** Used for both flat-top acoustic (J-200 style) and jumbo archtop (17"+ jazz guitar). These are completely different instruments.

2. **"Archtop" overloading:** Used for both carved-top jazz guitars (Benedetto, L-5) and semi-hollow electrics (ES-335). The body geometry differs significantly.

3. **"Solid body" vs specific models:** instrument_specs.py uses family="solid_body" for all electrics, but body-outline-editor.html treats stratocaster/les_paul/telecaster as distinct families.

4. **Missing family hierarchy:** No clear distinction between:
   - Category (acoustic, electric, bass, ukulele)
   - Body style (flat-top, archtop, solid-body, semi-hollow, hollow-body)
   - Family (dreadnought, jumbo, om, stratocaster, les_paul)
   - Model (J-200, D-28, 1959 Standard)

---

## Section 8: Current Test Output

**Test run:** 2026-05-27  
**Result:** 8 failed, 1 passed

```
FAILED test_dreadnought_dimensions_consistent
  AssertionError: body-outline-editor.html dreadnought lower_bout 394.0 != canonical 381.0

FAILED test_jumbo_dimensions_consistent
  AssertionError: instrument_specs.py jumbo lower_bout 419.0 != canonical 432.0

FAILED test_stratocaster_dimensions_consistent
  AssertionError: instrument_specs.py stratocaster lower_bout 408.0 != canonical 332.0

FAILED test_cuatro_venezolano_dimensions_consistent
  AssertionError: instrument_specs.py cuatro lower_bout 260.0 != canonical 250.1

PASSED test_body_dimension_reference_matches_instrument_specs

FAILED test_archtop_families_in_family_defaults
  AssertionError: No archtop families in FAMILY_DEFAULTS. Missing: ['es335', 'benedetto_17', 'jumbo_archtop', 'l5', 'super_400']

FAILED test_bass_families_in_family_defaults
  AssertionError: No bass families in FAMILY_DEFAULTS. Missing: ['bass_4string', 'jazz_bass', 'precision_bass', 'short_scale_bass']

FAILED test_ukulele_families_in_family_defaults
  AssertionError: No ukulele families in FAMILY_DEFAULTS. Missing: ['soprano', 'concert_uke', 'tenor_uke', 'baritone_uke']

FAILED test_electric_families_coverage
  AssertionError: Only 1 electric families in FAMILY_DEFAULTS: ['stratocaster']. Expected at least 3.
```

**Summary of divergences found:**

| Family | Dimension | Canonical (FAMILY_DEFAULTS) | Divergent Source | Divergent Value | Delta |
|--------|-----------|----------------------------|------------------|-----------------|-------|
| dreadnought | lower_bout | 381.0 | body-outline-editor.html | 394.0 | +13mm |
| jumbo | lower_bout | 432.0 | instrument_specs.py | 419.0 | -13mm |
| stratocaster | lower_bout | 332.0 | instrument_specs.py | 408.0 | **+76mm** |
| cuatro | lower_bout | 250.1 | instrument_specs.py | 260.0 | +10mm |

**Coverage gaps confirmed:**
- FAMILY_DEFAULTS has only 4 families: dreadnought, cuatro_venezolano, stratocaster, jumbo
- Missing: all archtop, bass, ukulele families
- Missing electric families: les_paul, telecaster, sg, flying_v, explorer

---

## Appendix A: Source File Excerpts

### IBG FAMILY_DEFAULTS (body_contour_solver.py:163)

```python
FAMILY_DEFAULTS = {
    "dreadnought": {
        "lower_bout_mm": 381.0,
        "upper_bout_mm": 292.0,
        "waist_mm": 241.0,
        "waist_y_norm": 0.44,
        "body_length_mm": 520.0,
        ...
    },
    "jumbo": {
        "lower_bout_mm": 432.0,
        "upper_bout_mm": 305.0,
        "waist_mm": 254.0,
        "waist_y_norm": 0.44,
        "body_length_mm": 530.0,
        ...
    },
    "stratocaster": {
        "lower_bout_mm": 332.0,
        "upper_bout_mm": 311.0,
        "waist_mm": 250.0,
        "waist_y_norm": 0.47,
        "body_length_mm": 406.0,
        ...
    },
    "cuatro_venezolano": {
        "lower_bout_mm": 250.1,
        "upper_bout_mm": 156.9,
        "waist_mm": 130.0,
        "waist_y_norm": 0.43,
        "body_length_mm": 350.0,
        ...
    },
}
```

### INSTRUMENT_TEMPLATES (body-outline-editor.html:2834)

```javascript
const INSTRUMENT_TEMPLATES = {
    dreadnought: {
        name: 'Dreadnought',
        type: 'acoustic',
        dimensions: { bodyLength: 508, lowerBout: 394, upperBout: 286, waist: 254, waistYNorm: 0.44 }
    },
    jumbo: {
        name: 'Jumbo',
        type: 'acoustic',
        dimensions: { bodyLength: 530, lowerBout: 432, upperBout: 305, waist: 254, waistYNorm: 0.44 }
    },
    // ... 6 more templates
};
```
