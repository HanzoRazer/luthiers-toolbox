# CAD Semantic Extension Model

**Date:** 2026-05-14  
**Sprint:** MRP-5B  
**Status:** PROPOSAL

---

## Purpose

Defines the governed semantic extensions to Export Objects required for future CAD-grade translators (STEP-class outputs) while preserving morphology/manufacturing authority boundaries.

---

## Core Principle

**CAD semantics extend approved geometry. They do not override approved geometry authority.**

Extensions are:
- Optional enrichment
- Translator-consumable hints
- Governance-controlled additions

Extensions are NOT:
- Geometry authority
- Manufacturing overrides
- Topology construction

---

## Extension Architecture

### Recommended: Option B — Separate Extension Block

```
BodyExportObject
    │
    ├── geometry (canonical 2D)
    ├── validation
    ├── intent
    └── extensions
            ├── ibg_morphology (existing)
            └── cad_semantics (NEW)
                    ├── thickness
                    ├── extrusion
                    └── profile_hints
```

**Rationale:** Preserves Export Object neutrality. DXF/SVG translators ignore `cad_semantics`. STEP translators consume it.

---

## Semantic Gap Inventory

### From MRP-5A Audit

| Semantic | MRP-5A Status | MRP-5B Classification |
|----------|---------------|----------------------|
| Profile (2D contour) | READY | N/A — already complete |
| Thickness value | MISSING | **REQUIRED_FOR_STEP** |
| Extrusion direction | PARTIAL | **REQUIRED_FOR_STEP** |
| Side heights | PARTIAL (IBG ext) | **USEFUL** |
| Surface intent | MISSING | **USEFUL** |
| Body zoning | MISSING | **FUTURE** |
| Carve regions | MISSING | **RESEARCH_ONLY** |
| Assembly references | MISSING | **OUT_OF_SCOPE** |
| Material thickness | MISSING | **FUTURE** |
| Neck/body interface | MISSING | **OUT_OF_SCOPE** |

### Classification Legend

| Classification | Meaning | Action |
|----------------|---------|--------|
| **REQUIRED_FOR_STEP** | Must exist for minimal STEP output | Include in proposal |
| **USEFUL** | Improves CAD quality but not required | Include as optional |
| **FUTURE** | Valuable for advanced use cases | Document, defer |
| **RESEARCH_ONLY** | Complex, needs investigation | Document only |
| **OUT_OF_SCOPE** | Beyond single-body focus | Exclude |

---

## Proposed Extensions: `extensions.cad_semantics`

### Tiered Thickness Model

**Level 1: Uniform Thickness (Flat Bodies)**

```python
class CadSemanticsLevel1(BaseModel):
    """Minimal CAD semantics for flat-body instruments."""
    uniform_thickness_mm: float  # Single scalar depth
```

Use case: Solid body electric guitars (Stratocaster, Les Paul)

**Level 2: Component Thickness (Acoustic Bodies)**

```python
class CadSemanticsLevel2(BaseModel):
    """Extended CAD semantics for acoustic instruments."""
    top_thickness_mm: Optional[float] = None      # Soundboard
    back_thickness_mm: Optional[float] = None     # Back plate
    side_depth_mm: Optional[float] = None         # Side height (uniform)
```

Use case: Acoustic flat-tops where top/back/side have different thicknesses

**Level 3: Zone-Based (Future)**

```python
class CadSemanticsLevel3(BaseModel):
    """Advanced CAD semantics for complex morphology."""
    thickness_zones: Optional[Dict[str, float]] = None  # Zone → thickness
    depth_profile: Optional[List[float]] = None         # Per-point depths
```

Use case: Graduated thickness tops, arch-tops (FUTURE)

### Recommended Schema

```python
class CadSemantics(BaseModel):
    """
    Optional CAD semantic extension for Export Objects.
    
    Consumed by CAD-grade translators (STEP, IGES).
    Ignored by 2D translators (DXF, SVG).
    """
    # Level 1 — Uniform (required for STEP)
    uniform_thickness_mm: Optional[float] = None
    
    # Level 2 — Component (optional enhancement)
    top_thickness_mm: Optional[float] = None
    back_thickness_mm: Optional[float] = None
    side_depth_mm: Optional[float] = None
    
    # Extrusion semantics
    extrusion_direction: Optional[str] = None  # "positive_z" | "negative_z"
    
    # Profile hints
    profile_type: Optional[str] = None  # "flat" | "variable" | "carved"
    
    # Future extension point
    level: int = 1  # Schema evolution marker
```

---

## Extrusion Semantics

### Current State

Export Object has:
```python
coordinate_system.z_axis = "thickness"
coordinate_system.z_zero = "top_face"
```

This defines semantic direction but not extrusion parameters.

### Proposed Extension

```python
class ExtrusionSemantics(BaseModel):
    """Extrusion hint for CAD translators."""
    direction: str = "positive_z"  # "positive_z" | "negative_z"
    origin: str = "top_face"       # "top_face" | "mid_plane" | "bottom_face"
    depth_source: str = "uniform_thickness_mm"  # Field reference
```

