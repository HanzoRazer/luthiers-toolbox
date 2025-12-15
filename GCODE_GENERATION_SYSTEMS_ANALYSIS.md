# G-Code Generation Systems Analysis

**Date:** December 11, 2025  
**Analysis Scope:** Comprehensive audit of G-code generation capabilities across Luthier's Tool Box repository  
**Status:** ✅ Complete

---

## 📋 Executive Summary

The Luthier's Tool Box repository contains **8 distinct G-code generation subsystems**, ranging from production-ready CAM engines to utility functions and analysis tools. This document provides a comprehensive overview of each system, their capabilities, integration points, and recommendations for extending the recently deployed rosette pattern generator.

### Key Findings

- **3 production-ready systems**: Adaptive Pocketing (L.3), CP-S57 Saw Generator, Fret Slots Multi-Post Export
- **5 post-processor configurations**: GRBL, Mach4, LinuxCNC, PathPilot, MASSO
- **3 adaptive feed modes**: Comment annotations, inline F-value scaling, M-code injection
- **Comprehensive tooling**: AI explainer, material-aware emission, arc fillet utilities
- **Multi-post architecture**: Single source to multiple CNC platform exports

### Recommended Integration Strategy

For the newly deployed rosette pattern generator, **Option A: Extend Fret Slots Export** is recommended due to existing multi-post infrastructure and proven DXF+SVG+G-code bundling capabilities.

---

## 🏗️ System Inventory

### **1. Adaptive Pocketing Engine (Module L - Production)**

**Location:** `services/api/app/routers/adaptive_router.py` + `cam/adaptive_core_l*.py`

**Maturity:** ✅ Production-ready (L.3 deployed)

**Purpose:** Advanced pocket milling with intelligent toolpath optimization and adaptive feed control.

#### **Capabilities**

**L.1 - Robust Offsetting:**
- Production-grade polygon offsetting via pyclipper
- Island/hole handling with automatic keepout zones
- Min-radius smoothing controls (0.05-1.0mm arc tolerance)
- Integer-safe coordinate space (no floating-point drift)

**L.2 - True Spiralizer:**
- Continuous spiral paths (nearest-point ring stitching)
- Adaptive local stepover (perimeter ratio heuristic)
- Min-fillet injection (automatic arc insertion at corners)
- HUD overlay system (tight radius markers, slowdown zones)

**L.3 - Trochoidal Intelligence:**
- Trochoidal insertion for overload zones (G2/G3 loops)
- Jerk-aware time estimation (realistic runtime predictions)
- S-curve acceleration model
- Classic vs jerk-aware time comparison

#### **Adaptive Feed Control (3 Modes)**

1. **Comment Mode** (Default):
```gcode
(FEED_HINT START scale=0.500)
G1 X100.0000 Y5.0000 F1200.0
G1 X105.0000 Y8.0000 F1200.0
(FEED_HINT END)
```

2. **Inline F Mode** (Direct scaling):
```gcode
G1 X100.0000 Y5.0000 F600.0   ; 50% slowdown applied
G1 X105.0000 Y8.0000 F600.0
G1 X110.0000 Y5.0000 F1200.0  ; Back to full speed
```

3. **M-Code Mode** (LinuxCNC M52):
```gcode
M52 P50              ; Set feed override to 50%
G1 X100.0000 Y5.0000 F1200.0
G1 X105.0000 Y8.0000 F1200.0
M52 P100             ; Restore 100% feed
```

#### **API Endpoints**

- `POST /cam/pocket/adaptive/plan` - Generate toolpath JSON
- `POST /cam/pocket/adaptive/gcode` - Export with post-processor headers
- `POST /cam/pocket/adaptive/batch_export` - Multi-post ZIP (DXF + SVG + multiple NC files)
- `POST /cam/pocket/adaptive/sim` - Simulate without full G-code generation

#### **Post-Processor Integration**

Supports 5 CNC platforms via JSON configuration files in `services/api/app/data/posts/`:

```json
// grbl.json
{
  "header": [
    "G90",           // Absolute positioning
    "G21",           // Metric units
    "G94",           // Feed per minute mode
    "F1000",         // Default feed rate
    "(post GRBL)"
  ],
  "footer": [
    "M5",            // Spindle off
    "M30"            // Program end
  ]
}
```

#### **Example G-Code Output**

```gcode
G21                              ; Units (mm)
G90                              ; Absolute positioning
G17                              ; XY plane selection
(POST=GRBL;UNITS=mm;DATE=2025-12-11T...)
G0 Z5.0000                       ; Safe height
G0 X3.0000 Y3.0000              ; Rapid to start
G1 Z-1.5000 F1200.0             ; Plunge
G1 X97.0000 Y3.0000 F1200.0     ; Cut
G2 X100.0000 Y5.0000 I1.5000 J0.0000 F1200.0  ; Arc (L.2 fillet)
(FEED_HINT START scale=0.500)   ; Adaptive zone (L.3)
G1 X100.0000 Y20.0000 F600.0    ; 50% feed reduction
(FEED_HINT END)
M30                             ; Program end
```

#### **Frontend Component**

`packages/client/src/components/AdaptivePocketLab.vue`
- Interactive parameter controls
- Canvas preview with HUD overlays
- Real-time statistics (classic + jerk-aware time)
- One-click multi-post export

#### **Documentation**

- [ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md) - Core system
- [PATCH_L1_ROBUST_OFFSETTING.md](./PATCH_L1_ROBUST_OFFSETTING.md) - L.1 upgrade
- [PATCH_L2_TRUE_SPIRALIZER.md](./PATCH_L2_TRUE_SPIRALIZER.md) - L.2 features
- [PATCH_L3_SUMMARY.md](./PATCH_L3_SUMMARY.md) - L.3 trochoids

---

### **2. CP-S57 Saw G-Code Generator (Production)**

**Location:** `services/api/app/cam_core/gcode/saw_gcode_generator.py`

**Maturity:** ✅ Production (80% complete per EXECUTION_PLAN.md)

**Purpose:** Saw-based CNC operations with multi-pass depth control.

#### **Capabilities**

- **Operation Types:** `slice`, `batch`, `contour`
- **Multi-pass depth planning:** Automatic DOC (depth of cut) control
- **Safe move sequencing:** Rapid → plunge → cut → retract
- **Feed rate conversion:** IPM ↔ mm/min
- **Path length estimation:** Accurate time predictions
- **Units support:** mm and inch

