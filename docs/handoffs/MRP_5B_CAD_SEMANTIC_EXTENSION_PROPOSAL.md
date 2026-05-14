# MRP-5B: CAD Semantic Extension Proposal

**Date:** 2026-05-14  
**Sprint:** MRP-5B  
**Status:** COMPLETE

---

## Executive Summary

MRP-5B proposes governed semantic extensions to Export Objects for future CAD-grade translators (STEP-class outputs) while preserving the canonical authority boundaries established by the morphology spine.

**Key Proposal:** Add `extensions.cad_semantics` block with tiered thickness model and extrusion hints. Keep IBG morphology as advisory enrichment. Use direct extension (Option A), not a separate CAD semantic layer.

---

## Proposed Schema Extension

### Location: `extensions.cad_semantics`

```python
class CadSemantics(BaseModel):
    """Optional CAD semantic extension for Export Objects."""
    
    # Schema version
    schema_version: str = "1.0.0"
    level: int = 1  # 1=uniform, 2=component, 3=zone (future)
    
    # Level 1: Uniform thickness (REQUIRED_FOR_STEP)
    uniform_thickness_mm: Optional[float] = None
    
    # Level 2: Component thickness (optional enhancement)
    top_thickness_mm: Optional[float] = None
    back_thickness_mm: Optional[float] = None
    side_depth_mm: Optional[float] = None
    
    # Extrusion hints
    extrusion_direction: str = "positive_z"
    extrusion_origin: str = "top_face"
    
    # Profile classification
    body_type: str = "flat"  # flat | variable | carved | hollow
    
    # IBG reference (advisory)
    use_ibg_side_heights: bool = False
```

### Backward Compatibility

| Export Object | DXF | SVG | STEP |
|---------------|-----|-----|------|
| Without cad_semantics | ✓ Works | ✓ Works | ✗ Clear error |
| With cad_semantics | ✓ Ignores | ✓ Ignores | ✓ Consumes |

---

## Semantic Gap Inventory

### Classified Requirements

| Semantic | Classification | Proposed Action |
|----------|----------------|-----------------|
| Thickness value | **REQUIRED_FOR_STEP** | Add `uniform_thickness_mm` |
| Extrusion direction | **REQUIRED_FOR_STEP** | Add `extrusion_direction` |
| Body type | **USEFUL** | Add `body_type` classification |
| Side heights | **USEFUL** | Reference IBG extension |
| Component thickness | **USEFUL** | Add Level 2 fields |
| Surface intent | **FUTURE** | Defer to MRP-5E+ |
| Body zoning | **FUTURE** | Defer |
| Assembly references | **OUT_OF_SCOPE** | Single-body focus |

---

## Authority Model

### Hierarchy

```
TIER 1: Geometry Authority (BOE) ─── IMMUTABLE
TIER 2: Morphology Authority (IBG) ─── ADVISORY
TIER 3: Manufacturing Authority (Export Object) ─── CANONICAL
TIER 4: CAD Semantic Authority (cad_semantics) ─── OPTIONAL
TIER 5: Serialization Authority (Translators) ─── ISOLATED
```

### Key Rule

**CAD semantics may extend approved geometry. They may not override approved geometry authority.**

---

## Architecture Decision

### Recommendation: Option A (Direct Extension)

```
Export Object
    └── extensions.cad_semantics
            │
            ▼
        STEP Translator
```

**Rationale:**
- Simplest architecture
- Consistent with DXF/SVG pattern
- No additional layer to maintain
- Sufficient for flat-body and simple acoustic guitars

### Option B Deferred (Separate CAD Semantic Layer)

Considered for future if:
- ≥3 CAD translators with >50% shared logic
- Complex morphology (arch-top) in scope
- Schema evolution becomes frequent

---

## Tiered Thickness Model

### Level 1: Uniform (MRP-5C Target)

```python
uniform_thickness_mm: float  # Single scalar depth
```

Use case: Solid body electric guitars

### Level 2: Component (MRP-5E Target)

```python
top_thickness_mm: float      # Soundboard
back_thickness_mm: float     # Back plate
side_depth_mm: float         # Side height (uniform)
```

Use case: Acoustic guitars with different plate thicknesses

### Level 3: Zone-Based (Future Research)

