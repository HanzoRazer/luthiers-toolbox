# DXF to G-code Workflow Guide

**Version:** 1.0.0
**Date:** 2026-01-14
**Status:** 95% Complete - API Working, UI Needs Enablement

---

## Executive Summary

The luthiers-toolbox provides a complete pipeline to convert DXF files to CNC-ready G-code. The backend API is fully functional; the frontend UI has some disabled buttons that need enabling.

**Quick Path (API):**
```
DXF File → /api/cam/pocket/adaptive/plan_from_dxf → response.request.loops → /api/cam/pocket/adaptive/gcode → .nc File
```

**Required fields:**
- `/plan_from_dxf`: `file` (form), `tool_d` (form)
- `/gcode`: `loops` (JSON), `tool_d` (JSON)

---

## 1. Complete API Workflow

### Step 1: Validate DXF (Optional but Recommended)

```bash
curl -X POST "http://localhost:8000/api/cam/blueprint/preflight" \
  -F "file=@your_design.dxf" \
  -F "layer_name=GEOMETRY"
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": ["Small dimension detected: 2.5mm"],
  "info": {
    "entity_count": 3,
    "lwpolyline_count": 2,
    "has_closed_paths": true,
    "bounding_box": {"x_min": 0, "y_min": 0, "x_max": 150, "y_max": 100}
  }
}
```

### Step 2: Generate Toolpath from DXF

```bash
curl -X POST "http://localhost:8000/api/blueprint/cam/to-adaptive?layer_name=GEOMETRY&tool_d=6&stepover=0.4&z_rough=-3&feed_xy=1200&safe_z=5"   -F "file=@your_design.dxf"   -o toolpath_response.json
```

**Response (toolpath_response.json):**
```json
{
  "loops_extracted": 1,
  "loops": [{"pts": [[0,0], [100,0], [100,50], [0,50]]}],
  "moves": [
    {"code": "G0", "z": 5.0},
    {"code": "G0", "x": 96.5, "y": 46.5},
    {"code": "G1", "z": -3.0, "f": 1200.0},
    {"code": "G1", "x": 3.5, "y": 46.5, "f": 1200.0}
  ],
  "stats": {"move_count": 23},
  "warnings": []
}
```

### Step 3: Generate G-code

```bash
curl -X POST "http://localhost:8000/api/cam/pocket/adaptive/gcode" \
  -H "Content-Type: application/json" \
  -d '{"loops":[{"pts":[[0,0],[100,0],[100,50],[0,50]]}],"tool_d":6,"z_rough":-3,"post_id":"GRBL"}' \
  -o output.nc
```

**Output (output.nc):**
```gcode
G90
G17
G21
M3 S18000           ; Spindle ON
G4 P2               ; Dwell for ramp-up
G0 Z5.0
G0 X96.5 Y46.5
G1 Z-3.0 F1200
G1 X3.5 Y46.5 F1200
...
G0 Z5.0
M5                  ; Spindle OFF
M30
```

---

## 2. Single-Step API (Recommended)

For a streamlined workflow, use the direct DXF-to-plan endpoint:

```bash
curl -X POST "http://localhost:8000/api/cam/pocket/adaptive/plan_from_dxf" \
  -F "file=@your_design.dxf" \
  -F "tool_d=6.0" \
  -F "stepover=0.45" \
  -F "stepdown=1.5" \
  -F "strategy=Spiral" \
  -F "feed_xy=1200" \
  -F "safe_z=5.0" \
  -F "z_rough=-3.0" \
  -o plan.json
```

---

## 3. Python Script: Complete Pipeline

Create this script for automated DXF → G-code conversion:

