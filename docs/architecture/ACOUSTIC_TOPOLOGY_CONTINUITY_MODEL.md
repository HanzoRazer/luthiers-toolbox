# Acoustic Topology Continuity Model

**Sprint:** MRP-5E  
**Status:** RESEARCH COMPLETE  
**Type:** Semantic Architecture

---

## Purpose

Define the topological continuity requirements for acoustic instrument body CAD representation. This model establishes how surfaces connect and what continuity level is required at each junction.

---

## Topology Overview

### Acoustic Body Components

```
                    ┌─────────────────┐
                    │       TOP       │
                    │   (soundboard)  │
                    └────────┬────────┘
                             │ G1 continuity
              ┌──────────────┼──────────────┐
              │              │              │
              │         ┌────┴────┐         │
              │         │  SIDE   │         │
              │         │  (rim)  │         │
              │         └────┬────┘         │
              │              │              │
              └──────────────┼──────────────┘
                             │ G1 continuity
                    ┌────────┴────────┐
                    │      BACK       │
                    │    (plate)      │
                    └─────────────────┘
```

---

## Continuity Classifications

### G0: Positional Continuity

**Definition:** Surfaces share common edge points.

**CAD Requirement:** Edges must be coincident (within tolerance).

**Tolerance:** 0.001mm (STEP default)

**Use Cases:**
- Flat-body electric guitars (current MRP-5C)
- Prototype visualization

### G1: Tangent Continuity

**Definition:** Surfaces share common edge AND tangent direction.

**CAD Requirement:** Surface normals align at shared edges.

**Tolerance:** 1° angular deviation maximum

**Use Cases:**
- Acoustic guitar bodies
- Side-to-plate junctions
- Binding ledge transitions

### G2: Curvature Continuity

**Definition:** Surfaces share edge, tangent, AND curvature.

**CAD Requirement:** Second derivative continuous across edge.

**Use Cases:**
- High-end archtop carving
- Smooth visual transitions
- Future acoustic optimization

---

## Junction Types

### Side-to-Top Junction

**Location:** Where rim meets soundboard.

**Physical Reality:**
- Kerfed lining creates transition
- Top overhangs side by binding thickness
- Glue joint creates mechanical bond

**Continuity Requirement:** G1 (tangent)

**CAD Representation:**
```
Option A: Sharp edge (G0)
  - Simple to generate
  - Acceptable for visualization
  - Sufficient for CNC roughing

Option B: Fillet edge (G1)
  - Represents kerfing curve
  - Required for accurate volume
  - Target for acoustic body STEP
```

**Current Status:** G0 implemented (flat-body). G1 is RESEARCH_ONLY.

### Side-to-Back Junction

**Location:** Where rim meets back plate.

**Physical Reality:** Similar to side-to-top, typically with radiused back.

**Continuity Requirement:** G1 (tangent)

**CAD Representation:**
- Must account for back radius
- Edge follows back arch curve
- More complex than flat-top case

**Current Status:** RESEARCH_ONLY

### Side Seam (Two-Piece Rim)

**Location:** Where upper and lower bout rim pieces meet at waist.

**Physical Reality:**
- Glued butt joint or scarf joint
- May have block reinforcement
- Typically at waist narrowest point

**Continuity Requirement:** G0 (positional)

**CAD Representation:**
- Single continuous rim for visualization
- Split rim for assembly planning
- Joint location from IBG radii_by_zone

**Current Status:** Single rim modeled. Split rim is RESEARCH_ONLY.

---

## Shell Continuity Model

### Closed Shell Requirement

For valid STEP MANIFOLD_SOLID_BREP:
- All faces must form CLOSED_SHELL
- No gaps between adjacent faces
- Consistent face normals (outward)

### Current Implementation (Flat-Body)

```
CLOSED_SHELL composed of:
  - Bottom face (profile at z=0)
  - Top face (profile at z=thickness)
  - Side faces (one per profile edge)
```

**Continuity:** G0 everywhere (sharp edges)

### Acoustic Body Target

```
CLOSED_SHELL composed of:
  - Back plate surface (possibly radiused)
  - Top plate surface (possibly arched)
  - Rim surface (tapered depth)
  - Rim-to-top transition (kerfing zone)
  - Rim-to-back transition (kerfing zone)
```

**Continuity Target:** G1 at plate-rim junctions

---

## Chamber Continuity

### Internal Volume

The acoustic chamber is the negative space inside the body shell.

**Representation Options:**

| Option | Description | Complexity |
|--------|-------------|------------|
| Implicit | Defined by shell interior | LOW |
| Explicit | Separate void solid | MEDIUM |
| Parametric | Volume function | HIGH |

**Current Approach:** Implicit (shell thickness creates chamber)

### Bracing Interruptions

Braces interrupt chamber continuity:
- X-brace pattern (steel string)
- Fan brace pattern (classical)
- Ladder brace pattern (parlor)

**Status:** OUT_OF_SCOPE for MRP-5E (assembly semantics)

---

## Surface Type Transitions

### Flat-to-Radiused

**Example:** Flat top meeting radiused back

**Junction:** At rim, where top edge meets back edge

**Continuity Challenge:**
- Top edge is planar curve
- Back edge follows radius arc
- Rim must interpolate between

**Solution Approach:**
- Rim depth varies to match both edges
- Side profile becomes 3D curve
- Requires loft surface generation

### Radiused-to-Radiused

**Example:** Radiused back meeting radiused top (classical style)

**Junction:** Both edges follow radius arcs

**Continuity Challenge:**
- Arcs may have different radii
- Arcs may have different centers
- Rim must smoothly connect

**Status:** RESEARCH_ONLY

---

## Topology Validation Rules

### Rule 1: Shell Closure

All acoustic body STEP must satisfy:
```
∀ edge ∈ body: edge.adjacent_faces.count == 2
```

No free edges allowed.

### Rule 2: Normal Consistency

All face normals must point outward:
```
∀ face ∈ shell: normal(face) · (centroid(face) - body_center) > 0
```

### Rule 3: Manifold Topology

No self-intersection, no degenerate faces:
```
∀ face_pair ∈ shell: intersection(face_pair) ⊆ shared_edges
```

### Rule 4: Continuity Verification

At each junction, verify claimed continuity:
```
G0: edge_gap < 0.001mm
G1: normal_angle < 1°
G2: curvature_delta < tolerance
```

---

## Implementation Roadmap

| Sprint | Capability | Continuity Level |
|--------|------------|------------------|
| MRP-5C | Flat-body STEP | G0 everywhere |
| MRP-5G | Side/rim topology | G0, G1 target |
| MRP-5H | Loft surfaces | G1 at junctions |
| MRP-5I | Acoustic STEP | G1 verified |
| MRP-6+ | Carved tops | G2 where needed |

---

## Authority Boundaries

| Continuity Decision | Authority |
|---------------------|-----------|
| Minimum required level | Governance (this doc) |
| Actual achieved level | CAD Translator (reports) |
| Surface type selection | User input / IBG |
| Junction smoothing | Translator (within rules) |

**Key Rule:** Translator may SMOOTH junctions to meet continuity requirements. It may NOT ALTER approved geometry to do so.

---

## Related Documents

- `ACOUSTIC_BODY_SEMANTIC_MODEL.md`
- `THICKNESS_HIERARCHY_MODEL.md`
- `ACOUSTIC_CAD_SEMANTIC_RULES.md`
- `CAD_TRANSLATOR_GOVERNANCE_RULES.md`
