# CAM Dev Order 6D — DXF Translator Boundary Alignment Handoff

**Date:** 2026-05-10  
**Author:** Claude (CAM Dev Order 6D)  
**Status:** COMPLETE

---

## Summary

Defined and prototyped the first governed translator boundary between Export Objects and DXF serialization infrastructure. Export objects can now be evaluated for DXF translator compatibility without generating any DXF output.

**Key outcome:** DXF is now formally established as a translator target, NOT the manufacturing representation.

---

## Core Architectural Rule

```
DXF must remain a translator target, NOT the manufacturing representation itself.
```

This boundary ensures:
- Export Object owns manufacturing intent
- DXF translator owns serialization adaptation
- Translation is separate from representation

---

## Scope

### In Scope (Completed)

- DXF translator adapter layer
- Translator-boundary models
- Export Object → DXF geometry classification
- Validation-only translator compatibility report
- Translator metadata
- 26 unit/integration tests

### Out of Scope (Per 6D Guardrails)

- No DXF file generation
- No DXF downloads
- No DXF persistence
- No machine-ready geometry
- No G-code
- No RMOS integration
- No translator execution pipeline

---

## Deliverables

| Deliverable | Location | Purpose |
|-------------|----------|---------|
| dxf_translator_boundary.py | app/cam/ | Translator-boundary models |
| export_object_to_dxf_adapter.py | app/cam/ | Export Object → translator mapping |
| dxf_translator_router.py | app/routers/cam/ | Endpoint |
| cam_manifest.py | app/router_registry/manifests/ | Router registration |
| test_dxf_translator_boundary.py | tests/cam/ | 26 test cases |
| CAM_6D_DXF_TRANSLATOR_ALIGNMENT_HANDOFF.md | docs/handoffs/ | This document |

---

## API

### Endpoint

```
POST /api/cam/dxf/translator/validate
```

### Request

```json
{
  "export_object": { "...GovernedExportObject..." },
  "translator_profile": {
    "translator_id": "generic_dxf_r14_validation_only",
    "supported_geometry_types": ["line", "polyline", "arc"],
    "supports_layers": true,
    "supports_blocks": false,
    "supports_splines": false,
    "units": "mm"
  }
}
```

### Response

```json
{
  "compatible": true,
  "gate": "green",
  "translator_output_generated": false,
  "dxf_generated": false,
  "translation_ready": true,
  "geometry_types_detected": ["line", "polyline"],
  "unsupported_geometry": [],
  "warnings": [],
  "blocking_issues": [],
  "required_translator_features": ["polyline_support", "layer_support"],
  "metadata": {
    "validation_only": true,
    "risk_class": "B",
    "translator_class": "DXF",
    "machine_ready": false
  }
}
```

---

## Gate Semantics

| Gate | Condition |
|------|-----------|
| GREEN | All checks pass, translation ready |
| YELLOW | Compatible with warnings (missing optional features) |
| RED | Incompatible (unsupported geometry, unit mismatch) |

---

## Checks Implemented

### 1. Geometry Type Detection

Maps Export Object structure to DXF-relevant geometry:

| Export Object Entity | DXF Geometry Type |
|---------------------|-------------------|
| slot, groove, channel | polyline, line |
| hole, circle | circle |
| arc, curve | arc |
| profile, contour | polyline |
| spline, bezier | spline |

### 2. Unit Compatibility

```
export_object.geometry.coordinate_system.units == translator_profile.units
```
- RED if mismatch

### 3. Geometry Support

```
all detected geometry types in translator_profile.supported_geometry_types
```
- RED if any unsupported geometry

### 4. Feature Support

| Feature | Check | Gate |
|---------|-------|------|
| polyline_support | Required for slots | RED if missing |
| line_support | Required for linear paths | RED if missing |
| arc_support | Required if arcs present | RED if missing |
| layer_support | Optional but recommended | YELLOW if missing |

---

## Safety Verified by Tests

- `translator_output_generated: false`
- `dxf_generated: false`
- `metadata.validation_only: true`
- `metadata.machine_ready: false`
- No DXF serialization tokens in response (SECTION, ENTITIES, POLYLINE, VERTEX, EOF)

---

## Adapter Design

The adapter performs **classification only**, not primitive construction:

```python
{
  "geometry_types_detected": ["polyline", "line"],
  "required_translator_features": ["polyline_support", "layer_support"],
  "unsupported_geometry": [],
  "analysis_only": True
}
```

This keeps the boundary clean:
- Export Object → translator compatibility analysis
- NOT Export Object → DXF primitive construction

Full primitive mapping belongs in a later dev order (6E or beyond).

---

## Relationship to Existing DXF Infrastructure

The following exist but are NOT integrated in 6D:

| Module | Status | Role |
|--------|--------|------|
| dxf_compat | Legacy | dxf_compat module for version-safe DXF |
| dxf_writer | Legacy | Central DXF writer (CLAUDE.md blocking item) |
| dxf_advanced_validation | Legacy | DXF validation utilities |

These represent:
- Legacy translator infrastructure
- Future translator execution layer

They do NOT define canonical manufacturing representation — that role belongs to the Export Object.

---

## What This Proves

1. **Translator boundary can exist** — Compatibility validation without output generation
2. **Export Object → DXF mapping works** — Geometry classification successful
3. **DXF remains translator-only** — Not promoted to canonical representation
4. **Architecture separation maintained** — Export Object owns manufacturing intent

---

## What This Does NOT Do

- Does not generate DXF files
- Does not produce DXF sections
- Does not serialize geometry
- Does not create downloadable output
- Does not persist to RMOS
- Does not execute translation pipeline

These are intentionally deferred to future dev orders.

---

## Recommended Next Steps

### 6E: DXF Translator IR Prototype

Build intermediate representation:
1. Export Object → DXF-ready primitives (with coordinates)
2. Layer assignment logic
3. Entity structuring without serialization

### 6F: DXF Translator Execution

Connect to dxf_compat/dxf_writer:
1. IR → DXF serialization
2. File generation
3. Governed DXF output

### 6G: RMOS Export Artifact Integration

Wire persistence:
1. Export artifact storage
2. Lineage tracking
3. Run ID generation

---

## Cross-Reference

| Document | Purpose |
|----------|---------|
| CAM_GOVERNED_EXPORT_ARCHITECTURE.md | 6A architecture |
| CAM_EXPORT_OBJECT_MODEL.md | Export object schema |
| CAM_6B_EXPORT_OBJECT_PROTOTYPE_HANDOFF.md | Export object prototype |
| CAM_6C_POSTPROCESSOR_BOUNDARY_HANDOFF.md | Postprocessor boundary |

---

*6D alignment complete: 2026-05-10*