```python
thickness_zones: Dict[str, float]  # Zone → thickness
depth_profile: List[float]         # Per-point depths
```

Use case: Graduated thickness tops, arch-tops

---

## IBG Extension Treatment

### Recommendation: Advisory Enrichment

**Do NOT promote `side_heights_mm` to core schema.**

Instead, STEP translator consumes from IBG extension:

```python
if export_object.extensions.ibg_morphology:
    if export_object.extensions.cad_semantics.use_ibg_side_heights:
        heights = export_object.extensions.ibg_morphology.side_heights_mm
```

**Rationale:**
- IBG is morphology authority, not CAD authority
- `side_heights_mm` is reconstruction data, not manufacturing specification
- User-specified thickness overrides IBG advisory data

---

## Compatibility Policy

### Backward Compatibility

- All `cad_semantics` fields are optional
- Existing Export Objects continue to work with DXF/SVG
- STEP translator requires explicit thickness

### Forward Compatibility

- Unknown fields ignored (Pydantic `extra='ignore'`)
- Schema version field for evolution tracking
- Deprecation process for field removal

---

## Translator Readiness

| Translator | cad_semantics Required | Status |
|------------|----------------------|--------|
| body_outline_dxf_r12 | NO | GOVERNED |
| body_outline_dxf_r2000 | NO | GOVERNED |
| body_outline_svg | NO | GOVERNED |
| body_outline_step_ap203 | YES | PROPOSED |

---

## Future Roadmap

| Sprint | Title | Scope |
|--------|-------|-------|
| MRP-5B | CAD Semantic Extension Proposal | This sprint (COMPLETE) |
| **MRP-5C** | **STEP Translator Prototype** | Flat-body only, AP203 |
| MRP-5D | CAD Regression Fixtures | Validation corpus |
| MRP-5E | Variable Height Support | Acoustic guitars |
| MRP-6A | Complex Morphology | Hollow body research |
| MRP-6B | Assembly Semantics | Multi-body (if needed) |

### MRP-5C Scope (Next Sprint)

1. Implement `cad_semantics` schema in runtime
2. Create `body_outline_step_ap203` translator
3. Support flat-body only (uniform thickness)
4. Register with TranslatorRegistry
5. Add `/api/translate/step` endpoint
6. Validate with FreeCAD or DWG TrueView

---

## Deliverables Created

| Document | Purpose |
|----------|---------|
| `docs/architecture/CAD_SEMANTIC_EXTENSION_MODEL.md` | Schema proposal |
| `docs/architecture/FUTURE_CAD_SEMANTIC_LAYER.md` | Option B evaluation |
| `docs/governance/CAD_SEMANTIC_AUTHORITY_RULES.md` | Authority boundaries |
| `docs/governance/CAD_EXTENSION_COMPATIBILITY_POLICY.md` | Compatibility rules |
| `docs/governance/CAD_TRANSLATOR_READINESS_MATRIX.md` | Capability matrix |
| `docs/handoffs/MRP_5B_CAD_SEMANTIC_EXTENSION_PROPOSAL.md` | This handoff |

---

## Governance Invariants

| Invariant | Status |
|-----------|--------|
| Export Object remains canonical | VERIFIED |
| CAD semantics are optional | PROPOSED |
| DXF/SVG translators unaffected | VERIFIED |
| IBG authority preserved | VERIFIED |
| BOE geometry immutable | VERIFIED |
| No runtime implementation | COMPLIANT |

---

## Non-Goals Confirmed

This sprint did NOT:
- Modify runtime schema
- Implement STEP export
- Implement CAD kernels
- Generate solids
- Implement topology construction
- Add assembly semantics
- Reinterpret approved geometry

---

## References

- `docs/handoffs/MRP_5A_STEP_FEASIBILITY_AUDIT.md`
- `docs/governance/CAD_SEMANTIC_READINESS_MATRIX.md`
- `docs/architecture/CAD_TRANSLATOR_BOUNDARY_MODEL.md`
- `docs/governance/CAD_TRANSLATOR_GOVERNANCE_RULES.md`
- `app/export/body_export_bridge.py`

---

*MRP-5B complete. CAD semantic extension proposed. Authority boundaries documented. No implementation performed.*