**Usage by STEP translator:**
```python
if cad_semantics.extrusion_direction == "positive_z":
    extrude(profile, thickness, direction=(0, 0, 1))
```

---

## Topology Descriptors (Semantic Only)

### Proposed Descriptors

| Descriptor | Meaning | Authority |
|------------|---------|-----------|
| `closed_region` | Profile is closed, suitable for extrusion | Derived from validation |
| `outer_boundary` | Entity is outer contour | From Export Object role |
| `void_boundary` | Entity is internal void | From Export Object role |
| `extrusion_candidate` | Profile can be extruded | Derived from closure check |

### Example Schema

```python
class TopologyDescriptor(BaseModel):
    """Semantic topology descriptor (not runtime topology)."""
    entity_id: str
    descriptor: str  # "closed_region" | "outer_boundary" | "void_boundary"
    derived_from: str  # "validation" | "role" | "geometry"
```

**Important:** These are semantic hints, NOT topology construction directives.

---

## Profile Hints

### Body Type Classification

```python
class ProfileHints(BaseModel):
    """Profile classification hints for CAD translators."""
    body_type: str = "flat"  # "flat" | "variable" | "carved" | "hollow"
    side_profile: str = "constant"  # "constant" | "tapered" | "ruled"
    arch_type: Optional[str] = None  # "none" | "spherical" | "catenary"
```

### Usage

| body_type | STEP Approach |
|-----------|---------------|
| `flat` | Simple extrusion |
| `variable` | Ruled surface from side_heights |
| `carved` | Surface modeling (RESEARCH) |
| `hollow` | Boolean CSG (COMPLEX) |

---

## IBG Extension Consumption

### Current: `extensions.ibg_morphology`

```python
class IBGMorphologyExtension(BaseModel):
    session_id: str
    confidence: float
    dimensions: Dict[str, float]
    instrument_spec: str
    side_heights_mm: Optional[List[float]] = None  # KEY DATA
    radii_by_zone: Optional[Dict[str, float]] = None
```

### Recommendation: Advisory Enrichment

**Do NOT promote `side_heights_mm` to core schema yet.**

Instead, document consumption pattern:

```python
# In STEP translator
if export_object.extensions and export_object.extensions.ibg_morphology:
    ibg = export_object.extensions.ibg_morphology
    if ibg.side_heights_mm:
        # Variable extrusion path
        heights = ibg.side_heights_mm
    else:
        # Constant extrusion path
        height = cad_semantics.uniform_thickness_mm
```

**Rationale:**
- IBG is morphology authority, not CAD authority
- side_heights_mm is reconstruction data, not manufacturing specification
- Promotion conflates morphology with CAD semantics

### Future Possibility

If governance approves, CAD semantic layer may reference IBG data:

```python
class CadSemantics(BaseModel):
    # ... existing fields ...
    
    # IBG-derived (governance-approved only)
    side_profile_from_ibg: bool = False
    ibg_confidence_threshold: float = 0.7
```

---

## Full Proposed Schema

```python
from pydantic import BaseModel
from typing import Dict, List, Optional


class CadSemantics(BaseModel):
    """
    CAD semantic extension for Export Objects.
    
    Location: extensions.cad_semantics
    Purpose: Provide hints for CAD-grade translators
    Authority: Optional enrichment (not geometry authority)
    """
    
    # Schema version
    schema_version: str = "1.0.0"
    level: int = 1  # 1=uniform, 2=component, 3=zone
    
    # Level 1: Uniform thickness
    uniform_thickness_mm: Optional[float] = None
    
    # Level 2: Component thickness
    top_thickness_mm: Optional[float] = None
    back_thickness_mm: Optional[float] = None
    side_depth_mm: Optional[float] = None
    
    # Extrusion hints
    extrusion_direction: str = "positive_z"
    extrusion_origin: str = "top_face"
    
    # Profile classification
    body_type: str = "flat"  # flat | variable | carved | hollow
    side_profile: str = "constant"  # constant | tapered | ruled
    
    # Topology descriptors
    is_closed_region: bool = True
    is_extrusion_candidate: bool = True
    
    # IBG reference (advisory)
    use_ibg_side_heights: bool = False
    ibg_confidence_required: float = 0.7


class ExportExtensions(BaseModel):
    """Export Object extensions block."""
    ibg_morphology: Optional[IBGMorphologyExtension] = None
    cad_semantics: Optional[CadSemantics] = None  # NEW
```

---

## Backward Compatibility

### Existing Translators

| Translator | CadSemantics Behavior |
|------------|----------------------|
| DXF R12 | Ignore (field absent or unused) |
| DXF R2000 | Ignore |
| SVG | Ignore |
| STEP (future) | Consume |

### Existing Export Objects

Export Objects without `cad_semantics`:
- DXF/SVG translators: No change
- STEP translator: Require explicit `uniform_thickness_mm` or fail gracefully

---

## References

- `docs/handoffs/MRP_5A_STEP_FEASIBILITY_AUDIT.md`
- `docs/governance/CAD_SEMANTIC_READINESS_MATRIX.md`
- `docs/architecture/CAD_TRANSLATOR_BOUNDARY_MODEL.md`
- `app/export/body_export_bridge.py`
