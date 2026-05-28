# Body Dimension Extraction Chronicle

**Document Type:** Developer Handoff - Procedure Reproduction Guide  
**Created:** 2026-05-27  
**Status:** Reference Implementation  
**Purpose:** Enable reproduction of instrument body dimension extraction sessions

---

## Executive Summary

This document chronicles the process, technology, and procedures used to extract instrument body dimensions from blueprints and DXF files. The extracted data populates:

1. `services/photo-vectorizer/body_dimension_reference.json` (14 specs)
2. `services/api/app/instrument_geometry/body/catalog.json` (23 bodies)
3. `services/api/app/instrument_geometry/specs/all_extractions.json` (16 extractions)

**Key Sessions:**
- **December 2025:** Initial DXF catalog extraction (16 instruments)
- **March 21, 2026:** Diff 3 spec-prior system (14 landmark specs)
- **April 1, 2026:** Carlos Jumbo 1:1 blueprint calibration
- **April 9, 2026:** Benedetto 17-inch archtop addition

---

## Part 1: Technology Stack

### Core Dependencies

```python
# Required packages
cv2                    # OpenCV - image processing, edge detection
numpy                  # Numerical operations, array manipulation
fitz (PyMuPDF)         # PDF to image conversion
ezdxf                  # DXF file reading and writing

# Optional enhancements
sklearn                # ML-based contour classification
joblib                 # Model persistence
```

### File Locations

| Component | Path |
|-----------|------|
| Main vectorizer | `services/blueprint-import/vectorizer_phase3.py` |
| Pixel calibrator | `services/blueprint-import/calibration/pixel_calibrator.py` |
| Dimension extractor | `services/blueprint-import/calibration/dimension_extractor.py` |
| Scale detector | `services/blueprint-import/calibration/scale_detector.py` |
| Landmark extractor | `services/photo-vectorizer/landmark_extractor.py` |
| Body model | `services/photo-vectorizer/body_model.py` |
| Geometry authority | `services/photo-vectorizer/geometry_authority.py` |
| DXF compatibility | `services/blueprint-import/dxf_compat.py` |

### Extraction Scripts

| Script | Purpose |
|--------|---------|
| `scripts/extract_benedetto.py` | Archtop front/back extraction |
| `scripts/extract_jazzmaster_*.py` | Multiple Jazzmaster approaches |
| `scripts/extract_gibson_335.py` | ES-335 semi-hollow extraction |
| `scripts/extract_j45_bracing.py` | J-45 with bracing data |
| `scripts/extract_selmer*.py` | Selmer Maccaferri D-hole |
| `calibrate_carlos_jumbo.py` | 1:1 blueprint calibration |

---

## Part 2: Extraction Pipeline

### Stage 1: Input Acquisition

**Supported Input Types:**
- PDF blueprints (converted to image via PyMuPDF at 150-300 DPI)
- DXF files (parsed directly via ezdxf)
- Raster images (JPEG, PNG)

**PDF Conversion:**
```python
import fitz

def pdf_page_to_image(pdf_path: Path, page_num: int = 0, dpi: int = 300) -> np.ndarray:
    doc = fitz.open(str(pdf_path))
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    doc.close()
    return img
```

### Stage 2: Scale Calibration

**Calibration Methods (priority order):**

1. **SCALE_LENGTH** - Detect labeled scale length (e.g., "25.5 scale")
2. **SOUNDHOLE** - Use known soundhole diameter (acoustic: 102mm typical)
3. **RULER** - Detect ruler markings in image
4. **PAPER_SIZE** - Assume standard paper size (A4, Letter, Arch D)
5. **BODY_HEURISTIC** - Assume typical body proportions
6. **KNOWN_DIMENSION** - User-provided reference

**Soundhole Detection (most reliable for acoustics):**
```python
def detect_soundhole_circle(image: np.ndarray) -> tuple:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    h, w = gray.shape
    
    min_radius = int(w * 0.03)
    max_radius = int(w * 0.15)
    
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_radius * 2,
        param1=50,
        param2=30,
        minRadius=min_radius,
        maxRadius=max_radius
    )
    # Returns (center_x, center_y, radius_px)
```

**Carlos Jumbo Example (commit 84f935cf):**
```python
# Reference: JUMBO-CARLOS-2-3.pdf view_7 (front body view)
# Soundhole detected at 360px diameter = 102mm
mm_per_px = 102.0 / 360.0  # = 0.2833 mm/px
```

### Stage 3: Body Isolation

