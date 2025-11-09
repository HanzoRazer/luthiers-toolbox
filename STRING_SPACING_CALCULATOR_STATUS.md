# String Spacing Calculator - Incomplete Source Code ⚠️

## Status: SOURCE CODE MISSING

### Problem Summary

The **String Spacing Calculator** exists in documentation and has complete dataclass definitions, but the **actual implementation functions are missing** from the Python source file.

---

## What Exists ✅

### 1. **Dataclass Definitions**
**Location**: `Guitar Design HTML app/10_06+2025/BenchMuse_StringSpacer_FretFind_StewMac_Module/stringspacer_fretfind_stewmac.py`

**File Size**: 36 lines (stub only)

**Complete Dataclasses**:
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SpacingInputs:
    """String spacing parameters"""
    nut_width: float          # Total nut width (mm)
    bridge_width: float       # Total bridge width (mm)
    edge_left_nut: float      # Left edge margin at nut (mm)
    edge_right_nut: float     # Right edge margin at nut (mm)
    edge_left_bridge: float   # Left edge margin at bridge (mm)
    edge_right_bridge: float  # Right edge margin at bridge (mm)
    string_diameters: List[float]  # Individual string gauges (mm)
    courses: int = 6          # Number of strings

@dataclass
class ScaleInputs:
    """Scale length and fret parameters"""
    scale_bass: float         # Bass-side scale length (inches)
    scale_treble: float       # Treble-side scale length (inches)
    n_frets: int              # Number of frets
    compensation: Optional[List[float]] = None  # Per-string saddle offsets (mm)

@dataclass
class LayoutOptions:
    """Export format options"""
    expand_courses_to_pairs: bool = False
    include_nut_line: bool = True
    include_bridge_base_polyline: bool = True
    include_bridge_comp_polyline: bool = True

@dataclass
class GeometryResult:
    """Calculated geometry"""
    nut_points: List[tuple]           # [(x, y), ...] at nut
    bridge_points_base: List[tuple]   # [(x, y), ...] at bridge (uncompensated)
    bridge_points_comp: List[tuple]   # [(x, y), ...] at bridge (compensated)
    frets: List[List[tuple]]          # [[(x1, y1), (x2, y2)], ...] fret lines
```

### 2. **Documentation**
**Location**: `BenchMuse_StringSpacer_FretFind_StewMac_Module/README.txt`

**Described Features**:
- **BenchMuse StringSpacer**: Gauge-aware edge-equal spacing algorithm
- **FretFind2D Integration**: Fret position formula `d = scale - (scale / (2^(n/12)))`
- **StewMac Compensation**: Per-string saddle offsets based on gauge and action

**Expected API**:
```python
# Usage described in README
spacing = SpacingInputs(
    nut_width=1.650,
    bridge_width=2.080,
    edge_left_nut=0.100,
    edge_right_nut=0.100,
    edge_left_bridge=0.120,
    edge_right_bridge=0.120,
    string_diameters=[0.010, 0.013, 0.017, 0.026, 0.036, 0.046],
    courses=6
)

scale = ScaleInputs(
    scale_bass=25.5,
    scale_treble=25.5,
    n_frets=22
)

