# CAM Coordinate System Governance

**Date:** 2026-05-07  
**Status:** LOCKED  
**Scope:** All CAM and export modules in luthiers-toolbox

---

## Purpose

This document locks coordinate system assumptions for all CAM-related code. Any module generating toolpaths, geometry, or machine-adjacent output must conform to these standards.

---

## Canonical Coordinate System

### Units

| Concern | Standard |
|---------|----------|
| Linear units | **mm only** |
| Angular units | **radians** (internal), degrees (display) |
| Precision | **3 decimal places** (0.001mm) |

No inch-mode toolpaths. No implicit unit conversion.

### Axis Definitions

| Axis | Positive Direction | Notes |
|------|-------------------|-------|
| X | Right (bass-to-treble for nut slots) | Work coordinate, not machine |
| Y | Away from operator | Slot length direction |
| Z | Up (away from stock) | Spindle axis |

### Z-Zero Convention

| Convention | Definition | Used By |
|------------|------------|---------|
| `top_of_stock` | Z=0 at workpiece surface | Nut slot CAM, fret slot CAM |
| `machine_table` | Z=0 at table surface | NOT USED — requires stock height |

**Rule:** All preview toolpaths use `top_of_stock` Z-zero. Machine-specific Z-zero is a postprocessor concern.

### Origin Convention

| Module | Origin Definition |
|--------|-------------------|
| `nut_slot_cam.py` | `local_nut_left_face` — left edge of nut blank (bass side at high X) |
| `fret_slots_cam.py` | `fretboard_nut_end` — nut end of fretboard |
| `fret_slots_fan_cam.py` | `fretboard_nut_end` — nut end of fretboard |
| `fret_slots_from_ecosphere.py` | Inherits from FretboardEcosphere |

**Rule:** Each operation declares its local origin explicitly in response metadata.

---

## Audit Results (2026-05-07)

### Tier 1 Modules — Deep Audit

#### `nut_slot_cam.py`

```
Location: services/api/app/cam/nut_slot_cam.py
Coordinate system: DOCUMENTED in docstring lines 8-14
  - Origin: left face of nut (bass side at high X)
  - X axis: string-to-string direction along nut
  - Y axis: slot length direction
  - Z-zero: top of stock
  - Units: mm
Status: CONFORMANT
```

#### `nut_slot_router.py`

```
Location: services/api/app/routers/cam/nut_slot_router.py
Coordinate system: Documented in endpoint docstring
Status: CONFORMANT (inherits from nut_slot_cam.py)
```

### Tier 2 Modules — Classification Pass

#### `util/gcode/simulator.py`

```
Location: services/api/app/util/gcode/simulator.py
Units: Supports both mm (G21) and inch (G20) via modal state
Z convention: Not enforced — parses whatever G-code provides
Status: LIBRARY (no coordinate assumptions imposed)
```

#### `util/gcode/types.py`

```
Location: services/api/app/util/gcode/types.py
Units: Default modal state uses mm (units: 1.0)
Status: LIBRARY
```

#### `gcode_consolidated_router.py`

```
Location: services/api/app/routers/gcode_consolidated_router.py
Purpose: Visualization/estimation only
Coordinate system: Passthrough — inherits from input G-code
Status: UTILITY (no governance required)
```

#### `simulation_consolidated_router.py`

```
Location: services/api/app/routers/simulation_consolidated_router.py
Purpose: Preview/metrics only
Coordinate system: Passthrough
Status: UTILITY
```

---

## Coordinate Metadata Requirements

All CAM preview responses MUST include:

```json
{
  "coordinate_system": {
    "origin": "local_nut_left_face",
    "z_zero": "top_of_stock",
    "x_axis": "string_to_string",
    "y_axis": "slot_length"
  },
  "units": "mm"
}
```

This metadata is declarative — it describes the toolpath, not the machine.

---

## Safe Z Semantics

| Parameter | Meaning |
|-----------|---------|
| `safe_z_mm` | Height above stock surface for rapid moves |
| Typical value | 5.0mm |
| Minimum warning | 2.0mm (triggers YELLOW gate) |

**Rule:** Safe Z is relative to `top_of_stock`, not machine Z-zero.

---

## Negative Z Semantics

| Value | Meaning |
|-------|---------|
| Z < 0 | Cutting into stock |
| Z = 0 | At stock surface |
| Z > 0 | Above stock (clearance) |

**Rule:** Cutting moves have negative Z. Rapid/retract moves have positive Z.

---

## Forbidden Patterns

1. **Implicit unit conversion** — No code that assumes input units without checking
2. **Machine-specific origins** — Preview code must not embed machine coordinate offsets
3. **Absolute machine Z** — Preview code must use stock-relative Z-zero
4. **Layer 0 geometry** — DXF output must use named layers only

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_POSTPROCESSOR_BOUNDARY.md` | Postprocessor handles coordinate transforms |
| `CAM_EXPORT_GOVERNANCE_POLICY.md` | Export validation gates |
| `dxf_writer.py` | Coordinate precision enforcement |
| `dxf_compat.py` | Version-aware geometry output |

---

*Governance locked: 2026-05-07*
