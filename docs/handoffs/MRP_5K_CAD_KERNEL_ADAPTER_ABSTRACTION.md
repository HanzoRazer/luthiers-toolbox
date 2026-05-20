# MRP Dev Order 5K — CAD Kernel Adapter Abstraction Handoff

**Date:** 2026-05-19  
**Author:** Claude (MRP Dev Order 5K)  
**Status:** COMPLETE

---

## Summary

Implemented formal adapter abstraction layer for CAD kernels, preventing kernel-native ontology leakage into the semantic layers. The adapter is now a MECHANICAL EXECUTOR with a narrow contract — it executes geometric primitives only and has no semantic authority.

**Key outcome:** The topology_builder can swap CAD kernels (Mock, OCC, CadQuery, build123d) without any kernel-specific terminology or concepts polluting the semantic infrastructure.

---

## Scope

### In Scope (Completed)

- KernelAdapterInterface protocol definition
- BaseKernelAdapter abstract base class
- Kernel-agnostic data types (AdapterPoint3D, AdapterBoundingBox, etc.)
- MockKernelAdapter updated to implement formal interface
- Adapter registry with capability declarations
- 34 tests covering protocol compliance, operations, registry, and isolation

### Out of Scope (Per 5K Guardrails)

- No real kernel adapters (OCC, CadQuery) — just interface
- No topology_builder integration changes
- No translator changes (handled by MRP-5J)
- No semantic inference in adapters

---

## Deliverables

| Deliverable | Location | Purpose |
|-------------|----------|---------|
| interface.py | app/cam/topology_builder/kernel_adapters/ | Protocol + data types |
| registry.py | app/cam/topology_builder/kernel_adapters/ | Adapter discovery |
| mock_adapter.py | app/cam/topology_builder/kernel_adapters/ | Updated implementation |
| __init__.py | app/cam/topology_builder/kernel_adapters/ | Public exports |
| test_kernel_adapter_interface.py | tests/cam/ | 34 tests |
| MRP_5K_CAD_KERNEL_ADAPTER_ABSTRACTION.md | docs/handoffs/ | This document |

---

## Architecture

### Architectural Chain (MRP-5H through 5K)

```
topology_builder        → CONSTRUCTS topology
topology_validation     → EVALUATES topology (returns CertifiedTopology)
translators            → SERIALIZE topology (accepts ONLY CertifiedTopology)
kernel_adapters        → EXECUTE geometric primitives ONLY
```

The adapter is DOWNSTREAM of all semantic decisions.

### Adapter Contract

**Adapters MUST:**
- Execute geometric operations only
- Return kernel-agnostic result types
- Remain stateless between operations

**Adapters MUST NOT:**
- Infer semantics from geometry
- Repair topology silently
- Reinterpret morphology
- Normalize geometry beyond precision
- Classify runtime feasibility
- Introduce kernel-native ontology into results
- Consume or produce CertifiedTopology
- Bypass validation

### Kernel-Agnostic Types

| Type | Purpose |
|------|---------|
| AdapterPoint3D | 3D coordinate (replaces gp_Pnt, Vector, etc.) |
| AdapterBoundingBox | Geometry bounds |
| AdapterGeometryHandle | Opaque handle to kernel geometry |
| AdapterResult | Operation outcome with optional handle |
| AdapterValidationResult | Validation outcome (closed, manifold) |
| AdapterExportResult | Export outcome with bytes content |
| AdapterOperationType | Enum for audit/logging |
| AdapterErrorCode | Kernel-agnostic error classification |

### Protocol Definition

```python
@runtime_checkable
class KernelAdapterInterface(Protocol):
    @property
    def adapter_id(self) -> str: ...
    
    @property
    def kernel_name(self) -> str: ...
    
    @property
    def is_available(self) -> bool: ...
    
    def create_face_from_points(self, points: List[AdapterPoint3D]) -> AdapterResult: ...
    def extrude_face(self, face_handle, direction, distance) -> AdapterResult: ...
    def loft_profiles(self, profile_handles: List[AdapterGeometryHandle]) -> AdapterResult: ...
    def validate_closed(self, geometry_handle) -> AdapterValidationResult: ...
    def validate_manifold(self, geometry_handle) -> AdapterValidationResult: ...
    def get_bounding_box(self, geometry_handle) -> Optional[AdapterBoundingBox]: ...
    def export_step(self, geometry_handle, header_metadata=None) -> AdapterExportResult: ...
```

