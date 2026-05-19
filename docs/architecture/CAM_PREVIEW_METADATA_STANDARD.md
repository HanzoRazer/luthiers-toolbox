# CAM Preview Metadata Standard

**Date:** 2026-05-09  
**Status:** ACTIVE STANDARD  
**Scope:** Required metadata and statistics fields  
**Reference Implementation:** `app/cam/nut_slot_cam.py`

---

## Purpose

This document defines the required and optional metadata fields for governed CAM preview responses.

---

## Statistics Structure

### Required Core Statistics

Every governed preview response must include these statistics:

```json
{
  "statistics": {
    "operation_count": 6,
    "move_count": 24,
    "warning_count": 0,
    "error_count": 0
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `operation_count` | integer | Number of discrete operations (slots, holes, passes) |
| `move_count` | integer | Total number of toolpath moves |
| `warning_count` | integer | Number of YELLOW issues |
| `error_count` | integer | Number of RED issues |

### Recommended Optional Statistics

Include when applicable and reliable:

```json
{
  "statistics": {
    "operation_count": 6,
    "move_count": 24,
    "warning_count": 0,
    "error_count": 0,
    "cutting_move_count": 12,
    "rapid_move_count": 12,
    "max_depth_mm": 2.5,
    "min_spacing_mm": 5.2,
    "max_spacing_mm": 7.8,
    "bounds": {
      "x_min": 3.5,
      "x_max": 38.5,
      "y_min": 0.0,
      "y_max": 3.0,
      "z_min": -2.5,
      "z_max": 5.0
    },
    "estimated_time_s": null
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `cutting_move_count` | integer | Number of G1/G2/G3 moves |
| `rapid_move_count` | integer | Number of G0 moves |
| `max_depth_mm` | float | Deepest Z coordinate reached |
| `min_spacing_mm` | float | Minimum spacing between features |
| `max_spacing_mm` | float | Maximum spacing between features |
| `bounds` | object | Bounding box of all moves |
| `estimated_time_s` | float \| null | Estimated cycle time |

### Estimated Time Rule

**Do not require fake precision.**

If time estimation is not reliable, use `null`:

```json
{
  "estimated_time_s": null
}
```

Do not provide estimates based on assumptions not documented in the operation.

---

## Metadata Object

### Standard Metadata Fields

```json
{
  "metadata": {
    "generator_id": "nut_slot_cam",
    "generator_version": "1.2.0",
    "preview_only": true,
    "machine_ready": false,
    "risk_class": "A",
    "generated_at": "2026-05-09T14:32:00Z"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `generator_id` | string | Module/function identifier |
| `generator_version` | string | Semantic version (optional) |
| `preview_only` | boolean | Always `true` for governed preview |
| `machine_ready` | boolean | Always `false` for governed preview |
| `risk_class` | string | Risk classification (A/B/C) from governance |
| `generated_at` | string | ISO 8601 timestamp |

### Risk Class Definitions

| Class | Description |
|-------|-------------|
| A | Visualization only — not machine-adjacent |
| B | Geometry export — can be imported to external CAM |
| C | Machine instructions — directly executable |

Governed preview is typically Class A or B, never Class C.

---

## Tool Metadata

When tool information is relevant:

```json
{
  "tool": {
    "diameter_mm": 0.5,
    "type": "endmill",
    "flute_count": 2,
    "flute_length_mm": 10.0
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `diameter_mm` | float | Yes | Tool diameter |
| `type` | string | No | Tool type (endmill, ballnose, vbit, etc.) |
| `flute_count` | integer | No | Number of flutes |
| `flute_length_mm` | float | No | Cutting length |

---

## Machine Profile Metadata

For governed preview, use a generic placeholder:

```json
{
  "machine_profile": "generic_cnc_mm_preview_only"
}
```

Machine-specific profiles are not used until GOVERNED EXPORT status.

---

## Reference Implementation (nut_slot_cam.py)

```python
class PreviewStatistics(BaseModel):
    """Preview statistics."""
    total_slots: int
    max_depth_mm: float
    min_adjacent_spacing_mm: Optional[float] = None
    max_adjacent_spacing_mm: Optional[float] = None
    cutting_move_count: int = 0
    rapid_move_count: int = 0
    estimated_time_s: Optional[float] = None


class ToolMetadata(BaseModel):
    """Tool information."""
    diameter_mm: float
```

---

## Operation-Specific Statistics

Different operations track different statistics. Map operation-specific fields to standard fields:

| Operation | operation_count | Specific Fields |
|-----------|-----------------|-----------------|
| Nut slot | total_slots | min/max_adjacent_spacing_mm |
| Fret slot | fret_count | perpendicular_fret_index |
| Drilling | hole_count | total_depth_mm, peck_count |
| Profiling | pass_count | perimeter_length_mm |
| V-carve | path_count | max_carve_width_mm |

---

## Validation Rules

1. **Core statistics required**: operation_count, move_count, warning_count, error_count
2. **Null over fake**: Use null for unreliable values
3. **Bounds when available**: Include bounds if toolpath is generated
4. **preview_only always true**: Until GOVERNED EXPORT

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_PREVIEW_CONTRACT_STANDARD.md` | Response shape |
| `CAM_EXPORT_GOVERNANCE_POLICY.md` | Risk classification |
| `nut_slot_cam.py` | Reference implementation |

---

*Standard established: 2026-05-09*
