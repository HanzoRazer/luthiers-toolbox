# Vectorizer API Routing & Secret Sauce

**Date:** 2026-05-17  
**Status:** VERIFIED — All modes tested  
**Sprint:** MRP-1C (Photo Vectorizer Resurrection)

---

## Executive Summary

This document captures the complete vectorizer ecosystem routing and the exact parameters ("secret sauce") that produce high-fidelity DXF output. Created after the May 17, 2026 session that resurrected the April 2026 `photo_refined` mode.

---

## API Endpoints Overview

### Primary Vectorization Endpoint

```
POST /api/blueprint/vectorize
Content-Type: multipart/form-data
```

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `file` | (required) | Image or PDF upload |
| `mode` | `refined` | CleanupMode value (see table below) |
| `target_height_mm` | 500.0 | Output scale target |
| `canny_low` | 50 | Edge detection low threshold |
| `canny_high` | 150 | Edge detection high threshold |
| `spec_name` | null | Instrument spec for validation |

### Available Modes

| Mode | Code Path | Use Case | Text Preserved |
|------|-----------|----------|----------------|
| `baseline` | blueprint_extract.py | Regression reference | No |
| `refined` | blueprint_extract.py + cleanup | Production default | No |
| `restored_baseline` | blueprint_extract.py (RETR_LIST) | April 2026 recovery | Partial |
| `enhanced` | blueprint_extract.py (multi-scale) | High detail | No |
| `cam_ready_r2000` | Phase3Vectorizer (R2000) | Paid CAM output | No |
| **`v2_raw`** | vectorizer_phase3._raw_extract() | **PDF blueprints** | **YES** |
| `photo_v2` | edge_to_dxf.convert_enhanced() | AI-generated images | No (masked) |
| **`photo_refined`** | edge_to_dxf.convert() | **Photos of blueprints** | **YES** |

---

## Mode Routing Details

### V2_RAW — For PDF Blueprints (Text Preserved)

**Route:** `CleanupMode.V2_RAW` → `vectorizer_phase3.py:_raw_extract()`

**Code path:**
```
vectorize_router.py
  → blueprint_orchestrator.py (line 533)
    → Phase3Vectorizer.extract(raw_output=True)
      → _raw_extract() (line 2838)
```

**Key parameters:**
```python
# In _raw_extract()
threshold = 120  # Dark line extraction threshold
cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
# CHAIN_APPROX_NONE = every boundary pixel preserved
layer_name = "CONTOURS"
dxf_version = "AC1009"  # R12
```

**CLI equivalent:**
```bash
python vectorizer_phase3.py --raw -o output.dxf input.pdf
```

---

### PHOTO_REFINED — For Photos of Blueprints (Text Preserved)

**Route:** `CleanupMode.PHOTO_REFINED` → `edge_to_dxf.py:EdgeToDXF.convert()`

**Code path:**
```
vectorize_router.py
  → blueprint_orchestrator.py (line 634+)
    → EdgeToDXF(layer_name='CONTOURS').convert(
        morph_close_kernel=0,  # CRITICAL: no closing preserves text
        max_entities=0,        # No cap
      )
```

**Key parameters (SECRET SAUCE):**
```python
# EdgeToDXF initialization
layer_name = 'CONTOURS'
canny_low = 50   # Default
canny_high = 150 # Default

# convert() call
target_height_mm = 500.0
blur_kernel = 3           # Gaussian blur
morph_close_kernel = 0    # CRITICAL: 0 = disabled, preserves text strokes
isolate_body = False      # Include all contours
max_entities = 0          # No cap (can produce 1GB+ files)
```

**CLI equivalent (sandbox runner):**
```bash
cd services/blueprint-import/sandbox/text_geometry_eval/runners
python -c "
import sys
sys.path.insert(0, '../../../../photo-vectorizer')
from edge_to_dxf import EdgeToDXF

converter = EdgeToDXF(layer_name='CONTOURS')
result = converter.convert(
    'input.jpg',
    output_path='output.dxf',
    target_height_mm=500.0,
    morph_close_kernel=0,  # TEXT PRESERVATION
)
"
```

---

### PHOTO_V2 — For AI-Generated Images (Text Removed)

**Route:** `CleanupMode.PHOTO_V2` → `edge_to_dxf.py:EdgeToDXF.convert_enhanced()`

**Key parameters:**
```python
# convert_enhanced() uses:
edge_levels = [
    (30, 100),   # Fine detail
    (50, 150),   # Standard
    (80, 200),   # Strong edges
]
gap_close_size = 7      # Morphological closing ENABLED
mask_text = True        # Text regions detected and removed
```

**Use when:** AI-generated images where text doesn't matter or should be removed.

---

## Direct Edge-to-DXF Endpoints

Separate from the main `/api/blueprint/vectorize` endpoint:

### Standard Conversion
```
POST /api/blueprint/edge-to-dxf/convert
```

