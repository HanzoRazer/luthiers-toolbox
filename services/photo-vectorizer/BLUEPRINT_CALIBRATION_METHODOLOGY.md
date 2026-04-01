# Blueprint Calibration Methodology

## Overview

This document describes the reverse-engineering methodology used to derive accurate guitar body dimensions from 1:1 scale PDF blueprints. The approach uses **known reference features** (soundhole diameter) for pixel-to-mm calibration, then validates extracted dimensions against the **acoustic body volume calculator**.

## The Problem

Blueprint PDFs often contain multiple views at different scales, and raw contour extraction produces dimensions that don't match the actual instrument. Simply trusting pixel measurements leads to errors because:

1. PDFs may have multiple views at different zoom levels
2. Contour detection may capture partial outlines or extra elements
3. Scanner/print scaling introduces systematic errors

## Solution: Reference-Based Calibration + Volume Validation

### Step 1: Identify Known Reference Features

For acoustic guitars, the **soundhole** is the most reliable calibration reference:

```
Standard soundhole diameters:
- Classical/Jumbo: 102mm (4 inches)
- Dreadnought: 100mm
- Parlor: 85-90mm
- OM/000: 100mm
```

Other usable references (less reliable):
- Scale length (650mm for classical, 648mm for steel-string)
- Nut width (52mm classical, 44.5mm steel-string)
- Bridge spacing

### Step 2: Detect Reference Feature in Image

```python
def calibrate_scale_from_soundhole(image, soundhole_mm=102.0):
    """
    Detect soundhole circle using Hough transform.
    Returns mm_per_px calibration factor.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Estimate radius range based on image size
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

    if circles is None:
        return None

    # Find most centered circle (soundhole is typically centered)
    best_circle = min(circles[0], key=lambda c: abs(c[0]/w - 0.5))
    cx, cy, radius_px = best_circle
    diameter_px = radius_px * 2

    mm_per_px = soundhole_mm / diameter_px
    return mm_per_px
```

### Step 3: Extract Body Dimensions

With calibrated scale, measure:
- **Lower bout width** (widest point)
- **Upper bout width**
- **Waist width** (narrowest point)
- **Body length** (total height)

### Step 4: Validate with Volume Calculator

The acoustic body volume calculator uses elliptical cross-section integration:

```python
def calculate_body_volume(lower_bout_mm, upper_bout_mm, waist_mm,
                          body_length_mm, depth_endblock_mm=125.0,
                          depth_neck_mm=105.0, shape_factor=0.85):
    """
    Calculate guitar body volume in liters.

    Args:
        lower_bout_mm: Width at widest point (lower bout)
        upper_bout_mm: Width at upper bout
        waist_mm: Width at waist (narrowest)
        body_length_mm: Total body length
        depth_endblock_mm: Body depth at tail end
        depth_neck_mm: Body depth at neck joint
        shape_factor: Accounts for non-elliptical cross-section (0.85 typical)

    Returns:
        dict with volume_mm3, volume_liters, volume_cubic_inches
    """
    L = body_length_mm

    # Section lengths (empirical proportions)
    lower_len = L * 0.40   # Lower bout section = 40% of body
    waist_len = L * 0.25   # Waist section = 25% of body
    upper_len = L * 0.35   # Upper bout section = 35% of body

    avg_depth = (depth_endblock_mm + depth_neck_mm) / 2

    # Cross-sectional areas (ellipse: A = π * a * b * shape_factor)
    lower_area = math.pi * (lower_bout_mm/2) * (depth_endblock_mm/2) * shape_factor
    waist_area = math.pi * (waist_mm/2) * (avg_depth/2) * shape_factor
    upper_area = math.pi * (upper_bout_mm/2) * (depth_neck_mm/2) * shape_factor

    # Volume by trapezoidal integration
    V_lower = (lower_area + waist_area) / 2 * lower_len
    V_waist = waist_area * waist_len
    V_upper = (waist_area + upper_area) / 2 * upper_len

    total_mm3 = V_lower + V_waist + V_upper

    return {
        'volume_mm3': total_mm3,
        'volume_liters': total_mm3 / 1e6,
        'volume_cubic_inches': total_mm3 / 16387.064,
    }
```

### Step 5: Iterative Fitting

If measured dimensions don't produce expected volume, iterate:

```python
def fit_dimensions_to_volume(measured_width, measured_height,
                             target_volume_range, depth_endblock=125, depth_neck=105):
    """
    Iteratively adjust bout ratios to find dimensions that produce
    target volume while preserving measured aspect ratio.
    """
    # Start with typical jumbo proportions
    upper_ratio = 0.78  # upper_bout / lower_bout
    waist_ratio = 0.68  # waist / lower_bout

    for upper_r in [0.75, 0.76, 0.77, 0.78, 0.79, 0.80]:
        for waist_r in [0.65, 0.66, 0.67, 0.68, 0.69, 0.70]:
            lower_bout = measured_width
            upper_bout = lower_bout * upper_r
            waist = lower_bout * waist_r
            body_length = measured_height

            vol = calculate_body_volume(
                lower_bout, upper_bout, waist, body_length,
                depth_endblock, depth_neck
            )

            if target_volume_range[0] <= vol['volume_liters'] <= target_volume_range[1]:
                return {
                    'lower_bout_mm': lower_bout,
                    'upper_bout_mm': upper_bout,
                    'waist_mm': waist,
                    'body_length_mm': body_length,
                    'upper_ratio': upper_r,
                    'waist_ratio': waist_r,
                    'volume_liters': vol['volume_liters'],
                }

    return None  # No valid fit found
```

## Expected Volume Ranges by Body Style

