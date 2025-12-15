# Neck Taper DXF Export Technical Guide

**Wave 17 - Instrument Geometry Integration**  
**Module:** DXF Exporter (`neck_taper/dxf_exporter.py`)  
**Format:** DXF R12 (AC1009)  
**Status:** Production Ready

---

## Overview

This document provides technical details on the DXF export implementation for neck taper profiles. It covers file format specifications, entity structures, and CAM software compatibility considerations.

**Target Audience:**
- CAM software developers integrating with Luthier's Tool Box
- CNC operators troubleshooting DXF import issues
- Contributors extending the DXF export system

---

## DXF Format Specification

### Why DXF R12 (AC1009)?

The Neck Taper Suite uses **AutoCAD R12 DXF** format for maximum compatibility:

**Advantages:**
- ✅ Supported by 100% of CAM software (1990s-era standard)
- ✅ Simple ASCII format (human-readable, easy to debug)
- ✅ No external dependencies (pure Python implementation)
- ✅ Minimal entity types (POLYLINE/VERTEX only)
- ✅ Cross-platform (Windows/Mac/Linux CAM tools)

**Tradeoffs:**
- ❌ No LWPOLYLINE support (modern format, not needed here)
- ❌ No spline entities (we use linear segments only)
- ❌ No extended data (XDATA) for metadata
- ❌ Larger file size than binary DXF (acceptable for our use case)

### File Structure

DXF R12 uses a **group code system** where each line contains:
1. **Group code** (integer, defines data type)
2. **Value** (string, coordinates, layer names, etc.)

**Minimal Neck Taper DXF Structure:**
```
  0
SECTION
  2
HEADER
  9
$ACADVER
  1
AC1009
  0
ENDSEC
  0
SECTION
  2
TABLES
  0
TABLE
  2
LAYER
  70
1
  0
LAYER
  2
NECK_OUTLINE
  62
7
  6
CONTINUOUS
  0
ENDTAB
  0
ENDSEC
  0
SECTION
  2
ENTITIES
  0
POLYLINE
  8
NECK_OUTLINE
  66
1
  70
1
  0
VERTEX
  8
NECK_OUTLINE
  10
0.0
  20
21.0
  30
0.0
  40
0.0
  0
VERTEX
  8
NECK_OUTLINE
  10
36.5
  20
21.5
  30
0.0
  40
0.0
  0
SEQEND
  8
NECK_OUTLINE
  0
ENDSEC
  0
EOF
```

---

## Entity Details

### POLYLINE Entity

**Group Codes:**
- `0` = Entity type ("POLYLINE")
- `8` = Layer name ("NECK_OUTLINE")
- `66` = Vertices follow flag (1 = yes)
- `70` = Polyline flags (1 = closed, 0 = open)

**Flags Bit Values (Group Code 70):**
```
Bit 0 (1):   Closed polyline
Bit 1 (2):   Curve-fit vertices added
Bit 2 (4):   Spline-fit vertices added
Bit 3 (8):   3D polyline
Bit 4 (16):  3D polygon mesh
Bit 5 (32):  Closed N direction
Bit 6 (64):  Polyface mesh
Bit 7 (128): Continuous linetype pattern
```

**Our Usage:** `flags=1` (bit 0 only) = closed 2D polyline

### VERTEX Entity

**Group Codes:**
- `0` = Entity type ("VERTEX")
- `8` = Layer name (must match POLYLINE layer)
- `10` = X coordinate (mm)
- `20` = Y coordinate (mm)
- `30` = Z coordinate (always 0.0 for 2D)
- `40` = Bulge factor (0.0 = linear segment)

**Bulge Factor:**
- `bulge = 0.0` → Straight line to next vertex
- `bulge > 0.0` → Counterclockwise arc (not used)
- `bulge < 0.0` → Clockwise arc (not used)

**Our Usage:** All bulge factors are 0.0 (linear segments only)

### SEQEND Entity

**Group Codes:**
- `0` = Entity type ("SEQEND")
- `8` = Layer name (must match POLYLINE layer)

**Purpose:** Marks end of VERTEX sequence for POLYLINE

---

## Implementation Details

### Function: `build_r12_polyline_dxf()`

**Signature:**
```python
def build_r12_polyline_dxf(
    outline: List[Point],
    layer_name: str = "NECK_OUTLINE"
) -> str
```

**Algorithm:**
1. **Write HEADER section** with `$ACADVER = AC1009`
2. **Write TABLES section** with single LAYER definition
3. **Write ENTITIES section**:
   - Start POLYLINE with `flags=1` (closed)
   - Write VERTEX for each point in outline
   - Write SEQEND to close vertex list