```python
#!/usr/bin/env python3
"""
DXF to G-code Converter (Golden Path)
Usage: python dxf_to_gcode.py input.dxf output.nc [--post GRBL]

Uses plan_from_dxf endpoint which returns loops in response.request.loops
"""
import sys
import json
import requests
from pathlib import Path

API_BASE = "http://localhost:8000/api"

DEFAULT_PARAMS = {
    "tool_d": 6.0,
    "stepover": 0.4,
    "z_rough": -3.0,
    "feed_xy": 1200,
    "safe_z": 5.0,
}


def plan_from_dxf(dxf_path: Path, params: dict) -> dict:
    """Generate toolpath from DXF using plan_from_dxf endpoint."""
    print(f"[1/2] Generating toolpath from DXF...")

    with open(dxf_path, "rb") as f:
        response = requests.post(
            f"{API_BASE}/cam/pocket/adaptive/plan_from_dxf",
            files={"file": (dxf_path.name, f, "application/dxf")},
            data=params
        )

    if response.status_code != 200:
        print(f"  Error: {response.text}")
        return None

    result = response.json()
    
    # Loops are in response["request"]["loops"]
    loops = result.get("request", {}).get("loops", [])
    if not loops:
        print("  Error: No loops extracted from DXF")
        return None

    plan_stats = result.get("plan", {})
    print(f"  Loops extracted: {len(loops)}")
    print(f"  Moves generated: {plan_stats.get('stats', {}).get('move_count', 'N/A')}")

    return result


def generate_gcode(plan_result: dict, post_id: str, output_path: Path, params: dict) -> bool:
    """Generate G-code from plan result."""
    print(f"[2/2] Generating G-code ({post_id})...")

    # Extract loops from plan_from_dxf response
    loops = plan_result["request"]["loops"]

    gcode_request = {
        "loops": loops,
        "tool_d": params["tool_d"],
        "z_rough": params["z_rough"],
        "feed_xy": params.get("feed_xy", 1200),
        "safe_z": params.get("safe_z", 5.0),
        "post_id": post_id,
        "units": "mm"
    }

    response = requests.post(
        f"{API_BASE}/cam/pocket/adaptive/gcode",
        json=gcode_request,
        stream=True
    )

    if response.status_code != 200:
        print(f"  Error: {response.text}")
        return False

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"  Saved: {output_path}")
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python dxf_to_gcode.py input.dxf output.nc [--post GRBL]")
        print("
Post-processors: GRBL, Mach4, LinuxCNC, PathPilot, MASSO")
        sys.exit(1)

    dxf_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    post_id = "GRBL"

    if "--post" in sys.argv:
        idx = sys.argv.index("--post")
        if idx + 1 < len(sys.argv):
            post_id = sys.argv[idx + 1]

    if not dxf_path.exists():
        print(f"Error: File not found: {dxf_path}")
        sys.exit(1)

    print(f"
DXF to G-code: {dxf_path.name} -> {output_path.name} ({post_id})")
    print("-" * 50)

    # Step 1: plan_from_dxf (returns loops in response.request.loops)
    plan_result = plan_from_dxf(dxf_path, DEFAULT_PARAMS)
    if plan_result is None:
        sys.exit(1)

    # Step 2: Generate G-code
    if not generate_gcode(plan_result, post_id, output_path, DEFAULT_PARAMS):
        sys.exit(1)

    print("-" * 50)
    print("Done!")


if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Basic usage (GRBL post-processor)
python dxf_to_gcode.py guitar_body.dxf output.nc

# Specify post-processor
python dxf_to_gcode.py guitar_body.dxf output.nc --post Mach4
python dxf_to_gcode.py guitar_body.dxf output.nc --post LinuxCNC
python dxf_to_gcode.py guitar_body.dxf output.nc --post MASSO
```

---

## 4. DXF File Requirements

### Supported Format
- **DXF Version:** R12 or R2000 (AutoCAD 2000)
- **Encoding:** ASCII or binary

### Required Structure
```
Layer: "GEOMETRY" (default, configurable)
  └── LWPOLYLINE entities
      ├── is_closed = True (or first point == last point)
      ├── Minimum 3 points per loop
      └── Clockwise winding for outer boundary
```

### Loop Classification
- **First loop (largest area):** Outer boundary - material to remove
- **Subsequent loops:** Islands - keepout zones (not machined)