# THESE FUNCTIONS DO NOT EXIST IN THE .py FILE:
geom = generate_geometry(spacing, scale)        # MISSING
export_dxf("guitar.dxf", geom)                   # MISSING
export_csv("guitar.csv", geom)                   # MISSING
```

### 3. **Example Output Files**
**Location**: `Guitar Design HTML app/10_06+2025/`

**Files Found**:
- `six_string_25_5in.csv` (spacing data table)
- `six_string_25_5in.dxf` (DXF with nut, frets, bridge lines)

**CSV Format**:
```csv
string,nut_x,nut_y,bridge_x,bridge_y,fret_1_x,fret_1_y,...
1,0.150,0.000,645.160,0.000,36.252,0.000,...
2,0.150,6.000,645.160,6.500,36.252,6.000,...
...
```

**DXF Layers**:
- `NUT` (line at x=0)
- `FRETS_1` through `FRETS_22` (individual fret lines)
- `BRIDGE_BASE` (uncompensated)
- `BRIDGE_COMP` (with saddle offsets)
- `STRING_1` through `STRING_6` (string centerlines)

---

## What's Missing ❌

### **Implementation Functions**

The `stringspacer_fretfind_stewmac.py` file is missing the following functions that are described in the README:

1. **`generate_geometry(spacing: SpacingInputs, scale: ScaleInputs, options: LayoutOptions = None) -> GeometryResult`**
   - **Purpose**: Calculate string positions at nut/bridge, fret lines, and compensation
   - **Algorithm**:
     ```python
     # BenchMuse StringSpacer (gauge-aware edge-equal)
     available_width = nut_width - edge_left - edge_right
     spacing_gaps = available_width - sum(string_diameters)
     gap_per_space = spacing_gaps / (courses - 1)
     
     x_positions = []
     current_x = edge_left + string_diameters[0]/2
     for i in range(courses):
         x_positions.append(current_x)
         if i < courses - 1:
             current_x += (string_diameters[i]/2 + gap_per_space + string_diameters[i+1]/2)
     
     # FretFind2D fret positions
     for n in range(1, n_frets + 1):
         d = scale - (scale / (2 ** (n / 12)))
         fret_lines.append([(d, y_treble), (d, y_bass)])
     
     # StewMac compensation (per-string offsets)
     for i, comp in enumerate(compensation or [0]*courses):
         bridge_comp_x[i] = scale + comp
     ```

2. **`export_dxf(filename: str, geom: GeometryResult, options: LayoutOptions = None)`**
   - **Purpose**: Write R12 DXF with string/fret layers
   - **Layers**: NUT, FRETS_1..n, BRIDGE_BASE, BRIDGE_COMP, STRING_1..n

3. **`export_csv(filename: str, geom: GeometryResult)`**
   - **Purpose**: Write tabular data for spreadsheet import
   - **Columns**: string, nut_x, nut_y, bridge_x, bridge_y, fret_1_x, fret_1_y, ...

4. **Helper Functions** (likely needed):
   - `calculate_fret_position(scale: float, fret_num: int) -> float`
   - `interpolate_string_y(string_idx: int, x: float, nut_y: float, bridge_y: float) -> float`
   - `apply_compensation(base_points: List[tuple], compensation: List[float]) -> List[tuple]`

---

## Investigation Results

### **File Search**
```powershell
# Confirmed: File exists but is only a stub
Get-Content "Guitar Design HTML app\10_06+2025\BenchMuse_StringSpacer_FretFind_StewMac_Module\stringspacer_fretfind_stewmac.py" | Measure-Object -Line
# Result: 36 lines (not 1,291 bytes as mentioned in docs)

# No implementation functions found
grep -r "def generate_geometry" .
grep -r "def export_dxf" .
# Result: No matches
```

### **Compressed Archives**
**Location**: `Guitar Design HTML app/10_06+2025/`

**Files Found**:
- `Luthiers_Tool_Box_Full_v1.zip`
- `Luthiers_Tool_Box_Full_v2.zip`
- `J45_CAM_Import_Kit.zip`
- `LesPaul_CAM_Import_Kit.zip`

**Status**: Not yet extracted/searched

### **Possible Locations**
1. **Compressed archives** (most likely) - full source may be in ZIP files
2. **MVP Build folders** - `MVP Build_10-11-2025/`, `MVP Build_1012-2025/`
3. **String Master Scaffolding** - `String Master Generic Scaffolding/cad_collab_scaffold_v10/`
4. **Other project variants** - `Guitar Design HTML app-2/`, `Lutherier Project 2/`

---

## Next Steps

### **Option 1: Extract from Compressed Archives** (RECOMMENDED)
**Estimated Time**: 1-2 hours

**Process**:
1. Extract all ZIP files in `Guitar Design HTML app/10_06+2025/`
2. Search for complete `stringspacer_fretfind_stewmac.py` implementation
3. Verify functions exist: `generate_geometry()`, `export_dxf()`, `export_csv()`
4. Copy to main project

**PowerShell Commands**:
```powershell
cd "Guitar Design HTML app\10_06+2025"

# Extract all ZIPs
Get-ChildItem -Filter "*.zip" | ForEach-Object {
    $dest = "extracted_$($_.BaseName)"
    Expand-Archive -Path $_.FullName -DestinationPath $dest -Force
    Write-Host "Extracted: $($_.Name)"
}

