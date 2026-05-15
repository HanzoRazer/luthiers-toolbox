# MRP Dev Order 5H — Acoustic Topology Builder Prototype Handoff

**Date:** 2026-05-14  
**Dev Order:** MRP-5H  
**Status:** COMPLETE

---

## Summary

MRP-5H implemented the Acoustic Topology Builder prototype layer, validating the architectural pattern established in MRP-5G research:

1. **TopologyBuilder Pattern** — Abstract builder with acoustic specialization
2. **Runtime Classification** — TopologyRuntimeSupport enum with classification logic
3. **Contract Objects** — TopologyRequest, TopologyResult, PrototypeTopologyObject
4. **Validation Framework** — Geometry preservation, shell closure, continuity
5. **Kernel Adapter Pattern** — MockKernelAdapter for testing
6. **Exception Hierarchy** — Structured error classification per MRP-5G spec

**Sprint Type:** Prototype code (no production CAD kernel)

---

## Deliverables

### 1. Package Structure

**Location:** `services/api/app/cam/topology_builder/`

```
topology_builder/
├── __init__.py           # Package exports
├── contracts.py          # Data contracts (request/result/topology)
├── runtime_support.py    # Runtime classification
├── builder.py            # TopologyBuilder + AcousticTopologyBuilder
├── validation.py         # Validation functions
├── exceptions.py         # Exception hierarchy
└── kernel_adapters/
    ├── __init__.py
    └── mock_adapter.py   # Mock kernel for testing
```

### 2. Core Contracts

**TopologyRequest:**
```python
@dataclass
class TopologyRequest:
    request_id: str
    body_category: str
    tier: TopologyTier = TopologyTier.PROTOTYPE
    profile_stack: Optional[ProfileStack] = None
    thickness_mm: float = 3.0
    continuity_targets: Dict[str, ContinuityLevel] = field(default_factory=dict)
    boe_geometry: Optional[Dict[str, Any]] = None
    cad_semantics: Optional[Dict[str, Any]] = None
```

**TopologyResult:**
```python
@dataclass
class TopologyResult:
    request_id: str
    success: bool
    topology: Optional[PrototypeTopologyObject] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_classification: Optional[str] = None
```

**PrototypeTopologyObject:**
```python
@dataclass
class PrototypeTopologyObject:
    request_id: str
    tier: TopologyTier
    shells: List[ShellDescriptor] = field(default_factory=list)
    kernel_handle: Optional[Any] = None
    warnings: List[str] = field(default_factory=list)
```

### 3. Runtime Classification

**TopologyRuntimeSupport Enum:**
```python
class TopologyRuntimeSupport(str, Enum):
    SUPPORTED_PROTOTYPE = "SUPPORTED_PROTOTYPE"
    PARTIAL_PROTOTYPE = "PARTIAL_PROTOTYPE"
    UNSUPPORTED_RUNTIME = "UNSUPPORTED_RUNTIME"
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"
```

**Body Category Support:**
| Category | Support Level |
|----------|---------------|
| flat_body | SUPPORTED_PROTOTYPE |
| acoustic_flat_top | SUPPORTED_PROTOTYPE |
| hollow_electric | PARTIAL_PROTOTYPE |
| archtop | RESEARCH_REQUIRED |
| acoustic_arched_top | RESEARCH_REQUIRED |
| resonator | RESEARCH_REQUIRED |
| unknown | UNSUPPORTED_RUNTIME |

### 4. Exception Hierarchy

```
TopologyBuildError (base)
├── GeometryMutationError      # BLOCKING - BOE point drift
├── UnsupportedTopologyError   # UNSUPPORTED_RUNTIME
├── ContinuityValidationError  # MAJOR/BLOCKING by tier
├── ShellClosureError          # BLOCKING
├── ProfileValidationError     # MAJOR/BLOCKING
└── KernelAdapterError         # BLOCKING
```

### 5. Validation Functions

| Function | Purpose |
|----------|---------|
| `validate_topology_request()` | Pre-build request validation |
| `validate_shell_closure()` | Open shell detection (BLOCKING) |
| `validate_shell_manifold()` | Non-manifold detection (tier-dependent) |
| `validate_geometry_preservation()` | BOE point drift detection |
| `validate_continuity()` | Junction continuity requirements |
| `validate_profile_data()` | Profile stack integrity |
| `validate_topology_result()` | Post-build result validation |

### 6. Kernel Adapter Pattern

**MockKernelAdapter Features:**
- Records all operations for test verification
- Configurable failure modes for error path testing
- Mock STEP export for serialization testing
- No external dependencies

---

## Test Coverage

**Location:** `services/api/tests/cam/`

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_topology_builder.py` | 22 | PASS |
| `test_topology_runtime_classification.py` | 22 | PASS |
| `test_topology_validation.py` | 29 | PASS |
| **Total** | **73** | **ALL PASS** |

---

## Key Architectural Decisions

### 1. PROTOTYPE Tier Focus

MRP-5H builds for PROTOTYPE tier only:
- G0 continuity acceptable
- Warnings on quality issues instead of blocking
- No real CAD kernel required
- Clear "prototype" marking on output

### 2. No Silent Degradation

Unsupported configurations fail with clear error:
```python
if not can_generate_topology(support):
    return TopologyResult.failure_result(
        request_id=request.request_id,
        error_type="UnsupportedTopologyError",
        error_message=reason,
        classification="UNSUPPORTED_RUNTIME",
    )
