# EdgeToDXF Test Procedures

**Date:** 2026-04-27  
**Tool:** `services/photo-vectorizer/edge_to_dxf.py`  
**Output Directory:** `services/api/test_temp/vectorizer_test_april21/`

---

## Overview

The EdgeToDXF converter transforms image edges directly into DXF LINE entities for high-fidelity archival of guitar blueprints and photos. It captures every detected edge pixel as vector geometry.

---

## CLI Usage

### Basic Command

```bash
cd services/photo-vectorizer
python edge_to_dxf.py "<source_image>" -o "<output.dxf>" --height 500
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `source` | (required) | Input image path (PNG, JPG, PDF) |
| `-o, --output` | `{source}_edges.dxf` | Output DXF path |
| `--height` | 500 | Target height in mm for scaling |
| `--canny-low` | 50 | Canny edge detection low threshold |
| `--canny-high` | 150 | Canny edge detection high threshold |
| `--adjacency` | 3.0 | Max pixel distance to connect edges |
| `--enhanced` | (flag) | Use multi-scale edge fusion |
| `--max-entities` | 5000000 | Per-image LINE entity cap (0=unlimited) |
| `--aggregate-cap` | 12000000 | Total cap for combine mode (0=unlimited) |
| `--batch` | (flag) | Combine multiple images into single DXF |
| `--spacing` | 50 | Space between images in batch mode (mm) |
| `--layout` | vertical | Layout: `vertical` (stack) or `grid` |
| `--grid-columns` | 4 | Columns for grid layout |
| `--separate-batch` | (flag) | Process each input to separate DXF |
| `--output-dir` | (auto) | Output directory for separate batch |
| `--recursive` | (flag) | Descend into subdirectories |
| `--pattern` | (all) | Glob pattern to filter inputs |
| `--skip-existing` | (flag) | Skip if output exists |

### Entity Cap System

Per-image cap (5M default) prevents memory exhaustion on texture-heavy images.
Aggregate cap (12M default) prevents combined DXFs from becoming unmanageable.

```bash
# Per-image cap test (will trigger on Benedetto Front at default thresholds)
python edge_to_dxf.py "Benedetto Front.jpg" --max-entities 5000000

# Output on cap exceeded:
# Edge-to-DXF Cap Exceeded
#   Entities at failure: 5,000,001
#   Cap: 5,000,000
#   Recommendation: Use higher edge thresholds (--canny-low 80 --canny-high 200)
```

### Batch Mode

Combine multiple images (e.g., 24 Fender headstock pages) into a single DXF:

```bash
# Multiple files
python edge_to_dxf.py page1.png page2.png page3.png --batch -o combined.dxf

# Directory of images
python edge_to_dxf.py "Guitar Plans/Fender Headstocks/" -o headstocks.dxf

# Zip file
python edge_to_dxf.py headstocks.zip -o headstocks.dxf --layout grid --grid-columns 6

# Vertical stack with custom spacing
python edge_to_dxf.py *.png --batch --spacing 100 -o stacked.dxf
```

Each image is placed on its own layer (e.g., `IMAGE_01_FILENAME`, `IMAGE_02_FILENAME`).

### Separate Batch Mode

Process each image in a directory to its own DXF file, with JSON report:

```bash
# Basic separate batch
python edge_to_dxf.py "Guitar Plans/" --separate-batch --output-dir outputs/

# With filtering and skip-existing
python edge_to_dxf.py "Guitar Plans/" --separate-batch --output-dir outputs/ \
  --pattern "*.png" --skip-existing --recursive