# Search for implementation
Get-ChildItem -Recurse -Filter "stringspacer*.py" | ForEach-Object {
    $lineCount = (Get-Content $_.FullName | Measure-Object -Line).Lines
    Write-Host "$($_.FullName): $lineCount lines"
}
```

### **Option 2: Rebuild from Scratch**
**Estimated Time**: 1-2 days

**Implementation Plan**:
1. Use existing dataclass definitions
2. Implement BenchMuse StringSpacer algorithm (gauge-aware spacing)
3. Implement FretFind2D fret position formula
4. Implement StewMac compensation lookup
5. Add DXF export with ezdxf (R12, layered)
6. Add CSV export
7. Create Vue component with preview

**Key Algorithms**:

**BenchMuse StringSpacer** (edge-equal, gauge-aware):
```python
def calculate_string_spacing(nut_width, edge_left, edge_right, gauges):
    """
    BenchMuse algorithm: Equal gaps between string edges (not centers).
    Adjusts for varying string diameters.
    """
    available = nut_width - edge_left - edge_right
    gap_space = available - sum(gauges)
    gap_size = gap_space / (len(gauges) - 1)
    
    positions = []
    x = edge_left + gauges[0]/2
    for i, d in enumerate(gauges):
        positions.append(x)
        if i < len(gauges) - 1:
            x += (d/2 + gap_size + gauges[i+1]/2)
    
    return positions
```

**FretFind2D** (equal temperament):
```python
def calculate_fret_position(scale_length, fret_number):
    """
    Standard equal temperament formula.
    Returns distance from nut to fret.
    """
    return scale_length - (scale_length / (2 ** (fret_number / 12)))
```

**StewMac Compensation** (per-string lookup):
```python
STEWMAC_COMPENSATION = {
    # Gauge (in): Offset (mm)
    0.010: 1.5,   # High E
    0.013: 1.8,   # B
    0.017: 2.2,   # G
    0.026: 3.0,   # D (wound)
    0.036: 3.5,   # A
    0.046: 4.0,   # Low E
}

def get_compensation(gauge_in):
    """Lookup compensation by string gauge."""
    return STEWMAC_COMPENSATION.get(gauge_in, 2.5)  # default 2.5mm
```

### **Option 3: Search Other Project Folders**
**Estimated Time**: 30 minutes

**Locations to Check**:
1. `MVP Build_10-11-2025/` (recent MVP implementation)
2. `MVP Build_1012-2025/` (newer MVP)
3. `String Master Generic Scaffolding/cad_collab_scaffold_v10/server/`
4. `Smart Guitar Build/` (may have string spacing utility)

---

## Temporary Workaround

Until the full implementation is found/created, the **Bridge Calculator** can serve as a partial replacement:

**Bridge Calculator Covers**:
- ✅ String spread (treble to bass)
- ✅ Compensation (Ct, Cb)
- ✅ DXF export

**Bridge Calculator Does NOT Cover**:
- ❌ Individual string positions (only 2 endpoints)
- ❌ Nut spacing calculation
- ❌ Fret positions
- ❌ Gauge-aware spacing
- ❌ Per-string compensation

---

## Priority Level

🔴 **CRITICAL** - This is a core lutherie calculation tool

**Why Critical**:
1. **Fundamental Design Parameter**: String spacing affects playability, ergonomics, and instrument feel
2. **CAM Integration**: DXF export is required for CNC routing of nut/bridge slots
3. **Accuracy Requirements**: 0.1mm precision is essential for intonation
4. **User Expectation**: Documentation and README describe complete functionality

---

## User Communication

**Recommended Response**:
> "I found the **Bridge Calculator** source code and successfully integrated it (371-line Vue component + DXF export pipeline). It's now accessible in the navigation menu.
>
> However, the **String Spacing Calculator** source file is incomplete—it only contains dataclass definitions (36 lines) but is missing the actual implementation functions (`generate_geometry()`, `export_dxf()`, `export_csv()`).
>
> **Next steps**:
> 1. Extract compressed archives in `Guitar Design HTML app/10_06+2025/` to search for the full implementation
> 2. If not found, I can rebuild the calculator from scratch using the documented algorithms (BenchMuse, FretFind2D, StewMac compensation)
>
> **Estimated time**:
> - Option 1 (extract): 1-2 hours
> - Option 2 (rebuild): 1-2 days
>
> Should I proceed with extracting the ZIP files first?"

---

## Files Referenced

```
Guitar Design HTML app/10_06+2025/
  BenchMuse_StringSpacer_FretFind_StewMac_Module/
    stringspacer_fretfind_stewmac.py     # 36 lines (STUB)
    README.txt                           # Complete documentation
  Luthiers_Tool_Box_Full_v1.zip          # Not extracted yet
  Luthiers_Tool_Box_Full_v2.zip          # Not extracted yet
  six_string_25_5in.csv                  # Example output
  six_string_25_5in.dxf                  # Example DXF
```

---

## Summary

✅ **Bridge Calculator**: Fully integrated and working
⚠️ **String Spacing Calculator**: Dataclasses exist, but implementation missing

**Recommended Action**: Extract compressed archives to find complete source code (1-2 hours), then integrate like Bridge Calculator.