### Example DXF Structure
```
SECTION
  ENTITIES
    LWPOLYLINE
      Layer: GEOMETRY
      Closed: 1
      Points: (0,0), (100,0), (100,50), (0,50)
    LWPOLYLINE
      Layer: GEOMETRY
      Closed: 1
      Points: (40,20), (60,20), (60,30), (40,30)  # Island
  ENDSEC
```

### Creating Compatible DXF Files

**From Inkscape:**
1. Draw closed paths (no open lines)
2. File → Save As → Desktop Cutting Plotter (DXF R12)
3. Ensure "LWPOLYLINE" option is selected

**From Fusion 360:**
1. Sketch → Create closed profiles
2. File → Export → DXF
3. Select "R2000" format

**From FreeCAD:**
1. Draw closed wires in Sketcher
2. File → Export → Autodesk DXF

---

## 5. CAM Parameters Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tool_d` | float | 6.0 | Tool diameter in mm |
| `stepover` | float | 0.45 | Fraction of tool diameter (0.1-0.95) |
| `stepdown` | float | 1.5 | Depth per pass in mm |
| `strategy` | string | "Spiral" | "Spiral" (continuous) or "Lanes" (back-forth) |
| `feed_xy` | float | 1200 | XY cutting feed rate (mm/min) |
| `feed_z` | float | 300 | Z plunge feed rate (mm/min) |
| `rapid` | float | 3000 | Rapid traverse rate (mm/min) |
| `safe_z` | float | 5.0 | Safe retract height (mm) |
| `z_rough` | float | -3.0 | Total cutting depth (mm, negative) |
| `climb` | bool | true | Climb milling (vs conventional) |
| `smoothing` | float | 0.1 | Arc smoothing tolerance (mm) |
| `margin` | float | 0.0 | Extra offset from boundary (mm) |

### Strategy Comparison

| Strategy | Best For | Characteristics |
|----------|----------|-----------------|
| **Spiral** | Pockets, soft materials | Continuous cut, no retracts, lower tool wear |
| **Lanes** | Slots, hard materials | Back-and-forth, retracts at ends, better chip clearing |

---

## 6. Post-Processor Profiles

All post-processors include automatic spindle control (M3 S18000 on, M5 off).

| Post ID | Machine Type | Spindle | End Code |
|---------|--------------|---------|----------|
| `GRBL` | Hobby CNC, 3018 | M3 S18000 | M30 |
| `Mach4` | Mach4 controllers | M3 S18000 | M30 |
| `LinuxCNC` | LinuxCNC/EMC2 | M3 S18000 | M2 |
| `PathPilot` | Tormach machines | M3 S18000 | M30 |
| `MASSO` | MASSO controllers | M3 S18000 | M30 |

### G-code Structure

All post-processors generate this structure:

```gcode
; === HEADER ===
G90                 ; Absolute positioning
G17                 ; XY plane selection
G21                 ; Metric units (mm)
M3 S18000           ; Spindle ON at 18000 RPM
G4 P2               ; 2-second dwell for spindle ramp-up

; === TOOLPATH ===
G0 Z5.0             ; Rapid to safe height
G0 X10.5 Y15.2      ; Rapid to start position
G1 Z-3.0 F300       ; Plunge to cutting depth
G1 X50.0 Y15.2 F1200 ; Cutting moves...

; === FOOTER ===
G0 Z5.0             ; Retract to safe height
M5                  ; Spindle OFF
M30                 ; Program end (M2 for LinuxCNC)
```

### Spindle Speed

Default: **18000 RPM** (typical wood router speed). The spindle speed is
currently fixed in the post-processor profile. For variable RPM support,
the `rpm` parameter would need to be added to the G-code endpoint.

---

## 7. Error Handling

### Common DXF Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "No closed paths found" | Open polylines | Close all paths in CAD software |
| "No LWPOLYLINE entities" | Wrong entity type | Export as LWPOLYLINE, not LINE |
| "Layer not found" | Wrong layer name | Use `layer_name=0` for default layer |
| "Self-intersecting path" | Overlapping geometry | Fix intersections in CAD |

