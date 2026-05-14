# CAD Semantic Readiness Matrix

**Date:** 2026-05-14  
**Sprint:** MRP-5A  
**Status:** AUDIT COMPLETE

---

## Purpose

Classifies the semantic readiness of current Export Object capabilities against future CAD-grade (STEP AP203-style) translator requirements.

---

## Classification Legend

| Status | Meaning |
|--------|---------|
| **READY** | Current schema supports this semantic |
| **PARTIAL** | Schema has related data but not CAD-complete |
| **MISSING** | Not present in current schema |
| **FUTURE_EXTENSION** | Planned future capability |
| **OUT_OF_SCOPE** | Beyond body outline domain |

---

## STEP Semantic Requirements Matrix

### Core Geometry Semantics

| Requirement | STEP Need | Export Object Status | Evidence | Notes |
|-------------|-----------|---------------------|----------|-------|
| Closed 2D contour | Required | **READY** | `entities[].type: "closed_contour"` | Fully supported |
| Contour closure validation | Required | **READY** | `validation.checks_performed[]` | First≈last point check |
| Winding direction | Required | **READY** | `entities[].winding: "ccw"\|"cw"` | Outer=ccw, voids=cw |
| Point coordinates | Required | **READY** | `entities[].points: [[x,y], ...]` | mm precision |
| Coordinate system | Required | **READY** | `geometry.coordinate_system.*` | Full definition |
| Units specification | Required | **READY** | `coordinate_system.units: "mm"` | Metric only |
| Bounding box | Required | **READY** | `geometry.bounds.*` | x/y complete |

### Topology Semantics

| Requirement | STEP Need | Export Object Status | Evidence | Notes |
|-------------|-----------|---------------------|----------|-------|
| Edge connectivity | Required | **PARTIAL** | Implicit in point sequence | No explicit edge entities |
| Vertex definitions | Required | **PARTIAL** | Points, not named vertices | Would need STEP vertex wrapper |
| Face regions | Required | **MISSING** | N/A | 2D contours only |
| Shell topology | Required | **MISSING** | N/A | No solid representation |
| Manifold validation | Required | **MISSING** | N/A | No topology checks |
| Watertight closure | Required | **MISSING** | N/A | 2D perimeter only |

### Extrusion Semantics

| Requirement | STEP Need | Export Object Status | Evidence | Notes |
|-------------|-----------|---------------------|----------|-------|
| Profile definition | Required | **READY** | `entities[].type: "closed_contour"` | Outer contour = profile |
| Extrusion direction | Required | **PARTIAL** | `coordinate_system.z_axis: "thickness"` | Direction defined, no vector |
| Extrusion depth | Required | **PARTIAL** | `intent.depth_strategy: "full_thickness"` | Strategy, not value |
| Variable height | Optional | **PARTIAL** | `extensions.ibg_morphology.side_heights_mm` | Morphology data, not topology |
| Draft angle | Optional | **MISSING** | N/A | Not applicable to instruments |

### Thickness Semantics

| Requirement | STEP Need | Export Object Status | Evidence | Notes |
|-------------|-----------|---------------------|----------|-------|
| Constant thickness | Required | **MISSING** | No `thickness_mm` field | Would be simple extension |
| Variable thickness | Optional | **PARTIAL** | `side_heights_mm` in IBG context | Morphology, not schema field |
| Top face offset | Optional | **MISSING** | N/A | Would derive from thickness |
| Back arch radius | Optional | **PARTIAL** | IBG `back_radius_mm` | In solver, not Export Object |

### Solid Body Semantics

| Requirement | STEP Need | Export Object Status | Evidence | Notes |
|-------------|-----------|---------------------|----------|-------|
| BREP solid | Required | **MISSING** | N/A | Would require construction |
| Face definitions | Required | **MISSING** | N/A | No face entities |
| Edge loops | Required | **MISSING** | N/A | No loop entities |
| Surface normals | Required | **MISSING** | N/A | No surface entities |
| Body volume | Optional | **MISSING** | N/A | Could compute from extrusion |

### Surface Semantics

| Requirement | STEP Need | Export Object Status | Evidence | Notes |
|-------------|-----------|---------------------|----------|-------|
| Planar surfaces | Required | **MISSING** | N/A | Top/bottom faces implied |
| Ruled surfaces | Required | **MISSING** | N/A | Side surfaces implied |
| Curved surfaces | Optional | **PARTIAL** | IBG `back_radius_mm`, `radii_by_zone` | Morphology, not geometry |
| Surface continuity | Optional | **MISSING** | N/A | No continuity data |
| NURBS/BREP | Optional | **MISSING** | N/A | Would require CAD kernel |

