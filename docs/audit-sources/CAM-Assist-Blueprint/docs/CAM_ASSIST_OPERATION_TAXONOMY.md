# CAM Assist Operation Taxonomy

## Taxonomy Purpose

This document defines the universe of lutherie operations that CAM Assist may support. Operations are categorized by:

1. **Geometry type** — 2D, 2.5D, or 3D complexity
2. **Precision class** — Required tolerance
3. **Implementation priority** — When in the roadmap
4. **Strategy complexity** — Simple, compound, or sequenced

## Geometry Types

### Type 2D: Planar Operations

Operations with geometry in a single plane, uniform depth.

| Operation | Geometry | Typical Depth | Priority |
|-----------|----------|---------------|----------|
| Fret slots | Line array | 0.055"-0.080" | **P1** |
| String slots (nut) | Line array | Variable | P2 |
| Tuner holes | Point array | Through | P2 |
| Bridge pin holes | Point array | Through | P2 |
| Position markers | Point array | Variable | P3 |

### Type 2.5D: Profiled Operations

Operations with planar geometry but variable depth.

| Operation | Geometry | Depth Profile | Priority |
|-----------|----------|---------------|----------|
| Pickup routes | Closed polygon | Stepped | P2 |
| Control cavity | Closed polygon | Flat bottom | P2 |
| Neck pocket | Closed polygon | Stepped | P2 |
| Truss rod channel | Open path | Flat bottom | P2 |
| Bridge recess | Closed polygon | Flat bottom | P3 |
| Binding channel | Offset path | Flat bottom | P3 |

### Type 3D: Sculptural Operations

Operations requiring true 3D surfacing.

| Operation | Geometry | Surface Type | Priority |
|-----------|----------|--------------|----------|
| Neck carve | Lofted surface | Freeform | P4 |
| Body contours | Blended surface | Freeform | P4 |
| Heel transition | Blended surface | Freeform | P4 |
| Top/back arching | Domed surface | Parametric | P4 |

## Priority Definitions

| Priority | Definition | CAM Assist Scope |
|----------|------------|------------------|
| **P1** | First implementation slice | Full strategy support |
| P2 | Near-term expansion | Strategy support planned |
| P3 | Medium-term | Under consideration |
| P4 | Future/research | Out of initial scope |

## P1 Operation: Fret Slots

### Operation Definition

**Name:** Fret Slot Strategy  
**Type:** 2D line array  
**Geometry:** Parallel slots perpendicular to centerline  
**Parameters:** Scale length, fret count, slot width, slot depth  

### Input Requirements

```json
{
  "operation": "fret_slots",
  "scale_length_inches": 25.5,
  "fret_count": 22,
  "slot_width_inches": 0.023,
  "slot_depth_inches": 0.060,
  "fretboard_width_nut_inches": 1.687,
  "fretboard_width_last_inches": 2.187,
  "extension_beyond_edge_inches": 0.020
}
```

### Output: Strategy Package

```
fret-slot-strategy/
├── geometry.dxf
│   └── Layer: FRET_SLOTS (22 lines, slot positions)
│   └── Layer: FRETBOARD_OUTLINE (boundary reference)
│   └── Layer: CENTERLINE (alignment reference)
├── strategy.json
│   └── positions[] (calculated fret positions)
│   └── parameters{} (slot width, depth, tool)
│   └── sequence{} (operation order)
├── review-checklist.md
│   └── Pre-cut verification points
│   └── Post-cut verification points
└── approval.json
    └── Approval workflow state
```

### Fret Position Calculation

Standard equal temperament:

```
position_n = scale_length / (2 ^ (n / 12))
distance_from_nut_n = scale_length - position_n
```

For a 25.5" scale:
| Fret | Distance from Nut |
|------|-------------------|
| 1 | 1.432" |
| 2 | 2.782" |
| 3 | 4.054" |
| 12 | 12.750" |
| 22 | 19.287" |

### Strategy Complexity: Simple

Fret slots are a "simple" strategy:
- Single tool operation
- Uniform depth
- Parallel geometry
- No compound sequencing
- Direct position calculation

## P2 Operations: Near-Term

### Pickup Routes

**Type:** 2.5D closed polygon  
**Complexity:** Compound (rough + finish)  
**Key parameters:** Pickup dimensions, mounting tab positions, depth steps

### Neck Pocket

**Type:** 2.5D closed polygon  
**Complexity:** Compound (depth steps for different fit zones)  
**Key parameters:** Pocket dimensions, depth steps, corner radius

### Truss Rod Channel

**Type:** 2.5D open path  
**Complexity:** Simple  
**Key parameters:** Rod dimensions, access point, depth

## Operation Schema

All operations share a common schema structure:

```json
{
  "$schema": "operation.schema.json",
  "operation_id": "string (unique identifier)",
  "operation_type": "enum (fret_slots | pickup_route | neck_pocket | ...)",
  "geometry_type": "enum (2D | 2.5D | 3D)",
  "precision_class": "enum (I | II | III | IV)",
  "strategy_complexity": "enum (simple | compound | sequenced)",
  
  "input": {
    "instrument_spec": {},
    "operation_params": {},
    "material_spec": {},
    "tool_library": {}
  },
  
  "output": {
    "geometry_files": [],
    "strategy_json": {},
    "review_checklist": "",
    "approval_state": {}
  }
}
```

## Strategy Complexity Classes

### Simple

Single-pass operations with uniform parameters.

- One tool
- One depth
- One speed/feed set
- Direct geometry → toolpath mapping

Examples: fret slots, drilling operations, simple profiles

### Compound

Multi-phase operations with different parameters per phase.

- Multiple tools or passes
- Depth stepping
- Rough + finish sequences
- Different speed/feed per phase

Examples: pickup routes (rough + finish), neck pockets (depth steps)

### Sequenced

Operations with explicit ordering dependencies.

- Multiple compound operations
- Order-critical execution
- Reference surfaces between operations
- Intermediate verification points

Examples: complete neck carve, body contour sequence

## Taxonomy Expansion Process

When adding new operations:

1. Classify geometry type (2D, 2.5D, 3D)
2. Assign precision class (I-IV)
3. Determine strategy complexity
4. Define input requirements
5. Specify output format
6. Document verification points
7. Add to priority queue