4. **Write EOF marker**

**Key Implementation Choices:**

**Coordinate Precision:** 4 decimal places (0.1 micron resolution)
```python
f"{point.x:.4f}"  # e.g., "42.1234" mm
f"{point.y:.4f}"  # e.g., "21.5678" mm
```

**Layer Color:** White (color code 7)
```python
"  62\n7\n"  # Group code 62 = color, value 7 = white
```

**Linetype:** CONTINUOUS (solid line)
```python
"  6\nCONTINUOUS\n"  # Group code 6 = linetype
```

### Function: `write_r12_polyline_dxf_file()`

**Signature:**
```python
def write_r12_polyline_dxf_file(
    path: Union[str, Path],
    outline: List[Point],
    layer_name: str = "NECK_OUTLINE"
) -> None
```

**File Writing:**
```python
with open(path, "w", encoding="utf-8") as f:
    dxf_content = build_r12_polyline_dxf(outline, layer_name)
    f.write(dxf_content)
```

**Error Handling:**
- Missing parent directories → raises `FileNotFoundError`
- Permission errors → raises `PermissionError`
- Invalid UTF-8 in layer name → raises `UnicodeEncodeError`

### Function: `export_neck_outline_to_dxf()`

**Signature:**
```python
def export_neck_outline_to_dxf(
    path: Union[str, Path],
    inputs: TaperInputs,
    num_frets: int = 22,
    sample_frets: Optional[List[int]] = None
) -> None
```

**Complete Workflow:**
1. Generate neck outline via `generate_neck_outline()`
2. Build DXF content via `build_r12_polyline_dxf()`
3. Write file via `write_r12_polyline_dxf_file()`

**Example:**
```python
from pathlib import Path
from instrument_geometry.neck_taper import TaperInputs, export_neck_outline_to_dxf

inputs = TaperInputs(
    nut_width_mm=42.0,
    heel_width_mm=57.0,
    taper_length_in=16.0,
    scale_length_mm=648.0
)

export_neck_outline_to_dxf(
    path=Path("output/strat_neck.dxf"),
    inputs=inputs,
    num_frets=22,
    sample_frets=[0, 5, 9, 12, 15, 17, 19, 22]  # Key frets only
)
```

---

## CAM Software Compatibility

### Fusion 360

**Import Method:** File → Insert → Insert DXF

**Settings:**
- ✅ **Units:** Millimeters (auto-detected from coordinates)
- ✅ **Plane:** XY (top view)
- ✅ **Target:** Root component or new component

**Validation:**
```
1. Right-click imported sketch → Edit Sketch
2. Inspect → Measure → verify nut width (e.g., 42mm)
3. Check closed loop icon (no gaps)
4. Create 2D toolpath (Pocket or Profile)
```

**Known Issues:**
- ⚠️ Very old Fusion versions (<2019) may not auto-detect units
- **Workaround:** Manually set sketch units to mm after import

### VCarve Pro/Desktop

**Import Method:** File → Import → Import Vectors

**Settings:**
- ✅ **File Type:** DXF (*.dxf)
- ✅ **Layer:** Import all layers or select NECK_OUTLINE
- ✅ **Close Open Vectors:** Tolerance 0.01mm (optional, should already be closed)

**Validation:**
```
1. Drawing tab → select imported vector
2. Right-click → Display Properties → verify closed path
3. Node Edit tool → check point count matches expectation
4. Create Pocket or Profile toolpath from vector
```

**Known Issues:**
- ⚠️ Some VCarve versions don't respect DXF layer colors
- **Workaround:** Manually assign color after import

### Aspire

**Import Method:** Same as VCarve Pro (Aspire uses same vector engine)

**Additional Features:**
- 3D relief carving from 2D vector boundaries
- V-bit inlay toolpaths
- Texture mapping within neck outline

### Mach4

**Import Method:** DXF → G-code via CAM plugin or Mach4's built-in DXF converter

**Typical Workflow:**
```
1. Load DXF in Mach4 Screen Editor or external CAM
2. Generate toolpath (profile cut for neck blank)
3. Post-process to Mach4 G-code
4. Load in Mach4 operator screen
5. Run job with proper tool offsets
```

**Known Issues:**
- ⚠️ Mach4's internal DXF converter is very basic (may not handle R12 properly)
- **Workaround:** Use external CAM (Fusion, VCarve) to generate G-code

### LinuxCNC

**Import Method:** DXF → G-code via `pycam`, `dxf2gcode`, or `dxf-export-gcode` tools

