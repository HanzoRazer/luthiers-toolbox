# CAD Translator Boundary Model

**Date:** 2026-05-14  
**Sprint:** MRP-5A  
**Status:** ARCHITECTURE DEFINITION

---

## Purpose

Defines the canonical boundary architecture for future CAD-grade translators (STEP, IGES, etc.) that consume Export Objects without collapsing the morphology/manufacturing boundary model.

---

## Key Question

> Can STEP translators consume Export Objects directly, or does a governed intermediate CAD semantic layer eventually become necessary?

**Answer:** For simple extrusion bodies (flat-body electric guitars), direct consumption is feasible. For complex morphology (acoustic guitars with variable side heights, arch-tops), an intermediate construction layer is recommended but not required in the translator layer itself.

---

## Architecture Options

### Option A: Direct Translation (Recommended for MVP)

```
Export Object
    │
    └── STEP Translator
            │
            ├── Construct profile from entities
            ├── Derive extrusion from thickness + coordinate_system
            ├── Build BREP faces
            └── Emit STEP AP203
```

**Pros:**
- Simplest architecture
- No new intermediate layer
- Translator owns all construction logic
- Consistent with DXF/SVG pattern

**Cons:**
- Topology construction embedded in translator
- Complex morphology requires per-instrument logic
- Variable side heights need special handling

**Recommended for:** Flat-body electric guitars, simple extrusions

### Option B: CAD Semantic Layer (Future Complex Bodies)

```
Export Object
    │
    └── CAD Semantic Layer (optional)
            │
            ├── Promote side_heights to height field
            ├── Resolve morphology to thickness parameters
            ├── Add face topology hints
            └── Produce CADExportObject
                    │
                    └── STEP Translator
                            │
                            └── Emit STEP AP203
```

**Pros:**
- Separates morphology resolution from serialization
- Multiple CAD translators share semantic layer
- Complex morphology handled once

**Cons:**
- Additional layer to maintain
- Schema extension required
- May over-engineer simple cases

**Recommended for:** Acoustic guitars with variable profiles, arch-tops

### Option C: Dual-Path (Recommended Architecture)

```
Export Object
    │
    ├── Simple Path (flat body)
    │       │
    │       └── STEP Translator (direct)
    │               └── Extrude profile × constant thickness
    │
    └── Complex Path (morphology)
            │
            └── Morphology Resolver
                    │
                    ├── Consume IBG extensions
                    ├── Compute variable heights
                    └── Generate ruled/swept surfaces
                            │
                            └── STEP Translator
```

**Decision Rule:**
- If `extensions.ibg_morphology.side_heights_mm` is present → Complex Path
- If `side_heights_mm` is absent or uniform → Simple Path

---

## Recommended Architecture

### Phase 1: Simple Extrusion (MRP-5C target)

```
BodyExportObject
    │
    ├── geometry.entities[] ─── profile contours
    ├── geometry.coordinate_system.z_axis ─── extrusion direction
    ├── extensions.thickness_mm? ─── constant depth (new field)
    └── intent.depth_strategy ─── "full_thickness"
            │
            ▼
STEP Translator (body_outline_step_ap203)
    │
    ├── Validate closed contour
    ├── Construct wire from points
    ├── Extrude wire × thickness
    ├── Cap top/bottom faces
    ├── Build BREP shell
    └── Emit AP203 STEP file
```

### Phase 2: Variable Height (MRP-5D+ target)

```
BodyExportObject (with IBG morphology)
    │
    ├── geometry.entities[]
    └── extensions.ibg_morphology
            ├── side_heights_mm[] ─── height at each point
            ├── back_radius_mm? ─── arch radius
            └── radii_by_zone? ─── zone curvatures
                    │
                    ▼
Morphology Geometry Builder (internal to translator)
    │
    ├── Pair outline points with heights
    ├── Generate 3D wire (x, y, z) where z = side_height
    ├── Loft/ruled surface between top edge and bottom profile
    ├── Cap ends
    └── Validate watertight
            │
            ▼
STEP Serializer
    │
    └── Emit AP203 STEP file
```

---

## Export Object Schema Extensions (Proposed)

For STEP feasibility, add these optional fields to Export Object:

### Minimal Extension (Phase 1)

```python
class ExportGeometry(BaseModel):
    # ... existing fields ...
    thickness_mm: Optional[float] = None  # Constant body thickness
```

### Morphology Extension (Phase 2)

Already exists in `extensions.ibg_morphology`:
- `side_heights_mm: List[float]`
- `radii_by_zone: Dict[str, float]`

**Decision:** Do not duplicate. Translator reads from IBG extension.

---

## Boundary Rules

### Export Object Layer

- **Owns:** 2D profile geometry, validation, intent, provenance
- **Does NOT own:** 3D topology, solid body, face definitions

### STEP Translator Layer

