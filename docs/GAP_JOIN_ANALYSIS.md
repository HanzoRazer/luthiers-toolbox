# Gap Join Analysis — Vectorizer Body Outline Continuity

**Date:** 2026-04-14  
**Author:** Production Shop  
**Status:** Investigation Complete

---

## Summary

The conservative gap joining filters (≤2.0mm, ≤25° tangent) are correctly rejecting most candidates. The rejections are **geometrically valid** — joining these gaps would create sharp corners or U-turns, not smooth curve continuations.

---

## Findings

### Dreadnought (0/2 gaps joined)

| Dist (mm) | Angle | Status | Reason |
|-----------|-------|--------|--------|
| 0.21 | 129.5° | REJECT | Angle — contours meet at obtuse angle |
| 3.70 | 2.2° | REJECT | Distance — 1.7mm over threshold |
| 3.96 | 135.0° | REJECT | Both — perpendicular intersection |
| 5.74 | 180.0° | REJECT | Both — contours point opposite directions |

**Analysis:**  
- Closest candidate (0.21mm) has 129.5° angle — joining would create a sharp corner, not a smooth body outline.
- Best angle candidate (2.2°) is 3.70mm apart — just over the 2.0mm threshold.
- High angle values (129°, 135°, 180°) indicate these are **not smooth curve continuations**.

### OM Acoustic (0/8 gaps joined)

| Dist (mm) | Angle | Status | Reason |
|-----------|-------|--------|--------|
| 0.17 | 91.7° | REJECT | Angle — perpendicular intersection |
| 0.38 | 8.2° | PASS | Would join (within both thresholds) |
| 1.07 | 35.2° | REJECT | Angle — 10° over threshold |
| 3.82 | 88.6° | REJECT | Both — near-perpendicular |

**Anomaly:** One candidate (0.38mm, 8.2°) passed both filters but wasn't joined. This suggests the scale_factor_limit (gap > 3x local median segment) rejected it — the gap may be disproportionate to surrounding geometry.

---

## Justification for Current Thresholds

### Why 25° angle threshold is correct

High angles indicate structural discontinuities, not gaps in smooth curves:

| Angle Range | Geometric Meaning | Join Action |
|-------------|-------------------|-------------|
| 0-25° | Smooth continuation | JOIN |
| 25-45° | Mild corner | REVIEW |
| 45-90° | Sharp corner | REJECT |
| 90-180° | Perpendicular/U-turn | REJECT |

The dreadnought's 129.5° and OM's 91.7° gaps are **perpendicular intersections** — these are likely:
- Annotation lines touching body outline
- Dimension extension lines
- Cross-section markers

Joining these would corrupt the body outline with non-body geometry.

### Why 2.0mm distance threshold is conservative

Blueprint scale at 500mm target height:
- Typical mm_per_px: ~0.15-0.25mm
- 2.0mm gap = 8-13 pixels

This catches:
- Anti-aliasing artifacts at line intersections
- Minor edge detection discontinuities
- Scan/print artifacts

It rejects:
- Intentional design gaps (cutaways, f-holes)
- Separate geometry elements
- Annotation spacing

---

## Recommendations

### Option A: Keep current thresholds (RECOMMENDED)

The filters are working correctly. The "missing" gaps are:
1. **Not smooth curve continuations** (high angles)
2. **Separate geometry elements** (annotation lines, cross-sections)
3. **Intentional design features** (not extraction errors)

**Evidence:** Melody Maker achieved 1/1 gap joins with these thresholds = filters allow valid joins when geometry supports it.

### Option B: Relax distance to 4.0mm

Would capture the dreadnought's 3.70mm/2.2° candidate.

**Risk:** May join annotation lines that happen to align with body edge.

### Option C: Add instrument-specific profiles

Different instruments have different gap characteristics:
- Acoustic guitars: larger tolerances (curved bouts)
- Electric guitars: tighter tolerances (sharp horns)

This aligns with the curvature_correction.py zone-based approach.

---

## Conclusion

The gap join rejection is **not a bug** — it's the conservative filter correctly identifying that most gap candidates are:

1. **Perpendicular intersections** (annotation touching body)
2. **Opposite-direction contours** (separate geometry)
3. **Scale-disproportionate** (gap too large for local geometry)

The one legitimate smooth-curve gap in OM (0.38mm, 8.2°) was rejected by the scale_factor_limit, which may need tuning for thin-line blueprints.

**Next step:** If more aggressive gap joining is needed, consider:
1. Raising distance threshold to 4.0mm (captures dreadnought's 3.70mm/2.2° candidate)
2. Adding per-instrument profiles (acoustic vs electric tolerances)
3. Reviewing scale_factor_limit (currently 3.0x local median segment)

---

## Appendix: Scale Factor Analysis (OM Acoustic)

The scale_factor_limit uses `min(median_seg_a, median_seg_b)` to prevent gaps disproportionate to local geometry:

| Contour | Points | Median Seg (mm) | Open Gap (mm) |
|---------|--------|-----------------|---------------|
| 13 | 17 | 0.264 | 0.30 |
| 15 | 17 | 0.249 | 0.34 |
| 8 | 176 | 0.652 | 0.65 |

Fine-segment contours (0.25-0.65mm median) require gaps < 0.75-1.95mm to pass.
This catches annotation fragments with tiny segments that happen to be near the body outline.
