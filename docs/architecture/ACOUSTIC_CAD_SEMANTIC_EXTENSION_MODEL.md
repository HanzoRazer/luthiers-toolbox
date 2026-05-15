# Acoustic CAD Semantic Extension Model

**Sprint:** MRP-5F  
**Status:** IMPLEMENTED  
**Type:** Schema Architecture

---

## Purpose

Document the implemented acoustic semantic extensions for Export Objects. This model enables future acoustic CAD translators while preserving authority boundaries and backward compatibility.

---

## Schema Structure

### Location

```
services/api/app/export/cad_semantics.py
```

### Class Hierarchy

```
CadSemantics
├── schema_version: str
├── body_category: BodyCategory (enum)
├── flat_body: Optional[FlatBodySemantics]
├── acoustic: Optional[AcousticSemantics]
└── uniform_thickness_mm: Optional[float] (legacy)

FlatBodySemantics
├── uniform_thickness_mm: float
├── extrusion_direction: str
└── extrusion_origin: str

AcousticSemantics
├── thickness: Optional[ThicknessSemantics]
├── side_profile: Optional[SideProfileSemantics]
├── rim: Optional[RimSemantics]
├── plate_relationship: Optional[PlateRelationshipSemantics]
└── use_ibg_side_heights: bool

ThicknessSemantics (Level 2)
├── top_thickness_mm: Optional[float]
├── back_thickness_mm: Optional[float]
└── side_depth_mm: Optional[float]

SideProfileSemantics
├── type: SideProfileType (enum)
├── taper_axis: str
├── max_depth_mm: Optional[float]
└── min_depth_mm: Optional[float]

RimSemantics
├── continuity_target: ContinuityTarget (enum)
└── closure_type: ClosureType (enum)

PlateRelationshipSemantics
├── top_type: PlateType (enum)
├── back_type: PlateType (enum)
└── back_radius_mm: Optional[float]
```

---

## Enums

### BodyCategory

| Value | Description | Runtime Support |
|-------|-------------|-----------------|
| `flat_body` | Solid electric guitars | SUPPORTED |
| `acoustic_flat_top` | Steel-string, classical | SEMANTIC_ONLY |
| `acoustic_arched_top` | Arched soundboard | SEMANTIC_ONLY |
| `hollow_electric` | Semi-hollow | SEMANTIC_ONLY |
| `archtop` | Jazz archtop | SEMANTIC_ONLY |
| `resonator` | Resonator guitars | UNSUPPORTED |
| `unknown` | Fallback | UNSUPPORTED |

### SideProfileType

| Value | Description |
|-------|-------------|
| `uniform` | Constant depth |
| `tapered` | Depth varies tail-to-neck |

### ContinuityTarget

| Value | Description |
|-------|-------------|
| `G0` | Positional continuity |
| `G1` | Tangent continuity |

### PlateType

| Value | Description |
|-------|-------------|
| `flat` | Planar surface |
| `radiused` | Spherical cap |
| `arched` | Carved arch (RESEARCH_ONLY) |

### RuntimeSupport

| Value | Meaning |
|-------|---------|
| `supported` | Full runtime generation |
| `semantic_only` | Schema valid, no topology |
| `unsupported` | Not supported |

---

## Integration with Export Object

### Extensions Block

```python
class ExportExtensions(BaseModel):
    ibg_morphology: Optional[IBGMorphologyExtension] = None
    cad_semantics: Optional[CadSemantics] = None
```

### Usage Example

```python
from app.export.cad_semantics import (
    CadSemantics,
    BodyCategory,
    AcousticSemantics,
    ThicknessSemantics,
    SideProfileSemantics,
    SideProfileType,
)

semantics = CadSemantics(
    body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
    acoustic=AcousticSemantics(
        thickness=ThicknessSemantics(
            top_thickness_mm=2.8,
            back_thickness_mm=2.5,
            side_depth_mm=121.0,
        ),
        side_profile=SideProfileSemantics(
            type=SideProfileType.TAPERED,
            max_depth_mm=121.0,
            min_depth_mm=105.0,
        ),
    ),
)

# Check runtime support
support = semantics.get_runtime_support()
# Returns: RuntimeSupport.SEMANTIC_ONLY

# Check if acoustic topology required
requires_topology = semantics.requires_acoustic_topology()
# Returns: True
```

---

## Validation

### Validation Function

```python
from app.export.cad_semantics import validate_acoustic_semantics

result = validate_acoustic_semantics(semantics)

# result.valid: bool
# result.blocking_errors: List[str]
# result.warnings: List[str]
# result.runtime_support: RuntimeSupport
```

### Blocking Errors

| Condition | Error |
|-----------|-------|
| Negative thickness | "X must be positive" |
| Zero thickness | "X must be positive" |
| Invalid enum | "Invalid body_category" |
| Taper min > max | "min_depth_mm cannot exceed max_depth_mm" |

### Warnings

| Condition | Warning |
|-----------|---------|
| Incomplete taper | "Tapered side_profile missing max/min depth values" |
| Radiused without radius | "Radiused back_type specified but back_radius_mm not provided" |
| Category mismatch | "body_category is flat_body but acoustic semantics suggest..." |

---

## Translator Behavior

### DXF/SVG Translators

- Ignore `cad_semantics` entirely
- No impact on existing functionality
- No error on acoustic semantics presence

### STEP Translator (Future)

When STEP translator encounters acoustic semantics:

```python
if semantics.requires_acoustic_topology():
    return TranslatorResult(
        success=False,
        error_classification="UNSUPPORTED_TOPOLOGY_RUNTIME",
        message="Acoustic topology generation not supported",
    )
```

**Key Rule:** No fallback extrusion. Do not silently degrade acoustic semantics.

### Flat Body Support

STEP translator supports `body_category=flat_body`:

```python
if semantics.body_category == BodyCategory.FLAT_BODY:
    thickness = semantics.get_effective_thickness()
    # Proceed with flat extrusion
```

---

## Authority Model

### Hierarchy

```
BOE (Geometry Authority)
    │ READ ONLY
    ▼
IBG (Morphology Advisory)
    │ CONSUME
    ▼
cad_semantics (CAD Hints)
    │ EXTEND
    ▼
Translator (Topology Construction)
```

### Key Rules

1. **cad_semantics may EXTEND** geometry context
2. **cad_semantics may NOT override** BOE-approved coordinates
3. **cad_semantics may NOT invent** geometry not in BOE
4. **Translator CONSUMES** semantics, does not require all fields
5. **Translator may REJECT** unsupported configurations

---

## Thickness Hierarchy Integration

| Level | Fields | Status |
|-------|--------|--------|
| 1 | `uniform_thickness_mm` | IMPLEMENTED |
| 2 | `top_thickness_mm`, `back_thickness_mm`, `side_depth_mm` | IMPLEMENTED |
| 3 | Zone-based thickness | RESEARCH_ONLY |
| 4 | Continuous field | RESEARCH_ONLY |

---

## Related Documents

- `ACOUSTIC_BODY_SEMANTIC_MODEL.md` — Research foundation
- `ACOUSTIC_SEMANTIC_VALIDATION_RULES.md` — Validation details
- `ACOUSTIC_RUNTIME_LIMITATIONS.md` — Runtime constraints
- `THICKNESS_HIERARCHY_MODEL.md` — Thickness levels
- `CAD_SEMANTIC_AUTHORITY_RULES.md` — Authority boundaries
