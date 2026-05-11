# CAM Dev Order 6H: Operation Capability Registry Handoff

**Date:** 2026-05-11
**Status:** Complete
**Predecessor:** 6G (Drilling Lifecycle Integration)

## Summary

Operations are now self-describing governed capabilities. The capability registry becomes the single source of truth for what the lifecycle supports, not hardcoded lists in the orchestrator.

## Files Created

- `app/cam/cam_operation_registry.py` — Capability models and registry
- `app/routers/cam/lifecycle_capability_router.py` — Introspection endpoints
- `tests/cam/test_operation_capability_registry.py` — Registry tests (31 tests)

## Files Modified

- `app/cam/export_lifecycle_orchestrator.py` — Uses registry instead of `SUPPORTED_OPERATIONS`
- `app/router_registry/manifests/cam_manifest.py` — Registered capability router
- `tests/cam/test_drilling_export_lifecycle.py` — Updated to use registry

## Architecture

### CAMOperationCapability Model

Each operation declares its lifecycle semantics explicitly:

```python
CAMOperationCapability(
    operation="nut_slot",
    lifecycle_supported=True,
    export_object_supported=True,
    machine_validation_supported=True,
    translator_validation_supported=True,
    rmos_persistence_supported=True,
    preview_route="/api/cam/nut-slot/preview",
    lifecycle_route="/api/cam/export/lifecycle/validate",
    exportability_class="governed_export",
    maturity="canonical",
    required_machine_capabilities=[...],
    required_translator_features=[...],
    supported_geometry_types=[...],
    machine_ready=False,  # Always false in 6H
    machine_output_supported=False,  # Always false in 6H
)
```

### Registry Functions

```python
get_operation_capability("nut_slot")  # -> CAMOperationCapability | None
list_lifecycle_supported_operations()  # -> ["nut_slot", "drilling"]
list_governed_operations()  # -> operations with maturity=governed|canonical
list_exportable_operations()  # -> operations with export_object_supported=True
get_all_capabilities()  # -> List[CAMOperationCapability]
```

### Dispatcher Integration

The lifecycle dispatcher now queries the registry:

```python
def dispatch_preview(operation, payload):
    capability = get_operation_capability(operation)
    if capability is None or not capability.lifecycle_supported:
        return None, "red", [f"Unsupported lifecycle operation: {operation}"], []
```

## Introspection Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/cam/lifecycle/capabilities` | Full capability list with counts |
| `GET /api/cam/lifecycle/capabilities/{operation}` | Single operation (404 if not found) |
| `GET /api/cam/lifecycle/capabilities/summary` | Lightweight summary |
| `GET /api/cam/lifecycle/supported-operations` | List of operation names |

## Registered Operations

| Operation | Maturity | Exportability | Lifecycle |
|-----------|----------|---------------|-----------|
| `nut_slot` | canonical | governed_export | Yes |
| `drilling` | canonical | governed_export | Yes |

## Safety Assertions

Every operation in the registry has:
- `machine_ready = False`
- `machine_output_supported = False`

These are enforced by tests.

## Adding New Operations

1. Add entry to `CAM_OPERATION_REGISTRY` in `cam_operation_registry.py`
2. Add dispatch branch in `dispatch_preview()` and `dispatch_export_object()`
3. The capability introspection endpoints update automatically

## Test Coverage

- 31 tests for capability registry
- Registry contents verification
- Safety assertion enforcement
- Endpoint response validation
- Lifecycle dispatcher integration

## What 6H Does NOT Do

- No machine execution
- No G-code generation
- No DXF output
- No runtime capability enforcement (semantic descriptors only)

## Next Steps

Potential 6I work:
- Runtime validation using `required_machine_capabilities`
- Capability-based routing in the lifecycle
- UI capability discovery using introspection endpoints