```

### 3. Geometry Preservation Enforcement

BOE geometry is immutable. Any drift beyond 1 micron tolerance raises:
```python
raise GeometryMutationError(
    message=f"Point {i} drifted {drift:.6f}mm during construction",
    original_point=[orig.x, orig.y, orig.z],
    output_point=[out.x, out.y, out.z],
    drift_mm=drift,
)
```

### 4. Kernel Adapter Isolation

Kernel operations are isolated behind adapter interface:
```python
class KernelAdapter(Protocol):
    def create_face_from_points(self, points: List[Point3D]) -> Any: ...
    def extrude_face(self, face_handle: Any, direction: Point3D, distance: float) -> Any: ...
    def validate_closed(self, shell_handle: Any) -> bool: ...
    def validate_manifold(self, shell_handle: Any) -> bool: ...
```

---

## What Was NOT Built (By Design)

Per MRP-5G architecture:

- **Real CAD kernel integration** — Deferred to MRP-5K
- **Lofting operations** — PROTOTYPE uses flat extrusion only
- **G1/G2 continuity enforcement** — PROTOTYPE allows G0
- **STEP export** — Mock export only, real export in MRP-5J
- **Production tier validation** — PROTOTYPE tier focus

---

## Usage Example

```python
from app.cam.topology_builder import (
    AcousticTopologyBuilder,
    TopologyRequest,
    TopologyTier,
)

# Create builder (optionally with kernel adapter)
builder = AcousticTopologyBuilder()

# Create request
request = TopologyRequest(
    request_id="guitar-001",
    body_category="acoustic_flat_top",
    tier=TopologyTier.PROTOTYPE,
    thickness_mm=3.0,
)

# Check support before building
support = builder.supports(request)
if support == TopologyRuntimeSupport.UNSUPPORTED_RUNTIME:
    print(f"Cannot build: {support}")
else:
    result = builder.build(request)
    if result.success:
        print(f"Built topology with {result.topology.shell_count} shells")
    else:
        print(f"Build failed: {result.error_message}")
```

---

## Files Created

### Code

| File | Purpose |
|------|---------|
| `app/cam/topology_builder/__init__.py` | Package exports |
| `app/cam/topology_builder/contracts.py` | Data contracts |
| `app/cam/topology_builder/runtime_support.py` | Runtime classification |
| `app/cam/topology_builder/builder.py` | Builder implementation |
| `app/cam/topology_builder/validation.py` | Validation functions |
| `app/cam/topology_builder/exceptions.py` | Exception hierarchy |
| `app/cam/topology_builder/kernel_adapters/__init__.py` | Adapter exports |
| `app/cam/topology_builder/kernel_adapters/mock_adapter.py` | Mock kernel |

### Tests

| File | Purpose |
|------|---------|
| `tests/cam/test_topology_builder.py` | Builder tests |
| `tests/cam/test_topology_runtime_classification.py` | Classification tests |
| `tests/cam/test_topology_validation.py` | Validation tests |

### Documentation

| File | Purpose |
|------|---------|
| `docs/handoffs/MRP_5H_ACOUSTIC_TOPOLOGY_BUILDER_PROTOTYPE.md` | This document |

---

## Future Implementation Roadmap

| Sprint | Focus | Depends On |
|--------|-------|------------|
| MRP-5H | Topology builder prototype | MRP-5G (this sprint) |
| MRP-5I | Shell validation prototype | MRP-5H |
| MRP-5J | Acoustic STEP runtime prototype | MRP-5H, MRP-5I |
| MRP-5K | CAD kernel adapter abstraction | MRP-5J |
| MRP-5L | Continuity verification corpus | MRP-5K |

---

## Definition of Done

✅ TopologyBuilder abstract class defined  
✅ AcousticTopologyBuilder implemented  
✅ TopologyRuntimeSupport classification working  
✅ Contract objects (request/result/topology) defined  
✅ Exception hierarchy per MRP-5G spec  
✅ Validation functions implemented  
✅ MockKernelAdapter for testing  
✅ 73 tests passing  
✅ Handoff exists

---

## Related Documents

- `MRP_5G_ACOUSTIC_TOPOLOGY_BOUNDARY_RESEARCH.md` — Research foundation
- `TOPOLOGY_AUTHORITY_CHAIN.md` — Authority hierarchy
- `ACOUSTIC_TOPOLOGY_BUILDER_MODEL.md` — Builder pattern rationale
- `ACOUSTIC_TOPOLOGY_RUNTIME_RULES.md` — Runtime constraints
- `TOPOLOGY_FAILURE_CLASSIFICATION.md` — Error classification
- `CAD_KERNEL_BOUNDARY_ANALYSIS.md` — Kernel adapter rationale
