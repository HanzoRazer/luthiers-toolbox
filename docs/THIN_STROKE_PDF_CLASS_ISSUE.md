# Thin-Stroke Fragmented Blueprint PDF Class Issue

**Status:** Open diagnostic case  
**Date identified:** 2026-04-14  
**Affects:** Pass A structural extraction

## Summary

The current structural extraction path is less reliable on blueprint PDFs whose body/profile geometry is defined by extremely thin, partially discontinuous strokes. These files may produce fragmented structural contours even when higher-DPI rasterization improves annotation readability.

## Class characteristics

Blueprint PDFs affected by this limitation share these traits:

- Very thin line weights (1-2px even at 300 DPI)
- Fragmented source outline construction
- Weak stroke continuity after rasterization
- Profile strokes that rasterize into disconnected contour segments

## What was tested

| Approach | Result |
|----------|--------|
| Morphological close (3x3) | Made fragmentation worse |
| Lower epsilon (0.001 → 0.00075) | Improved some stats but regressed text fidelity |
| Higher DPI (200 → 250/300) | Marginal stroke width improvement, gaps remain |

## Why global changes were not adopted

Global simplification changes improved some contour-closure statistics but introduced regressions in other files (OM text became incomplete). The tradeoff indicated two different structural regimes:

1. **Profile/outline curves** - benefit from lower simplification
2. **Fine drafting strokes / text-adjacent linework** - degrade under same policy

A single flat epsilon rule cannot optimize both simultaneously.

## Recommended next steps

1. Build diagnostic overlay comparing:
   - Source grayscale
   - Post-threshold binary  
   - Pre-simplification contours
   - Post-simplification BODY contours

2. Implement selective contour policy within Pass A:
   - **Profile candidate path**: lower epsilon for long curved structural contours
   - **General structural path**: stable epsilon for everything else

3. Evaluate fixes against a class of similar PDFs, not just one file

## Files in this class (known)

- `A003-Dreadnought-MM.pdf` - confirmed thin-stroke fragmentation

## Files NOT in this class

- `Gibson-Melody-Maker.pdf` - production_ready quality
- `OM_acoustic_guitar_en.pdf` - usable quality, good text fidelity
- `Classical-Santos-Hernandez-MM.pdf` - usable quality
