# Topology Authority Chain

**Sprint:** MRP-5G  
**Status:** RESEARCH COMPLETE  
**Type:** Architectural Governance

---

## Purpose

Define the explicit authority chain for acoustic topology generation. This model establishes who owns what decisions in the path from approved geometry to CAD solid output.

---

## Authority Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    BOE (Body Outline Engine)                    │
│                   GEOMETRY APPROVAL AUTHORITY                   │
│                                                                 │
│   Owns: Profile coordinates, soundhole position, void shapes   │
│   Status: IMMUTABLE — downstream systems may not modify        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ READ ONLY
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 IBG (Instrument Body Generator)                 │
│                  ADVISORY MORPHOLOGY AUTHORITY                  │
│                                                                 │
│   Owns: Side heights, radii by zone, dimensional hints         │
│   Status: ADVISORY — may be overridden by user/cad_semantics   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ CONSUME (optional)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       cad_semantics                             │
│                 SEMANTIC ENRICHMENT AUTHORITY                   │
│                                                                 │
│   Owns: Body category, thickness hierarchy, continuity targets │
│   Status: EXTENDS geometry context, may NOT override geometry  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ CONSUME
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               Topology Builder (PROPOSED LAYER)                 │
│               TOPOLOGY CONSTRUCTION AUTHORITY                   │
│                                                                 │
│   Owns: Shell construction, loft generation, continuity impl   │
│   Status: RECOMMENDED_PENDING_MRP_5H_VALIDATION                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ TOPOLOGY OUTPUT
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Translator                              │
│                   SERIALIZATION AUTHORITY                       │
│                                                                 │
│   Owns: Format encoding (STEP, DXF, SVG), entity ordering      │
│   Status: CONSUMES topology, serializes to target format       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ IMPLEMENTATION CALL
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAD Kernel (Adapter)                         │
│                  IMPLEMENTATION DEPENDENCY                      │
│                                                                 │
│   Owns: Low-level geometry ops, B-rep construction, export     │
│   Status: HIDDEN behind adapter — not a semantic authority     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Authority Definitions

### BOE: Geometry Approval Authority

**Scope:** All 2D profile geometry that defines the instrument body shape.

**Owns:**
- Outer profile coordinates (x, y)
- Void positions and shapes (soundholes, f-holes)
- Profile closure verification
- Winding direction

**Key Rule:**
```
BOE-approved geometry is IMMUTABLE.
No downstream system may modify, reinterpret, or substitute
coordinates approved by BOE.
```

**Conflict Resolution:** BOE always wins. If downstream system needs different geometry, the change must flow back through BOE approval.

### IBG: Advisory Morphology Authority

**Scope:** Lutherie-derived dimensional hints for body morphology.

**Owns:**
- `side_heights_mm` — depth profile along outline
- `radii_by_zone` — brace-fitting radii
- `dimensions` — bout measurements
- Instrument specification reference

**Key Rule:**
```
IBG data is ADVISORY.
It may be consumed, ignored, or overridden by cad_semantics.
It does not modify BOE geometry.
```

**Conflict Resolution:** User-specified cad_semantics override IBG advisory data.

### cad_semantics: Semantic Enrichment Authority

**Scope:** CAD construction hints that extend geometry context.

**Owns:**
- `body_category` — flat, acoustic, archtop
- Thickness hierarchy (Level 1-3)
- Side profile type (uniform, tapered)
- Continuity targets (G0, G1)
- Plate relationships (flat, radiused)

**Key Rule:**
```
cad_semantics may EXTEND approved geometry context.
It may NOT override, reinterpret, or invent geometry.
```

**Conflict Resolution:** cad_semantics must be consistent with BOE geometry. Inconsistent semantics produce validation warnings.

### Topology Builder: Construction Authority (Proposed)

**Scope:** 3D topology construction from approved 2D geometry + semantics.

**Owns:**
- Shell surface generation
- Loft interpolation between profiles
- Rim closure construction
- Continuity enforcement at junctions
- Topology validation (closed shell, manifold)

**Key Rule:**
```
Topology Builder may CONSTRUCT surfaces that pass through
approved geometry points. It may NOT modify the points themselves.
```

**Status:** RECOMMENDED_PENDING_MRP_5H_VALIDATION

**Conflict Resolution:** Topology builder failures produce BLOCKING errors. No degraded output.

### Translator: Serialization Authority

**Scope:** Format-specific encoding of topology to output files.

**Owns:**
- STEP entity ordering and encoding
- DXF layer structure
- SVG element organization
- Provenance embedding
- Deterministic serialization

**Key Rule:**
```
Translator SERIALIZES topology. It does not construct topology.
```

**Conflict Resolution:** Serialization failures are translator bugs, not geometry issues.

### CAD Kernel: Implementation Dependency

**Scope:** Low-level geometry operations hidden behind adapters.

**Owns:**
- B-rep construction primitives
- NURBS/spline evaluation
- Boolean operations
- Mesh generation (if needed)

**Key Rule:**
```
CAD kernels are implementation dependencies, not semantic authorities.
They must be isolated behind adapters.
```

**Conflict Resolution:** Kernel failures are treated as infrastructure issues. Kernel selection does not affect semantic model.

---

## Authority Conflict Resolution

### Precedence Order

```
1. BOE geometry (highest)
2. cad_semantics
3. IBG advisory
4. Topology builder defaults
5. Translator defaults
6. Kernel defaults (lowest)
```

### Conflict Examples

| Conflict | Resolution |
|----------|------------|
| IBG side_heights differs from cad_semantics.side_depth_mm | cad_semantics wins |
| Topology builder cannot achieve G1 continuity | Fail with BLOCKING error |
| Translator cannot encode topology | Fail with translator error |
| Kernel fails to construct surface | Fail, select different strategy |

---

## Authority Boundaries

### What Each Layer May NOT Do

| Layer | Prohibited Actions |
|-------|-------------------|
| BOE | — (source of truth) |
| IBG | Modify BOE coordinates |
| cad_semantics | Override BOE geometry, invent new geometry |
| Topology Builder | Modify approved coordinates, skip continuity validation |
| Translator | Construct topology, modify topology |
| Kernel | Make semantic decisions, skip adapter isolation |

### Boundary Enforcement

```python
# Example: Topology builder must verify geometry preservation
def build_topology(approved_outline, semantics):
    topology = construct_shell(approved_outline, semantics)
    
    # REQUIRED: Verify approved points are preserved
    for point in approved_outline.points:
        if not topology.contains_point(point, tolerance=0.001):
            raise GeometryMutationError(
                f"Approved point {point} not in topology output"
            )
    
    return topology
```

---

## Future Implementation Notes

### MRP-5H: Topology Builder Prototype

Validate:
- Builder layer separation is practical
- BOE geometry preservation is verifiable
- Continuity targets are achievable

### MRP-5I: Shell Validation

Validate:
- Closed shell verification works
- Manifold topology enforceable
- Failure classification accurate

### MRP-5J: Acoustic STEP Runtime

Validate:
- Full authority chain functions
- Provenance flows through all layers
- Failures traced to correct layer

---

## Related Documents

- `ACOUSTIC_TOPOLOGY_BUILDER_MODEL.md` — Builder layer details
- `ACOUSTIC_TOPOLOGY_RUNTIME_RULES.md` — Runtime constraints
- `ACOUSTIC_CAD_SEMANTIC_RULES.md` — Semantic authority rules
- `CAD_TRANSLATOR_GOVERNANCE_RULES.md` — Translator boundaries