#### **Core Function**

```python
def generate_saw_gcode(request: SawGCodeRequest) -> SawGCodeResult:
    """
    Generate machine-ready G-code for saw operations.
    
    Args:
        op_type: "slice" | "batch" | "contour"
        toolpaths: List[SawToolpath] - cutting paths
        total_depth_mm: Total cut depth
        doc_per_pass_mm: Depth of cut per pass
        feed_ipm: Lateral feed rate (inches/min)
        plunge_ipm: Plunge feed rate
    
    Returns:
        SawGCodeResult:
            - gcode: Complete G-code program
            - path_length_mm: Total cutting distance
            - estimated_time_s: Runtime estimate
            - num_passes: Calculated passes
    """
```

#### **API Endpoint**

`POST /saw_gcode/generate`

**Request:**
```json
{
  "op_type": "slice",
  "toolpaths": [
    {"points": [[0, 0], [100, 0], [100, 50]]}
  ],
  "total_depth_mm": 3.0,
  "doc_per_pass_mm": 1.0,
  "feed_ipm": 60,
  "plunge_ipm": 20
}
```

**Response:**
```json
{
  "gcode": "G21\nG90\nG0 Z5.000\n...",
  "path_length_mm": 150.0,
  "estimated_time_s": 18.5,
  "num_passes": 3
}
```

#### **Example G-Code Output**

```gcode
G21                              ; mm units
G90                              ; Absolute mode
G0 Z5.000                        ; Safe Z
; === Pass 1/3 (Z=-1.000) ===
G0 X0.000 Y0.000                ; Position
G1 Z-1.000 F508                 ; Plunge (20 IPM → 508 mm/min)
G1 X100.000 Y0.000 F1524        ; Cut (60 IPM → 1524 mm/min)
G1 X100.000 Y50.000 F1524
G0 Z5.000                        ; Retract
; === Pass 2/3 (Z=-2.000) ===
G0 X0.000 Y0.000
G1 Z-2.000 F508
G1 X100.000 Y0.000 F1524
G1 X100.000 Y50.000 F1524
G0 Z5.000
; === Pass 3/3 (Z=-3.000) ===
G0 X0.000 Y0.000
G1 Z-3.000 F508
G1 X100.000 Y0.000 F1524
G1 X100.000 Y50.000 F1524
G0 Z5.000
M30
```

#### **Data Models**

```python
# cam_core/gcode/gcode_models.py

class SawGCodeRequest(BaseModel):
    op_type: Literal["slice", "batch", "contour"]
    toolpaths: List[SawToolpath]
    total_depth_mm: float
    doc_per_pass_mm: float
    feed_ipm: float
    plunge_ipm: float = 20

class SawGCodeResult(BaseModel):
    gcode: str
    path_length_mm: float
    estimated_time_s: float
    num_passes: int
```

#### **Status**

- ✅ Core generation complete
- ✅ Multi-pass depth control
- ✅ Feed rate conversion
- ⚠️ Post-processor integration pending (currently uses generic header/footer)
- ⚠️ Arc support planned (G2/G3 for curved saw paths)

---

### **3. Fret Slots Multi-Post Export (Production - Wave 19)**

**Location:** `services/api/app/calculators/fret_slots_export.py`

**Maturity:** ✅ Production (Wave 19 complete)

**Purpose:** Generate G-code for fret slot cutting with multi-post export capabilities.

#### **Capabilities**

- **Multi-post ZIP bundles:** Export to 5 CNC platforms simultaneously
- **Geometry support:** Straight and fan-fret configurations
- **File formats:** DXF R12 + SVG + G-code (per post)
- **Metadata injection:** `(POST=<id>;UNITS=<units>;DATE=<timestamp>)` comments
- **Instrument models:** Pre-configured templates (dreadnought, benedetto, etc.)

#### **Supported Post-Processors**

1. **GRBL** - Hobby CNC (3-axis routers)
2. **Mach4** - Industrial CNC controllers
3. **LinuxCNC** - Open-source EMC2 derivative
4. **PathPilot** - Tormach machine controllers
5. **MASSO** - MASSO G3 Australian controller

#### **API Endpoints**

- `POST /api/cam/fret_slots/export` - Single post-processor export
- `POST /api/cam/fret_slots/export/multi` - Multi-post ZIP bundle
- `POST /api/cam/fret_slots/export/raw` - Plain G-code without headers
- `GET /api/cam/fret_slots/post_processors` - List available posts

#### **Request Example (Multi-Post)**

```json
{
  "model_id": "benedetto_17",
  "fret_count": 22,
  "slot_depth_mm": 2.5,
  "slot_width_mm": 0.6,
  "post_ids": ["GRBL", "Mach4", "LinuxCNC"],
  "units": "mm"
}
```

#### **Response (ZIP Bundle)**

```
fret_slots_benedetto_17.zip
├── fret_slots_geometry.dxf         # DXF R12 format
├── fret_slots_geometry.svg         # SVG with metadata
├── fret_slots_GRBL.nc              # GRBL G-code
├── fret_slots_Mach4.nc             # Mach4 G-code
├── fret_slots_LinuxCNC.nc          # LinuxCNC G-code
└── fret_slots_meta.json            # Export metadata
```

#### **Example G-Code (GRBL)**

```gcode
G90
G21
G94
F1000
(post GRBL)
(POST=GRBL;UNITS=mm;DATE=2025-12-11T10:30:45Z)
G0 Z5.0                          ; Safe height
; === Fret 1 (Scale position 25.4mm) ===
G0 X25.4 Y50.0                   ; Position over slot
G1 Z-2.5 F300                    ; Plunge to depth
G1 Y52.0 F600                    ; Cut slot width
G0 Z5.0                          ; Retract
; === Fret 2 (Scale position 47.6mm) ===
G0 X47.6 Y50.0
G1 Z-2.5 F300
G1 Y52.0 F600
G0 Z5.0
; ... (repeat for each fret)
M5
M30
```

#### **Key Function**

```python
def generate_gcode(
    model_id: str,
    fret_count: int,
    slot_depth_mm: float,
    slot_width_mm: float,
    post_id: str = "GRBL",
    units: str = "mm"
) -> str:
    """
    Generate fret slot G-code for specified post-processor.
    
    Returns:
        Complete G-code program with post-specific headers/footers
    """
```

#### **Integration with Instrument Geometry**

Uses instrument model database (`services/api/app/data/instrument_models/`) for scale length and layout:

```json
// benedetto_17.json
{
  "model_id": "benedetto_17",
  "scale_length_mm": 648.0,
  "fret_spacing_rule": "equal_temperament",
  "nut_width_mm": 43.0,
  "bridge_width_mm": 54.0
}
```

#### **Frontend Integration**

Part of CAM Essentials UI (`packages/client/src/views/CAMEssentialsView.vue`)

#### **Documentation**

Referenced in Wave 19 completion notes and CAM_ESSENTIALS_N0_N10_QUICKREF.md

---

### **4. Rosette CNC G-Code Exporter (N16.3 + N16.5)**

**Location:** `services/api/app/cam/rosette/cnc/cnc_gcode_exporter.py`

**Maturity:** ✅ Production (RMOS Studio integration)

**Purpose:** Generate G-code for rosette ring cutting operations with machine profile support.

#### **Capabilities**

- **Machine profiles:** GRBL and FANUC variants
- **Tool management:** Tool change commands (Tn M6)
- **Spindle control:** Configurable RPM (S parameter)
- **Safe Z positioning:** Automatic retract between segments
- **Per-segment depth:** Individual Z control for each toolpath segment

#### **Machine Profiles**

```python
class MachineProfile(str, Enum):
    GRBL = "grbl"      # Hobby/maker machines (comments, semicolons)
    FANUC = "fanuc"    # Industrial (O-numbers, minimal comments)

@dataclass
class GCodePostConfig:
    profile: MachineProfile
    program_number: Optional[int] = None  # FANUC O-number
    safe_z_mm: float = 5.0
    spindle_rpm: int = 12000
    tool_id: int = 1
```

#### **Core Function**

```python
def generate_gcode_from_toolpaths(
    plan: ToolpathPlan,
    post: GCodePostConfig
) -> str:
    """
    Convert ToolpathPlan into profile-aware G-code.
    
    Args:
        plan: ToolpathPlan with segments in machine coordinates
        post: Post-processor configuration
    
    Returns:
        Complete G-code program with profile-specific formatting
    """
```

#### **GRBL Profile Output**

```gcode
( RMOS Studio Rosette Ring 1 )
G21  ; mm
G90  ; absolute
T1 M6  ; tool change
G0 Z5.000
M3 S12000
G0 X10.000 Y5.000               ; Start position
G1 Z-2.000 F300                 ; Plunge
G1 X50.000 Y5.000 F1200         ; Cut segment 1
G0 Z5.000                        ; Retract
G0 X60.000 Y10.000              ; Next segment
G1 Z-2.000 F300
G1 X100.000 Y10.000 F1200
G0 Z5.000
M5
M30
```

#### **FANUC Profile Output**

```gcode
O0001
( RMOS Studio Rosette Ring 1 )
G21
G90
T1 M6
G0 Z5.000
S12000 M3
G0 X10.000 Y5.000
G1 Z-2.000
G1 X50.000 Y5.000 F1200
G0 Z5.000
G0 X60.000 Y10.000
G1 Z-2.000
G1 X100.000 Y10.000 F1200
G0 Z5.000
M30
```

#### **Integration with RMOS Studio**

Part of the Rosette Manufacturing OS (RMOS) pipeline for CNC ring production. Toolpath segments generated by RMOS Studio planning engine, then converted to machine-specific G-code.

#### **Status**

- ✅ GRBL profile complete
- ✅ FANUC profile complete
- ✅ Tool change support
- ⚠️ Arc commands (G2/G3) planned but not implemented
- ⚠️ Additional profiles (Mach4, LinuxCNC) pending

---

### **5. VCarve SVG-to-G-Code Converter (Testing Only)**

**Location:** `services/api/app/art_studio/vcarve_router.py`

**Maturity:** ⚠️ Preview/Testing Only (NOT production-ready)

**Purpose:** Quick SVG path conversion for smoke testing and preview.

#### **Capabilities**

- SVG path parsing (basic `<path>` elements)
- Naive G-code emitter (linear moves only)
- Useful for quick previews and CI smoke tests

#### **Limitations**

❌ **NOT for production machining:**
- No feed optimization
- No arc support (all curves linearized)
- No post-processor integration
- No safety checks
- No multi-pass depth control

#### **API Endpoint**

`POST /vcarve/gcode`

**Request:**
```json
{
  "svg": "<svg><path d='M 0 0 L 100 0 L 100 50' /></svg>"
}
```

**Response:**
```json
{
  "gcode": "G21\nG90\nG0 X0 Y0\nG1 Z-1.0\nG1 X100 Y0\nG1 X100 Y50\nM30"
}
```

#### **Key Functions**

```python
def mlpaths_to_naive_gcode(...) -> str:
    """
    Convert multi-layer paths to basic G1 linear moves.
    
    WARNING: No optimization, no arcs, testing only.
    """

def svg_to_naive_gcode(svg: str) -> str:
    """
    Parse SVG and emit naive G-code.
    
    For smoke testing Art Studio features only.
    """
```

#### **Use Cases**

- ✅ Art Studio feature smoke tests
- ✅ Quick SVG → G-code preview
- ✅ CI pipeline validation
- ❌ **DO NOT use for actual CNC machining**

#### **Status**

Intentionally kept minimal as a testing utility. Production SVG-to-G-code should use adaptive pocketing or other CAM systems.

---

### **6. RMOS Material-Aware G-Code (MM-2 Reference)**

**Location:** `services/api/app/core/rmos_gcode_materials.py`

**Maturity:** 📚 Reference Implementation (MM-2 module)

**Purpose:** Demonstrate integration of material database with G-code generation.

#### **Capabilities**

- **Per-material feeds/speeds:** Material-specific CAM parameters
- **Per-segment overrides:** Individual segment feed/RPM control
- **Material database integration:** Reference material properties
- **Template for production systems:** Pattern for other generators

#### **Key Function**

```python
def emit_rosette_gcode_with_materials(...):
    """
    Generate G-code with material-aware feed rates.
    
    Each ring/segment specifies:
    - Material ID (walnut, maple, rosewood, etc.)
    - Optional chipload override
    - Optional RPM override
    
    Returns:
        G-code with dynamically calculated feeds based on material properties
    """
```

#### **Material Property Example**