### Toolpath Warnings

| Warning | Cause | Impact |
|---------|-------|--------|
| "Small dimension" | Feature < tool diameter | May not machine correctly |
| "Steep plunge" | High feed_z vs material | Reduce feed_z or increase passes |
| "Tight corner" | Radius < tool radius | Tool won't reach corner |

---

## 8. Frontend UI Status

### Current State
The backend API is **fully functional**, but some frontend buttons are disabled:

| Component | Location | Status | Issue |
|-----------|----------|--------|-------|
| BlueprintLab.vue | Phase 1-2 UI | ✅ Working | Analysis + vectorization work |
| "Send to CAM" button | BlueprintLab.vue:232 | ❌ Disabled | `disabled` attribute set |
| PipelineLab.vue | Phase 3 UI | ⚠️ Partial | Toolpath works, G-code button missing |
| G-code download | PipelineLab.vue | ❌ Missing | No UI button exists |

### To Enable Frontend (Developer Task)

**1. Enable "Send to CAM" in BlueprintLab.vue:**
```vue
<!-- Line ~232: Remove disabled attribute -->
<button
  @click="sendToCAM"
  class="btn btn-primary"
  <!-- Remove: :disabled="true" -->
>
  Send to CAM
</button>
```

**2. Add G-code download to PipelineLab.vue:**
```vue
<button
  @click="downloadGcode"
  class="btn btn-success"
  :disabled="!toolpathReady"
>
  Download G-code (.nc)
</button>

<script setup>
async function downloadGcode() {
  const response = await fetch('/api/cam/pocket/adaptive/gcode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      loops: currentLoops.value,
      tool_d: params.tool_d,
      // ... other params
      post_id: selectedPost.value,
      units: 'mm'
    })
  });

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${jobName.value}_${selectedPost.value}.nc`;
  a.click();
}
</script>
```

---

## 9. Troubleshooting

### API Not Responding
```bash
# Check if server is running
curl http://localhost:8000/health

# Check CAM endpoints
curl http://localhost:8000/api/cam/pocket/adaptive/health
```

### DXF Parsing Fails
```bash
# Test with preflight
curl -X POST "http://localhost:8000/api/cam/blueprint/preflight" \
  -F "file=@problem.dxf" \
  -F "layer_name=0"  # Try default layer
```

### Toolpath Empty
- Check DXF has closed LWPOLYLINE entities
- Verify layer name matches
- Ensure tool diameter < smallest feature

### G-code Missing Moves
- Verify toolpath generation succeeded
- Check z_rough is negative
- Ensure loops array is populated

---

## 10. Quick Reference

### Minimal API Call Sequence
```bash
# 1. DXF → Toolpath (params in URL, file as form data)
curl -X POST "http://localhost:8000/api/blueprint/cam/to-adaptive?tool_d=6&z_rough=-3"   -F "file=@design.dxf" -o plan.json

# 2. Toolpath → G-code (JSON body - use loops from plan.json response)
curl -X POST "http://localhost:8000/api/cam/pocket/adaptive/gcode"   -H "Content-Type: application/json"   -d '{"loops":[{"pts":[[0,0],[100,0],[100,50],[0,50]]}],"tool_d":6,"z_rough":-3,"post_id":"GRBL"}'   -o output.nc
```

### Supported File Types
- **Input:** DXF (R12, R2000)
- **Output:** NC, GCode, TAP (via post-processor)

### API Endpoints Summary
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/cam/blueprint/preflight` | POST | Validate DXF |
| `/api/cam/blueprint/to-adaptive` | POST | DXF → Toolpath |
| `/api/cam/pocket/adaptive/gcode` | POST | Toolpath → G-code |
| `/api/cam/pocket/adaptive/plan_from_dxf` | POST | Direct DXF → Plan |

---

*Document created as part of luthiers-toolbox developer documentation.*
