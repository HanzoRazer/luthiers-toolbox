# DXF to G-code Workflow Guide

**Version:** 1.1.0
**Date:** 2026-01-14
**Status:** 95% Complete - API Working, UI Needs Enablement

---

## Executive Summary

The luthiers-toolbox provides a complete pipeline to convert DXF files to CNC-ready G-code. The backend API is fully functional; the frontend UI has some disabled buttons that need enabling.

**Golden Path (API):**

    DXF File -> /api/cam/pocket/adaptive/plan_from_dxf -> response.request.loops -> /api/cam/pocket/adaptive/gcode -> .nc File

**Required fields:**
- /plan_from_dxf: file (form), tool_d (form)
- /gcode: loops (JSON), tool_d (JSON)

---

## 1. Golden Path: Two-Step API (Recommended)

This is the **canonical workflow** for MVP. Use plan_from_dxf to extract loops, then /gcode to generate output.

### Step 1: Generate Plan from DXF

    curl -X POST "http://localhost:8000/api/cam/pocket/adaptive/plan_from_dxf" \
      -F "file=@your_design.dxf" \
      -F "tool_d=6.0" \
      -F "stepover=0.4" \
      -F "z_rough=-3.0" \
      -F "feed_xy=1200" \
      -F "safe_z=5.0" \
      -o plan.json

**Response (plan.json):**

    {
      "request": {
        "loops": [{"pts": [[0,0], [100,0], [100,50], [0,50]]}],
        "tool_d": 6.0,
        "stepover": 0.4,
        "z_rough": -3.0
      },
      "plan": {
        "moves": [...],
        "stats": {"move_count": 23}
      }
    }

### Step 2: Generate G-code

Extract loops from response.request.loops and pass to /gcode:

    curl -X POST "http://localhost:8000/api/cam/pocket/adaptive/gcode" \
      -H "Content-Type: application/json" \
      -d '{"loops":[{"pts":[[0,0],[100,0],[100,50],[0,50]]}],"tool_d":6,"z_rough":-3,"post_id":"GRBL"}' \
      -o output.nc

**Output (output.nc):**

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

---

## 2. Optional: DXF Validation (Preflight)

Before processing, you can validate your DXF file:

    curl -X POST "http://localhost:8000/api/cam/blueprint/preflight" \
      -F "file=@your_design.dxf" \
      -F "layer_name=GEOMETRY"

---

## 3. Python Script: Complete Pipeline

See the Python script example in the repository for automated DXF to G-code conversion using the plan_from_dxf endpoint.

Key points:
- Call /api/cam/pocket/adaptive/plan_from_dxf with DXF file
- Extract loops from response["request"]["loops"]
- Pass loops to /api/cam/pocket/adaptive/gcode

---

## 4. DXF File Requirements

### Supported Format
- **DXF Version:** R12 or R2000 (AutoCAD 2000)
- **Encoding:** ASCII or binary

### Required Structure
- Layer: "GEOMETRY" (default, configurable)
- LWPOLYLINE entities with is_closed = True
- Minimum 3 points per loop
- Clockwise winding for outer boundary

### Loop Classification
- **First loop (largest area):** Outer boundary - material to remove
- **Subsequent loops:** Islands - keepout zones (not machined)

---

## 5. CAM Parameters Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| tool_d | float | 6.0 | Tool diameter in mm |
| stepover | float | 0.45 | Fraction of tool diameter (0.1-0.95) |
| stepdown | float | 1.5 | Depth per pass in mm |
| strategy | string | Spiral | Spiral (continuous) or Lanes (back-forth) |
| feed_xy | float | 1200 | XY cutting feed rate (mm/min) |
| feed_z | float | 300 | Z plunge feed rate (mm/min) |
| safe_z | float | 5.0 | Safe retract height (mm) |
| z_rough | float | -3.0 | Total cutting depth (mm, negative) |

---

## 6. Post-Processor Profiles

All post-processors include automatic spindle control (M3 S18000 on, M5 off).

| Post ID | Machine Type | Spindle | End Code |
|---------|--------------|---------|----------|
| GRBL | Hobby CNC, 3018 | M3 S18000 | M30 |
| Mach4 | Mach4 controllers | M3 S18000 | M30 |
| LinuxCNC | LinuxCNC/EMC2 | M3 S18000 | M2 |
| PathPilot | Tormach machines | M3 S18000 | M30 |
| MASSO | MASSO controllers | M3 S18000 | M30 |

### G-code Structure

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

### Spindle Speed

Default: **18000 RPM** (typical wood router speed). The spindle speed is
currently fixed in the post-processor profile.

---

## 7. Error Handling

### Common DXF Errors

| Error | Cause | Solution |
|-------|-------|----------|
| No closed paths found | Open polylines | Close all paths in CAD software |
| No LWPOLYLINE entities | Wrong entity type | Export as LWPOLYLINE, not LINE |
| Layer not found | Wrong layer name | Use layer_name=0 for default layer |

---

## 8. Frontend UI Status

The backend API is **fully functional**, but some frontend buttons are disabled:

| Component | Location | Status |
|-----------|----------|--------|
| BlueprintLab.vue | Phase 1-2 UI | OK |
| Send to CAM button | BlueprintLab.vue:232 | Disabled |
| PipelineLab.vue | Phase 3 UI | Partial |

---

## 9. Troubleshooting

### API Not Responding

    curl http://localhost:8000/health

### Toolpath Empty
- Check DXF has closed LWPOLYLINE entities
- Verify layer name matches
- Ensure tool diameter < smallest feature

---

## 10. Quick Reference

### Golden Path (Recommended)

    # 1. DXF -> Plan (extracts loops into response.request.loops)
    curl -X POST "http://localhost:8000/api/cam/pocket/adaptive/plan_from_dxf" \
      -F "file=@design.dxf" \
      -F "tool_d=6" \
      -o plan.json

    # 2. Plan -> G-code (use loops from plan.json)
    curl -X POST "http://localhost:8000/api/cam/pocket/adaptive/gcode" \
      -H "Content-Type: application/json" \
      -d '{"loops":[{"pts":[[0,0],[100,0],[100,50],[0,50]]}],"tool_d":6,"z_rough":-3,"post_id":"GRBL"}' \
      -o output.nc

### API Endpoints Summary

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| /api/cam/pocket/adaptive/plan_from_dxf | POST | DXF -> Plan (Golden Path) | Recommended |
| /api/cam/pocket/adaptive/gcode | POST | Plan -> G-code | Required |
| /api/cam/blueprint/preflight | POST | Validate DXF | Optional |
| /api/blueprint/cam/to-adaptive | POST | Legacy DXF -> Toolpath | Advanced |

---

*Document created as part of luthiers-toolbox developer documentation.*