```python
# Material database lookup
materials = {
    "walnut": {
        "chipload_mm": 0.15,
        "max_rpm": 18000,
        "surface_speed_m_min": 300
    },
    "maple": {
        "chipload_mm": 0.18,
        "max_rpm": 20000,
        "surface_speed_m_min": 350
    }
}

# Calculate feed rate
tool_diameter_mm = 6.0
rpm = materials[material_id]["max_rpm"]
chipload = materials[material_id]["chipload_mm"]
flutes = 2

feed_mm_min = rpm * flutes * chipload
# walnut: 18000 * 2 * 0.15 = 5400 mm/min
# maple:  20000 * 2 * 0.18 = 7200 mm/min
```

#### **Example G-Code Output**

```gcode
G21
G90
( Material: Walnut )
S18000 M3                        ; Walnut max RPM
G1 X0 Y0 F5400                   ; Walnut feed rate
G1 X50 Y0 F5400
G0 Z5.0
( Material: Maple )
S20000 M3                        ; Maple max RPM
G1 X60 Y0 F7200                  ; Maple feed rate
G1 X110 Y0 F7200
M30
```

#### **Integration Pattern**

```python
# Other generators can use this pattern:
from core.rmos_gcode_materials import get_material_params

material_params = get_material_params("walnut")
feed_rate = calculate_feed(
    rpm=material_params["max_rpm"],
    chipload=material_params["chipload_mm"],
    flutes=tool_flutes
)
```

#### **Status**

Reference implementation only. Not directly exposed as API endpoint. Serves as template for integrating material database with production G-code generators.

---

### **7. AI G-Code Explainer (Production - Wave 11/12)**

**Location:** `services/api/app/ai_cam/explain_gcode.py`

**Maturity:** ✅ Production (Wave 11/12 deployed)

**Purpose:** Line-by-line G-code analysis with risk annotation and human-readable explanations.

#### **Capabilities**

- **Command parsing:** G0, G1, G2, G3, M-codes, F/S/T parameters
- **Human explanations:** Plain English descriptions of each command
- **Risk detection:** `safe`, `caution`, `danger` classifications
- **Parameter extraction:** X, Y, Z, I, J, F, S values
- **Danger zones:** Rapid moves, tool changes, spindle control, deep plunges

#### **API Endpoint**

`POST /api/ai-cam/explain-gcode`

**Request:**
```json
{
  "gcode": "G21\nG90\nG0 X100 Y50\nM3 S12000\nG1 Z-5.0 F300\n"
}
```

**Response:**
```json
{
  "explanations": [
    {
      "line": "G21",
      "command": "G21",
      "explanation": "Set units to millimeters",
      "risk": "safe",
      "params": {}
    },
    {
      "line": "G90",
      "command": "G90",
      "explanation": "Set absolute positioning mode",
      "risk": "safe",
      "params": {}
    },
    {
      "line": "G0 X100 Y50",
      "command": "G0",
      "explanation": "Rapid move to X100 Y50 (DANGER: Fast positioning)",
      "risk": "danger",
      "params": {"x": 100.0, "y": 50.0}
    },
    {
      "line": "M3 S12000",
      "command": "M3",
      "explanation": "Spindle on clockwise at 12000 RPM (DANGER: Tool rotating)",
      "risk": "danger",
      "params": {"s": 12000}
    },
    {
      "line": "G1 Z-5.0 F300",
      "command": "G1",
      "explanation": "Linear plunge to Z-5.0 at 300mm/min (CAUTION: Entering material)",
      "risk": "caution",
      "params": {"z": -5.0, "f": 300.0}
    }
  ]
}
```

#### **Core Class**

```python
class GCodeExplainer:
    """
    Parse and explain G-code line by line.
    
    Risk levels:
    - safe: Setup commands (G21, G90, G17)
    - caution: Cutting moves, plunges
    - danger: Rapids, spindle on/off, tool changes
    """
    
    def explain_line(self, line: str) -> Dict[str, Any]:
        """
        Analyze single G-code line.
        
        Returns:
            {
                'command': str,          # Primary command (G1, M3, etc.)
                'explanation': str,      # Human-readable description
                'risk': str,             # safe | caution | danger
                'params': dict           # Extracted parameters (x, y, z, f, s, etc.)
            }
        """
```

#### **Risk Classification Rules**

```python
DANGER_COMMANDS = {
    "G0": "Rapid move (fast, uncontrolled)",
    "M3": "Spindle on clockwise",
    "M4": "Spindle on counterclockwise",
    "M6": "Tool change",
    "M8": "Coolant on"
}

CAUTION_COMMANDS = {
    "G1": "Linear move (check Z depth)",
    "G2": "Clockwise arc (verify I/J)",
    "G3": "Counterclockwise arc (verify I/J)"
}

SAFE_COMMANDS = {
    "G21": "Metric units",
    "G20": "Inch units",
    "G90": "Absolute positioning",
    "G91": "Relative positioning",
    "G17": "XY plane"
}
```

#### **Frontend Component**

`packages/client/src/components/cam/GCodeExplainerPanel.vue`

**Features:**
- Paste G-code text area
- Real-time line-by-line analysis
- Color-coded risk levels (green/yellow/red)
- Parameter tooltips
- Export explained G-code as annotated text

#### **Example UI Output**

```
Line 1: G21
  ✅ Set units to millimeters (SAFE)

Line 2: G90
  ✅ Set absolute positioning mode (SAFE)

Line 3: G0 X100 Y50
  ⚠️ Rapid move to X100 Y50 (DANGER: Fast positioning)
  Parameters: X=100.0, Y=50.0

Line 4: M3 S12000
  🔴 Spindle on clockwise at 12000 RPM (DANGER: Tool rotating)
  Parameters: S=12000

Line 5: G1 Z-5.0 F300
  ⚠️ Linear plunge to Z-5.0 at 300mm/min (CAUTION: Entering material)
  Parameters: Z=-5.0, F=300.0
```

#### **Use Cases**

- ✅ Education: Teach users G-code syntax
- ✅ Safety review: Pre-flight check before running programs
- ✅ Debugging: Identify problematic commands
- ✅ Documentation: Auto-annotate G-code for shop documentation

#### **Status**

- ✅ Production ready (Wave 11/12)
- ✅ Full UI integration
- ✅ Comprehensive command coverage
- 🔄 Ongoing: Add support for more M-codes and G-code variants

---

### **8. Polygon Offset G-Code Utilities (N17 Arc System)**

**Location:** `services/api/app/util/gcode_emit_basic.py` + `gcode_emit_advanced.py`

**Maturity:** 🛠️ Utility Functions (Internal use)

