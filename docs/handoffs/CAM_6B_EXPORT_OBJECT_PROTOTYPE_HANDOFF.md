# CAM Dev Order 6B — Export Object Prototype Handoff

**Date:** 2026-05-10  
**Author:** Claude (CAM Dev Order 6B)  
**Status:** COMPLETE

---

## Summary

Implemented the export object prototype for Nut Slot CAM, proving the 6A architecture can exist as running code. The export object transforms governed previews into portable manufacturing representations without generating machine-executable output.

**Key outcome:** The repo now has a working prototype demonstrating the preview→export boundary crossing.

---

## Scope

### In Scope (Completed)

- Export object schema (all blocks)
- Pure function: `create_nut_slot_export_object(preview, request)`
- Endpoint: `POST /api/cam/nut-slot/export-object`
- Gate logic: GREEN/YELLOW exportable, RED rejected
- 24 unit/integration tests

### Out of Scope (Per 6B Guardrails)

- No postprocessor code
- No machine profile loading
- No G-code generation
- No DXF output
- No RMOS persistence
- No tool library file system

---

## Deliverables

| Deliverable | Location | Purpose |
|-------------|----------|---------|
| export_object.py | app/cam/ | Export object schema |
| nut_slot_export.py | app/cam/ | Nut slot export function |
| nut_slot_router.py | app/routers/cam/ | Updated with export-object endpoint |
| test_nut_slot_export.py | tests/cam/ | 24 test cases |
| CAM_6B_EXPORT_OBJECT_PROTOTYPE_HANDOFF.md | docs/handoffs/ | This document |

---

## Architecture Implementation

### Export Object Schema

All 8 blocks implemented as Pydantic models:

```python
ExportObject(
    schema_version="1.0.0",
    export_id="EXP-NUT-20260510-abc123",
    export_type="toolpath",
    metadata=ExportMetadata(...),
    geometry=ExportGeometry(...),
    toolpaths=ExportToolpaths(...),
    tooling=ExportTooling(...),
    material=ExportMaterial(...),
    stock=ExportStock(...),
    validation=ExportValidation(...),
    intent=ExportIntent(...),
)
```

### Pure Function

```python
def create_nut_slot_export_object(
    preview: NutSlotPreviewResponse,
    request: NutSlotPreviewRequest,
) -> ExportObject:
    """Transform governed preview into export object."""
```

### Endpoint

```
POST /api/cam/nut-slot/export-object
```

Request: Same as preview endpoint (NutSlotPreviewRequest)

Response:
```json
{
  "exportable": true,
  "gate": "green",
  "export_object": { ... },
  "errors": [],
  "warnings": []
}
```

### Gate Logic

| Preview Gate | Response |
|--------------|----------|
| GREEN | exportable=true, export_object populated |
| YELLOW | exportable=true, export_object populated, warnings present |
| RED | exportable=false, export_object=null, errors populated |

---

## Export Object Blocks

### Metadata Block

- export_id: `EXP-NUT-{date}-{hash}` pattern
- schema_version: "1.0.0"
- source: preview_id, preview_hash, generator_id, generator_version
- operation_category: "slot_cutting"

### Geometry Block

- coordinate_system: Mapped from preview
- bounds: Calculated from toolpath moves
- entities: Slot geometry for each string

### Toolpaths Block

- operations: One per slot (4 moves each)
- statistics: Move counts from preview

### Tooling Block

- tool_id: Derived from diameter
- tool_type: "slot_saw"
- geometry: diameter, cutting_length, shank_diameter

### Material Block (Minimal)

- material_type: "unknown"
- material_profile_id: null

### Stock Block

- dimensions: From request
- fixture: Default jig_clamped

### Validation Block

- gate_status: From preview
- source_preview_hash: SHA256 of preview JSON
- issues/warnings: From preview

### Intent Block

- operation_type: "nut_slot_cutting"
- depth_strategy: "full_depth_single_pass"
- finish_requirements: functional, 0.05mm tolerance

---

## Test Coverage

| Test Class | Tests | Coverage |
|------------|-------|----------|
| TestCreateExportObject | 10 | All blocks populated |
| TestGenerateExportObject | 3 | Gate logic |
| TestExportObjectEndpoint | 6 | HTTP behavior |
| TestUtilityFunctions | 2 | Hash/ID generation |
| TestSerialization | 2 | JSON round-trip |
| **Total** | **24** | **100% of new code** |

All 203 CAM tests pass after 6B.

---

## What This Proves

1. **Export Object schema can be instantiated** — All blocks populate correctly
2. **Preview→Export boundary works** — Gate logic enforced
3. **Reproducibility** — Export objects regenerate identically from inputs
4. **Traceability** — Preview hash links export to source
5. **Non-executability** — No G-code, no machine-specific output

---

## What This Does NOT Do

- Does not persist to RMOS
- Does not load tool profiles from files
- Does not generate machine output
- Does not require machine profile
- Does not download files

These are intentionally deferred to future dev orders.

---

## Recommended Next Steps

### 6C: RMOS Integration

Wire export object persistence:
1. Add export artifact storage
2. Generate run_id for exports
3. Store lineage (preview → export)

### 6D: Second Preview Source

Add drilling export object:
1. Reuse export_object.py schema
2. Create drilling_export.py
3. Validate architecture generalization

### 6E: Postprocessor Foundation

Begin postprocessor work:
1. Implement GRBLPostprocessor skeleton
2. Add machine profile loading
3. Wire validation against profile

---

## Cross-Reference

| Document | Purpose |
|----------|---------|
| CAM_GOVERNED_EXPORT_ARCHITECTURE.md | 6A architecture |
| CAM_EXPORT_OBJECT_MODEL.md | Schema definition |
| CAM_6A_GOVERNED_EXPORT_HANDOFF.md | Prior dev order |

---

*6B prototype complete: 2026-05-10*