**Recommended Tool:** `dxf2gcode` (Python-based, well-maintained)
```bash
# Install dxf2gcode
pip install dxf2gcode

# Convert neck taper DXF to G-code
dxf2gcode -i strat_neck.dxf -o strat_neck.ngc -p profile_cut
```

**Known Issues:**
- ⚠️ LinuxCNC has no native DXF import (requires external converter)
- **Workaround:** Use `pycam` for full CAM features (more complex setup)

---

## Validation & Testing

### Manual Validation

**Visual Inspection (Text Editor):**
```bash
# Check DXF header
head -n 20 neck_outline.dxf
# Should show "AC1009" on line ~6

# Count VERTEX entities
grep -c "^  0$" neck_outline.dxf
grep -c "^VERTEX$" neck_outline.dxf
# Counts should differ by 3 (SECTION, POLYLINE, SEQEND)

# Check closure
tail -n 30 neck_outline.dxf | head -n 20
# Last VERTEX coordinates should match first VERTEX
```

**Geometric Validation (Python):**
```python
from instrument_geometry.neck_taper import generate_neck_outline, TaperInputs

inputs = TaperInputs(42.0, 57.0, 16.0, 648.0)
outline = generate_neck_outline(22, inputs)

# Check closure
assert outline[0].x == outline[-1].x, "X coordinates don't match"
assert outline[0].y == outline[-1].y, "Y coordinates don't match"
print("✅ Outline is properly closed")

# Check symmetry (bass/treble should be equal magnitude, opposite sign)
mid = len(outline) // 2
for i in range(mid):
    treble_y = outline[i].y
    bass_y = outline[-(i+1)].y
    assert abs(treble_y + bass_y) < 0.01, f"Asymmetry at index {i}"
print("✅ Outline is symmetric about centerline")

# Check nut width
nut_width_measured = abs(outline[0].y - outline[-2].y)  # -2 because -1 is closure point
assert abs(nut_width_measured - inputs.nut_width_mm) < 0.01, "Nut width mismatch"
print(f"✅ Nut width correct: {nut_width_measured:.2f}mm")
```

### Automated Testing

**Pytest Test Suite (create in `tests/test_neck_taper_dxf_export.py`):**

```python
import pytest
from pathlib import Path
from instrument_geometry.neck_taper import (
    TaperInputs, 
    export_neck_outline_to_dxf,
    build_r12_polyline_dxf,
    Point
)

def test_build_r12_polyline_dxf_minimal():
    """Test DXF generation with minimal 3-point outline."""
    outline = [
        Point(0.0, 10.0),
        Point(100.0, 15.0),
        Point(0.0, 10.0)  # Closed
    ]
    dxf = build_r12_polyline_dxf(outline, "TEST_LAYER")
    
    assert "AC1009" in dxf
    assert "TEST_LAYER" in dxf
    assert "POLYLINE" in dxf
    assert "VERTEX" in dxf
    assert "SEQEND" in dxf
    assert dxf.count("VERTEX") == 3

def test_export_neck_outline_to_dxf_file(tmp_path):
    """Test complete DXF file export workflow."""
    inputs = TaperInputs(42.0, 57.0, 16.0, 648.0)
    output_file = tmp_path / "test_neck.dxf"
    
    export_neck_outline_to_dxf(output_file, inputs, num_frets=22)
    
    assert output_file.exists()
    assert output_file.stat().st_size > 1000  # Should be >1KB
    
    # Verify content
    content = output_file.read_text()
    assert "AC1009" in content
    assert "NECK_OUTLINE" in content
    assert content.count("VERTEX") == 46  # 23 treble + 23 bass (frets 0-22)

def test_dxf_coordinate_precision():
    """Test that coordinates are written with proper precision."""
    outline = [Point(1.23456789, 9.87654321), Point(1.23456789, 9.87654321)]
    dxf = build_r12_polyline_dxf(outline)
    
    # Should round to 4 decimal places
    assert "1.2346" in dxf
    assert "9.8765" in dxf
    assert "1.23456789" not in dxf  # Too much precision
```

**Run Tests:**
```bash
cd services/api
pytest tests/test_neck_taper_dxf_export.py -v
```

---

## Troubleshooting

### Issue: "Invalid DXF file" Error

**Symptoms:** CAM software refuses to open DXF

**Diagnostic Steps:**
```bash
# Check file encoding (should be UTF-8 or ASCII)
file -i neck_outline.dxf

# Check for binary characters (should be none)
cat neck_outline.dxf | od -c | grep -v "\\n"

# Verify header
head -n 10 neck_outline.dxf
```