### Assembly Semantics

| Requirement | STEP Need | Export Object Status | Evidence | Notes |
|-------------|-----------|---------------------|----------|-------|
| Part identity | Optional | **PARTIAL** | `export_id`, `metadata.description` | Identity exists |
| Component hierarchy | Optional | **MISSING** | N/A | Single body only |
| Coordinate transforms | Optional | **READY** | `geometry.coordinate_system` | Local frame defined |
| Mating features | Optional | **MISSING** | N/A | Future extension |

### Manufacturing Semantics

| Requirement | STEP Need | Export Object Status | Evidence | Notes |
|-------------|-----------|---------------------|----------|-------|
| Operation intent | Optional | **READY** | `intent.operation_type` | "body_profiling" |
| Finish requirements | Optional | **READY** | `intent.finish_requirements` | Tolerance, surface finish |
| Depth strategy | Optional | **READY** | `intent.depth_strategy` | "full_thickness" |
| Material reference | Optional | **MISSING** | N/A | Future extension |

### Provenance Semantics

| Requirement | STEP Need | Export Object Status | Evidence | Notes |
|-------------|-----------|---------------------|----------|-------|
| Creation timestamp | Recommended | **READY** | `metadata.created_at` | ISO8601 |
| Generator ID | Recommended | **READY** | `metadata.source.generator_id` | "boe_export" |
| Source hash | Recommended | **READY** | `metadata.source.preview_hash` | SHA256 |
| Export ID | Recommended | **READY** | `export_id` | "EXP-BODY-..." |

---

## Summary by Category

| Category | READY | PARTIAL | MISSING | Total |
|----------|-------|---------|---------|-------|
| Core Geometry | 7 | 0 | 0 | 7 |
| Topology | 0 | 2 | 4 | 6 |
| Extrusion | 1 | 3 | 1 | 5 |
| Thickness | 0 | 2 | 2 | 4 |
| Solid Body | 0 | 0 | 5 | 5 |
| Surface | 0 | 2 | 4 | 6 |
| Assembly | 1 | 1 | 2 | 4 |
| Manufacturing | 3 | 0 | 1 | 4 |
| Provenance | 4 | 0 | 0 | 4 |
| **Total** | **16** | **10** | **19** | **45** |

---

## Key Findings

### CAD-Ready (No Changes Needed)

1. Core 2D geometry is complete
2. Coordinate system is well-defined
3. Validation infrastructure exists
4. Manufacturing intent is captured
5. Provenance is comprehensive

### Requires Schema Extension

1. **Thickness value** — Add `geometry.thickness_mm` or `extensions.thickness`
2. **Extrusion vector** — Derive from coordinate system (z_axis direction)
3. **Side height integration** — Promote `side_heights_mm` from IBG extension to schema

### Requires Construction Layer

1. **Face topology** — Must be constructed from contour + extrusion
2. **Edge loops** — Must be derived from face boundaries
3. **BREP solid** — Must be constructed from faces
4. **Watertight validation** — Must be computed post-construction

### Out of Scope for Body Profiling

1. NURBS surfaces
2. Assembly hierarchies
3. PMI annotations
4. Manufacturing planning

---

## Observed Runtime vs Schema Capability

| Capability | OBSERVED_RUNTIME | SCHEMA_SUPPORTED | DOCUMENTED_ONLY | MISSING |
|------------|------------------|------------------|-----------------|---------|
| Closed contours | Yes | Yes | Yes | - |
| Winding direction | Yes | Yes | Yes | - |
| Bounds computation | Yes | Yes | Yes | - |
| Side heights | Yes (IBG) | Yes (extension) | Yes | - |
| Back radius | Yes (IBG) | No | Yes (IBG docs) | Schema |
| Thickness value | No | No | Partial (intent) | Both |
| Face topology | No | No | No | Both |

---

## Recommendations for MRP-5B

1. **Add `thickness_mm` to Export Object** — Simple scalar for flat bodies
2. **Formalize side_heights** — Move from IBG extension to core schema
3. **Define extrusion semantic** — Pair profile with height vector
4. **Do NOT add topology yet** — Keep Export Object as 2D+semantic

---

## References

- `app/export/body_export_bridge.py` — Export Object schema (runtime)
- `docs/architecture/BOE_EXPORT_OBJECT_BRIDGE_MODEL.md` — Schema contracts
- `app/instrument_geometry/body/ibg/body_contour_solver.py` — Morphology model
- STEP AP203 Part 42 (Geometry) — External reference