**Purpose:** Geometry-to-G-code conversion utilities for N17 polygon offset feature.

#### **Basic Emitter (Linear Only)**

**File:** `gcode_emit_basic.py`

```python
def emit_xy_polyline_nc(
    paths: List[List[Pt]],
    *,
    z: float = -1.0,
    safe_z: float = 5.0,
    units: str = "mm",
    feed: float = 600.0,
    spindle: int = 12000
) -> str:
    """
    Generate basic G-code with linear moves (G1) only.
    
    Args:
        paths: List of polygons (each polygon is list of (x, y) points)
        z: Cutting depth in mm
        safe_z: Retract height in mm
        units: "mm" or "inch"
        feed: Feed rate (mm/min or in/min)
        spindle: Spindle RPM
    
    Returns:
        G-code string with linear moves only
    """
```

**Example Output:**
```gcode
(N17 Polygon Offset)
G21
G90
G17
S12000 M3
G0 Z5.000
G0 X0.000 Y0.000                ; Start polygon 1
G1 Z-1.000 F600.0
G1 X100.000 Y0.000
G1 X100.000 Y50.000
G1 X0.000 Y50.000
G0 Z5.000                        ; Retract
M5
M30
```

#### **Advanced Emitter (Arc Fillets)**

**File:** `gcode_emit_advanced.py`

```python
def emit_xy_with_arcs(
    paths: List[List[Pt]],
    *,
    z: float = -1.0,
    safe_z: float = 5.0,
    units: str = "mm",
    feed: float = 600.0,
    feed_arc: Optional[float] = None,
    feed_floor: Optional[float] = None,
    link_radius: float = 1.0
) -> str:
    """
    Generate G-code with arc fillets at corners for smooth motion.
    
    Automatically inserts G2/G3 arc commands at polygon corners.
    
    Args:
        paths: List of polygons
        link_radius: Fillet radius for corner arcs in mm/inch
        feed_arc: Optional arc feed rate (defaults to feed)
        feed_floor: Optional minimum feed for tight arcs
    
    Returns:
        G-code string with G2/G3 arc commands at corners
    """
```

**Example Output (with arcs):**
```gcode
(N17 Polygon Offset — arcs + feed floors)
G21
G90
G17
S12000 M3
G0 Z5.000
G0 X1.000 Y0.000                ; Start with fillet offset
G1 Z-1.000 F600.0
G1 X99.000 Y0.000               ; Line to corner approach
G2 X100.000 Y1.000 I0.000 J1.000 F400.0  ; Arc fillet (90° corner)
G1 X100.000 Y49.000             ; Line to next corner
G2 X99.000 Y50.000 I-1.000 J0.000 F400.0 ; Arc fillet
G1 X1.000 Y50.000
G2 X0.000 Y49.000 I0.000 J-1.000 F400.0  ; Arc fillet
G1 X0.000 Y1.000
G2 X1.000 Y0.000 I1.000 J0.000 F400.0    ; Close with arc
G0 Z5.000
M5
M30
```

#### **Fillet Calculation Algorithm**

```python
def _fillet_points(a: Pt, b: Pt, c: Pt, r: float):
    """
    Calculate fillet arc parameters at corner b between points a-b-c.
    
    Args:
        a, b, c: Three consecutive points forming a corner at b
        r: Fillet radius
    
    Returns:
        Tuple of (p1, p2, ccw, center) where:
        - p1: Arc start point
        - p2: Arc end point
        - ccw: 1 for CCW arc (G3), -1 for CW arc (G2)
        - center: Arc center point (for I/J calculation)
    
    Algorithm:
        1. Calculate angle at corner b
        2. Compute tangent length: t = r / tan(angle/2)
        3. Find arc start/end points on incoming/outgoing edges
        4. Calculate arc center using bisector
        5. Determine arc direction (CW/CCW) via cross product
    """
```

#### **Integration**

These utilities are used by:
- N17 Polygon Offset feature (internal)
- Adaptive pocketing (for certain toolpath generation modes)
- Future geometry-based CAM operations

**Not exposed as direct API endpoints** - used internally by higher-level systems.

---

## 🏗️ Post-Processor Architecture

### **JSON-Based Configuration System**

All post-processors are defined in `services/api/app/data/posts/*.json`:

```
posts/
├── grbl.json          # GRBL 1.1 (hobby CNC)
├── mach4.json         # Mach4 (industrial)
├── linuxcnc.json      # LinuxCNC/EMC2
├── pathpilot.json     # Tormach PathPilot
├── masso.json         # MASSO G3 controller
└── custom_posts.json  # User-defined posts
```

### **Post Configuration Schema**

```json
{
  "header": [
    "G90",           // Array of G-code lines for program start
    "G21",
    "G94",
    "F1000",
    "(post GRBL)"
  ],
  "footer": [
    "M5",            // Array of G-code lines for program end
    "M30"
  ]
}
```

### **Post Injection Helper**

**File:** `services/api/app/post_injection_helpers.py`

Centralized utility for all G-code export endpoints to inject post-processor headers/footers.

#### **Key Functions**

```python
def quick_context_standard(body, mode="standard"):
    """
    Build context dictionary for post injection.
    
    Modes:
    - standard: POST, UNITS, DATE tokens
    - safe: Add SAFE_Z, RETRACT_Z tokens
    - helical: Add HELIX_PITCH, HELIX_ANGLE tokens
    
    Returns:
        Dict with replacement tokens for header/footer expansion
    """

def build_post_response(gcode: str, body, mode="standard"):
    """
    One-line post injection + filename generation + streaming response.
    
    Usage in routers:
        @router.post("/operation_gcode")
        def export_operation(body: OperationIn):
            raw_gcode = generate_moves(body)
            return build_post_response(raw_gcode, body, "standard")
    
    Handles:
    - Load post configuration
    - Inject header/footer
    - Add metadata comment
    - Set correct filename
    - Return StreamingResponse
    """

def validate_post_exists(post_id: str) -> Tuple[bool, str]:
    """
    Verify post configuration exists before export.
    
    Returns:
        (exists: bool, error_message: str)
    
    Usage:
        exists, error = validate_post_exists(body.post_id)
        if not exists:
            raise HTTPException(404, error)
    """

def verify_post_injection(gcode: str, post_id: str) -> bool:
    """
    Assert G-code has headers/footers (testing utility).
    
    Returns:
        True if post headers/footers detected in G-code
    
    Usage in tests:
        gcode = export_operation(body)
        assert verify_post_injection(gcode, "grbl")
    """
```

