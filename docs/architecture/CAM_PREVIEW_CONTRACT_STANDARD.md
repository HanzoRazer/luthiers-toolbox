# CAM Preview Contract Standard

**Date:** 2026-05-09  
**Status:** ACTIVE STANDARD  
**Scope:** Governed preview response specification  
**Reference Implementation:** `app/cam/nut_slot_cam.py`

---

## Purpose

This document defines the canonical response shape for governed CAM preview endpoints. All preview-capable modules promoted to GOVERNED PREVIEW status must conform to this contract.

---

## Reference Implementation

`nut_slot_cam.py` is the current canonical reference pattern for governed preview contracts.

Key patterns to follow:
- Structured response with explicit fields
- Gate evaluation with GREEN/YELLOW/RED
- Structured issues with severity and field reference
- Coordinate system metadata
- Statistics bundle
- Preview-only status (no machine-ready output)

---

## Canonical Preview Response Shape

```json
{
  "operation": "string",
  "status": "preview",
  "gate": "green | yellow | red",
  "units": "mm",
  "coordinate_system": {
    "origin": "string",
    "x_axis": "string",
    "y_axis": "string",
    "z_axis": "string",
    "z_zero": "string",
    "handedness": "right_handed",
    "frame": "local_part"
  },
  "canonical_toolpath": { },
  "preview_geometry": { },
  "warnings": [ ],
  "errors": [ ],
  "issues": [ ],
  "statistics": { },
  "metadata": { }
}
```

---

## Field Definitions

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `operation` | string | Operation identifier (e.g., "nut_slot_preview", "fret_slot_preview") |
| `status` | string | Always "preview" for governed preview responses |
| `gate` | enum | Gate evaluation result: "green", "yellow", or "red" |
| `units` | string | Always "mm" for governed CAM operations |
| `coordinate_system` | object | Full coordinate system metadata (see below) |
| `canonical_toolpath` | object | Operation-native toolpath data |
| `warnings` | array | Human-readable warning messages |
| `errors` | array | Human-readable error messages |
| `statistics` | object | Operation statistics (see CAM_PREVIEW_METADATA_STANDARD.md) |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `preview_geometry` | object | Simplified visualization geometry (when frontend cannot render canonical_toolpath) |
| `issues` | array | Structured issues with code, severity, message, field (Dev Order 2B) |
| `metadata` | object | Additional metadata (generator version, timestamps, etc.) |
| `tool` | object | Tool information (diameter, type, etc.) |
| `machine_profile` | string | Target machine profile identifier |

### Future-Reserved Fields

| Field | Type | Description |
|-------|------|-------------|
| `export_ready` | boolean | Reserved for GOVERNED EXPORT status |
| `machine_ready` | boolean | Reserved for MACHINE OUTPUT status |
| `rmos_run_id` | string | Reserved for RMOS integration |

---

## Canonical Toolpath vs Preview Geometry

### canonical_toolpath (Required)

Operation-native moves/toolpaths owned by the backend.

Used for:
- Validation
- Export review
- Future promotion to GOVERNED EXPORT
- Gate evaluation

Example (nut slot):
```json
{
  "canonical_toolpath": {
    "slots": [
      {
        "slot_index": 0,
        "string_number": 1,
        "x_mm": 3.5,
        "moves": [
          {"type": "rapid", "x": 3.5, "y": 0, "z": 5.0},
          {"type": "plunge", "x": 3.5, "y": 0, "z": -2.5},
          {"type": "linear", "x": 3.5, "y": 3.0, "z": -2.5},
          {"type": "retract", "x": 3.5, "y": 3.0, "z": 5.0}
        ]
      }
    ]
  }
}
```

### preview_geometry (Optional)

Simplified visualization geometry for frontend rendering.

Required only when frontend cannot easily render canonical_toolpath directly.

Example:
```json
{
  "preview_geometry": {
    "polylines": [
      {"points": [[3.5, 0], [3.5, 3.0]], "type": "cutting"},
      {"points": [[3.5, 3.0], [7.0, 0]], "type": "rapid"}
    ],
    "bounds": {
      "x_min": 0, "x_max": 42,
      "y_min": 0, "y_max": 3.5,
      "z_min": -2.5, "z_max": 5.0
    }
  }
}
```

**Rule:** For simple operations like nut slot CAM, the canonical_toolpath is simple enough to drive preview directly. preview_geometry is only required for complex operations.

---

## Coordinate System Object

Full coordinate system metadata aligned with CAM_COORDINATE_SYSTEM_GOVERNANCE.md.

### Required Fields

```json
{
  "coordinate_system": {
    "units": "mm",
    "origin": "local_nut_left_face",
    "x_axis": "string_to_string",
    "y_axis": "slot_length",
    "z_axis": "depth_into_stock",
    "z_zero": "top_of_stock",
    "handedness": "right_handed",
    "frame": "local_part"
  }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `units` | Yes | Always "mm" |
| `origin` | Yes | Origin point description |
| `x_axis` | Yes | X axis direction |
| `y_axis` | Yes | Y axis direction |
| `z_axis` | Yes | Z axis direction (typically "depth_into_stock") |
| `z_zero` | Yes | Z-zero reference (typically "top_of_stock") |
| `handedness` | Yes | "right_handed" (standard) |
| `frame` | Yes | "local_part" for part-relative coordinates |

**Rule:** Vague coordinate metadata is not allowed in governed preview modules.

---

## Structured Issues (Dev Order 2B)

```json
{
  "issues": [
    {
      "code": "SLOT_DEPTH_EXCEEDS_SAFE_RATIO",
      "severity": "red",
      "message": "Slot depth (2.8mm) > 80% of stock thickness (3.0mm)",
      "field": "slot_depth_mm"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Machine-readable issue code |
| `severity` | enum | "yellow" or "red" |
| `message` | string | Human-readable description |
| `field` | string | Request field that caused the issue (optional) |

---

## Pydantic Model Pattern

Reference implementation from nut_slot_cam.py:

```python
class NutSlotPreviewResponse(BaseModel):
    """Response for nut slot CAM preview."""
    operation: str = "nut_slot_preview"
    status: str = "preview"
    gate: CamGate
    units: str = "mm"
    coordinate_system: CoordinateSystem
    machine_profile: str = "generic_cnc_mm_preview_only"
    tool: ToolMetadata
    toolpaths: List[SlotToolpath]
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    issues: List[CamIssue] = Field(default_factory=list)
    statistics: PreviewStatistics
```

---

## Validation Rules

1. **Gate must reflect issues**: If `errors` is non-empty, gate must be "red"
2. **Coordinate system must be complete**: All required fields present
3. **Units must be mm**: No imperial units in governed preview
4. **Status must be "preview"**: Not "experimental", not "production"
5. **canonical_toolpath must be present**: Even if empty for invalid requests

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_GATE_SEMANTICS_STANDARD.md` | Gate evaluation rules |
| `CAM_PREVIEW_METADATA_STANDARD.md` | Statistics and metadata |
| `CAM_COORDINATE_SYSTEM_GOVERNANCE.md` | Coordinate standards |
| `nut_slot_cam.py` | Reference implementation |

---

*Standard established: 2026-05-09*
