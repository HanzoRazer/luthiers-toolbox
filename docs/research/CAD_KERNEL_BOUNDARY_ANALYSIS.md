# CAD Kernel Boundary Analysis

**Sprint:** MRP-5G  
**Status:** RESEARCH COMPLETE  
**Type:** Architectural Research

---

## Purpose

Analyze CAD kernel integration boundaries for acoustic topology generation. This document defines evaluation criteria and architectural placement without selecting a specific kernel.

---

## Core Principle

```
CAD kernels are IMPLEMENTATION DEPENDENCIES,
not SEMANTIC AUTHORITIES.

Kernels must be:
- Isolated behind adapters
- Swappable without semantic changes
- Failure-transparent
- Not exposed to higher layers
```

---

## Kernel Role in Architecture

### What Kernels DO

```
┌─────────────────────────────────────────┐
│           CAD KERNEL SCOPE              │
│                                         │
│  - B-rep primitive construction         │
│  - NURBS/spline evaluation              │
│  - Boolean operations                   │
│  - Surface lofting                      │
│  - Topology validation (closed, manifold) │
│  - Format export (STEP, IGES)           │
│                                         │
└─────────────────────────────────────────┘
```

### What Kernels DO NOT DO

```
┌─────────────────────────────────────────┐
│         NOT KERNEL SCOPE                │
│                                         │
│  ✗ Semantic interpretation              │
│  ✗ Authority decisions                  │
│  ✗ Validation policy                    │
│  ✗ Error classification                 │
│  ✗ Provenance embedding                 │
│  ✗ Tier selection (PROTOTYPE/PRODUCTION)│
│                                         │
└─────────────────────────────────────────┘
```

---

## Candidate Kernels

### OpenCASCADE (OCCT)

**Type:** Full CAD kernel (C++)

**Pros:**
- Industry-standard B-rep kernel
- Complete STEP/IGES support
- Robust topology operations
- Extensive documentation
- Used by FreeCAD, Blender, etc.

**Cons:**
- Large dependency (~100MB+)
- Complex build on Windows
- Steep learning curve
- C++ bindings required

**Python Access:**
- `pythonocc-core` package
- `OCP` (newer binding)

### CadQuery

**Type:** Python CAD library (OCCT-based)

**Pros:**
- Pythonic API
- Built on OCCT
- Active development
- Good documentation
- pip installable

**Cons:**
- Still large dependency (OCCT underneath)
- Windows deployment complex
- Version compatibility issues

**License:** Apache 2.0

### build123d

**Type:** Python CAD library (OCCT-based)

**Pros:**
- Modern Python API
- Builder pattern (fluent)
- Jupyter integration
- Active community

**Cons:**
- Newer, less proven
- OCCT dependency
- API still evolving

**License:** Apache 2.0

### Custom Topology Builder

**Type:** In-house implementation

**Pros:**
- No external dependency
- Full control
- Minimal footprint
- Tailored to needs

**Cons:**
- Significant development effort
- Limited operations
- No kernel validation guarantees
- Must implement STEP export

**Viability:** For flat extrusion only; insufficient for lofting

---

## Evaluation Criteria

### 1. Dependency Weight

| Criterion | Weight | Notes |
|-----------|--------|-------|
| Install size | MEDIUM | Affects deployment |
| Compile requirements | HIGH | Windows build complexity |
| Runtime memory | MEDIUM | Server resource usage |
| Transitive dependencies | MEDIUM | Supply chain risk |

### 2. Windows Deployability

| Criterion | Weight | Notes |
|-----------|--------|-------|
| pip install works | HIGH | Must work on Windows |
| Pre-built wheels | HIGH | No compile required |
| Path handling | MEDIUM | Windows path quirks |
| Virtual env support | HIGH | Isolation needed |

### 3. Deterministic Output

| Criterion | Weight | Notes |
|-----------|--------|-------|
| Same input → same output | CRITICAL | Regression testing |
| Floating-point stability | HIGH | 6 decimal precision |
| Entity ordering | MEDIUM | STEP determinism |
| No random behavior | CRITICAL | Auditable results |

### 4. STEP Support

| Criterion | Weight | Notes |
|-----------|--------|-------|
| AP203 export | CRITICAL | Required format |
| AP214 export | MEDIUM | Future option |
| Valid Part 21 | CRITICAL | Correct syntax |
| Custom header | HIGH | Provenance embedding |

### 5. Topology Validation

| Criterion | Weight | Notes |
|-----------|--------|-------|
| Closed shell check | CRITICAL | Shell closure |
| Manifold check | HIGH | Topology quality |
| Self-intersection | HIGH | Geometry validity |
| Gap detection | MEDIUM | Continuity checking |

### 6. Licensing

| Criterion | Weight | Notes |
|-----------|--------|-------|
| Open source | HIGH | No licensing fees |
| Attribution requirements | LOW | Acceptable |
| Copyleft restrictions | MEDIUM | GPL concerns |
| Commercial use | HIGH | Must be allowed |

### 7. Adapter Isolation

| Criterion | Weight | Notes |
|-----------|--------|-------|
| Clean interface | HIGH | Boundary enforcement |
| Error transparency | HIGH | Failure classification |
| Mock-ability | HIGH | Testing without kernel |
| Swap-ability | MEDIUM | Kernel change possible |