### Enhanced Multi-Scale
```
POST /api/blueprint/edge-to-dxf/enhanced
```

### Status Check
```
GET /api/blueprint/edge-to-dxf/status
```

---

## Other Vectorizer Endpoints

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `/api/blueprint/vectorize/async` | Async job submission | Active |
| `/api/blueprint/vectorize/status/{job_id}` | Job status check | Active |
| `/api/blueprint/vectorize/download/{job_id}` | Download result | Active |
| `/api/blueprint/phase2/vectorize-geometry` | Phase 2 vectorizer | Legacy |
| `/api/blueprint/phase3/vectorize` | Phase 3 direct | Active |
| `/api/photo-vectorizer/extract` | Photo vectorizer v2 | Active |

---

## Secret Sauce: Test File Generation Commands

### Gibson Double-Neck REFINED (418 MB)

```python
from edge_to_dxf import EdgeToDXF

converter = EdgeToDXF(layer_name='CONTOURS')
result = converter.convert(
    'Guitar Plans/Gibson-Double-Neck-esd1275.png',
    output_path='test_gibson_doubleneck_REFINED.dxf',
    target_height_mm=500.0,
    morph_close_kernel=0,
)
# Result: 2,812,722 LINE entities, 17,672 contours
```

### Cuatro PDF V2_RAW (121.7 MB)

```bash
python vectorizer_phase3.py --raw \
    -o test_cuatro_raw_output.dxf \
    "Guitar Plans/El Cuatro/cuatro puertoriqueño.pdf"
# Result: 1,150,754 LINE entities, CONTOURS layer
```

### Cuatro Photo REFINED (294 MB)

```python
# After PDF rasterization at 400 DPI
converter = EdgeToDXF(layer_name='CONTOURS')
result = converter.convert(
    temp_raster_path,  # 400 DPI PNG from PyMuPDF
    output_path='test_cuatro_REFINED.dxf',
    target_height_mm=500.0,
    morph_close_kernel=0,
)
# Result: 2,022,289 LINE entities
```

### Benedetto Photos REFINED

```python
# Higher Canny thresholds for photo texture
converter = EdgeToDXF(layer_name='CONTOURS', canny_low=80, canny_high=200)
result = converter.convert(
    'Guitar Plans/Archtop Measurements/Benedetto Front.jpg',
    output_path='test_Benedetto_Front_REFINED.dxf',
    target_height_mm=500.0,
    morph_close_kernel=0,
    max_entities=0,  # No cap
)
# Result: 7,569,901 LINE entities, 1.13 GB
```

---

## Output Signature Comparison

| File | Mode | Entities | Size | Layer |
|------|------|----------|------|-------|
| March 6 Reference | Unknown | 128,997 | 15.5 MB | CONTOURS |
| Cuatro V2_RAW | `--raw` | 1,150,754 | 121.7 MB | CONTOURS |
| Cuatro PHOTO_REFINED | `photo_refined` | 2,022,289 | 294 MB | CONTOURS |
| Gibson Double-Neck | `photo_refined` | 2,812,722 | 418 MB | CONTOURS |
| Benedetto Front | `photo_refined` | 7,569,901 | 1.13 GB | CONTOURS |
| Benedetto Back | `photo_refined` | 2,574,644 | 384 MB | CONTOURS |

---

## Decision Tree: Which Mode to Use

```
Input Type?
├── PDF Blueprint
│   └── Use: mode=v2_raw
│       → vectorizer_phase3._raw_extract()
│       → Text preserved, CONTOURS layer
│
├── Photo of Blueprint (need text)
│   └── Use: mode=photo_refined
│       → edge_to_dxf.convert(morph_close_kernel=0)
│       → Text preserved, large files
│
├── AI-Generated Image (no text needed)
│   └── Use: mode=photo_v2
│       → edge_to_dxf.convert_enhanced()
│       → Text masked, cleaner geometry
│
└── Standard Blueprint Processing
    └── Use: mode=refined (default)
        → Blueprint pipeline with cleanup
        → Classified layers
```

---

## Protection Notes

All recovery modes are tagged as `PROTECTED_EXPERIMENTAL_RECOVERY_MODE` in the code.

**DO NOT MODIFY** the following without reviewing the archaeology handoff:
- `_raw_extract()` in vectorizer_phase3.py
- `convert()` parameters in PHOTO_REFINED routing
- `convert_enhanced()` parameters in PHOTO_V2 routing

Reference: `docs/handoffs/MRP_1C_VECTORIZER_V2_ARCHAEOLOGY_HANDOFF.md`

---

## Files Modified (2026-05-17)

| File | Change |
|------|--------|
| `services/api/app/services/blueprint_clean.py` | Added `PHOTO_REFINED` to CleanupMode |
| `services/api/app/services/blueprint_orchestrator.py` | Added PHOTO_REFINED extraction and cleanup bypass |

---

*Vectorizer API Routing & Secret Sauce — 2026-05-17*