**Width Profile Analysis:**
```python
def extract_landmarks_from_profile(model: BodyModel) -> BodyModel:
    """
    Extract five primary body landmarks from smoothed W(y) profile.
    
    Landmark positions from three body band slices:
      - Upper third  (0%-35%): argmax -> upper bout
      - Middle third (30%-70%): argmin -> waist
      - Lower half   (50%-100%): argmax -> lower bout
    """
    w = model.row_width_profile_smoothed_px
    arr = np.asarray(w, dtype=float)
    
    x, y, bw, bh = model.body_bbox_px
    y0, y1 = max(0, int(y)), min(len(arr), int(y + bh))
    body_band = arr[y0:y1]
    body_length = float(max(1, y1 - y0))
    
    upper_end = max(1, int(0.35 * len(body_band)))
    mid_start = int(0.30 * len(body_band))
    mid_end = max(mid_start + 1, int(0.70 * len(body_band)))
    lower_start = int(0.50 * len(body_band))
    
    upper_local = int(np.argmax(body_band[:upper_end]))
    waist_local = int(np.argmin(body_band[mid_start:mid_end])) + mid_start
    lower_local = int(np.argmax(body_band[lower_start:])) + lower_start
```

### Stage 4: Dimension Extraction

**Output Data Structure:**
```python
@dataclass
class BodyLandmarks:
    centerline_x_px: float
    body_top_y_px: int
    body_bottom_y_px: int
    body_length_px: float
    
    waist_y_px: int
    waist_width_px: float
    
    upper_bout_y_px: int
    upper_bout_width_px: float
    
    lower_bout_y_px: int
    lower_bout_width_px: float
    
    waist_y_norm: float           # Position as fraction of body length
    upper_bout_y_norm: float
    lower_bout_y_norm: float
    waist_to_lower_ratio: float
    upper_to_lower_ratio: float
    width_to_length_ratio: float
```

**Conversion to Millimeters:**
```python
body_length_mm = body_length_px * mm_per_px
lower_bout_mm = lower_bout_width_px * mm_per_px
upper_bout_mm = upper_bout_width_px * mm_per_px
waist_mm = waist_width_px * mm_per_px
```

### Stage 5: Validation

**Geometric Constraints (invariants):**
```python
def validate_body_constraints(model: BodyModel) -> GeometryConstraints:
    """
    Four hard geometric invariants:
      1. lower_bout > waist > upper_bout
      2. waist y-position between 35% and 55% of body length
      3. width-to-length ratio between 0.70 and 0.95
      4. bilateral symmetry > 0.80 (bypassed for cutaway bodies)
    """
```

**Volume Validation (acoustic only):**
```python
def calculate_body_volume(lower_bout_mm, upper_bout_mm, waist_mm,
                          body_length_mm, depth_endblock_mm=125.0,
                          depth_neck_mm=105.0, shape_factor=0.85) -> dict:
    """
    Expected volume ranges:
      - Dreadnought: 12-16 liters
      - Jumbo: 14-19 liters
      - OM/000: 10-13 liters
      - Parlor: 8-11 liters
    """
```

---

## Part 3: DXF Extraction Process

### Direct DXF Bounding Box Extraction

For existing DXF files with body outlines, dimensions are extracted via bounding box:

```python
import ezdxf

def extract_dxf_dimensions(dxf_path: Path) -> dict:
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    
    # Collect all vertices from LWPOLYLINE and LINE entities
    all_points = []
    for entity in msp:
        if entity.dxftype() == 'LWPOLYLINE':
            all_points.extend(entity.get_points())
        elif entity.dxftype() == 'LINE':
            all_points.append(entity.dxf.start)
            all_points.append(entity.dxf.end)
    
    if not all_points:
        return None
    
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    
    return {
        'width_mm': max(xs) - min(xs),
        'height_mm': max(ys) - min(ys),
        'points': len(all_points),
    }
```

### Catalog Generation Session (December 2025)

**Commit:** `8d06e1ab` - "feat: Recover remaining modules"

**Process:**
1. Iterate through all DXF files in `services/api/app/instrument_geometry/body/dxf/`
2. Extract bounding box dimensions
3. Count vertices
4. Generate `catalog.json` and `all_extractions.json`

**Instruments Extracted:**
| Instrument | Width (mm) | Height (mm) | Points |
|------------|------------|-------------|--------|
| Stratocaster | 322.3 | 458.8 | 1417 |
| Les Paul | 383.5 | 269.2 | 669 |
| Gibson SG | 905.3 | 340.4 | 4502 |
| JS1000 | 450.7 | 314.6 | 345 |
| J-45 | 398.5 | 504.8 | 30 |
| Jumbo | 474.2 | 385.1 | 57 |
| Dreadnought | 404.0 | 510.2 | 2990 |
| Classical | 371.0 | 490.0 | 1156 |
| OM/000 | 397.6 | 499.6 | 5451 |
| L-00 | 376.3 | 500.0 | 2510 |
| Soprano Ukulele | 176.9 | 200.0 | 1572 |
| Explorer | 556.5 | 434.7 | 24 |
| Concert Ukulele | 203.1 | 393.7 | 14 |
| Martin D-28 | 386.0 | 507.3 | 64 |
| Octave Mandolin | 364.8 | 408.3 | 52 |
| Harmony H44 | 389.8 | 269.9 | 389 |