### 8. Failure Transparency

| Criterion | Weight | Notes |
|-----------|--------|-------|
| Clear error messages | HIGH | Debugging |
| Exception types | MEDIUM | Classification |
| Partial results | LOW | Useful but optional |
| Recovery options | LOW | Nice to have |

---

## Evaluation Matrix Template

| Kernel | Dep Weight | Windows | Determinism | STEP | Validation | License | Isolation | Failure |
|--------|------------|---------|-------------|------|------------|---------|-----------|---------|
| OpenCASCADE | ? | ? | ? | ? | ? | ? | ? | ? |
| CadQuery | ? | ? | ? | ? | ? | ? | ? | ? |
| build123d | ? | ? | ? | ? | ? | ? | ? | ? |
| Custom | ? | ? | ? | ? | ? | ? | ? | ? |

**Legend:** ✓ Good | △ Acceptable | ✗ Poor | ? Not evaluated

**Status:** Evaluation deferred to MRP-5H prototype

---

## Adapter Architecture

### Interface Definition

```python
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Point3D:
    x: float
    y: float
    z: float

@dataclass
class ShellResult:
    success: bool
    handle: Optional[object]  # Kernel-specific handle
    error: Optional[str]

class CADKernelAdapter(ABC):
    """Abstract CAD kernel adapter interface."""
    
    @abstractmethod
    def create_face_from_wire(
        self, points: List[Point3D]
    ) -> ShellResult:
        """Create planar face from closed wire."""
        ...
    
    @abstractmethod
    def extrude_face(
        self, face_handle: object, direction: Point3D, distance: float
    ) -> ShellResult:
        """Extrude face to create solid."""
        ...
    
    @abstractmethod
    def loft_profiles(
        self, profiles: List[List[Point3D]]
    ) -> ShellResult:
        """Loft between multiple profiles."""
        ...
    
    @abstractmethod
    def validate_closed(self, shell_handle: object) -> bool:
        """Check if shell is closed."""
        ...
    
    @abstractmethod
    def validate_manifold(self, shell_handle: object) -> bool:
        """Check if shell is manifold."""
        ...
    
    @abstractmethod
    def export_step(
        self, shell_handle: object, header: dict
    ) -> bytes:
        """Export to STEP format with custom header."""
        ...
```

### Implementation Pattern

```python
class CadQueryAdapter(CADKernelAdapter):
    """CadQuery implementation of kernel adapter."""
    
    def __init__(self):
        try:
            import cadquery as cq
            self._cq = cq
        except ImportError as e:
            raise KernelNotAvailable("CadQuery not installed") from e
    
    def create_face_from_wire(self, points: List[Point3D]) -> ShellResult:
        try:
            # CadQuery-specific implementation
            vertices = [(p.x, p.y, p.z) for p in points]
            wire = self._cq.Workplane("XY").polyline(vertices).close()
            face = wire.val()
            return ShellResult(success=True, handle=face, error=None)
        except Exception as e:
            return ShellResult(success=False, handle=None, error=str(e))
    
    # ... other methods
```

### Mock Adapter (Testing)

```python
class MockKernelAdapter(CADKernelAdapter):
    """Mock adapter for testing without real kernel."""
    
    def __init__(self, should_fail: bool = False):
        self._should_fail = should_fail
        self._operations = []
    
    def create_face_from_wire(self, points: List[Point3D]) -> ShellResult:
        self._operations.append(("create_face", points))
        if self._should_fail:
            return ShellResult(success=False, handle=None, error="Mock failure")
        return ShellResult(success=True, handle={"type": "mock_face"}, error=None)
    
    def get_operations(self) -> List[Tuple]:
        """Return list of operations for test verification."""
        return self._operations
```

---

## Inside vs Outside Repository

### Inside Repository (Required)

| Component | Reason |
|-----------|--------|
| Adapter interface | Contract definition |
| Adapter implementations | Integration code |
| Mock adapter | Testing |
| Error translation | Failure classification |

### Outside Repository (Dependency)

| Component | Reason |
|-----------|--------|
| CAD kernel library | External package |
| Kernel binaries | Too large to vendor |
| Kernel documentation | External reference |

### Behind Adapter (Hidden)

| Component | Reason |
|-----------|--------|
| Kernel-specific handles | Implementation detail |
| Kernel-specific errors | Translated to our types |
| Kernel-specific options | Wrapped in our config |

---

## Selection Timeline

| Sprint | Action |
|--------|--------|
| MRP-5G | Define evaluation criteria (this doc) |
| MRP-5H | Evaluate candidates with prototype |
| MRP-5I | Select kernel for validation prototype |
| MRP-5J | Production integration |

### Selection Decision Point

Kernel selection requires:
- [ ] MRP-5H prototype validates adapter pattern
- [ ] Candidate evaluation matrix completed
- [ ] Windows deployment verified
- [ ] Determinism verified
- [ ] STEP export verified

---

## Related Documents

- `TOPOLOGY_AUTHORITY_CHAIN.md` — Kernel position in hierarchy
- `ACOUSTIC_TOPOLOGY_BUILDER_MODEL.md` — Builder-kernel relationship
- `ACOUSTIC_TOPOLOGY_RUNTIME_RULES.md` — Runtime constraints
