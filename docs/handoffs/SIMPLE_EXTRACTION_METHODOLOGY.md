# SIMPLE Extraction: Methodology & Developer Handoff

**Date:** 2026-04-28  
**Status:** VALIDATED — Production-ready alongside EdgeToDXF REFINED  
**Output Location:** `services/blueprint-import/sandbox/text_geometry_eval/outputs/`

---

## Executive Summary

SIMPLE extraction is the `--raw` mode of `vectorizer_phase3.py`. It uses fixed-threshold dark line extraction with no classification, no filtering, and no scale conversion. Outputs are in pixel coordinates.

**Key insight:** SIMPLE produces smaller files than EdgeToDXF REFINED (~40-50% reduction) because it uses threshold-based masking rather than Canny edge detection, resulting in fewer boundary pixels.

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SIMPLE Extraction Pipeline                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. PDF RASTERIZATION (if needed)                                   │
│     ├── PyMuPDF (fitz) at 400 DPI                                   │
│     └── Output: in-memory numpy array                               │
│                                                                      │
│  2. DARK LINE MASK                                                   │
│     ├── extract_dark_lines(image, threshold=120)                    │
│     └── Binary mask: pixels < 120 brightness → white                │
│                                                                      │
│  3. CONTOUR TRACING                                                  │
│     ├── cv2.findContours(RETR_TREE, CHAIN_APPROX_NONE)              │
│     ├── NO simplification — every boundary pixel preserved          │
│     └── Filter: contours with < 2 points discarded                  │
│                                                                      │
│  4. COORDINATE TRANSFORM                                             │
│     ├── Pixel coordinates only — NO mm conversion                   │
│     ├── Y-axis flipped for CAD coordinate convention                │
│     └── float(x), float(image_height - y)                           │
│                                                                      │
│  5. DXF GENERATION                                                   │
│     ├── Format: R12 (AC1009) for maximum compatibility              │
│     ├── Entity type: LINE (via add_polyline with version='R12')     │
│     ├── All contours closed (last point → first point)              │
│     ├── Layer: "CONTOURS"                                           │
│     └── No entity cap                                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Parameters (SIMPLE Mode)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `threshold` | 120 | Dark line extraction cutoff |
| `contour_mode` | RETR_TREE | Hierarchical contours |
| `contour_method` | CHAIN_APPROX_NONE | No simplification |
| `coordinates` | Pixel | No mm scaling applied |
| `dxf_version` | R12 | Maximum CAD compatibility |
| `layer` | CONTOURS | Single layer, no classification |

---

## Source Code Location

| File | Line | Purpose |
|------|------|---------|
| `services/blueprint-import/vectorizer_phase3.py` | 2838 | `_raw_extract()` method |
| `services/blueprint-import/dxf_compat.py` | — | R12 LINE entity generation |

---

## Call Chain

```
CLI: python vectorizer_phase3.py --raw input.pdf output.dxf
    │
    ▼
VectorizerPhase3.extract(raw_mode=True)
    │
    ▼
_raw_extract(image, output_path, source_path)
    │
    ├── extract_dark_lines(image, threshold=120)
    │       └── Binary mask of dark pixels
    │
    ├── cv2.findContours(mask, RETR_TREE, CHAIN_APPROX_NONE)
    │       └── All boundary pixels as contours
    │
    ├── Y-flip: (x, image_height - y)
    │
    └── add_polyline(msp, points, layer='CONTOURS', closed=True, version='R12')
            └── LINE entities to DXF
```

---

## Comparison: SIMPLE vs EdgeToDXF REFINED

### Methodology Differences

| Aspect | SIMPLE | EdgeToDXF REFINED |
|--------|--------|-------------------|
| Edge detection | Threshold (< 120) | Canny (50/150) |
| Pre-processing | None | Gaussian blur (3×3) |
| Morphological ops | None | Optional (kernel=0 in REFINED) |
| Contour method | CHAIN_APPROX_NONE | CHAIN_APPROX_NONE |
| Coordinates | Pixel | mm (target_height=500mm) |
| Layer name | CONTOURS | EDGES |
| Source file | vectorizer_phase3.py | edge_to_dxf.py |

### Output Comparison (Test Suite)

| Blueprint | SIMPLE | EdgeToDXF REFINED | Ratio |
|-----------|--------|-------------------|-------|
| cuatro puertoriqueño | 122 MB | 295 MB | 0.41× |
| Gibson-Melody-Maker | 167 MB | 452 MB | 0.37× |
| Fender-Stratocaster-62 | 134 MB | 367 MB | 0.37× |
| Guitar-Jumbo-MM-A0 | 176 MB | 494 MB | 0.36× |

**SIMPLE produces 36-41% of EdgeToDXF REFINED file size.**

### Why the Size Difference?

1. **Threshold vs Canny:** Threshold-based extraction captures only the darkest pixels. Canny edge detection finds gradient boundaries, which includes more edge pixels (both sides of lines).

2. **No blur:** SIMPLE operates on raw pixels. EdgeToDXF's Gaussian blur slightly expands edge regions.

3. **Same contour method:** Both use CHAIN_APPROX_NONE, so the difference is purely in what pixels are detected as "edges."

---

## When to Use Each

| Use Case | Recommended Extractor |
|----------|----------------------|
| PDF blueprints (line art) | **SIMPLE** — smaller files, cleaner lines |
| Scanned images (photos) | **EdgeToDXF REFINED** — better noise handling |
| Text preservation critical | **EdgeToDXF REFINED** — Canny preserves text strokes |
| File size constrained | **SIMPLE** — ~40% smaller output |
| Needs mm scaling | **EdgeToDXF REFINED** — built-in target_height_mm |

---

## Output Files (Validated)

| Blueprint | Output Path |
|-----------|-------------|
| cuatro puertoriqueño | `outputs/cuatro_puertoriqueño_SIMPLE.dxf` |
| Gibson-Melody-Maker | `outputs/Gibson-Melody-Maker_SIMPLE.dxf/Gibson-Melody-Maker_phase3.dxf` |
| Fender-Stratocaster-62 | `outputs/Fender-Stratocaster-62_SIMPLE.dxf/Fender-Stratocaster-62_phase3.dxf` |
| Guitar-Jumbo-MM-A0 | `outputs/Guitar-Jumbo-MM-A0_SIMPLE.dxf/Guitar-Jumbo-MM-A0_phase3.dxf` |

Note: Some outputs have nested directory structure due to a naming bug in the test run.

---

## Known Limitations

1. **Pixel coordinates:** No real-world scaling. User must scale in CAD software.

2. **No classification:** All geometry goes to single "CONTOURS" layer. No body/neck/fret separation.

3. **Threshold sensitivity:** Fixed threshold (120) may miss lighter lines or include noise on low-contrast blueprints.

4. **No text handling:** Text is extracted as contours, same as geometry.

---

## Integration Status

| Component | Status |
|-----------|--------|
| CLI (`--raw` flag) | Working |
| API endpoint | NOT WIRED |
| Frontend | NOT WIRED |

---

## Verification Command

```bash
cd services/blueprint-import
python vectorizer_phase3.py --raw "path/to/blueprint.pdf" "./output.dxf"
```

Output: `output.dxf` with all dark lines as LINE entities on CONTOURS layer.

---

## Related Documentation

- [EDGE_TO_DXF_REFINED_METHODOLOGY.md](EDGE_TO_DXF_REFINED_METHODOLOGY.md) — EdgeToDXF REFINED handoff
- [EDGE_TO_DXF_API_MIGRATION_HANDOFF.md](EDGE_TO_DXF_API_MIGRATION_HANDOFF.md) — API migration notes