# Output: batch_report.json
# {
#   "aggregate": {"total_files": 125, "success_count": 118, "failure_count": 7, ...},
#   "files": [{"input_path": "...", "status": "SUCCESS", "entity_count": 769604}, ...]
# }
```

### Unicode Filename Support

Files with non-ASCII characters (e.g., `cuatro puertoriqueño.png`) are now handled via a fallback loader when OpenCV's standard imread fails.

### Threshold Guidelines

| Image Type | Recommended | Notes |
|------------|-------------|-------|
| Clean blueprints (scanned) | 50/150 (default) | Good balance |
| High-detail photos | 80/200 | Reduces edge noise |
| Low-contrast blueprints | 30/100 | Captures faint lines |
| Photos with wood grain | 100/250 | Minimizes texture |

---

## Test Run: 2026-04-27

### Test Files

**Source Directory:** `Guitar Plans/`

| File | Type | Resolution | Notes |
|------|------|------------|-------|
| Acoustic-Archtop-Bailey_Page_1.png | Blueprint scan | 9364x6623 | Multi-view acoustic |
| Acoustic-Archtop-Bailey_Page_2.png | Blueprint scan | 9364x6623 | Multi-view acoustic |
| 12 String Dreadnaught_1.jpg | Photo | 10785x7208 | High texture |
| 12 StringDreadnaught_2.jpg | Photo | 10764x7165 | High texture |
| Benedetto/Benedetto Front.jpg | Photo | 15225x10797 | Archtop, wood grain |
| Benedetto/Benedetto Back.jpg | Photo | 15346x8652 | Archtop, wood grain |

### Results: Default Thresholds (50/150)

| File | Edge Pixels | Contours | LINE Entities | Size | Status |
|------|-------------|----------|---------------|------|--------|
| Bailey_Page1 | 516,068 | 1,227 | 955,692 | 139 MB | SUCCESS |
| Bailey_Page2 | 280,798 | 346 | 544,796 | 79 MB | SUCCESS |
| 12 String Dread 1 | 2,402,855 | 13,968 | — | — | FAILED (MemoryError) |
| 12 String Dread 2 | 1,735,513 | 13,086 | 3,123,516 | 456 MB | SUCCESS |
| Benedetto Front | 4,494,477 | 69,811 | — | — | FAILED (MemoryError) |
| Benedetto Back | 1,540,333 | 16,056 | 2,669,225 | 389 MB | SUCCESS |

### Results: High Thresholds (80/200) - Retry of Failures

| File | Edge Pixels | Contours | LINE Entities | Size | Status |
|------|-------------|----------|---------------|------|--------|
| 12 String Dread 1 | 2,395,287 | 12,430 | 4,260,743 | 622 MB | SUCCESS |
| Benedetto Front | 4,369,396 | 55,705 | 7,569,875 | 1,106 MB | SUCCESS |

---

## Memory Limits

The converter hits Python MemoryError when:
- Edge pixels > 4M AND contours > 60K
- Total LINE entities approaches 8M+

### Mitigation Strategies

1. **Raise Canny thresholds** — Reduces edge count by ~10-20%
2. **Downsample image** — Pre-process with ImageMagick: `convert input.jpg -resize 50% output.jpg`
3. **Use `--enhanced` mode** — Multi-scale fusion may produce cleaner results
4. **Batch by region** — Crop image into quadrants, process separately

---

## Output Characteristics

- **Format:** DXF R12 (AC1009) for maximum CAD compatibility
- **Entities:** Individual LINE segments (not LWPOLYLINE)
- **Layer:** `CONTOURS` (single layer)
- **Scale:** Calculated from `--height` parameter
- **Coordinates:** mm, Y-up orientation

### File Size Estimation

```
Approximate file size = LINE_entities * 145 bytes
```

| Entities | Approx Size |
|----------|-------------|
| 100,000 | 15 MB |
| 500,000 | 73 MB |
| 1,000,000 | 145 MB |
| 3,000,000 | 437 MB |
| 5,000,000 | 725 MB |

---

## API Endpoint

The same functionality is available via API:

```bash
# Check status
curl http://127.0.0.1:8000/api/blueprint/edge-to-dxf/status

# Convert (returns JSON metadata)
curl -X POST http://127.0.0.1:8000/api/blueprint/edge-to-dxf/convert \
  -F "file=@image.png" \
  -F "target_height_mm=500" \
  -F "canny_low=50" \
  -F "canny_high=150"

# Convert with file download
curl -X POST http://127.0.0.1:8000/api/blueprint/edge-to-dxf/convert \
  -F "file=@image.png" \
  -F "return_file=true" \
  -o output.dxf
```

---

## Previous Test Results (Morning Session)

| File | LINE Entities | Size |
|------|---------------|------|
| Gibson-Melody-Maker_edges.dxf | 769,604 | 110 MB |
| A003-Dreadnought-MM_edges.dxf | 1,017,490 | 148 MB |
| Acoustic-Orchestra-Model-MM_edges.dxf | 1,103,297 | 161 MB |
| Gibson-Double-Neck-esd1275_edges.dxf | 1,360,054 | 198 MB |

---

## Notes

- The Gibson L0 blueprint (attached image) shows a typical scanned blueprint with dimensions, bracing patterns, and section views — ideal for EdgeToDXF processing
- Photos with wood grain texture (Benedetto) generate extremely high entity counts due to texture edges
- Blueprint scans (Bailey) produce cleaner results with fewer entities
- Processing time scales with entity count: ~500K entities/minute on save

---

## File Locations

```
services/api/test_temp/vectorizer_test_april21/
├── A003-Dreadnought-MM_edges.dxf
├── Acoustic-Orchestra-Model-MM_edges.dxf
├── Gibson-Double-Neck-esd1275_edges.dxf
├── Gibson-Melody-Maker_edges.dxf
├── Bailey_Page1_edges.dxf
├── Bailey_Page2_edges.dxf
├── Bailey_combined.dxf              # Batch: 2 images, 1.49M lines
├── 12String_Dread_1_edges_high_thresh.dxf
├── 12String_Dread_2_edges.dxf
├── Benedetto_Back_edges.dxf
├── Benedetto_Front_edges_high_thresh.dxf
├── cuatro_pr_unicode_test.dxf       # Unicode filename test
└── EDGE_TO_DXF_TEST_PROCEDURES.md

## Performance Summary

| Metric | Min | Max | Notes |
|--------|-----|-----|-------|
| Processing time | 91s | 1088s | Scales with entity count |
| Edge pixels | 281K | 4.4M | High texture = more edges |
| Contours | 346 | 55,705 | Photos >> blueprints |
| LINE entities | 545K | 7.57M | Direct function of edges |
| File size | 79 MB | 1.1 GB | ~145 bytes/entity |

**Threshold impact:** Higher thresholds (80/200) reduced contour count by ~20% on high-texture photos but still produced millions of entities due to wood grain.
```
