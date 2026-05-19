# CAM Export Object Model

**Date:** 2026-05-10  
**Status:** ARCHITECTURAL DEFINITION  
**Dev Order:** 6A  
**Scope:** Portable export schema for manufacturing representation

---

## Purpose

This document defines the **Export Object** — the canonical portable manufacturing representation that sits between governed preview and machine-specific postprocessing.

---

## Design Principles

1. **Self-contained** — All information needed to manufacture the part
2. **Machine-agnostic** — No controller-specific syntax
3. **Traceable** — Links to source geometry and validation
4. **Extensible** — Core schema with operation-specific extensions
5. **Versionable** — Schema version for forward compatibility

---

## Export Object Schema

### Top-Level Structure

```json
{
  "schema_version": "1.0.0",
  "export_id": "EXP-...",
  "export_type": "toolpath|geometry|bundle",
  
  "metadata": { ... },
  "geometry": { ... },
  "toolpaths": { ... },
  "tooling": { ... },
  "material": { ... },
  "stock": { ... },
  "validation": { ... },
  "intent": { ... }
}
```

---

### Metadata Block

```json
{
  "metadata": {
    "export_id": "EXP-NUT-20260510-abc123",
    "schema_version": "1.0.0",
    "created_at": "2026-05-10T12:00:00Z",
    "created_by": "user@example.com",
    "source": {
      "preview_id": "nut_slot_preview",
      "preview_hash": "sha256:...",
      "generator_id": "nut_slot_cam",
      "generator_version": "1.0.0"
    },
    "operation_category": "slot_cutting",
    "description": "Nut slot toolpaths for 6-string acoustic"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| export_id | string | Yes | Unique identifier (pattern: `EXP-{type}-{date}-{hash}`) |
| schema_version | string | Yes | Export object schema version |
| created_at | ISO8601 | Yes | Creation timestamp |
| created_by | string | No | User or system identifier |
| source.preview_id | string | Yes | Source preview operation |
| source.preview_hash | string | Yes | SHA256 of source preview |
| source.generator_id | string | Yes | CAM generator identifier |
| operation_category | string | Yes | Operation type category |

---

### Geometry Block

```json
{
  "geometry": {
    "coordinate_system": {
      "origin": "nut_left_face",
      "x_axis": "string_to_string",
      "y_axis": "slot_length",
      "z_axis": "depth_into_stock",
      "z_zero": "top_of_stock",
      "units": "mm",
      "handedness": "right_handed",
      "frame": "local_workpiece"
    },
    "bounds": {
      "x_min": 0.0,
      "x_max": 35.5,
      "y_min": 0.0,
      "y_max": 4.5,
      "z_min": -2.0,
      "z_max": 5.0
    },
    "entities": [
      {
        "type": "slot",
        "id": "slot_0",
        "x_mm": 3.5,
        "y_start_mm": 0.0,
        "y_end_mm": 4.5,
        "width_mm": 0.56,
        "depth_mm": 1.5
      }
    ]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| coordinate_system | object | Yes | Complete coordinate specification |
| coordinate_system.origin | string | Yes | Origin definition |
| coordinate_system.z_zero | string | Yes | Z datum definition |
| coordinate_system.units | string | Yes | Units (always "mm") |
| bounds | object | Yes | Bounding box in workpiece coordinates |
| entities | array | No | Geometric entities (operation-specific) |

---

### Toolpaths Block

```json
{
  "toolpaths": {
    "operations": [
      {
        "operation_id": "slot_0_cut",
        "operation_type": "slot_cut",
        "entity_ref": "slot_0",
        "sequence": 0,
        "moves": [
          {"type": "rapid", "x": 3.5, "y": 0.0, "z": 5.0},
          {"type": "plunge", "x": 3.5, "y": 0.0, "z": -1.5, "f": 100},
          {"type": "linear", "x": 3.5, "y": 4.5, "z": -1.5, "f": 500},
          {"type": "retract", "x": 3.5, "y": 4.5, "z": 5.0}
        ]
      }
    ],
    "statistics": {
      "total_operations": 6,
      "total_moves": 24,
      "rapid_moves": 12,
      "cutting_moves": 12,
      "total_rapid_distance_mm": 120.5,
      "total_cutting_distance_mm": 27.0,
      "estimated_time_s": 45.0
    }
  }
}
```

**Move Types:**

| Type | Description | Required Fields |
|------|-------------|-----------------|
| rapid | G0 equivalent, non-cutting traverse | x, y, z |
| plunge | Z-only cutting move | z, f |
| linear | G1 equivalent, linear cutting | x, y, z, f |
| retract | Z-only retract (non-cutting) | z |
| arc_cw | G2 equivalent, clockwise arc | x, y, i, j, f |
| arc_ccw | G3 equivalent, counter-clockwise arc | x, y, i, j, f |

---

### Tooling Block

```json
{
  "tooling": {
    "tool_id": "nut_slot_saw_056",
    "tool_type": "slot_saw",
    "geometry": {
      "diameter_mm": 0.56,
      "cutting_length_mm": 5.0,
      "shank_diameter_mm": 3.175,
      "overall_length_mm": 38.0,
      "flute_count": 2
    },
    "material": "carbide",
    "coating": "TiAlN",
    "operation_class": ["slot_cutting", "grooving"],
    "notes": "Specific to nut slot cutting"
  }
}
```

See `CAM_TOOL_LIBRARY_STANDARD.md` for complete tool schema.

---

### Material Block

```json
{
  "material": {
    "material_id": "bone_nut_blank",
    "material_class": "bone",
    "properties": {
      "hardness": "medium",
      "machinability": "good"
    },
    "notes": "Standard bone nut blank"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| material_id | string | No | Material identifier |
| material_class | string | No | Material category |
| properties | object | No | Material properties |

---

### Stock Block

```json
{
  "stock": {
    "stock_type": "rectangular",
    "dimensions": {
      "length_mm": 44.0,
      "width_mm": 6.0,
      "thickness_mm": 9.5
    },
    "orientation": {
      "length_axis": "x",
      "width_axis": "y",
      "thickness_axis": "z"
    },
    "fixture": {
      "method": "jig_clamped",
      "notes": "Nut slot cutting jig"
    }
  }
}
```

---

### Validation Block

```json
{
  "validation": {
    "gate_status": "green",
    "preview_gate": "green",
    "export_gate": "green",
    "issues": [],
    "warnings": [],
    "checks_performed": [
      {"check": "tool_diameter_vs_slot_width", "result": "passed"},
      {"check": "depth_vs_stock_thickness", "result": "passed"},
      {"check": "position_bounds", "result": "passed"}
    ],
    "source_preview_hash": "sha256:abc123..."
  }
}
```

---

### Intent Block

```json
{
  "intent": {
    "operation_type": "nut_slot_cutting",
    "depth_strategy": "full_depth_single_pass",
    "finish_requirements": {
      "surface_finish": "functional",
      "tolerance_mm": 0.05
    },
    "notes": "Standard nut slot for wound string"
  }
}
```

The **intent block** preserves manufacturing intent that may not be explicit in the geometry or toolpaths. This enables intelligent postprocessing decisions.

---

## Export Types

### Type: toolpath

Contains toolpaths ready for postprocessing. Full export object with all blocks.

### Type: geometry

Contains only geometry entities (DXF-equivalent). Minimal toolpaths block.

### Type: bundle

Contains both geometry and toolpaths, plus additional artifacts (DXF file, SVG preview).

---

## Extension Points

The export object schema supports operation-specific extensions:

### Slot Cutting Extension

```json
{
  "extensions": {
    "slot_cutting": {
      "string_gauges": [0.012, 0.016, 0.024, 0.032, 0.042, 0.053],
      "slot_spacing_mm": [7.0, 7.0, 7.0, 7.0, 7.0],
      "fret_crown_height_mm": 1.2
    }
  }
}
```

### Drilling Extension

```json
{
  "extensions": {
    "drilling": {
      "peck_depth_mm": 3.0,
      "retract_increment_mm": 0.5,
      "dwell_ms": 100
    }
  }
}
```

### Profiling Extension

```json
{
  "extensions": {
    "profiling": {
      "tab_count": 4,
      "tab_width_mm": 8.0,
      "tab_height_mm": 2.0,
      "climb_milling": true
    }
  }
}
```

---

## Validation Rules

### Required for All Exports

| Rule | Condition |
|------|-----------|
| Schema version | Must be valid semver |
| Export ID | Must follow pattern |
| Coordinate system | All required fields present |
| Units | Must be "mm" |
| Source hash | Must be valid SHA256 |
| Gate status | Must be "green" or "yellow" |

### Required for Toolpath Exports

| Rule | Condition |
|------|-----------|
| Operations present | At least one operation |
| Moves present | At least one move per operation |
| Tool specified | tooling block present |
| Statistics complete | All statistic fields present |

---

## Example: Complete Nut Slot Export Object

```json
{
  "schema_version": "1.0.0",
  "export_id": "EXP-NUT-20260510-abc123",
  "export_type": "toolpath",
  
  "metadata": {
    "export_id": "EXP-NUT-20260510-abc123",
    "schema_version": "1.0.0",
    "created_at": "2026-05-10T12:00:00Z",
    "source": {
      "preview_id": "nut_slot_preview",
      "preview_hash": "sha256:abc123...",
      "generator_id": "nut_slot_cam",
      "generator_version": "1.0.0"
    },
    "operation_category": "slot_cutting"
  },
  
  "geometry": {
    "coordinate_system": {
      "origin": "nut_left_face",
      "x_axis": "string_to_string",
      "y_axis": "slot_length",
      "z_axis": "depth_into_stock",
      "z_zero": "top_of_stock",
      "units": "mm",
      "handedness": "right_handed",
      "frame": "local_workpiece"
    },
    "bounds": {
      "x_min": 0.0, "x_max": 35.5,
      "y_min": 0.0, "y_max": 4.5,
      "z_min": -2.0, "z_max": 5.0
    }
  },
  
  "toolpaths": {
    "operations": [
      {
        "operation_id": "slot_0_cut",
        "operation_type": "slot_cut",
        "sequence": 0,
        "moves": [
          {"type": "rapid", "x": 3.5, "y": 0.0, "z": 5.0},
          {"type": "plunge", "x": 3.5, "y": 0.0, "z": -1.5, "f": 100},
          {"type": "linear", "x": 3.5, "y": 4.5, "z": -1.5, "f": 500},
          {"type": "retract", "x": 3.5, "y": 4.5, "z": 5.0}
        ]
      }
    ],
    "statistics": {
      "total_operations": 6,
      "total_moves": 24,
      "estimated_time_s": 45.0
    }
  },
  
  "tooling": {
    "tool_id": "nut_slot_saw_056",
    "tool_type": "slot_saw",
    "geometry": {
      "diameter_mm": 0.56,
      "cutting_length_mm": 5.0,
      "flute_count": 2
    }
  },
  
  "stock": {
    "stock_type": "rectangular",
    "dimensions": {
      "length_mm": 44.0,
      "width_mm": 6.0,
      "thickness_mm": 9.5
    }
  },
  
  "validation": {
    "gate_status": "green",
    "issues": [],
    "source_preview_hash": "sha256:abc123..."
  },
  
  "intent": {
    "operation_type": "nut_slot_cutting",
    "depth_strategy": "full_depth_single_pass"
  }
}
```

---

## Cross-Reference

| Document | Purpose |
|----------|---------|
| `CAM_GOVERNED_EXPORT_ARCHITECTURE.md` | Architectural context |
| `CAM_TOOL_LIBRARY_STANDARD.md` | Tooling schema |
| `CAM_MACHINE_PROFILE_STANDARD.md` | Machine abstraction |
| `CAM_POSTPROCESSOR_INTERFACE_STANDARD.md` | Consumer interface |

---

*Schema defined: 2026-05-10*
