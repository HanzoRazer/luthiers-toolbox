# Acoustic Body Semantic Model

**Sprint:** MRP-5E  
**Status:** RESEARCH COMPLETE  
**Type:** Semantic Architecture

---

## Purpose

Define the semantic model for representing acoustic instrument body topology within the MRP spine. This model establishes vocabulary and concepts for future acoustic CAD translation without implementing runtime generation.

---

## Current State

### Flat-Body Semantics (MRP-5C)

```
Export Object
→ cad_semantics.uniform_thickness_mm
→ STEP AP203 extrusion
```

**Supported:** Single closed 2D profile extruded to uniform depth.

### IBG Morphology Data (Current)

From `IBGMorphologyExtension`:

| Field | Type | Description |
|-------|------|-------------|
| `side_heights_mm` | `List[float]` | Side depth at profile points |
| `radii_by_zone` | `Dict[str, float]` | Zone-based radii for brace fitting |
| `dimensions` | `Dict[str, float]` | lower_bout, upper_bout, waist, body_length |

From `INSTRUMENT_SPECS` constraints:

| Field | Type | Description |
|-------|------|-------------|
| `back_radius_mm` | `float` | Back arch radius (7620mm = 25ft standard) |
| `butt_depth_mm` | `float` | Depth at butt (121mm dreadnought) |
| `shoulder_depth_mm` | `float` | Depth at shoulder (105mm dreadnought) |
| `top_thickness_mm` | `float` | Top plate thickness (2.8mm) |
| `back_thickness_mm` | `float` | Back plate thickness (2.5mm) |

**Status:** CURRENT_IBG_ADVISORY_DATA

---

## Acoustic Semantic Inventory

### SCHEMA_READY (Can be schema fields now)

| Concept | Type | Source | Notes |
|---------|------|--------|-------|
| `side_depth_profile` | `List[float]` | IBG | Already exists as side_heights_mm |
| `butt_depth_mm` | `float` | IBG | Depth at tail block |
| `shoulder_depth_mm` | `float` | IBG | Depth at neck joint |
| `top_thickness_mm` | `float` | IBG | Top plate nominal thickness |
| `back_thickness_mm` | `float` | IBG | Back plate nominal thickness |
| `back_radius_mm` | `float` | IBG | Back arch radius |
| `body_type` | `enum` | cad_semantics | flat_body, acoustic, archtop |

### DERIVABLE (Can be computed from existing data)

| Concept | Derivation | Complexity |
|---------|------------|------------|
| Side taper profile | Interpolate butt_depth → shoulder_depth | LOW |
| Approximate side area | profile perimeter × average depth | LOW |
| Chamber volume estimate | outline area × average depth | MEDIUM |
| Rim centerline curve | offset from outline by side thickness | MEDIUM |

### REQUIRES_USER_INPUT

| Concept | Why User Input | Fallback |
|---------|---------------|----------|
| Top arch height | Design decision | Flat (0mm) |
| Back arch height | Design decision | Derive from back_radius |
| Side thickness | Material choice | Default 2.0mm |
| Kerfing/lining presence | Construction style | Assume kerfed |

### RESEARCH_ONLY

| Concept | Barrier | Target Sprint |
|---------|---------|---------------|
| Longitudinal arch curve | Requires NURBS | MRP-5H+ |
| Transverse arch profiles | Requires loft surfaces | MRP-5I+ |
| Tap-tuned thickness maps | Requires acoustic feedback | MRP-6+ |
| Fan bracing topology | Assembly semantics | MRP-5G |

### OUT_OF_SCOPE

| Concept | Reason |
|---------|--------|
| Sound post position | Violin family only |
| F-hole carving | Archtop-specific, complex topology |
| Resonator cone | Specialized instrument |
| Multi-piece backs | Assembly semantics |

---

## Side/Rim Semantic Model

### Concept: Side Profile

The side (rim) of an acoustic guitar varies in depth from butt to shoulder.

```
Depth Profile:
  Butt (tail) → Waist → Shoulder (neck)
  121mm      → 115mm → 105mm  (typical dreadnought)
```

### Semantic Fields

```python
class AcousticSideSemantics:
    """Side/rim semantic descriptors."""
    
    # Profile type
    side_profile_type: Literal["constant", "tapered", "custom"] = "tapered"
    
    # Key depth points (mm)
    butt_depth_mm: float          # Depth at tail block
    waist_depth_mm: Optional[float]  # Depth at waist (interpolated if None)
    shoulder_depth_mm: float      # Depth at neck block
    
    # Per-point depths (from IBG)
    side_depths_at_profile: Optional[List[float]] = None
    
    # Material
    side_thickness_mm: float = 2.0  # Side bending stock thickness
    
    # Construction
    kerfing_style: Literal["kerfed", "solid", "none"] = "kerfed"
```

### Authority Boundary