---

## Part 4: Diff 3 Spec-Prior Session (March 21, 2026)

**Commit:** `0219871e` - "feat(photo-vectorizer): Diff 3 - spec-prior contour election"

### Purpose
Create a reference dataset of known instrument body landmarks for spec-prior contour validation during vectorization.

### Data Schema
```json
{
  "instrument_name": {
    "body_length_mm": 406,
    "upper_bout_width_mm": 311,
    "waist_width_mm": 308,
    "lower_bout_width_mm": 408,
    "waist_y_norm": 0.47,
    "family": "solid_body"
  }
}
```

### Instruments Added (14 specs)

| Spec | Family | Body Length | Lower Bout | Upper Bout | Waist | Waist Y |
|------|--------|-------------|------------|------------|-------|---------|
| stratocaster | solid_body | 406 | 408 | 311 | 308 | 0.47 |
| telecaster | solid_body | 406 | 398 | 311 | 310 | 0.46 |
| les_paul | solid_body | 450 | 340 | 283 | 266 | 0.44 |
| es335 | archtop | 500 | 420 | 375 | 295 | 0.43 |
| dreadnought | acoustic | 520 | 381 | 292 | 241 | 0.43 |
| om_000 | acoustic | 476 | 341 | 274 | 228 | 0.44 |
| jumbo | acoustic | 521 | 419 | 320 | 272 | 0.43 |
| smart_guitar | solid_body | 444.5 | 368.3 | 310 | 307 | 0.46 |
| jumbo_archtop | archtop | 520 | 432 | 340 | 248 | 0.42 |
| classical | acoustic | 481 | 365 | 280 | 225 | 0.45 |
| j45 | acoustic | 506 | 394 | 295 | 248 | 0.44 |
| flying_v | solid_body | 450 | 410 | 380 | 200 | 0.52 |
| bass_4string | bass | 430 | 370 | 310 | 280 | 0.45 |
| gibson_sg | solid_body | 444 | 330 | 330 | 180 | 0.35 |

### Data Sources
- Manufacturer specifications
- Verified blueprint measurements
- DXF bounding box extractions
- Published technical drawings

---

## Part 5: Carlos Jumbo Calibration Session (April 1, 2026)

**Commit:** `84f935cf` - "feat(specs): update Carlos Jumbo dimensions from 1:1 blueprint calibration"

### Calibration Method
1. Load 1:1 scale PDF blueprint (`JUMBO-CARLOS-2-3.pdf`, view 7)
2. Detect soundhole circle (102mm known diameter)
3. Calculate mm/px from soundhole: `102mm / 360px = 0.2833 mm/px`
4. Measure body dimensions using calibrated scale
5. Validate with acoustic body volume calculator

### Script Location
`services/photo-vectorizer/calibrate_carlos_jumbo.py`

### Results
| Dimension | Before | After | Change |
|-----------|--------|-------|--------|
| lower_bout_mm | 430 | 477 | +47mm |
| upper_bout_mm | 310 | 372 | +62mm |
| waist_mm | 270 | 324 | +54mm |
| body_length_mm | 520 | 522 | +2mm |

### Validation
- Calculated volume: 14.65 liters (PASSES jumbo range 14-19L)
- Helmholtz frequency: 134.8 Hz
- Bout height proportions: upper 30%, lower 70%

---

## Part 6: Benedetto Addition Session (April 9, 2026)

**Commit:** `0e88248d` - "feat(vectorizer): add benedetto_17 to body dimension reference"

### Source
Original Benedetto 17-inch archtop blueprints (`benedetto_17.json` spec)

### Extracted Dimensions
| Field | Value |
|-------|-------|
| body_length_mm | 482.6 |
| upper_bout_width_mm | 279.4 |
| waist_width_mm | 228.6 |
| lower_bout_width_mm | 431.8 |
| waist_y_norm | 0.42 |
| family | archtop |

---

## Part 7: Reproduction Procedure

### Prerequisites

```bash
# Install dependencies
pip install opencv-python numpy PyMuPDF ezdxf

# Optional ML support
pip install scikit-learn joblib
```

### Step 1: Prepare Input

**For PDF blueprints:**
```bash
# Place PDF in Guitar Plans directory
cp MyInstrument.pdf "Guitar Plans/My Instrument/"
```

