# MRP-5A: STEP Translator Feasibility & Semantic CAD Boundary Audit

**Date:** 2026-05-14  
**Sprint:** MRP-5A  
**Status:** COMPLETE

---

## Executive Summary

MRP-5A audits the semantic gap between current Export Objects and future CAD-grade (STEP) translators. This sprint is an audit and boundary-definition sprint, not an implementation sprint.

**Key Finding:** The current Export Object architecture can support STEP translation for flat-body instruments with minor schema extensions. Complex morphology (acoustic guitars with variable side heights) requires the existing IBG morphology extension, which already contains the necessary semantic data.

---

## STEP Semantic Requirements Analysis

### What STEP Requires Beyond DXF/SVG

| Category | DXF/SVG | STEP AP203 |
|----------|---------|------------|
| Geometry | 2D polylines | 3D BREP solid |
| Topology | None | Vertices, edges, faces, shells |
| Closure | Visual (drawing) | Watertight (manifold) |
| Surfaces | Line/arc entities | Planar, ruled, swept |
| Units | Header metadata | Formal unit definition |
| Precision | Drawing tolerance | Manufacturing tolerance |

### Classification of STEP Requirements

| Requirement | Classification | Notes |
|-------------|----------------|-------|
| Closed profile | REQUIRED | Export Object validates this |
| Profile extrusion | REQUIRED | Direction from coordinate_system |
| Thickness value | REQUIRED | Missing from schema, needs extension |
| Face definitions | REQUIRED | Must be constructed by translator |
| Watertight topology | REQUIRED | Post-construction validation |
| Variable height | OPTIONAL | IBG extension provides this |
| Surface continuity | OPTIONAL | Not required for body profiling |
| Assembly semantics | OUT_OF_SCOPE | Future extension |
| PMI annotations | OUT_OF_SCOPE | Not body profiling concern |

---

## Export Object CAD Readiness Summary

### Current Capabilities (from audit)

| Capability | Status | Evidence |
|------------|--------|----------|
| Closed 2D contours | READY | `entities[].type: "closed_contour"` |
| Contour validation | READY | `validation.checks_performed[]` |
| Winding direction | READY | `entities[].winding` |
| Coordinate system | READY | Full 3D coordinate frame defined |
| Units | READY | `coordinate_system.units: "mm"` |
| Provenance | READY | Complete metadata chain |
| Manufacturing intent | READY | `intent.operation_type` |

### Current Gaps

| Gap | Impact | Proposed Solution |
|-----|--------|-------------------|
| `thickness_mm` not in schema | Cannot extrude without depth | Add optional field |
| `side_heights_mm` in extension only | Complex morphology requires IBG | Promote to schema or consume extension |
| No face topology | Must be constructed | Translator responsibility |
| No watertight validation | Must be added | Post-construction check |

---

## CAD Boundary Model

### Recommended Architecture

```
Export Object
    │
    ├── Simple Path (flat body)
    │       │
    │       └── STEP Translator (direct extrusion)
    │
    └── Complex Path (morphology)
            │
            └── IBG morphology consumed by translator
                    │
                    └── STEP Translator (ruled surfaces)
```

### Key Boundary Rule

**CAD translators may CONSTRUCT topology from approved geometry, but may NOT REINTERPRET approved geometry authority.**

---

## Topology & Body Continuity Analysis

### By Instrument Class

| Instrument Type | Side Heights | Back Arch | Topology | STEP Feasibility |
|-----------------|--------------|-----------|----------|------------------|
| Flat electric (Strat, LP) | Constant | None | Simple extrusion | **HIGH** |
| Acoustic flat-top (Dread, OM) | Variable | Present | Ruled surfaces | **MODERATE** |
| Hollow body (ES-335) | Multiple depths | None | Boolean CSG | **COMPLEX** |
| Arch-top carved | Variable | Curved | Surface modeling | **RESEARCH** |
| Multi-piece assembly | N/A | N/A | Multi-body | **FUTURE** |

### Contour Continuity

| Property | Status | Notes |
|----------|--------|-------|
| Closed contours | Validated | First ≈ last point check |
| Winding consistency | Validated | outer=ccw, voids=cw |
| Minimum point count | Validated | ≥10 points required |
| Self-intersection | Not validated | Future check |

---

## STEP Feasibility Classification

### Instrument Type Matrix

| Instrument Type | STEP Feasibility | Confidence | Required Translator |
|-----------------|------------------|------------|---------------------|
| Solid body electric | **HIGH** | 95% | body_outline_step_ap203 |
| Acoustic flat-top | **MODERATE** | 75% | body_acoustic_step_ap203 |
| Classical | **MODERATE** | 75% | body_acoustic_step_ap203 |
| Hollow body | **COMPLEX** | 50% | Future research |
| Arch-top | **RESEARCH** | 25% | Surface modeling required |
| Mandolin | **COMPLEX** | 40% | Compound curves |
| Ukulele | **HIGH** | 90% | body_outline_step_ap203 |
| Cuatro | **MODERATE** | 70% | body_acoustic_step_ap203 |

