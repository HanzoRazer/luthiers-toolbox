# Adopted CAM Capabilities

## Purpose

This document maps which CAM system capabilities CAM Assist adopts, adapts, or explicitly avoids. CAM Assist is not a CAM replacement—it produces strategy packages that feed into CAM systems.

## Capability Categories

### Category A: Adopted (Strategy-Level)

Capabilities that CAM Assist incorporates into strategy packages.

| Capability | CAM Assist Implementation | Notes |
|------------|---------------------------|-------|
| Geometry definition | DXF export with layers | Standard interchange format |
| Operation sequencing | Strategy JSON with order | Human reviews sequence |
| Tool selection | Recommended tools in strategy | Human confirms availability |
| Speed/feed parameters | Suggested values in strategy | Material-aware recommendations |
| Depth parameters | Specified in strategy | Per-operation definitions |

### Category B: Deferred to CAM

Capabilities that CAM Assist explicitly leaves to downstream CAM systems.

| Capability | Why Deferred | CAM Assist Role |
|------------|--------------|-----------------|
| Toolpath generation | Machine-specific | Provide geometry input |
| Post-processing | Controller-specific | None |
| Simulation | CAM software feature | None |
| Tool library management | Shop-specific | Reference only |
| Material removal optimization | CAM software feature | Provide boundaries |

### Category C: Explicitly Avoided

Capabilities that CAM Assist will not implement.

| Capability | Reason for Avoidance |
|------------|---------------------|
| G-code generation | Violates portability principle |
| Machine control | Outside scope, safety critical |
| Autonomous operation | Violates human authority model |
| Real-time adaptation | Requires machine integration |
| Automatic collision detection | Requires full CAM context |

## DXF Export Conventions

### Layer Naming

CAM Assist DXF files use consistent layer naming:

| Layer Name | Content | Color Code |
|------------|---------|------------|
| `OPERATION_GEOMETRY` | Primary cut geometry | 1 (Red) |
| `REFERENCE_OUTLINE` | Workpiece boundary | 2 (Yellow) |
| `CENTERLINE` | Alignment reference | 3 (Green) |
| `DATUM_POINTS` | Origin and reference points | 4 (Cyan) |
| `ANNOTATIONS` | Human-readable notes | 7 (White) |
| `NO_CUT` | Reference-only geometry | 8 (Gray) |

### Entity Types

| Geometry | DXF Entity | Use Case |
|----------|------------|----------|
| Slot positions | LINE | Fret slots |
| Pocket boundaries | LWPOLYLINE | Routes, cavities |
| Hole positions | CIRCLE | Drilling operations |
| Contour paths | SPLINE | Profile curves |
| Reference points | POINT | Datum locations |

### Coordinate System

All CAM Assist DXF files use:

- **Origin:** Lower-left corner of workpiece OR explicit datum
- **X-axis:** Length direction (along neck)
- **Y-axis:** Width direction (across fretboard)
- **Units:** Inches (mm version planned)
- **Precision:** 6 decimal places

## Strategy JSON Format

### Core Structure

```json
{
  "strategy_version": "1.0",
  "strategy_id": "unique-identifier",
  "created": "ISO-8601 timestamp",
  "operation_type": "fret_slots",
  
  "source": {
    "instrument_spec_id": "reference to input spec",
    "cam_assist_version": "version string"
  },
  
  "geometry": {
    "dxf_file": "geometry.dxf",
    "primary_layer": "FRET_SLOTS",
    "units": "inches",
    "datum": {"x": 0, "y": 0, "description": "nut position"}
  },
  
  "operation": {
    "type": "slot_cut",
    "tool": {
      "type": "slot_cutter",
      "diameter": 0.023,
      "description": "Fret saw or slot cutter"
    },
    "parameters": {
      "depth": 0.060,
      "feed_rate_ipm": 10,
      "spindle_rpm": 10000
    },
    "sequence": "sequential_from_nut"
  },
  
  "positions": [
    {"fret": 1, "distance_from_nut": 1.432},
    {"fret": 2, "distance_from_nut": 2.782}
  ],
  
  "warnings": [],
  "approval_state": "pending"
}
```

### Parameter Recommendations

CAM Assist provides parameter recommendations based on:

| Factor | Influence |
|--------|-----------|
| Material hardness | Speed/feed adjustments |
| Material grain | Direction warnings |
| Tool type | Speed/feed baseline |
| Operation type | Depth/pass recommendations |
| Precision class | Tolerance callouts |

Recommendations are **suggestions**, not commands. The strategy JSON includes:

```json
"parameters": {
  "recommended": {
    "feed_rate_ipm": 10,
    "spindle_rpm": 10000,
    "depth_per_pass": 0.030
  },
  "basis": "hardwood_standard",
  "notes": "Reduce feed 20% for figured maple"
}
```

## Tool Library Integration

### CAM Assist Tool References

CAM Assist does not manage tool libraries. It references tools by:

| Reference Type | Example | Resolution |
|----------------|---------|------------|
| Generic type | "slot_cutter" | Human matches to shop tooling |
| Dimension spec | "0.023 slot cutter" | Human verifies tool matches |
| Named tool | "FRET_SAW_1" | If shop naming is known |

### Tool Specification in Strategy

```json
"tool": {
  "reference_type": "dimension_spec",
  "tool_type": "slot_cutter",
  "required_dimensions": {
    "width": 0.023,
    "min_depth": 0.080
  },
  "optional_properties": {
    "material": "carbide",
    "coating": "TiN"
  },
  "alternatives": [
    "manual fret saw",
    "table saw with fret blade"
  ]
}
```

## Integration Patterns

### Pattern A: CAM Import

```
CAM Assist → DXF + Strategy JSON → CAM Software → Toolpath → Machine
```

CAM software imports DXF geometry. Operator uses strategy JSON for parameters.

### Pattern B: Manual Layout

```
CAM Assist → DXF + Strategy JSON → Print DXF → Manual Layout → Hand Tools
```

DXF printed 1:1 for manual transfer. Strategy JSON guides hand work.

### Pattern C: Hybrid

```
CAM Assist → DXF + Strategy JSON → Partial CAM + Partial Manual
```

Some operations to CAM, others to hand work. Common in lutherie.

## Capability Roadmap

### Currently Implemented

- DXF export for 2D operations
- Strategy JSON for simple operations
- Review checklist generation

### Planned

- SVG export option
- Strategy JSON for compound operations
- Parameter recommendations based on material database

### Under Consideration

- Direct CAM software plugin integration
- Feedback loop from machining results
- Parameter optimization from historical data

### Not Planned

- G-code generation
- Machine control
- Autonomous operation
- Real-time adaptation