**Common Causes:**
1. **Wrong encoding:** Use UTF-8 or ASCII (not UTF-16 or binary)
2. **Missing EOF:** File must end with `  0\nEOF\n`
3. **Malformed group codes:** Every value must be preceded by group code

**Fix:**
```python
# Regenerate with explicit encoding
export_neck_outline_to_dxf("fixed.dxf", inputs)
```

### Issue: Polyline Not Closed in CAM

**Symptoms:** Gap between start and end points

**Diagnostic Steps:**
```python
from instrument_geometry.neck_taper import generate_neck_outline, TaperInputs

inputs = TaperInputs(42.0, 57.0, 16.0, 648.0)
outline = generate_neck_outline(22, inputs)

# Check closure manually
print(f"First point: {outline[0]}")
print(f"Last point: {outline[-1]}")
print(f"Distance: {((outline[0].x - outline[-1].x)**2 + (outline[0].y - outline[-1].y)**2)**0.5:.6f}mm")
```

**Common Causes:**
1. **Floating-point error:** Distance > 0.0001mm (effectively zero, but CAM may flag)
2. **CAM tolerance too tight:** Some software requires exact match
3. **Missing closure point:** Outline doesn't include duplicate first point

**Fix:**
```python
# Ensure explicit closure in outline generator
outline.append(outline[0])  # Already done in our implementation
```

### Issue: Wrong Units (Inches vs Millimeters)

**Symptoms:** Dimensions off by factor of 25.4

**Diagnostic Steps:**
```bash
# Check coordinate magnitudes
grep "^  10$" neck_outline.dxf -A 1 | grep -v "^  10$" | head -n 5
# Values should be 0-600 range for mm, 0-24 range for inches
```

**Common Causes:**
1. **CAM software assumes inches:** DXF has no explicit units field in R12
2. **User selected wrong units on import**

**Fix:**
- **In CAM software:** Manually set units to millimeters after import
- **In code:** All coordinates are mm (cannot be changed without breaking spec)

### Issue: Too Many Points (Slow Toolpath)

**Symptoms:** CAM software lags, G-code file enormous

**Diagnostic Steps:**
```bash
# Count VERTEX entities
grep -c "^VERTEX$" neck_outline.dxf
# Should be ~50 for all frets (0-22), ~16 for sample_frets=[0,5,9,12,17,22]
```

**Fix:**
```python
# Use sparse sampling for faster CAM
export_neck_outline_to_dxf(
    "sparse_neck.dxf",
    inputs,
    num_frets=22,
    sample_frets=[0, 5, 9, 12, 17, 22]  # Only 6 points per side = 12 total
)
```

---

## Future Enhancements

### Planned DXF Extensions (Wave 18+)

1. **LWPOLYLINE Support** (DXF R2000+)
   - More compact format
   - Better arc representation
   - Requires version detection on import

2. **SPLINE Entities**
   - Smooth curves instead of linear segments
   - Better for compound tapers
   - May not be supported by older CAM

3. **Extended Data (XDATA)**
   - Embed metadata (nut width, scale length, taper rate)
   - CAM plugins could read and display
   - Requires R13+ format

4. **Multiple Layers**
   - `NECK_OUTLINE` = outer boundary
   - `CENTERLINE` = reference axis
   - `FRET_POSITIONS` = fret slot locations
   - `DIMENSIONS` = annotated measurements

### Export Format Alternatives

**STEP/IGES (3D Solid):**
- When neck thickness profiles are added
- Requires OpenCASCADE or similar CAD kernel
- Much larger file sizes

**SVG (2D Vector):**
- Web-friendly format
- Already supported by `geometry_router.py`
- Good for visual preview, less ideal for CAM

**G-code Direct Export:**
- Skip DXF intermediate step entirely
- Requires full toolpath generation (use Module L: Adaptive Pocketing)
- Machine-specific (need post-processor selection)

---

## See Also

- [Neck Taper Theory Guide](./Neck_Taper_Theory.md) - Mathematical foundations and CNC workflows
- [Instrument DXF Mapping Guide](./Instrument_DXF_Mapping.md) - Asset registry system
- [DXF R12 Specification](http://www.autodesk.com/techpubs/autocad/acad2000/dxf/) - Official AutoCAD reference
- [Module L: Adaptive Pocketing](../../ADAPTIVE_POCKETING_MODULE_L.md) - G-code generation from DXF

---

**Last Updated:** December 8, 2025  
**Author:** Luthier's Tool Box Development Team  
**Version:** 1.0 (Wave 17)
