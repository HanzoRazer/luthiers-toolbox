# CAM Dev Order 5E — Drilling Preview Governed Introduction

**Date:** 2026-05-09  
**Author:** Claude (CAM Dev Order 5E)  
**Status:** COMPLETE

---

## Summary

Introduced governed preview for drilling CAM — the first preview endpoint created from scratch under governed preview standards.

**Key achievement:** Validates that governed preview can be introduced to operations without existing preview routes.

---

## What Was Built

### File: `app/cam/routers/drilling/drilling_preview_router.py` (NEW)

Complete governed preview implementation with:

**Governed Preview Types:**
- `CamGate` enum (GREEN/YELLOW/RED)
- `CamIssue` model (code, severity, message, field)
- `CoordinateSystem` model with drilling-specific metadata
- `PreviewMetadata` model with generator provenance

**Gate Evaluation:**
```python
RED conditions:
- Overlapping holes (center_distance < sum_of_radii)
- Depth exceeds stock thickness
- Hole extends past stock edge

YELLOW conditions:
- Near-touching holes (gap < 1mm)
- Hole near stock edge (within min_edge_distance)
- Deep hole (depth > 3x diameter)
- Small diameter (< 1mm)
```

**Coordinate System:**
```python
DRILLING_COORDINATE_SYSTEM = CoordinateSystem(
    units="mm",
    origin="workpiece_origin",
    x_axis="left_to_right",
    y_axis="front_to_back",
    z_axis="tool_depth",
    z_zero="top_of_stock",
    handedness="right_handed",
    frame="local_workpiece",
    notes="X/Y define hole center position on workpiece surface. "
          "Z depth is positive value representing depth into material.",
    coordinate_confidence="documented_from_current_code",
)
```

**Route:** `POST /api/cam/drilling/preview`

### File: `app/cam/routers/drilling/drilling_consolidated_router.py` (MODIFIED)

Added preview router mounting:
```python
from .drilling_preview_router import router as preview_router
router.include_router(preview_router)
```

### File: `tests/cam/test_drilling_preview_normalization.py` (NEW)

40 tests covering:
- All governed preview fields
- Gate semantics (GREEN/YELLOW/RED conditions)
- Statistics normalization
- Preview geometry format
- Input validation
- No RMOS persistence
- Hole label preservation

---

## Request/Response Shape

### Request
```json
{
  "holes": [
    {"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 3.0, "depth_mm": 8.0, "label": "string_1"}
  ],
  "stock_thickness_mm": 20.0,
  "stock_width_mm": 100.0,
  "stock_height_mm": 50.0,
  "min_edge_distance_mm": 3.0
}
```

### Response
```json
{
  "operation": "drilling_preview",
  "status": "preview",
  "gate": "green",
  "units": "mm",
  "coordinate_system": { ... },
  "canonical_toolpath": {
    "holes": [ ... ],
    "hole_count": 1
  },
  "preview_geometry": {
    "holes": [{"x": 10.0, "y": 10.0, "diameter_mm": 3.0, "radius_mm": 1.5}],
    "stock_bounds": {"width_mm": 100.0, "height_mm": 50.0, "thickness_mm": 20.0}
  },
  "warnings": [],
  "errors": [],
  "issues": [],
  "statistics": {
    "operation_count": 1,
    "move_count": 3,
    "hole_count": 1,
    "min_diameter_mm": 3.0,
    "max_diameter_mm": 3.0,
    ...
  },
  "metadata": {
    "generator_id": "drilling_preview",
    "preview_only": true,
    "machine_ready": false,
    "risk_class": "A",
    "generated_at": "2026-05-09T..."
  }
}
```

---

## Gate Semantics

| Condition | Gate | Code |
|-----------|------|------|
| Overlapping holes | RED | OVERLAPPING_HOLES |
| Depth >= stock thickness | RED | DEPTH_EXCEEDS_STOCK |
| Hole past stock edge | RED | OUT_OF_BOUNDS_X/Y |
| Near-touching holes (gap < 1mm) | YELLOW | NEAR_TOUCHING_HOLES |
| Hole near edge | YELLOW | NEAR_EDGE_X/Y |
| Deep hole (depth > 3x diameter) | YELLOW | DEEP_HOLE |
| Small diameter (< 1mm) | YELLOW | SMALL_DIAMETER |

---

## What Was NOT Built

Per 5E guardrails:
1. **No G-code generation** — Preview only
2. **No RMOS persistence** — No run_id, no artifact storage
3. **No pattern generation** — Raw holes array only
4. **No peck-cycle execution** — Preview warns about deep holes but doesn't generate peck cycles

---

## Relationship to Existing Drilling Routes

| Route | Purpose | 5E Scope |
|-------|---------|----------|
| `/drilling/gcode` | Modal drilling G-code (G81/G83) | Unchanged |
| `/drilling/info` | Modal drilling metadata | Unchanged |
| `/drilling/pattern/gcode` | Pattern-based drilling G-code | Unchanged |
| `/drilling/pattern/info` | Pattern drilling metadata | Unchanged |
| `/drilling/preview` | **NEW** Governed preview | **5E** |

The preview route complements existing routes by providing validation before G-code generation.

---

## Test Results

```
tests/cam/test_drilling_preview_normalization.py: 40 passed
Coverage: 21.99%
```

---

## Strategic Outcome

After 5E:
- The governed preview pipeline now covers drilling operations
- First "greenfield" governed preview validates the pattern for future CAM operations
- Gate semantics specific to drilling (overlap, depth, edge proximity) established

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_5C_NORMALIZATION_NOTES.md` | Base normalization pattern |
| `CAM_5D_FAN_FRET_NORMALIZATION_NOTES.md` | Inheritance pattern |
| `CAM_PREVIEW_CONTRACT_STANDARD.md` | Response shape spec |
| `CAM_GATE_SEMANTICS_STANDARD.md` | Gate derivation rules |
| `test_drilling_preview_normalization.py` | Test coverage |

---

*5E normalization complete: 2026-05-09*