### Technical Justification

**HIGH feasibility:**
- Constant thickness extrusion
- Simple profile × depth
- No variable morphology
- Standard CAD operation

**MODERATE feasibility:**
- Variable side heights present (Sevy/Mottola formula)
- IBG morphology extension provides data
- Ruled surface generation required
- Standard but more complex

**COMPLEX/RESEARCH:**
- Surface modeling required
- Boolean operations for chambers
- Arch carving is sculpted, not extruded
- May require external CAD kernel

---

## Future Sprint Roadmap

### Recommended Sequence

| Sprint | Title | Scope |
|--------|-------|-------|
| **MRP-5A** | STEP Feasibility Audit | This sprint (COMPLETE) |
| **MRP-5B** | CAD Semantic Extension | Add `thickness_mm` to schema |
| **MRP-5C** | STEP Translator Prototype | Flat-body only, AP203 |
| **MRP-5D** | CAD Regression Fixtures | Validation corpus |
| **MRP-5E** | Variable Height Support | Acoustic guitars |
| **MRP-6A** | Complex Morphology | Hollow body research |

### MRP-5B Scope (Next Sprint)

1. Add `thickness_mm: Optional[float]` to Export Object geometry
2. Add `body_type: Literal["flat", "variable", "carved", "hollow"]`
3. Formalize `side_heights_mm` consumption pattern
4. Update validation to check thickness availability
5. Update CAD_SEMANTIC_READINESS_MATRIX.md

### MRP-5C Scope (STEP Prototype)

1. Create `app/cam/translators/step/` package
2. Implement `BodyOutlineStepTranslator` for flat bodies
3. Use simple extrusion (profile × thickness)
4. Register with TranslatorRegistry
5. Add `/api/translate/step` endpoint
6. Validate with DWG TrueView or FreeCAD

---

## Deliverables Created

| Document | Purpose |
|----------|---------|
| `docs/governance/CAD_SEMANTIC_READINESS_MATRIX.md` | Readiness classification |
| `docs/architecture/CAD_TRANSLATOR_BOUNDARY_MODEL.md` | Boundary architecture |
| `docs/governance/CAD_TRANSLATOR_GOVERNANCE_RULES.md` | CAD-specific rules |
| `docs/handoffs/MRP_5A_STEP_FEASIBILITY_AUDIT.md` | This handoff |

---

## Governance Invariants Verified

| Invariant | Status |
|-----------|--------|
| Export Object remains canonical | VERIFIED |
| Translators consume, not create semantics | DOCUMENTED |
| CAD translators extend, not replace governance | DOCUMENTED |
| Morphology authority remains with IBG | VERIFIED |
| No CAD implementation in this sprint | COMPLIANT |

---

## Key Decisions

### Decision 1: Direct vs Intermediate Layer

**Decision:** Direct translation for flat bodies, morphology consumption for complex.

**Rationale:** Avoids over-engineering. IBG extension already contains necessary data.

### Decision 2: Target STEP Protocol

**Decision:** AP203 only for MVP.

**Rationale:** Simplest viable CAD interchange. AP214/AP242 are future extensions.

### Decision 3: Thickness Schema Extension

**Decision:** Add `thickness_mm` to Export Object for MRP-5B.

**Rationale:** Required for any extrusion operation. Currently missing.

### Decision 4: Translator Category

**Decision:** CAD translators are `TranslatorCategory.SERIALIZATION`, not `MANUFACTURING`.

**Rationale:** STEP files are interchange format, not machine code.

---

## Non-Goals Confirmed

This sprint did NOT:
- Implement STEP export
- Generate STEP files
- Implement solids or BREP
- Add CAD kernels
- Modify IBG math
- Modify BOE
- Modify Export Object schema
- Introduce CAD assumptions upstream

---

## References

- `docs/governance/TRANSLATOR_LAYER_RULES.md`
- `docs/governance/MULTI_TARGET_TRANSLATOR_POLICY.md`
- `docs/handoffs/MRP_4A_MULTI_TARGET_TRANSLATOR_HANDOFF.md`
- `docs/handoffs/MRP_4B_TRANSLATOR_REGISTRY_INTEGRATION_HANDOFF.md`
- `app/export/body_export_bridge.py`
- `app/instrument_geometry/body/ibg/body_contour_solver.py`
- STEP AP203 (ISO 10303-203)

---

*MRP-5A complete. STEP feasibility audited. CAD boundary defined. No implementation performed.*
