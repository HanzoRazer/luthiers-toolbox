# CAM Postprocessor Boundary

**Date:** 2026-05-07  
**Status:** ARCHITECTURAL DEFINITION  
**Scope:** Defines the boundary between preview toolpaths and machine output

---

## Purpose

This document defines where preview output ends and machine-specific output begins. No machine-ready code exists today; this boundary must be established before any is written.

---

## Current System Status

```
Preview-grade CAM    ← CURRENT STATE
NOT machine-grade CAM
```

The system generates:
- Toolpath JSON (moves, coordinates, feed rates)
- Preview visualization (SVG backplots)
- Gate evaluation (GREEN/YELLOW/RED safety checks)
- Statistics (move counts, travel distances, time estimates)

The system does **NOT** generate:
- G-code for any specific machine
- Machine-specific postprocessed output
- Executable machine instructions

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Geometry                                          │
│  ─────────────────                                          │
│  FretboardEcosphere, NeckGeometry, body outlines            │
│  Pure dimensional data — no machining semantics             │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Toolpath                                          │
│  ─────────────────                                          │
│  nut_slot_cam.py, fret_slots_cam.py                         │
│  Local coordinates, stock-relative Z, mm units              │
│  Output: ToolpathMove[] — generic, machine-agnostic         │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Validated Preview                                 │
│  ────────────────────────                                   │
│  Gate evaluation, integrity checks, statistics              │
│  Output: NutSlotPreviewResponse — JSON for frontend         │
│  STATUS: ✓ COMPLETE                                         │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Export Contract                                   │
│  ──────────────────────                                     │
│  Machine profile validation, travel bounds, tool checks     │
│  Output: Validated toolpath + machine binding               │
│  STATUS: ✗ NOT IMPLEMENTED                                  │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: Postprocessor                                     │
│  ──────────────────────                                     │
│  Converts validated toolpath to machine-specific output     │
│  Handles: dialect, coordinate transforms, headers/footers   │
│  Output: G-code string for specific machine/controller      │
│  STATUS: ✗ NOT IMPLEMENTED                                  │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 6: Machine Output                                    │
│  ─────────────────────                                      │
│  File delivery or machine streaming                         │
│  Output: .nc file, serial stream, network protocol          │
│  STATUS: ✗ NOT IMPLEMENTED                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## The Postprocessor Boundary

### Definition

The **postprocessor boundary** is the line between:
- **Above:** Generic toolpath JSON (machine-agnostic)
- **Below:** Machine-specific output (G-code, proprietary formats)

### Location

```
Layer 3 (Validated Preview)
           ↓
    ═══════════════════════════════════════
    ║     POSTPROCESSOR BOUNDARY          ║
    ║     (nothing exists below here)     ║
    ═══════════════════════════════════════
           ↓
Layer 4+ (Export Contract, Postprocessor, Machine Output)
```

---

## Toolpath JSON Format

The canonical intermediate representation (IR) is the toolpath JSON returned by preview endpoints.

### Current Format (nut_slot_cam.py)

```json
{
  "operation": "nut_slot_preview",
  "status": "experimental",
  "gate": "green",
  "units": "mm",
  "coordinate_system": {
    "origin": "local_nut_left_face",
    "z_zero": "top_of_stock",
    "x_axis": "string_to_string",
    "y_axis": "slot_length"
  },
  "machine_profile": "generic_cnc_mm_preview_only",
  "tool": {
    "diameter_mm": 0.5
  },
  "toolpaths": [
    {
      "slot_index": 0,
      "string_number": 1,
      "x_mm": 3.5,
      "slot_width_mm": 0.56,
      "slot_depth_mm": 1.5,
      "moves": [
        {"type": "rapid", "x": 3.5, "y": 0, "z": 5.0},
        {"type": "plunge", "x": 3.5, "y": 0, "z": -1.5},
        {"type": "linear", "x": 3.5, "y": 4.0, "z": -1.5},
        {"type": "retract", "x": 3.5, "y": 4.0, "z": 5.0}
      ]
    }
  ],
  "warnings": [],
  "errors": [],
  "issues": [],
  "statistics": {
    "total_slots": 6,
    "max_depth_mm": 1.5,
    "cutting_move_count": 12,
    "rapid_move_count": 12
  }
}
```

---

## Forbidden: Direct Interpretation as Machine Code

**Toolpath JSON is NOT machine code.**

The following is explicitly forbidden:

```
toolpath JSON → directly interpreted as G-code
toolpath JSON → direct serial streaming to machine
toolpath JSON → automatic execution without postprocessor
```

### Why?

1. **No machine profile** — JSON has no knowledge of machine limits
2. **No coordinate transform** — Local origin ≠ machine origin
3. **No dialect handling** — GRBL vs LinuxCNC vs Mach3 differ
4. **No safety gates** — Machine-specific validation not performed

---

## Future Postprocessor Requirements

When Layer 5 (Postprocessor) is implemented, it must:

### 1. Accept Validated Toolpath + Machine Profile

```python
def postprocess(
    toolpath: ValidatedToolpath,
    machine: MachineProfile,
    options: PostOptions,
) -> GcodeOutput:
    ...
```

### 2. Perform Coordinate Transformation

```
Local origin (e.g., local_nut_left_face)
    ↓
Work coordinate offset (G54/G55/etc.)
    ↓
Machine coordinate system
```

### 3. Emit Dialect-Specific G-code

| Dialect | Header | Rapid | Feed | Spindle |
|---------|--------|-------|------|---------|
| GRBL | `G21 G90` | `G0` | `G1` | `M3 S{rpm}` |
| LinuxCNC | `G21 G90 G64 P0.01` | `G0` | `G1` | `M3 S{rpm}` |
| Mach3 | `G21 G90` | `G0` | `G1` | `M3 S{rpm}` |

### 4. Validate Against Machine Envelope

```
if any(move.x > machine.x_max or move.x < machine.x_min):
    raise EnvelopeViolation(...)
```

### 5. Return Auditable Output

```python
@dataclass
class GcodeOutput:
    gcode: str
    line_count: int
    estimated_time_s: float
    machine_id: str
    validation_gates: List[ValidationGate]
    coordinate_transform_applied: CoordinateTransform
```

---

## Governance Rules

### Rule 1: No G-code Generation Without Postprocessor

Until Layer 5 exists, no endpoint may return G-code.

### Rule 2: Preview JSON Is Not Executable

All preview responses must include:

```json
{
  "status": "experimental",
  "machine_profile": "generic_cnc_mm_preview_only"
}
```

### Rule 3: Postprocessor Must Be Auditable

When implemented, postprocessor must log:
- Input toolpath hash
- Machine profile used
- Coordinate transform applied
- Output G-code hash

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_COORDINATE_SYSTEM_GOVERNANCE.md` | Coordinate standards for Layer 2 |
| `CAM_MACHINE_READINESS_PLAN.md` | Roadmap for Layers 4-6 |
| `CAM_EXPORT_GOVERNANCE_POLICY.md` | Safety gates before machine output |

---

*Boundary defined: 2026-05-07*
