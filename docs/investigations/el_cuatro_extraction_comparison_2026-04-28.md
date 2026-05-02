# El Cuatro Extraction Comparison: SIMPLE vs EdgeToDXF

**Date:** 2026-04-28  
**Test File:** `Guitar Plans/El Cuatro/El Cuatro 1.pdf`  
**Image Size:** 3400×4400px at 400 DPI

---

## Executive Summary

Both extractors successfully processed the El Cuatro blueprint. **EdgeToDXF produces 3× more geometry at 3× the file size**, while SIMPLE runs faster and produces smaller files. The choice depends on whether fidelity or file size is the priority.

| Metric | SIMPLE | EdgeToDXF REFINED | Ratio |
|--------|--------|-------------------|-------|
| File size | 20 MB | 60 MB | 3.0× |
| LINE entities | 184,720 | 421,196 | 2.3× |
| Contours detected | 781 | 1,753 | 2.2× |
| Runtime | 20.5s | ~120s | ~6× |
| Coordinates | Pixel | mm (500mm height) | — |
| Layer | CONTOURS | EDGES | — |

---

## Key Differences

### Edge Detection Method

| Aspect | SIMPLE | EdgeToDXF |
|--------|--------|-----------|
| Algorithm | Threshold (< 120) | Canny (50/150) |
| Pre-processing | None | Gaussian blur 3×3 |
| What it captures | Dark pixels only | Gradient edges |

**Result:** Canny detects both sides of every line, doubling edge count. Threshold captures only the darkest pixels.

### Coordinate System

- **SIMPLE:** Pixel coordinates. User must scale in CAD.
- **EdgeToDXF:** mm coordinates, scaled to 500mm target height. Ready for CAD use.

### Contour Count

EdgeToDXF detected 2.2× more contours (1,753 vs 781). This includes:
- Finer detail in text strokes
- Both inner and outer edges of lines
- Noise edges from gradient detection

---

## Output Files

| File | Path |
|------|------|
| SIMPLE | `outputs/el_cuatro_comparison/El Cuatro 1_phase3.dxf` |
| EdgeToDXF | `outputs/el_cuatro_comparison/El Cuatro 1_edges.dxf` |

---

## Recommendation

| Use Case | Recommended |
|----------|-------------|
| Quick extraction, small files | **SIMPLE** |
| Maximum fidelity, archival | **EdgeToDXF** |
| CAD-ready coordinates | **EdgeToDXF** |
| Downstream processing (simplification, classification) | **SIMPLE** (less noise) |

---

## Technical Notes

- Both use R12 DXF format with LINE entities
- Both use CHAIN_APPROX_NONE (no simplification)
- SIMPLE extracts 352,529 dark pixels → 781 contours
- EdgeToDXF extracts 223,839 edge pixels → 1,753 contours
- The edge pixel count is lower but contour count is higher because Canny finds more distinct boundaries
