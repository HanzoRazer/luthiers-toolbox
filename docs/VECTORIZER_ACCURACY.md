# Blueprint Vectorizer Accuracy

**Version:** 1.0.0
**Last validated:** 2026-04-05
**Test corpus:** 3 instruments (Dreadnought, Les Paul, Cuatro)

---

## Accuracy Summary

The blueprint vectorizer extracts geometry from PDF blueprints and produces
DXF files for CAD/CAM workflows. Accuracy varies based on input quality,
blueprint style, and instrument type.

**Validated accuracy (±20% tolerance threshold):**

| Instrument | Expected (W×H mm) | Extracted (W×H mm) | Width Error | Height Error | Status |
|------------|-------------------|---------------------|-------------|--------------|--------|
| Dreadnought | 390 × 505 | 362 × 493 | 7.1% | 2.5% | PASS |
| Gibson Les Paul 59 | 340 × 450 | 284 × 539 | 16.5% | 19.7% | PASS |
| Cuatro Puertorriqueño | 265 × 460 | 258 × 472 | 2.6% | 2.6% | PASS |

**Typical accuracy range:** 2–20% dimensional error depending on input quality.

---

## Five Technical Factors Affecting Accuracy

### 1. Input Resolution and Quality

| Input Type | Expected Accuracy | Notes |
|------------|-------------------|-------|
| Flatbed scan at 300+ DPI | Best (2–8% error) | Known DPI enables precise scale calculation |
| High-quality PDF (vector or 200+ DPI raster) | Good (5–15% error) | Scale detection from reference dimensions |
| Phone photo of blueprint | Variable (10–25% error) | Perspective distortion, uneven lighting |
| Low-resolution PDF (<150 DPI) | Poor (15–30%+ error) | Insufficient detail for edge detection |

**Recommendation:** Use flatbed scans at 300 DPI minimum for best results.

### 2. Blueprint Style and Clarity

- **Clean line drawings** with high contrast produce the best results
- **Multi-view blueprints** (front + side on same page) may confuse body detection
- **Decorative elements** (rosettes, inlays, binding patterns) are not separated
- **Faded or low-contrast prints** reduce edge detection accuracy
- **Hand-drawn sketches** have lower accuracy than CAD-generated plans

### 3. Scale Reference Availability

The vectorizer attempts scale detection in this priority order:

1. **Vision API analysis** — Reads dimension annotations from the blueprint
2. **Spec-based fallback** — Uses known instrument dimensions when spec_name provided
3. **DPI fallback** — Assumes 25.4mm per inch at specified DPI (least accurate)

**Best practice:** Always provide `spec_name` parameter when the instrument type is known.

### 4. Instrument Type Detection

Body contour election uses geometric heuristics:
- Aspect ratio (rejects contours > 2:1 as likely necks or components)
- Minimum dimension (rejects contours < 200mm as likely pickguards)
- Height ceiling (rejects contours > 1.5× expected body height)
- Solidity score (prefers filled shapes over hollow outlines)

Electric guitars with cutaways may have lower solidity scores than acoustic bodies.

### 5. Contour Continuity

Blueprint edge detection produces open contours when:
- Line gaps exist in the original drawing
- Scan artifacts introduce breaks
- Low contrast causes edge dropout

The vectorizer applies gap-closing (default 7px kernel) but cannot recover
gaps larger than ~5mm at typical scan resolutions.

---

## Recommended Workflow

### Before Vectorization

1. **Verify source quality** — Scan at 300+ DPI, ensure high contrast
2. **Identify instrument type** — Know the spec_name for your instrument
3. **Note reference dimension** — Measure one known feature (scale length, body width)

### During Vectorization

```bash
# Best accuracy: provide spec_name and use classified mode
python -m vectorizer_phase3 extract \
    --input blueprint.pdf \
    --spec-name dreadnought \
    --mode classified

# Fallback: raw mode for maximum fidelity (no classification)
python -m vectorizer_phase3 extract \
    --input blueprint.pdf \
    --raw
```

### After Vectorization

1. **Open DXF in CAD software** (Fusion 360, FreeCAD, LibreCAD)
2. **Measure body dimensions** — Compare against known spec
3. **Scale if necessary** — Apply uniform scale factor to match spec
4. **Verify against physical template** — Print at 1:1 and overlay on known-good template
5. **Never cut material** without physical verification

---

## What This Tool IS and IS NOT

### IS

- A **geometry extraction tool** that converts raster blueprints to vector DXF
- A **starting point** for CAD/CAM workflows
- **Accurate enough** for initial design exploration and template creation
- **Faster than manual tracing** for most blueprints

### IS NOT

- A **replacement for physical templates** — Always verify before cutting
- **CAM-ready output** — DXF requires cleanup, layer assignment, toolpath generation
- **Guaranteed accurate** — Dimensional errors of 5–20% are normal
- **A measurement tool** — Do not use extracted dimensions as authoritative
- **Suitable for production** without human verification step

---

## Error Recovery

If extracted dimensions are significantly wrong (>25% error):

1. **Try raw mode** — `--raw` flag bypasses classification, exports all contours
2. **Provide spec_name** — Enables spec-based scale correction
3. **Check input quality** — Rescan at higher DPI if possible
4. **Manual scale** — Measure known feature in DXF, compute and apply scale factor
5. **Report issue** — File GitHub issue with source PDF for vectorizer improvement

---

## Technical Reference

**Validation methodology:**
- Extract with `spec_name` parameter in classified mode
- Compare `dimensions_mm` tuple against known instrument specifications
- Pass threshold: both width and height within ±20% of spec

**Spec sources:**
- Dreadnought: Martin D-28 standard (390mm W × 505mm H)
- Les Paul: Gibson 1959 Standard (340mm W × 450mm H)
- Cuatro: Puerto Rican traditional (265mm W × 460mm H)

**Test commits:**
- Phase 5G validation: `cb0761ed`
- Spec definitions: `vectorizer_phase3.py:INSTRUMENT_SPECS`

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-04-05 | 1.0.0 | Initial accuracy documentation |

---

*This document is part of The Production Shop — Luthiers Toolbox.*