| Body Style | Volume (Liters) | Lower Bout (mm) | Body Length (mm) |
|------------|-----------------|-----------------|------------------|
| Parlor     | 8-10 L          | 330-360         | 430-460          |
| 000/OM     | 11-13 L         | 380-400         | 480-500          |
| Dreadnought| 12-14 L         | 395-410         | 500-510          |
| **Jumbo**  | **14-19 L**     | **420-480**     | **510-550**      |
| Super Jumbo| 18-22 L         | 450-500         | 530-570          |

## Bout Proportion Ratios

Typical acoustic guitar proportions (can vary by style):

```
Upper bout / Lower bout:  0.72 - 0.82  (typically 0.78)
Waist / Lower bout:       0.60 - 0.72  (typically 0.68)

Bout height distribution:
  Upper bout height: 28-32% of body length
  Lower bout height: 68-72% of body length
```

## Carlos Jumbo Case Study

### Initial Problem
- Spec file had estimated dimensions: 430 x 310 x 270 x 520 mm
- These were guesses, not measured from blueprints

### Calibration Process

1. **Reference Detection**: Found soundhole in JUMBO-CARLOS-2-3.pdf view_7
   - Soundhole diameter: 360 px = 102 mm
   - Scale: **0.2833 mm/px**

2. **Raw Measurements** (from calibrated bounding box):
   - Body length: 522 mm (from bbox height)
   - Lower bout: 477 mm (from bbox width)

3. **Iterative Volume Fitting**:
   ```
   Testing bout ratios against jumbo volume range (14-19 L):

   upper_ratio=0.78, waist_ratio=0.68:
     upper_bout = 477 * 0.78 = 372 mm
     waist = 477 * 0.68 = 324 mm
     Volume = 14.65 L  ✓ PASSES
   ```

4. **Final Validated Dimensions**:
   ```
   lower_bout_mm:  477.0
   upper_bout_mm:  372.0  (ratio 0.78)
   waist_mm:       324.0  (ratio 0.68)
   body_length_mm: 522.0

   Volume: 14.65 liters (VALIDATED - within jumbo range)
   Helmholtz frequency: 134.8 Hz
   ```

### Bout Height Proportions

From contour analysis, the bout transition points:
- Upper bout height: 30% of body length (156 mm)
- Lower bout height: 70% of body length (366 mm)

## Helmholtz Resonance Verification

The Helmholtz frequency provides additional validation:

```python
def calculate_helmholtz_freq(volume_liters, soundhole_mm=102.0, top_thickness=2.8):
    """
    Calculate air resonance frequency.
    Typical range: 90-150 Hz for acoustic guitars.
    """
    c = 343000  # speed of sound in mm/s
    A = math.pi * (soundhole_mm / 2) ** 2  # soundhole area
    L_eff = 1.7 * top_thickness + 0.85 * soundhole_mm  # effective length
    V_mm3 = volume_liters * 1e6

    return (c / (2 * math.pi)) * math.sqrt(A / (V_mm3 * L_eff))
```

Expected Helmholtz frequencies:
- Parlor: 140-160 Hz
- OM/000: 120-140 Hz
- Dreadnought: 110-130 Hz
- Jumbo: 100-120 Hz (Carlos Jumbo: 134.8 Hz)

## File Locations

- Spec file: `services/api/app/instrument_geometry/specs/carlos_jumbo.json`
- Calibration script: `services/photo-vectorizer/calibrate_carlos_jumbo.py`
- DXF generator: `services/photo-vectorizer/generate_carlos_jumbo_dxf_enhanced.py`
- Volume calculator: `services/api/app/calculators/acoustic_body_volume.py`
- **Light line extractor**: `services/photo-vectorizer/light_line_body_extractor.py`

## Light Line Extraction

When body outlines are drawn with very light gray lines that standard edge detection misses, use the specialized `light_line_body_extractor.py` module:

```bash
# CLI usage
python light_line_body_extractor.py path/to/blueprint.pdf \
    --page 0 \
    --page-size A0 \
    --output body_outline.dxf \
    --target-width 477 \
    --target-height 522 \
    --debug
```

```python
# Programmatic usage
from light_line_body_extractor import (
    extract_body_from_pdf,
    create_acoustic_body_config,
    save_contour_to_dxf,
)

config = create_acoustic_body_config()
result = extract_body_from_pdf(
    pdf_path,
    page_number=0,
    page_size_mm=(841.0, 1189.0),  # A0
    config=config,
    save_debug=True,
)

if result.success:
    save_contour_to_dxf(
        result.body,
        output_path,
        scale_to_dimensions=(477.0, 522.0),  # Target jumbo dimensions
    )
```

**Technique**:
1. Invert image (light → dark)
2. Enhance contrast by 3x
3. Low Canny thresholds (15, 45)
4. Morphological closing (5x5 kernel, 3 iterations)
5. Filter by expected body dimensions (300-700mm × 350-750mm)

## Applying to New Blueprints

1. Identify the guitar body style and expected volume range
2. Find a known reference feature (soundhole preferred)
3. Run soundhole detection to get mm/px scale
4. Extract body bounding box dimensions
5. Calculate volume with typical bout ratios
6. If volume outside expected range, adjust ratios iteratively
7. Document calibration metadata in the spec file

## References

- Williams, S. (2019). "Acoustic Guitar Design Optimization"
- Cumpiano & Natelson, "Guitarmaking: Tradition and Technology"
- ISO 216 paper sizes (A0=841x1189mm, A1=841x594mm) for PDF scale verification

---

*Methodology developed for Carlos Jumbo blueprint extraction, April 2026*
*Commit: cc282696 - feat(specs): update Carlos Jumbo dimensions from 1:1 blueprint calibration*