- **Owns:** Topology construction, BREP generation, STEP serialization
- **May:** Interpret morphology extensions for 3D construction
- **May NOT:** Modify approved 2D geometry (x, y coordinates)
- **May NOT:** Invent morphology not present in Export Object

### Key Invariant

```
CAD translators may CONSTRUCT topology from approved geometry,
but may NOT REINTERPRET approved geometry authority.
```

**Allowed:**
- Extrude approved profile by declared thickness
- Generate faces from approved contours
- Derive edges from face intersections

**Forbidden:**
- Modify profile point coordinates
- Add geometry not derivable from Export Object
- Change winding direction
- Merge or split entities

---

## CAD Translator Categories

| Category | Input | Output | Example |
|----------|-------|--------|---------|
| **Profile Extrusion** | 2D contour + thickness | 3D solid | Flat electric body |
| **Variable Extrusion** | 2D contour + height field | 3D solid | Acoustic sides |
| **Surface Loft** | 2D contours + radii | 3D shell | Arch-top carve |
| **Assembly** | Multiple Export Objects | Multi-body | Neck + body |

### Translator IDs (Proposed)

| ID | Format | Category | Status |
|----|--------|----------|--------|
| `body_outline_step_ap203` | STEP | Profile Extrusion | FUTURE |
| `body_acoustic_step_ap203` | STEP | Variable Extrusion | RESEARCH |
| `body_archtop_step_ap203` | STEP | Surface Loft | COMPLEX |

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Export Object (Current)                                         │
│                                                                 │
│  geometry:                                                      │
│    coordinate_system: {z_axis: "thickness", z_zero: "top_face"} │
│    bounds: {x_min, x_max, y_min, y_max, z_min: 0, z_max: 0}    │
│    entities: [{type: "closed_contour", points: [[x,y]...]}]    │
│                                                                 │
│  extensions:                                                    │
│    ibg_morphology:                                              │
│      side_heights_mm: [h0, h1, h2, ...]  ← KEY MORPHOLOGY      │
│      radii_by_zone: {waist: R1, lower_bout: R2}                │
│                                                                 │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP Translator (Future)                                        │
│                                                                 │
│  1. Read 2D profile from entities                               │
│  2. Check for side_heights_mm                                   │
│     ├── Present: Variable extrusion path                        │
│     └── Absent: Constant extrusion path                         │
│  3. Construct 3D wire (profile with Z values)                   │
│  4. Build BREP topology                                         │
│     ├── Top face (planar, z = max_height)                       │
│     ├── Bottom face (planar, z = 0)                             │
│     └── Side faces (ruled surfaces)                             │
│  5. Validate watertight                                         │
│  6. Emit STEP AP203                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feasibility Assessment

### Flat-Body Electric (Stratocaster, Les Paul, etc.)

```
Morphology: Constant thickness slab
Side heights: Uniform
Extrusion: Simple profile × depth
CAD complexity: LOW
STEP feasibility: HIGH
```

### Acoustic Flat-Top (Dreadnought, OM, etc.)

```
Morphology: Variable side heights per Sevy/Mottola
Side heights: side_heights_mm array
Extrusion: Ruled surface with variable depth
CAD complexity: MODERATE
STEP feasibility: MODERATE (requires ruled surface support)
```

### Arch-Top (Jazz Guitar, Mandolin)

```
Morphology: Carved top, carved back
Side heights: Variable + arch curvatures
Extrusion: Not applicable (sculpted surfaces)
CAD complexity: HIGH
STEP feasibility: COMPLEX (requires surface modeling)
```

### Hollow Body (ES-335, Semi-Hollow)

```
Morphology: Routed chambers + cap
Side heights: Multiple depth regions
Extrusion: Boolean operations
CAD complexity: HIGH
STEP feasibility: COMPLEX (requires CSG or multi-body)
```

---

## Recommendations

### For MRP-5B (Schema Extension)

1. Add `thickness_mm` field to geometry or extensions
2. Formalize `side_heights_mm` as optional geometry field
3. Add `body_type` enum: `flat | variable | carved | hollow`

### For MRP-5C (STEP Prototype)

1. Target `body_outline_step_ap203` translator
2. Support flat-body electric only (constant thickness)
3. Require explicit `thickness_mm` value
4. Fail gracefully if morphology present

### For MRP-5D+ (Complex Bodies)

1. Implement ruled surface generation
2. Consume IBG `side_heights_mm`
3. Validate CAD topology
4. Consider assembly patterns

---

## References

- `docs/governance/CAD_SEMANTIC_READINESS_MATRIX.md` — Readiness analysis
- `docs/governance/CAD_TRANSLATOR_GOVERNANCE_RULES.md` — Governance rules
- `app/export/body_export_bridge.py` — Export Object schema
- `app/instrument_geometry/body/ibg/body_contour_solver.py` — Morphology model
- STEP AP203 (ISO 10303-203) — External reference