**For DXF files:**
```bash
# Place in appropriate category
cp my_instrument.dxf services/api/app/instrument_geometry/body/dxf/electric/
```

### Step 2: Run Extraction

**Option A: Direct DXF extraction**
```python
import ezdxf

doc = ezdxf.readfile("path/to/instrument.dxf")
msp = doc.modelspace()

all_points = []
for entity in msp:
    if entity.dxftype() == 'LWPOLYLINE':
        all_points.extend(entity.get_points())
    elif entity.dxftype() == 'LINE':
        all_points.append(entity.dxf.start)
        all_points.append(entity.dxf.end)

xs = [p[0] for p in all_points]
ys = [p[1] for p in all_points]

print(f"Width: {max(xs) - min(xs):.1f} mm")
print(f"Height: {max(ys) - min(ys):.1f} mm")
print(f"Points: {len(all_points)}")
```

**Option B: Blueprint calibration**
```python
import sys
sys.path.insert(0, "services/photo-vectorizer")

from calibrate_carlos_jumbo import calibrate_and_extract
from pathlib import Path

result = calibrate_and_extract(Path("Guitar Plans/My Instrument/blueprint.pdf"))
print(result['dimensions'])
```

**Option C: Full vectorizer pipeline**
```python
import sys
sys.path.insert(0, "services/blueprint-import")

from vectorizer_phase3 import Phase3Vectorizer

vectorizer = Phase3Vectorizer()
result = vectorizer.extract(
    source_path="path/to/blueprint.pdf",
    output_dir="output/",
    instrument_type="acoustic",
    dpi=300,
)
```

### Step 3: Add to Reference Data

**For body_dimension_reference.json:**
```json
{
  "my_instrument": {
    "body_length_mm": 500,
    "upper_bout_width_mm": 280,
    "waist_width_mm": 230,
    "lower_bout_width_mm": 380,
    "waist_y_norm": 0.44,
    "family": "acoustic"
  }
}
```

**For catalog.json:**
```json
{
  "my_instrument": {
    "name": "My Instrument",
    "category": "acoustic",
    "dimensions_mm": {
      "width": 380.0,
      "height": 500.0
    },
    "points": 150,
    "dxf": "acoustic/my_instrument_body.dxf",
    "source": "Blueprint extraction with soundhole calibration"
  }
}
```

### Step 4: Validate

```python
# Check geometric constraints
assert lower_bout_mm > waist_mm > upper_bout_mm
assert 0.35 <= waist_y_norm <= 0.55
assert 0.70 <= lower_bout_mm / body_length_mm <= 0.95

# Check volume (acoustic only)
from calibrate_carlos_jumbo import calculate_body_volume
vol = calculate_body_volume(lower_bout_mm, upper_bout_mm, waist_mm, body_length_mm)
print(f"Volume: {vol['volume_liters']:.2f} L")
```

---

## Part 8: Common Issues

### Scale Errors

**Symptom:** Dimensions are 2-3x too large or small

**Cause:** Incorrect mm/px calibration

**Fix:** Use known reference (soundhole, scale length, nut width)

### Missing Waist Detection

**Symptom:** `waist_width_mm` equals `lower_bout_mm`

**Cause:** Profile sampling didn't find local minimum

**Fix:** Adjust band percentages (30%-70% is default)

### Asymmetric Bodies

**Symptom:** Centerline offset, constraints fail

**Cause:** Cutaway or asymmetric design

**Fix:** Set `has_cutaway=True` in constraint validation

---

## Part 9: Reference Commits

| Date | Commit | Description |
|------|--------|-------------|
| 2025-12-14 | 8d06e1ab | Initial DXF catalog extraction (16 instruments) |
| 2026-03-21 | 0219871e | Diff 3 spec-prior system (14 landmark specs) |
| 2026-03-22 | 4ddeffeb | PHOTO-001 sync AI specs |
| 2026-04-01 | 84f935cf | Carlos Jumbo 1:1 calibration |
| 2026-04-09 | 0e88248d | Benedetto 17-inch + Gibson SG addition |

---

## Part 10: Output File Locations

| File | Purpose |
|------|---------|
| `services/photo-vectorizer/body_dimension_reference.json` | Spec-prior landmarks (14 specs) |
| `services/api/app/instrument_geometry/body/catalog.json` | DXF catalog (23 bodies) |
| `services/api/app/instrument_geometry/specs/all_extractions.json` | Extraction log (16 entries) |
| `services/api/app/instrument_geometry/specs/*.json` | Individual instrument specs |

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-27  
**Author:** Claude Code  
**Co-Authored-By:** Claude Opus 4.5 <noreply@anthropic.com>
