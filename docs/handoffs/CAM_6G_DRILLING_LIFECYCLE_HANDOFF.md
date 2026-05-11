# CAM Dev Order 6G — Drilling Lifecycle Integration Handoff

**Date:** 2026-05-11  
**Author:** Claude (CAM Dev Order 6G)  
**Status:** COMPLETE

---

## Summary

Extended the governed export lifecycle to support drilling operations. This proves the lifecycle architecture is operation-extensible and not hardcoded around Nut Slot CAM.

**Key outcome:** Multi-operation dispatcher pattern validated with two operations.

---

## Core Architectural Rule

```
6G extends governed lifecycle orchestration, NOT machine execution.
```

No serialization or executable output is added.

---

## Scope

### In Scope (Completed)

- Drilling lifecycle dispatch
- Drilling export object generation
- Drilling compatibility validation
- Drilling RMOS persistence support
- 26 drilling lifecycle tests
- Drilling preview function extraction (refactor)

### Out of Scope (Per 6G Guardrails)

- No drilling G-code
- No drilling DXF generation
- No machine execution
- No peck cycles
- No canned cycles
- No postprocessor execution
- No translator execution

---

## Deliverables

| Deliverable | Location | Purpose |
|-------------|----------|---------|
| drilling_export.py | app/cam/ | Export object builder |
| drilling_preview_router.py | app/cam/routers/drilling/ | Refactored with extract |
| export_lifecycle_orchestrator.py | app/cam/ | Drilling dispatch added |
| test_drilling_export_lifecycle.py | tests/cam/ | 26 test cases |
| CAM_6G_DRILLING_LIFECYCLE_HANDOFF.md | docs/handoffs/ | This document |

---

## Dispatcher Extension

### Before (6E)

```python
SUPPORTED_OPERATIONS = ["nut_slot"]
```

### After (6G)

```python
SUPPORTED_OPERATIONS = ["nut_slot", "drilling"]
```

All unsupported operations still return RED.

---

## Drilling Preview Refactor

Extracted `generate_drilling_preview(request)` as a standalone function:

```python
# In drilling_preview_router.py

def generate_drilling_preview(req: DrillingPreviewRequest) -> DrillingPreviewResponse:
    """Pure function for preview generation."""
    ...

@router.post("/preview")
def preview_drilling(req: DrillingPreviewRequest) -> DrillingPreviewResponse:
    """Thin wrapper around generate_drilling_preview."""
    return generate_drilling_preview(req)
```

This allows the lifecycle orchestrator to call the same preview logic as the route.

---

## Geometry Semantics

### Drilling Geometry Entities

| Entity Type | DXF Mapping | Properties |
|-------------|-------------|------------|
| hole | circle | x_mm, y_mm, diameter_mm, depth_mm |

### Drilling Toolpath Operations

| Operation Type | Moves |
|----------------|-------|
| drill | rapid → plunge → retract |

---

## Compatibility Semantics

### Machine Compatibility

Drilling requires:
- `drilling` in `supported_operations`
- `axis_count >= 3` (Z-axis for plunge)

### Translator Compatibility

Drilling requires:
- `circle` in `supported_geometry_types`

If translator lacks circle support → RED gate.

---

## Export Object Mapping

### Drilling Export Object Schema

```json
{
  "export_id": "EXP-DRILL-20260511-abc123",
  "export_type": "toolpath",
  "metadata": {
    "operation_category": "drilling",
    "generator_id": "drilling_preview"
  },
  "geometry": {
    "entities": [
      {"type": "hole", "id": "hole_1", "properties": {...}}
    ]
  },
  "toolpaths": {
    "operations": [
      {"operation_type": "drill", "moves": [...]}
    ]
  },
  "intent": {
    "operation_type": "drilling",
    "depth_strategy": "single_plunge"
  }
}
```

---

## RMOS Persistence

Drilling artifacts persist using the same 6F infrastructure:

```json
{
  "persist_to_rmos": true
}
```

Results in:
- `export_object_json` artifact
- `export_lifecycle_report_json` artifact

No new artifact types required.

---

## Safety Verified by Tests

- `machine_output_generated: false` — always
- `translator_output_generated: false` — always
- `machine_ready: false` — always
- No G-code tokens (G81, G83, etc.)
- No DXF tokens (CIRCLE, SECTION, etc.)
- Unsupported operations still return RED

---

## How Drilling Differs from Nut Slot

| Aspect | Nut Slot | Drilling |
|--------|----------|----------|
| Geometry | slot (linear) | hole (circular) |
| DXF Mapping | polyline | circle |
| Toolpath | slot_cut | drill |
| Depth | slot depth | hole depth |
| Tool | slot saw | drill bit |

Same lifecycle pipeline, different operation semantics.

---

## Future Extensibility Path

To add another operation (e.g., fret slots):

1. Create `{operation}_export.py` with `create_{operation}_export_object()`
2. Add operation to `SUPPORTED_OPERATIONS` list
3. Add dispatch branches in `dispatch_preview()` and `dispatch_export_object()`
4. Ensure preview function is callable (extract if inline)
5. Map geometry types for translator compatibility
6. Create tests

The dispatcher pattern scales to N operations.

---

## Cross-Reference

| Document | Purpose |
|----------|---------|
| CAM_GOVERNED_EXPORT_ARCHITECTURE.md | 6A architecture |
| CAM_6B_EXPORT_OBJECT_PROTOTYPE_HANDOFF.md | Export object prototype |
| CAM_6C_POSTPROCESSOR_BOUNDARY_HANDOFF.md | Postprocessor boundary |
| CAM_6D_DXF_TRANSLATOR_ALIGNMENT_HANDOFF.md | DXF translator boundary |
| CAM_6E_EXPORT_LIFECYCLE_HANDOFF.md | Lifecycle orchestration |
| CAM_6F_RMOS_EXPORT_OBJECT_HANDOFF.md | RMOS persistence |

---

## Test Summary

| Category | Tests |
|----------|-------|
| Dispatcher Extension | 3 |
| Drilling Preview | 2 |
| Drilling Export Object | 4 |
| Drilling Lifecycle | 5 |
| Compatibility | 3 |
| RMOS Persistence | 2 |
| Safety Assertions | 5 |
| Endpoint | 2 |
| **Total** | **26** |

---

*6G drilling lifecycle complete: 2026-05-11*