| Data | Authority | CAD Translator Role |
|------|-----------|---------------------|
| Profile outline (x, y) | BOE/Export Object | READ ONLY |
| Depth at profile points | IBG advisory | CONSUME |
| Side thickness | User input / default | CONSUME |
| Rim centerline | COMPUTED | DERIVE from profile + thickness |

---

## Top/Back Semantic Model

### Concept: Plate Surfaces

Acoustic bodies have distinct top and back surfaces:

- **Top (soundboard):** Primary acoustic radiator, typically flat or slightly arched
- **Back:** Structural, may be flat, radiused, or arched

### Surface Classifications

| Classification | Description | Topology |
|----------------|-------------|----------|
| `flat` | No curvature | Plane |
| `radiused` | Single-radius dome | Spherical cap |
| `arched` | Carved arch (archtop) | Complex surface |
| `compound` | Multi-radius (classical) | Compound curves |

### Semantic Fields

```python
class AcousticPlateSemantics:
    """Top/back plate semantic descriptors."""
    
    # Surface type
    top_surface_type: Literal["flat", "radiused", "arched"] = "flat"
    back_surface_type: Literal["flat", "radiused", "arched"] = "radiused"
    
    # Arch parameters (if applicable)
    top_arch_height_mm: Optional[float] = None  # Peak height from baseline
    back_arch_height_mm: Optional[float] = None
    back_radius_mm: Optional[float] = None  # Spherical radius
    
    # Thickness
    top_thickness_mm: float = 2.8
    back_thickness_mm: float = 2.5
    
    # For future regional thickness
    top_graduation_map: Optional[Dict[str, float]] = None  # zone → thickness
    back_graduation_map: Optional[Dict[str, float]] = None
```

### Authority Boundary

| Data | Authority | CAD Translator Role |
|------|-----------|---------------------|
| Outline shape | BOE | READ ONLY |
| Surface type | User input | CONSUME |
| Arch parameters | User input / IBG | CONSUME |
| Plate thickness | User input / IBG | CONSUME |
| Graduation maps | User input | CONSUME (future) |

---

## Thickness Hierarchy

See: `THICKNESS_HIERARCHY_MODEL.md`

| Level | Description | Schema Fields |
|-------|-------------|---------------|
| 1 | Uniform | `uniform_thickness_mm` |
| 2 | Component | `top_thickness_mm`, `back_thickness_mm`, `side_depth_mm` |
| 3 | Zonal | `thickness_by_zone: Dict[str, float]` |
| 4 | Continuous | `thickness_field: SurfaceField` (RESEARCH_ONLY) |

---

## Acoustic cad_semantics Extension

Proposed extension to existing `CadSemantics`:

```python
class AcousticCadSemantics(BaseModel):
    """Acoustic body CAD semantic extension."""
    
    # Existing flat-body fields
    cad_intent: Literal["flat_body", "acoustic_body", "archtop_body"]
    
    # Acoustic-specific
    acoustic_type: Optional[Literal["flat_top", "arched_top", "hollow_electric"]] = None
    
    # Side semantics
    side_profile_type: Optional[Literal["constant", "tapered"]] = None
    butt_depth_mm: Optional[float] = None
    shoulder_depth_mm: Optional[float] = None
    
    # Plate semantics
    top_surface_type: Optional[Literal["flat", "radiused", "arched"]] = None
    back_surface_type: Optional[Literal["flat", "radiused"]] = None
    back_radius_mm: Optional[float] = None
    
    # Thickness (Level 2)
    top_thickness_mm: Optional[float] = None
    back_thickness_mm: Optional[float] = None
```

**Status:** PROPOSED (not implemented in MRP-5E)

---

## Relationship to IBG

### IBG as Data Source

```
IBG Morphology Extension
  → side_heights_mm
  → dimensions
  → radii_by_zone

  ↓ (consumed by)

Acoustic cad_semantics
  → butt_depth_mm (from constraints)
  → shoulder_depth_mm (from constraints)
  → back_radius_mm (from constraints)
```

### Authority Model

```
IBG = Advisory morphology authority (may provide hints)
BOE = Geometry approval authority (owns outline)
cad_semantics = CAD construction hints (for translator use)
CAD Translator = Topology construction (from approved data only)
```

**Key Rule:** cad_semantics may EXTEND context from IBG.  
It may NOT OVERRIDE geometry approved by BOE.

---

## Future Work

| Sprint | Capability |
|--------|------------|
| MRP-5F | Acoustic semantic extension prototype |
| MRP-5G | Side/rim topology prototype |
| MRP-5H | Loft/surface research |
| MRP-5I | Acoustic STEP prototype |
| MRP-5J | Carved-top topology governance |

---

## Related Documents

- `ACOUSTIC_TOPOLOGY_CONTINUITY_MODEL.md`
- `ACOUSTIC_CAD_SEMANTIC_RULES.md`
- `ACOUSTIC_CAD_READINESS_MATRIX.md`
- `THICKNESS_HIERARCHY_MODEL.md`
- `CAD_TRANSLATOR_GOVERNANCE_RULES.md`