#### **Integration Pattern**

**Before (Manual post injection):**
```python
@router.post("/export_gcode")
def export_gcode(body: ExportIn):
    gcode = generate_toolpath(body)
    
    # Manual post loading
    posts = load_posts()
    post = posts.get(body.post_id, posts["grbl"])
    
    # Manual header/footer assembly
    header = post["header"]
    footer = post["footer"]
    program = "\n".join(header + [gcode] + footer)
    
    # Manual filename generation
    filename = f"{body.job_name or 'program'}.nc"
    
    return StreamingResponse(
        io.BytesIO(program.encode()),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

**After (Using helpers):**
```python
from ..post_injection_helpers import build_post_response

@router.post("/export_gcode")
def export_gcode(body: ExportIn):
    gcode = generate_toolpath(body)
    return build_post_response(gcode, body, "standard")
```

### **Metadata Comment Injection**

All post-processor exports include standardized metadata comments:

```gcode
(POST=GRBL;UNITS=mm;DATE=2025-12-11T10:30:45Z)
```

**Format:**
- Semicolon-delimited key=value pairs
- Always in parentheses (G-code comment syntax)
- Injected after header, before G-code body
- Preserved in DXF (999 code) and SVG (XML comment)

**Tokens:**
- `POST` - Post-processor ID (GRBL, Mach4, etc.)
- `UNITS` - mm or inch
- `DATE` - ISO 8601 timestamp with Z suffix

---

## 📊 System Comparison Matrix

| System | Maturity | Post Support | Adaptive Feed | Arcs (G2/G3) | Multi-Pass | Frontend UI | Documentation |
|--------|----------|--------------|---------------|--------------|------------|-------------|---------------|
| **Adaptive Pocketing** | ✅ Production (L.3) | ✅ 5 posts | ✅ 3 modes | ✅ L.2/L.3 | ✅ Stepdown | ✅ AdaptivePocketLab | ✅ Complete |
| **CP-S57 Saw** | ✅ Production (80%) | ⚠️ Generic | ❌ | ❌ | ✅ DOC control | ❌ | ⚠️ Partial |
| **Fret Slots** | ✅ Production (Wave 19) | ✅ 5 posts | ❌ | ❌ | ✅ Multi-depth | ✅ CAM Essentials | ✅ Complete |
| **Rosette CNC** | ✅ Production (RMOS) | ✅ 2 profiles | ❌ | ⚠️ Planned | ✅ Per-segment Z | ✅ RMOS Studio | ✅ Complete |
| **VCarve** | ⚠️ Preview Only | ❌ | ❌ | ❌ | ❌ | ✅ Art Studio | ❌ |
| **RMOS Material** | 📚 Reference (MM-2) | ❌ | ✅ Material-based | ❌ | ✅ | ❌ | ⚠️ Partial |
| **AI Explainer** | ✅ Production (Wave 11/12) | N/A (analysis) | N/A | ✅ Parse all | N/A | ✅ GCodeExplainerPanel | ✅ Complete |
| **Polygon Offset Utils** | 🛠️ Utility | ❌ | ❌ | ✅ Fillets | ❌ | ❌ | ❌ |

**Legend:**
- ✅ Implemented and production-ready
- ⚠️ Partial implementation or testing only
- ❌ Not implemented
- 📚 Reference implementation (not directly exposed)
- 🛠️ Internal utility (not for direct use)

---

## 🎯 Integration Recommendations for Rosette Pattern Generator

Based on the analysis above, here are **three integration strategies** for adding G-code export to the newly deployed rosette pattern generator:

### **Option A: Extend Fret Slots Export** ⭐ **RECOMMENDED**

**Why this is the best choice:**
- ✅ Already has multi-post ZIP export infrastructure
- ✅ Proven DXF + SVG + G-code bundling
- ✅ Production-ready with 5 post-processor support
- ✅ Metadata injection system in place
- ✅ Minimal code duplication

**Implementation approach:**

1. **Add `rosette_pattern` mode to `fret_slots_export.py`:**
```python
# services/api/app/calculators/fret_slots_export.py

def generate_rosette_pattern_gcode(
    pattern_id: str,
    ring_count: int,
    outer_diameter_mm: float,
    post_id: str = "GRBL",
    units: str = "mm"
) -> str:
    """
    Generate G-code for rosette pattern cutting.
    
    Reuses multi-post export infrastructure from fret slots.
    """
    # Load pattern from catalog
    from ..cam.rosette.pattern_generator import load_pattern_catalog
    catalog = load_pattern_catalog()
    pattern = catalog[pattern_id]
    
    # Convert pattern matrix to cutting paths
    # ... (implementation details)
    
    # Generate G-code with post-processor support
    return inject_post(toolpath_gcode, post_id=post_id, units=units)
```

2. **Add new endpoint to existing router:**
```python
# services/api/app/routers/cam_fret_slots_export_router.py

@router.post("/api/cam/rosette_pattern/export/multi")
def export_rosette_pattern_multi(body: RosettePatternExportIn):
    """
    Export rosette pattern to multiple post-processors.
    
    Returns ZIP with:
    - rosette_pattern_<id>_geometry.dxf
    - rosette_pattern_<id>_geometry.svg
    - rosette_pattern_<id>_<POST>.nc (one per post_id)
    """
    # Reuse multi-post ZIP bundling from fret slots
    pass
```

3. **Update `RosettePatternLibrary.vue`:**
```vue
<button @click="exportMultiPost" class="btn-primary">
  Export Multi-Post G-Code
</button>

<script setup>
async function exportMultiPost() {
  const response = await fetch('/api/cam/rosette_pattern/export/multi', {
    method: 'POST',
    body: JSON.stringify({
      pattern_id: selectedPattern.value.id,
      ring_count: selectedPattern.value.ring_count,
      post_ids: ['GRBL', 'Mach4', 'LinuxCNC']
    })
  })
  const blob = await response.blob()
  downloadBlob(blob, `rosette_${selectedPattern.value.id}_multi.zip`)
}
</script>
```

**Effort:** Low (2-4 hours)  
**Risk:** Low (reuses proven infrastructure)  
**Benefits:** Multi-post support, ZIP bundling, DXF/SVG/G-code in one call

---

### **Option B: Extend Rosette CNC Exporter**

**Advantages:**
- Already designed for rosette operations
- Toolpath segment architecture fits pattern generation
- GRBL and FANUC profiles ready

**Implementation approach:**

1. **Bridge pattern catalog to toolpath segments:**
```python
# services/api/app/cam/rosette/pattern_to_toolpath.py

