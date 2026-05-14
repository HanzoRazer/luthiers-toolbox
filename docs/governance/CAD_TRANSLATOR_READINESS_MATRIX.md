# CAD Translator Readiness Matrix

**Date:** 2026-05-14  
**Sprint:** MRP-5B  
**Status:** PROPOSAL

---

## Purpose

Classifies translator capabilities across formats (DXF, SVG, future STEP) with maturity, governance status, and implementation readiness.

---

## Capability Matrix

### Core Capabilities

| Capability | DXF R12 | DXF R2000 | SVG | STEP (Future) |
|------------|---------|-----------|-----|---------------|
| Closed contour | ✓ | ✓ | ✓ | ✓ Required |
| Open polyline | ✓ | ✓ | ✓ | N/A |
| Void handling | ✓ | ✓ | ✓ | ✓ Required |
| Layer naming | ✓ | ✓ | ✓ (groups) | ✓ (colors) |
| Coordinate precision | 3dp | 3dp | 3dp | 3dp |
| Units (mm) | ✓ | ✓ | ✓ | ✓ Required |

### Provenance Capabilities

| Capability | DXF R12 | DXF R2000 | SVG | STEP (Future) |
|------------|---------|-----------|-----|---------------|
| Export ID | ✓ (layer text) | ✓ (XDATA) | ✓ (comment) | ✓ Required |
| Translator ID | ✓ | ✓ | ✓ | ✓ Required |
| Timestamp | ✓ | ✓ | ✓ | ✓ Required |
| Source hash | ✓ | ✓ | ✓ | ✓ Required |
| IBG session | ✓ | ✓ | ✓ | ✓ Optional |

### Topology Capabilities

| Capability | DXF R12 | DXF R2000 | SVG | STEP (Future) |
|------------|---------|-----------|-----|---------------|
| 2D contours | ✓ | ✓ | ✓ | ✓ (profile) |
| Edge entities | LINE | LWPOLYLINE | path | EDGE |
| Face definitions | ✗ | ✗ | ✗ | ✓ Required |
| Shell topology | ✗ | ✗ | ✗ | ✓ Required |
| Solid body | ✗ | ✗ | ✗ | ✓ Required |
| Watertight validation | ✗ | ✗ | ✗ | ✓ Required |

### Surface Capabilities

| Capability | DXF R12 | DXF R2000 | SVG | STEP (Future) |
|------------|---------|-----------|-----|---------------|
| Planar faces | ✗ | ✗ | ✗ | ✓ Required |
| Ruled surfaces | ✗ | ✗ | ✗ | ✓ Optional |
| Swept surfaces | ✗ | ✗ | ✗ | ✗ Future |
| NURBS | ✗ | ✗ | ✗ | ✗ Research |

### Assembly Capabilities

| Capability | DXF R12 | DXF R2000 | SVG | STEP (Future) |
|------------|---------|-----------|-----|---------------|
| Single body | ✓ | ✓ | ✓ | ✓ |
| Multi-body | ✗ | ✗ | ✗ | ✗ Future |
| Component hierarchy | ✗ | ✗ | ✗ | ✗ Future |
| Mating references | ✗ | ✗ | ✗ | ✗ Future |

### CAD Semantics Consumption

| Capability | DXF R12 | DXF R2000 | SVG | STEP (Future) |
|------------|---------|-----------|-----|---------------|
| cad_semantics required | ✗ | ✗ | ✗ | ✓ |
| uniform_thickness_mm | Ignored | Ignored | Ignored | ✓ Required |
| body_type | Ignored | Ignored | Ignored | ✓ Required |
| extrusion_direction | Ignored | Ignored | Ignored | ✓ Required |
| use_ibg_side_heights | Ignored | Ignored | Ignored | ✓ Optional |

---

## Maturity Classification

| Translator | Maturity | Notes |
|------------|----------|-------|
| body_outline_dxf_r12 | **GOVERNED** | Production, free tier |
| body_outline_dxf_r2000 | **GOVERNED** | Production, paid tier |
| body_outline_svg | **GOVERNED** | Production |
| body_outline_step_ap203 | **PROPOSAL** | Not implemented |

### Maturity Levels

| Level | Definition |
|-------|------------|
| PLACEHOLDER | Registered, not implemented |
| EXPERIMENTAL | Under development |
| CANDIDATE | Feature complete, validation pending |
| GOVERNED | Production-ready, governance-approved |
| DEPRECATED | Scheduled for removal |
| PROPOSAL | Documented, not yet registered |

---

## Governance Status

| Translator | Execution State | Gate Enforcement | Provenance |
|------------|-----------------|------------------|------------|
| body_outline_dxf_r12 | governed_execution | ✓ RED blocks | ✓ XDATA |
| body_outline_dxf_r2000 | governed_execution | ✓ RED blocks | ✓ XDATA |
| body_outline_svg | governed_execution | ✓ RED blocks | ✓ Comment |
| body_outline_step_ap203 | validation_only | ✓ RED blocks | ✓ Header |

