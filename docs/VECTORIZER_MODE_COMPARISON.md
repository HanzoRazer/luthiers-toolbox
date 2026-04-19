# Vectorizer Mode Comparison

**Date:** 2026-04-19  
**Test File:** 12 String Dreadnaught_1.jpg

## Mode Comparison Results

| Mode | Dimensions | Entities | Closed Contours | File Size | Recommendation |
|------|------------|----------|-----------------|-----------|----------------|
| ENHANCED | 748 × 500 mm | 1,319,757 | 0 | 192 MB | ACCEPT |
| RESTORED_BASELINE | 748 × 500 mm | 902,612 | 601 | 136 MB | REVIEW |
| LAYERED_DUAL_PASS | 450 × 466 mm | 2,808 | 83 | 437 KB | ACCEPT |

## Mode Descriptions

### ENHANCED
- Multi-scale Canny edge detection (30/100, 50/150, 80/200)
- Full edge detail preservation
- No layer classification — all geometry exported
- Produces very large files unsuitable for typical CAD workflows
- Use case: archival, research, or when maximum detail is required

### RESTORED_BASELINE
- Historical 86c49526 behavior (Melody Maker fix)
- Full contour extraction without simplification
- Some closed contour detection (601 closed)
- Large files but with contour structure
- Use case: debugging, comparing against known-good outputs

### LAYERED_DUAL_PASS
- Pass A: SIMPLE extraction with approxPolyDP simplification
- Pass B: Layer classification (BODY, BRACING, ANNOTATION, AUX_VIEWS)
- Extracts BODY dimensions from largest central contour
- Practical file sizes for CAD import
- Use case: **production workflow** — Fusion 360, FreeCAD, etc.

## Key Observations

1. **Dimension Reporting**
   - ENHANCED/BASELINE report full image dimensions (748 × 500 mm)
   - DUAL_PASS reports BODY bounding box dimensions (450 × 466 mm)

2. **Entity Count vs Usability**
   - More entities ≠ better output
   - 1.3M entities causes CAD software to freeze or crash
   - 2,808 entities with 83 closed contours is workable

3. **Closed Contours**
   - ENHANCED: 0 closed (all edge fragments)
   - BASELINE: 601 closed (contour tracing active)
   - DUAL_PASS: 83 closed (simplified, classified)

## Recommendations

- **For production DXF export:** Use `mode=layered_dual_pass`
- **For maximum detail (research):** Use `mode=enhanced`
- **For debugging regressions:** Use `mode=restored_baseline`

## API Usage

```bash
# Production (default)
curl -X POST /api/blueprint/vectorize \
  -F file=@blueprint.jpg \
  -F mode=refined

# Full detail
curl -X POST /api/blueprint/vectorize \
  -F file=@blueprint.jpg \
  -F mode=enhanced

# With spec-based scaling
curl -X POST /api/blueprint/vectorize \
  -F file=@blueprint.jpg \
  -F mode=layered_dual_pass \
  -F spec_name=dreadnought
```

## Sprint 3: Corpus Consistency Validation

**Corpus directory:** `Guitar Plans/`  
**Status:** Corpus curation is open — representative PNG variety TBD.

Validation will run `mode=enhanced` across corpus and report:
- Entity count variance
- Bounding box match vs spec
- Closed-contour rate

## Test Artifacts

Output files from this test run:
- `phase4_output/12_string_dreadnaught_enhanced.dxf` (192 MB)
- `phase4_output/12_string_dreadnaught_baseline.dxf` (136 MB)
- `phase4_output/12_string_dreadnaught_dual_pass.dxf` (437 KB)