def pattern_to_toolpath_plan(pattern: dict) -> ToolpathPlan:
    """
    Convert pattern matrix to CNC toolpath segments.
    
    Each ring becomes a toolpath segment with:
    - Start/end XY coordinates
    - Z depth (based on ring tier)
    - Material ID (for multi-material patterns)
    """
    segments = []
    for ring in pattern['rings']:
        segments.append(ToolpathSegment(
            x_start_mm=ring['inner_radius'],
            y_start_mm=0,
            x_end_mm=ring['outer_radius'],
            y_end_mm=0,
            z_start_mm=-ring['depth'],
            z_end_mm=-ring['depth']
        ))
    return ToolpathPlan(ring_id=pattern['id'], segments=segments)
```

2. **Add pattern export endpoint:**
```python
# services/api/app/routers/rosette_pattern_router.py

@router.post("/api/cam/rosette/patterns/export_gcode")
def export_pattern_gcode(body: PatternGCodeExportIn):
    """
    Export pattern as G-code using existing CNC exporter.
    """
    from ..cam.rosette.cnc.cnc_gcode_exporter import generate_gcode_from_toolpaths
    from ..cam.rosette.pattern_to_toolpath import pattern_to_toolpath_plan
    
    pattern = load_pattern(body.pattern_id)
    toolpath_plan = pattern_to_toolpath_plan(pattern)
    
    post_config = GCodePostConfig(
        profile=MachineProfile[body.post_id],
        safe_z_mm=5.0,
        spindle_rpm=body.spindle_rpm or 12000
    )
    
    gcode = generate_gcode_from_toolpaths(toolpath_plan, post_config)
    return build_post_response(gcode, body, "standard")
```

**Effort:** Medium (4-8 hours)  
**Risk:** Medium (need to design pattern→toolpath mapping)  
**Benefits:** Native rosette workflow, can leverage RMOS Studio tooling

---

### **Option C: Adaptive Pocketing for Channel Milling**

**Use case:** If patterns include channel pockets (not just ring profiles)

**When to use:**
- Patterns have bounded regions requiring material removal
- Need adaptive stepover and spiraling
- Patterns include islands/keepouts

**Implementation approach:**

1. **Convert pattern rings to boundary loops:**
```python
# services/api/app/cam/rosette/pattern_to_boundaries.py

def pattern_to_adaptive_loops(pattern: dict) -> List[Loop]:
    """
    Convert pattern rings to boundary loops for adaptive pocketing.
    
    Returns:
        List of loops (first = outer boundary, rest = islands)
    """
    loops = []
    
    # Outer boundary from pattern extent
    outer_radius = pattern['outer_diameter_mm'] / 2
    loops.append(Loop(pts=circle_to_polygon(outer_radius, segments=64)))
    
    # Each ring becomes an island (hole to avoid)
    for ring in pattern['rings']:
        inner = circle_to_polygon(ring['inner_radius'], segments=32)
        loops.append(Loop(pts=inner))
    
    return loops
```

2. **Call adaptive pocketing endpoint:**
```typescript
// packages/client/src/components/RosettePatternLibrary.vue

async function exportAdaptivePocket() {
  const loops = patternToBoundaries(selectedPattern.value)
  
  const response = await fetch('/cam/pocket/adaptive/gcode', {
    method: 'POST',
    body: JSON.stringify({
      loops,
      tool_d: 6.0,
      stepover: 0.45,
      strategy: 'Spiral',
      post_id: 'GRBL'
    })
  })
  
  downloadGCode(await response.blob())
}
```

**Effort:** Medium-High (6-12 hours)  
**Risk:** Medium (requires geometric transformation)  
**Benefits:** Advanced toolpath optimization, adaptive feed, L.3 features

---

## 🎯 Final Recommendation

**Implement Option A: Extend Fret Slots Export**

**Rationale:**
1. ✅ **Lowest effort** - Reuses existing multi-post ZIP infrastructure
2. ✅ **Lowest risk** - Proven system (Wave 19 production-ready)
3. ✅ **Immediate value** - One endpoint gives 5 CNC platforms
4. ✅ **Consistent UX** - Matches CAM Essentials workflow
5. ✅ **Minimal dependencies** - Only needs pattern catalog integration

**Implementation Timeline:**
- **Phase 1 (2 hours):** Add `generate_rosette_pattern_gcode()` function
- **Phase 2 (1 hour):** Create `/api/cam/rosette_pattern/export/multi` endpoint
- **Phase 3 (1 hour):** Add export button to `RosettePatternLibrary.vue`
- **Total:** ~4 hours for complete multi-post G-code export

**Deliverables:**
- Multi-post ZIP export (DXF + SVG + 5× NC files)
- Single-post export for quick testing
- UI integration with pattern library
- Metadata injection (POST, UNITS, DATE)
- Documentation update

---

## 📚 Related Documentation

### **Core Systems**
- [ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md) - Module L overview
- [PATCH_L1_ROBUST_OFFSETTING.md](./PATCH_L1_ROBUST_OFFSETTING.md) - L.1 polygon offsetting
- [PATCH_L2_TRUE_SPIRALIZER.md](./PATCH_L2_TRUE_SPIRALIZER.md) - L.2 continuous spiral
- [PATCH_L3_SUMMARY.md](./PATCH_L3_SUMMARY.md) - L.3 trochoids + jerk-aware time

### **Post-Processor System**
- [PATCH_K_POST_AWARE_COMPLETE.md](./__ARCHIVE__/docs_historical/PATCH_K_POST_AWARE_COMPLETE.md) - Post-aware exports
- [PATCH_N03_STANDARDIZATION.md](./PATCH_N03_STANDARDIZATION.md) - Post validation
- [POST_CHOOSER_SYSTEM.md](./POST_CHOOSER_SYSTEM.md) - UI multi-select integration

### **CAM Systems**
- [CAM_ESSENTIALS_N0_N10_QUICKREF.md](./CAM_ESSENTIALS_N0_N10_QUICKREF.md) - Fret slots CAM
- [CP_S57_SAW_BLADE_VALIDATOR.md](./CP_S57_SAW_BLADE_VALIDATOR.md) - Saw G-code system
- [RMOS_STUDIO_CNC_EXPORT.md](./docs/specs/rmos_studio/RMOS_STUDIO_CNC_EXPORT.md) - RMOS CNC export

### **AI/Analysis Tools**
- [WAVE_11_AI_CAM_Upgrade.md](./WAVE_11_AI_CAM_Upgrade.md) - AI G-code explainer
- [AI_CAM_QUICKREF.md](./AI_CAM_QUICKREF.md) - AI CAM features overview

### **Recent Deployments**
- [ROSETTE_PATTERN_GENERATOR_DEPLOYMENT.md](./ROSETTE_PATTERN_GENERATOR_DEPLOYMENT.md) - Pattern generator system
- [DXF_SECURITY_PATCH_DEPLOYMENT.md](./DXF_SECURITY_PATCH_DEPLOYMENT.md) - Security hardening

---

## 🔧 Next Steps

### **Immediate Actions**

1. **Review this analysis** with team/stakeholders
2. **Choose integration strategy** (recommend Option A)
3. **Estimate effort** and schedule implementation
4. **Assign developer** for G-code export integration

### **Implementation Tasks (Option A)**

- [ ] Create `generate_rosette_pattern_gcode()` in `fret_slots_export.py`
- [ ] Add `/api/cam/rosette_pattern/export/multi` endpoint
- [ ] Update `RosettePatternLibrary.vue` with export button
- [ ] Add multi-post selector (reuse `PostChooser.vue`)
- [ ] Create smoke test script (`test_rosette_gcode.ps1`)
- [ ] Update `ROSETTE_PATTERN_GENERATOR_DEPLOYMENT.md` with G-code export section
- [ ] Add CI workflow for multi-post validation

### **Testing Checklist**

- [ ] Single-post export (GRBL)
- [ ] Multi-post ZIP bundle (all 5 posts)
- [ ] Metadata injection verification
- [ ] DXF/SVG/G-code parity check
- [ ] Units conversion (mm ↔ inch)
- [ ] Filename sanitization
- [ ] Error handling (invalid pattern_id, missing post)

### **Documentation Updates**

- [ ] Add G-code export section to `ROSETTE_PATTERN_GENERATOR_DEPLOYMENT.md`
- [ ] Create `ROSETTE_GCODE_QUICKREF.md` for operator reference
- [ ] Update `CAM_ESSENTIALS_N0_N10_QUICKREF.md` with rosette integration
- [ ] Add example workflows to README.md

---

## 📊 Appendix: Code Examples

### **Example A: Multi-Post Export Request**

```typescript
// Frontend call
const response = await fetch('/api/cam/rosette_pattern/export/multi', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    pattern_id: "torres_traditional_1",
    ring_count: 12,
    outer_diameter_mm: 90.0,
    post_ids: ["GRBL", "Mach4", "LinuxCNC", "PathPilot", "MASSO"],
    units: "mm",
    job_name: "rosette_torres_1"
  })
})

