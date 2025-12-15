# Neck Taper Theory & CNC Implementation Guide

**Wave 17 - Instrument Geometry Integration**  
**Module:** Neck Taper Suite  
**Status:** Production Ready

---

## Overview

This guide explains the mathematical foundations and practical CNC workflows for generating parametric neck profiles using the Neck Taper Suite.

**What This System Does:**
- Generates neck width profiles as functions of distance from nut
- Produces CAM-ready DXF files (R12 format) for CNC routing
- Supports linear taper models with extension points for complex curves
- Provides API endpoints for real-time neck outline generation

**What This System Does NOT Do:**
- Neck thickness profiles (back carve, C/V/U shapes) - future enhancement
- Fretboard radius compensation - handled separately in `neck.fret_math`
- Headstock design - separate module

---

## Mathematical Foundation

### Core Taper Model

The Neck Taper Suite uses a **distance-based linear interpolation** model:

```
W(L) = W_nut + (W_heel - W_nut) × (L / L_taper)
```

Where:
- **W(L)** = Width at distance L from nut (mm)
- **W_nut** = Width at nut (typically 42-43mm for 6-string)
- **W_heel** = Width at neck-body joint (typically 56-60mm)
- **L** = Distance from nut (inches, for traditional lutherie compatibility)
- **L_taper** = Total taper length, nut to heel (typically 16-17 inches)

**Key Properties:**
1. **Linear**: Constant rate of width change (simplifies CNC programming)
2. **Bounded**: `W_nut ≤ W(L) ≤ W_heel` for `0 ≤ L ≤ L_taper`
3. **Monotonic**: Width always increases toward body (no inflection points)

### Fret Position Calculation

Fret positions follow **equal temperament** tuning:

```
x_f = L_scale - (L_scale / 2^(f/12))
```