---

## Implementation Readiness

### DXF R12/R2000

| Component | Status | Location |
|-----------|--------|----------|
| Translator class | ✓ Implemented | `app/cam/translators/dxf/` |
| Registry registration | ✓ Registered | `base/registry.py` |
| Target negotiation | ✓ Mapped | `base/negotiation.py` |
| API endpoint | ✓ Active | `/api/translate/dxf` |
| Test coverage | ✓ Verified | `tests/mrp_spine_verification/` |

### SVG

| Component | Status | Location |
|-----------|--------|----------|
| Translator class | ✓ Implemented | `app/cam/translators/svg/` |
| Registry registration | ✓ Registered | `base/registry.py` |
| Target negotiation | ✓ Mapped | `base/negotiation.py` |
| API endpoint | ✓ Active | `/api/translate/svg` |
| Test coverage | ✓ Verified | `tests/mrp_spine_verification/` |

### STEP AP203 (Proposed)

| Component | Status | Dependency |
|-----------|--------|------------|
| Translator class | ✗ Not implemented | MRP-5C |
| Registry registration | ✗ Not registered | Translator required |
| Target negotiation | ✗ Not mapped | Registry required |
| API endpoint | ✗ Not active | Negotiation required |
| CAD semantics schema | ✗ Proposed | MRP-5B (this sprint) |
| Test coverage | ✗ Not started | Implementation required |

---

## Carve Semantics Assessment

### Current Support

| Feature | DXF | SVG | STEP (Future) |
|---------|-----|-----|---------------|
| Profile carve (void subtraction) | ✓ | ✓ | ✓ |
| 3D pocket carve | ✗ | ✗ | ✗ Future |
| Arch-top carve | ✗ | ✗ | ✗ Research |
| Relief carve | ✗ | ✗ | ✗ Research |

### Carve Readiness Classification

| Carve Type | Classification | Notes |
|------------|----------------|-------|
| Through-cut void | READY | Void entities in Export Object |
| Pocket at uniform depth | FUTURE | Requires depth field |
| Graduated depth pocket | RESEARCH | Requires depth profile |
| Sculpted surface | OUT_OF_SCOPE | Beyond extrusion model |

---

## Dimensional Hierarchy

### Current Export Object

| Level | Status | Description |
|-------|--------|-------------|
| 2D contour | **CURRENT** | Profile geometry |
| Profile semantics | **CURRENT** | Closed region, winding |
| Extrusion semantics | **PROPOSED** | uniform_thickness_mm |
| Surface semantics | **FUTURE** | Ruled/swept surfaces |
| Body semantics | **FUTURE** | Solid validation |
| Assembly semantics | **RESEARCH** | Multi-body |

### Future Evolution Path

```
2D Contour (CURRENT)
    │
    ▼
Profile Semantics (CURRENT)
    │
    ├─► Extrusion Semantics (MRP-5B PROPOSAL)
    │       │
    │       ▼
    │   Surface Semantics (MRP-5E+ FUTURE)
    │       │
    │       ▼
    │   Body Semantics (MRP-6+ FUTURE)
    │
    └─► Assembly Semantics (RESEARCH)
```

---

## Risk Assessment

### STEP Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| CAD kernel dependency | Medium | High | Evaluate OCC, FreeCAD |
| Topology construction complexity | High | Medium | Start with flat bodies |
| IBG integration complexity | Medium | Medium | Optional consumption |
| Performance (large bodies) | Low | Medium | Chunked processing |
| Validation failure rate | Medium | Low | Graceful degradation |

### Compatibility Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Schema evolution breaks old exports | Low | High | Optional fields only |
| DXF regression from CAD changes | Low | High | Isolation policy |
| Unknown field handling | Low | Low | Pydantic extra='ignore' |

---

## Recommendations

### For MRP-5C (STEP Prototype)

1. Start with flat-body only (uniform thickness)
2. Require explicit `cad_semantics.uniform_thickness_mm`
3. Skip IBG integration initially
4. Use simple extrusion (profile × thickness)
5. Evaluate OCC/FreeCAD for BREP

### For MRP-5D (CAD Regression)

1. Create validation corpus (known-good STEP files)
2. Test DXF regression (no behavior change)
3. Test SVG regression (no behavior change)
4. Validate provenance continuity

### For MRP-5E+ (Advanced)

1. Add ruled surface support
2. Consume IBG side_heights
3. Implement watertight validation
4. Consider Level 2 thickness

---

## References

- `docs/governance/CAD_SEMANTIC_READINESS_MATRIX.md` — Semantic readiness
- `docs/architecture/CAD_SEMANTIC_EXTENSION_MODEL.md` — Extension model
- `docs/governance/CAD_TRANSLATOR_GOVERNANCE_RULES.md` — Translator rules
- `app/cam/translators/base/registry.py` — Registry implementation