const blob = await response.blob()
downloadBlob(blob, 'rosette_torres_1_multi.zip')
```

**ZIP Contents:**
```
rosette_torres_1_multi.zip
├── rosette_torres_1_geometry.dxf
├── rosette_torres_1_geometry.svg
├── rosette_torres_1_GRBL.nc
├── rosette_torres_1_Mach4.nc
├── rosette_torres_1_LinuxCNC.nc
├── rosette_torres_1_PathPilot.nc
├── rosette_torres_1_MASSO.nc
└── rosette_torres_1_meta.json
```

### **Example B: GRBL G-Code Output**

```gcode
G90
G21
G94
F1000
(post GRBL)
(POST=GRBL;UNITS=mm;DATE=2025-12-11T10:30:45Z)
(Pattern: Torres Traditional 1)
(Rings: 12, Outer Diameter: 90mm)

; === Ring 1: Outer Perimeter ===
G0 Z5.0                          ; Safe height
G0 X45.0 Y0.0                    ; Position at outer radius
G1 Z-1.5 F300                    ; Plunge
G3 X45.0 Y0.0 I-45.0 J0.0 F1200  ; Full circle cut
G0 Z5.0                          ; Retract

; === Ring 2: Inner Tier 1 ===
G0 X40.0 Y0.0
G1 Z-1.5 F300
G3 X40.0 Y0.0 I-40.0 J0.0 F1200
G0 Z5.0

; ... (repeat for rings 3-12)

M5
M30
(End of rosette pattern program)
```

### **Example C: Pattern-to-Toolpath Conversion**

```python
# services/api/app/cam/rosette/pattern_to_gcode.py

def pattern_to_ring_cuts(pattern: dict) -> str:
    """
    Convert pattern matrix to G-code ring cuts.
    
    Each ring in the pattern matrix becomes a circular G3 command.
    """
    gcode_lines = []
    safe_z = 5.0
    cut_depth = -1.5  # mm
    plunge_feed = 300  # mm/min
    cut_feed = 1200    # mm/min
    
    for i, ring in enumerate(pattern['rings'], 1):
        radius = ring['outer_radius']
        
        gcode_lines.extend([
            f"; === Ring {i}: {ring['name']} ===",
            f"G0 X{radius:.3f} Y0.0",           # Position
            f"G1 Z{cut_depth:.3f} F{plunge_feed}",  # Plunge
            f"G3 X{radius:.3f} Y0.0 I{-radius:.3f} J0.0 F{cut_feed}",  # Cut
            f"G0 Z{safe_z:.3f}",                # Retract
            ""
        ])
    
    return "\n".join(gcode_lines)
```

---

## 🎯 Conclusion

The Luthier's Tool Box repository has **comprehensive G-code generation infrastructure** spanning 8 distinct systems with varying maturity levels and use cases. The adaptive pocketing engine (Module L) represents the most advanced CAM system with L.3 features, while fret slots export provides production-ready multi-post capabilities.

**For rosette pattern generator integration, extending the fret slots export system (Option A) is the recommended path** due to minimal effort, low risk, and immediate multi-post ZIP export functionality.

The post-processor architecture is well-designed with JSON configurations, centralized injection helpers, and proven metadata systems. All production systems follow consistent patterns for header/footer injection, units handling, and filename generation.

**Next steps:** Schedule implementation of Option A (estimated 4 hours), add smoke tests, and update documentation with G-code export workflows.

---

**Document Version:** 1.0  
**Last Updated:** December 11, 2025  
**Author:** AI Analysis (GitHub Copilot)  
**Status:** ✅ Analysis Complete