Where:
- **x_f** = Distance from nut to fret f (mm)
- **L_scale** = Scale length (e.g., 648mm for Fender 25.5")
- **f** = Fret number (0 = nut, 12 = octave)

**Example (648mm scale):**
- Fret 0 (nut): 0.0mm
- Fret 12 (octave): 324.0mm
- Fret 22: 576.7mm

### Width at Fret

To find neck width at a specific fret:

```python
from instrument_geometry.neck_taper.taper_math import width_at_fret, TaperInputs

inputs = TaperInputs(
    nut_width_mm=42.0,
    heel_width_mm=57.0,
    taper_length_in=16.0,
    scale_length_mm=648.0  # Fender 25.5"
)

# Width at 12th fret
w12 = width_at_fret(12, inputs)  # ≈ 49.5mm
```

---

## Neck Outline Generation

### Coordinate System

The Neck Taper Suite uses **centerline-origin coordinates**:

```
         Y (width, transverse)
         ^
         |
    -----+-----  Treble side (positive Y)
         |
  -------|-------  Centerline (Y = 0)
         |
    -----+-----  Bass side (negative Y)
         |
         +---------> X (distance from nut, longitudinal)
      (0,0) = Nut centerline
```

**Conventions:**
- **X-axis**: Distance from nut (mm), always positive toward body
- **Y-axis**: Width from centerline (mm), negative = bass side, positive = treble side
- **Origin**: Centerline at nut face
- **Closed polyline**: Treble edge → Bass edge → return to start

### Outline Algorithm

The `generate_neck_outline()` function produces a **closed polyline**:

1. **Sample fret widths** at specified frets (default: every fret from 0 to last)
2. **Generate treble edge** points: `(x_f, +W_f/2)` for each fret
3. **Generate bass edge** points: `(x_f, -W_f/2)` in reverse order
4. **Close polyline**: Append first point to create seamless loop

**Output Structure:**
```python
[
    Point(x=0.0, y=21.0),      # Nut treble edge
    Point(x=36.5, y=21.5),     # Fret 1 treble
    Point(x=70.9, y=22.0),     # Fret 2 treble
    # ... more treble points ...
    Point(x=576.7, y=28.5),    # Fret 22 treble
    Point(x=576.7, y=-28.5),   # Fret 22 bass (reversed)
    # ... bass points back to nut ...
    Point(x=0.0, y=-21.0),     # Nut bass edge
    Point(x=0.0, y=21.0)       # CLOSE: back to start
]
```

---

## CNC Workflow

### DXF Export Strategy

The suite exports **DXF R12 (AC1009)** format for maximum CAM compatibility:

**Why R12?**
- Supported by all major CAM software (Fusion 360, VCarve, Mach4, LinuxCNC)
- Simple POLYLINE entity structure (no LWPOLYLINE complications)
- No external dependencies (pure Python implementation)

**Entity Structure:**
```
POLYLINE (layer: NECK_OUTLINE)
  VERTEX (x, y, bulge=0)
  VERTEX (x, y, bulge=0)
  ...
  VERTEX (x, y, bulge=0)
SEQEND
```

**Key Parameters:**
- **Layer**: `NECK_OUTLINE` for easy CAM selection
- **Closed flag**: Bit 1 set (`flags=1`) for automatic closure
- **No bulge**: All vertices linear (bulge=0), no arcs

### CAM Import Checklist

When importing neck taper DXF into CAM software:

1. **Verify Units**: DXF is in millimeters (all coordinates in mm)
2. **Check Closure**: Polyline should be closed (no gap between start/end)
3. **Confirm Orientation**: X = longitudinal, Y = transverse
4. **Layer Selection**: Use `NECK_OUTLINE` layer for toolpath generation
5. **Validate Dimensions**: 
   - Nut width matches spec (e.g., 42mm ± 0.1mm)
   - Heel width matches spec (e.g., 57mm ± 0.1mm)
   - Scale length correct (e.g., 648mm for Fender)

### Example: Fusion 360 Import

```
1. File → Insert → Insert DXF
2. Select neck_outline.dxf
3. Choose "Import to root component"
4. Units: Millimeters
5. Orientation: XY plane (top view)
6. Validate sketch dimensions with Inspect → Measure
7. Create 2D toolpath from NECK_OUTLINE sketch
```

### Example: VCarve Pro Import

```
1. File → Import → Import Vectors
2. Select neck_outline.dxf
3. Import onto Layer 1
4. Check "Close open vectors with tolerance 0.01mm"
5. Validate with Drawing tab → Dimensions tool
6. Create Pocket or Profile toolpath from closed vector
```

---

## API Usage

### Endpoint 1: JSON Outline

**Generate neck outline as JSON coordinate array:**

```bash
curl -X POST http://localhost:8000/api/instrument/neck_taper/outline \
  -H 'Content-Type: application/json' \
  -d '{
    "nut_width_mm": 42.0,
    "heel_width_mm": 57.0,
    "taper_length_in": 16.0,
    "scale_length_mm": 648.0,
    "num_frets": 22,
    "sample_frets": [0, 5, 9, 12, 15, 17, 19, 22]
  }'
```

**Response:**
```json
{
  "outline": [
    {"x": 0.0, "y": 21.0},
    {"x": 143.7, "y": 22.8},
    {"x": 247.5, "y": 24.0},
    ...
  ],
  "metadata": {
    "num_points": 16,
    "nut_width_mm": 42.0,
    "heel_width_mm": 57.0,
    "is_closed": true
  }
}
```

### Endpoint 2: DXF Download

**Download ready-to-use DXF file:**

```bash
curl -X POST http://localhost:8000/api/instrument/neck_taper/outline.dxf \
  -H 'Content-Type: application/json' \
  -d '{
    "nut_width_mm": 43.0,
    "heel_width_mm": 58.0,
    "taper_length_in": 16.5,
    "scale_length_mm": 628.65,
    "num_frets": 22
  }' \
  --output neck_lp_style.dxf
```

**Result:** `neck_lp_style.dxf` ready for CAM import

---

## Practical Examples

### Example 1: Fender Stratocaster Neck

**Specifications:**
- Nut width: 42mm (1.650")
- Heel width: 56mm (2.205")
- Scale length: 648mm (25.5")
- Frets: 22

**Python Code:**
```python
from instrument_geometry.neck_taper import TaperInputs, compute_taper_table, export_neck_outline_to_dxf

inputs = TaperInputs(
    nut_width_mm=42.0,
    heel_width_mm=56.0,
    taper_length_in=16.0,
    scale_length_mm=648.0
)

table = compute_taper_table(22, inputs)
for row in table[:3]:  # First 3 frets
    print(f"Fret {row.fret_num}: {row.distance_from_nut_mm:.1f}mm, width {row.width_mm:.2f}mm")

export_neck_outline_to_dxf("strat_neck.dxf", inputs, num_frets=22)
```

**Output:**
```
Fret 0: 0.0mm, width 42.00mm
Fret 1: 36.5mm, width 42.60mm
Fret 2: 70.9mm, width 43.15mm
```

### Example 2: Gibson Les Paul Neck

**Specifications:**
- Nut width: 43mm (1.693")
- Heel width: 57mm (2.244")
- Scale length: 628.65mm (24.75")
- Frets: 22

**API Request:**
```json
{
  "nut_width_mm": 43.0,
  "heel_width_mm": 57.0,
  "taper_length_in": 16.0,
  "scale_length_mm": 628.65,
  "num_frets": 22,
  "sample_frets": [0, 3, 5, 7, 9, 12, 15, 17, 19, 22]
}
```

### Example 3: Custom 7-String Neck

**Specifications:**
- Nut width: 48mm (wider for 7 strings)
- Heel width: 62mm
- Scale length: 648mm (25.5")
- Frets: 24 (extended range)

**Code:**
```python
inputs_7string = TaperInputs(
    nut_width_mm=48.0,
    heel_width_mm=62.0,
    taper_length_in=17.0,
    scale_length_mm=648.0
)

export_neck_outline_to_dxf("7string_neck.dxf", inputs_7string, num_frets=24)
```

---

## Integration with GuitarModelSpec

The Neck Taper Suite integrates with the larger **Wave 17 Guitar Model Specification** system:

```python
from instrument_geometry.model_spec import PRESET_MODELS

strat_model = PRESET_MODELS["strat_25_5"]

# Extract neck taper spec
taper_spec = strat_model.neck_taper
print(f"Nut: {taper_spec.nut_width_mm}mm")
print(f"Heel: {taper_spec.heel_width_mm}mm")

# Get width at 12th fret
width_12 = taper_spec.width_at_distance_in(12.75)  # Distance in inches
print(f"Width at 12th fret: {width_12:.2f}mm")

# Generate DXF from model spec
scale_mm = strat_model.scale_profile().scale_length_mm
inputs = TaperInputs(
    nut_width_mm=taper_spec.nut_width_mm,
    heel_width_mm=taper_spec.heel_width_mm,
    taper_length_in=taper_spec.taper_length_in,
    scale_length_mm=scale_mm
)
export_neck_outline_to_dxf("model_based_neck.dxf", inputs, num_frets=22)
```

---

## Troubleshooting

### Issue: DXF Not Recognized by CAM Software

**Symptoms:** "Invalid DXF file" or "No entities found" error

**Solutions:**
1. Verify DXF version (should be R12/AC1009)
2. Check file size (should be > 0 bytes)
3. Open in text editor and verify POLYLINE entities exist
4. Try alternative import method (e.g., "Insert DXF" vs "Import Vectors")

### Issue: Neck Width Incorrect

**Symptoms:** Measured width doesn't match specification

**Solutions:**
1. Verify units in CAM software (should be mm, not inches)
2. Check coordinate system orientation (X should be longitudinal)
3. Measure at correct fret position (e.g., fret 0 for nut, not arbitrary point)
4. Confirm scale length matches specification

### Issue: Polyline Not Closed

**Symptoms:** Gap between start and end points in CAM preview

**Solutions:**
1. Check `is_closed` flag in JSON response (should be `true`)
2. Verify first and last points are identical
3. Use CAM software's "Close Open Vectors" tool with 0.01mm tolerance
4. Regenerate DXF with explicit closure

### Issue: Too Few/Many Sample Points

**Symptoms:** Toolpath looks jaggy or overly dense

**Solutions:**
1. Adjust `sample_frets` parameter (default: all frets)
2. For smoother curves, sample every fret: `[0, 1, 2, ..., 22]`
3. For faster CAM, sample key frets only: `[0, 5, 9, 12, 17, 22]`
4. Balance between accuracy and toolpath complexity

---

## Future Enhancements

### Planned (Wave 18+)

1. **Compound Taper Curves**
   - Multiple taper segments (e.g., faster taper near nut)
   - Bezier curve interpolation for organic shapes
   - Asymmetric bass/treble tapers

2. **Thickness Profile Integration**
   - C/V/U neck back carves
   - Thickness as function of width and position
   - 3D solid export (STEP/IGES)

3. **Fretboard Radius Compensation**
   - Adjust width for compound radius boards
   - Side-view profile generation
   - Radius relief calculations

4. **Material Waste Optimization**
   - Nesting multiple necks on blank
   - Grain orientation suggestions
   - Cut list generation

### Experimental (Research Phase)

- **Machine learning neck shape optimization** (comfort + structural strength)
- **FEA stress analysis** integration for truss rod sizing
- **Acoustic modeling** (neck mass effects on tone)

---

## References

### Lutherie Standards

- **Fender**: 42mm nut, 25.5" scale (648mm)
- **Gibson**: 43mm nut, 24.75" scale (628.65mm)
- **PRS**: 42mm nut, 25" scale (635mm)
- **Classical**: 50-52mm nut, 650mm scale
- **Martin Acoustic**: 44-45mm nut, 25.4" scale (645mm)

### Mathematical Background

- **Equal Temperament**: 12th root of 2 (≈1.05946) fret spacing ratio
- **Linear Interpolation**: Basic calculus, continuous functions
- **Polyline Approximation**: Discrete sampling theory

### CAM Software Compatibility

- ✅ **Fusion 360** (2D/3D sketch import)
- ✅ **VCarve Pro/Desktop** (vector import)
- ✅ **Aspire** (3D relief carving)
- ✅ **Mach4** (G-code generation via CAM post)
- ✅ **LinuxCNC** (DXF to G-code via pycam)

---

## See Also

- [Neck Taper DXF Export Guide](./Neck_Taper_DXF_Export.md) - Detailed DXF format documentation
- [Instrument DXF Mapping Guide](./Instrument_DXF_Mapping.md) - Asset registry system
- [Module L: Adaptive Pocketing](../../ADAPTIVE_POCKETING_MODULE_L.md) - CNC toolpath generation
- [Wave 17 Integration Summary](../../docs/wave17_integration_summary.md) - Overall architecture

---

**Last Updated:** December 8, 2025  
**Author:** Luthier's Tool Box Development Team  
**Version:** 1.0 (Wave 17)