### Adapter Registry

```python
# Get available adapters
adapters = list_available_adapters()

# Get specific adapter
adapter = get_adapter("mock")

# Get mock with configuration (for testing)
adapter = get_mock_adapter(should_fail_create=True)

# Query by capability
extrude_adapters = registry.list_by_capability(AdapterCapability.EXTRUDE)
```

### Maturity Levels

| Level | Description |
|-------|-------------|
| MOCK | Testing only, no real kernel |
| EXPERIMENTAL | In development, may change |
| CANDIDATE | Feature complete, under validation |
| STABLE | Production ready |

---

## Test Coverage

34 tests in 7 categories:

| Category | Tests | Coverage |
|----------|-------|----------|
| Protocol Compliance | 3 | Interface implementation |
| Data Types | 4 | Point3D, BoundingBox, Handle |
| Mock Operations | 12 | Create, extrude, loft, validate, export |
| Operation Recording | 3 | Test utilities |
| Registry | 7 | Discovery, capability filtering |
| Declaration | 1 | Capability checking |
| Isolation | 4 | No kernel ontology leakage |

All tests pass.

---

## Isolation Guarantees

The isolation tests verify:

1. **Result types are kernel-agnostic** — No `occ_shape`, `cadquery_solid`, etc.
2. **Validation results use adapter enums** — Not kernel-specific status codes
3. **Export produces bytes** — Not kernel-specific stream types
4. **Bounding box uses AdapterPoint3D** — Not gp_Pnt, Vector, etc.

---

## Future Adapter Implementation Guide

When implementing a real kernel adapter (e.g., OCCAdapter):

1. **Inherit from BaseKernelAdapter**
2. **Implement all abstract methods**
3. **Convert kernel-native types at adapter boundary**
4. **Store kernel references in AdapterGeometryHandle.kernel_ref** (internal only)
5. **Register in _register_default_adapters()**
6. **Do NOT add semantic logic** — that belongs in cad_semantics

Example skeleton:

```python
class OCCAdapter(BaseKernelAdapter):
    def __init__(self):
        super().__init__(adapter_id="occ", kernel_name="OpenCASCADE")
    
    @property
    def is_available(self) -> bool:
        try:
            import OCC.Core.BRepBuilderAPI
            return True
        except ImportError:
            return False
    
    def create_face_from_points(self, points: List[AdapterPoint3D]) -> AdapterResult:
        # Convert AdapterPoint3D → gp_Pnt (internal only)
        # Execute OCC operation
        # Wrap result in AdapterGeometryHandle (kernel_ref holds TopoDS_Shape)
        # Return AdapterResult (no OCC types exposed)
        ...
```

---

## Connection to MRP-5I and MRP-5J

**MRP-5I (Topology Validation):**
- CertifiedTopology ensures only validated topology proceeds

**MRP-5J (STEP Translator):**
- AcousticStepTranslator accepts ONLY CertifiedTopology
- Produces governed translation artifacts

**MRP-5K (This Sprint):**
- Kernel adapters execute geometric primitives
- No semantic authority — downstream of all decisions
- Prevents kernel ontology from polluting semantic layers

Together these three sprints establish the complete semantic-execution boundary.

---

## Verification

```bash
cd services/api
python -m pytest tests/cam/test_kernel_adapter_interface.py -v
# 34 passed
```

---

## Next Steps

1. **MRP-5L:** Wire kernel adapters into topology_builder
2. **MRP-5M:** Implement OCCAdapter (when OCC available)
3. **MRP-5N:** Implement CadQueryAdapter
4. **MRP-5O:** Adapter selection policy (based on capability, maturity)
