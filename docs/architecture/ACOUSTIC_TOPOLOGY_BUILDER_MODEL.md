# Acoustic Topology Builder Model

**Sprint:** MRP-5G  
**Status:** RECOMMENDED_PENDING_MRP_5H_VALIDATION  
**Type:** Architectural Research

---

## Purpose

Define the proposed Topology Builder layer for acoustic CAD generation. This layer sits between cad_semantics and translators, owning topology construction responsibilities.

---

## Recommendation

**Introduce a dedicated Topology Builder layer.**

**Status:** RECOMMENDED_PENDING_MRP_5H_VALIDATION

**Rationale:**
- Topology construction is semantically heavy (continuity, lofting, shell closure)
- Translators should serialize, not construct
- Separation enables kernel-agnostic topology validation
- Multiple translators can share topology construction

---

## Layer Position

```
cad_semantics (semantic descriptors)
        │
        │ SEMANTIC INPUT
        ▼
┌───────────────────────────────────┐
│       TOPOLOGY BUILDER LAYER      │
│                                   │
│  Responsibilities:                │
│  - Shell construction             │
│  - Loft generation                │
│  - Continuity enforcement         │
│  - Rim closure                    │
│  - Topology validation            │
│                                   │
│  Output: Validated topology       │
└───────────────────┬───────────────┘
                    │
                    │ TOPOLOGY OUTPUT
                    ▼
        Translator (serialization)
```

---

## Why Not Inside Translators?

### Problem: Translator Scope Creep

If topology construction lives inside translators:

```
STEP Translator
  ├── Parse Export Object
  ├── Validate cad_semantics
  ├── [TOPOLOGY] Construct shell from profile
  ├── [TOPOLOGY] Generate loft surfaces
  ├── [TOPOLOGY] Enforce G1 continuity
  ├── [TOPOLOGY] Validate closed shell
  ├── Serialize to STEP Part 21
  └── Embed provenance
```

Problems:
1. **Duplication** — Each translator reimplements topology logic
2. **Testing** — Topology bugs mixed with serialization bugs
3. **Kernel coupling** — Translator becomes kernel-dependent
4. **Semantic drift** — Topology decisions hidden inside format code

### Solution: Separated Concerns

```
Topology Builder
  ├── Construct shell from profile + semantics
  ├── Generate loft surfaces
  ├── Enforce continuity
  ├── Validate topology
  └── Output: Validated TopologyResult

STEP Translator
  ├── Receive TopologyResult
  ├── Serialize to STEP Part 21
  └── Embed provenance
```

Benefits:
1. **Single implementation** — Topology logic in one place
2. **Testable** — Topology validation independent of format
3. **Kernel-agnostic** — Builder can swap kernels behind adapter
4. **Clear boundaries** — Semantics → Topology → Serialization

---

## Topology Builder Responsibilities

### MUST Own

| Responsibility | Description |
|----------------|-------------|
| Shell construction | Build closed 3D shell from 2D profile + depth |
| Loft generation | Interpolate between depth profiles |
| Continuity enforcement | Achieve G0/G1 at junctions |
| Rim closure | Connect top/back plates via rim |
| Topology validation | Verify closed, manifold, no self-intersection |
| Geometry preservation | Verify BOE points in output |

### MUST NOT Own

| Responsibility | Owner |
|----------------|-------|
| Semantic interpretation | cad_semantics |
| Format encoding | Translator |
| Provenance embedding | Translator |
| Entity ordering | Translator |
| Kernel selection | Adapter layer |

---

## Proposed Interface

### Input: TopologyRequest

```python
@dataclass
class TopologyRequest:
    """Input to topology builder."""
    
    # Approved geometry (from BOE)
    outline_points: List[Tuple[float, float]]
    voids: List[List[Tuple[float, float]]]
    
    # Semantic descriptors (from cad_semantics)
    body_category: BodyCategory
    thickness: ThicknessSemantics
    side_profile: Optional[SideProfileSemantics]
    plate_relationship: Optional[PlateRelationshipSemantics]
    continuity_target: ContinuityTarget
    
    # Builder options
    tolerance_mm: float = 0.001
    validation_level: ValidationLevel = ValidationLevel.STRICT
```

### Output: TopologyResult

```python
@dataclass
class TopologyResult:
    """Output from topology builder."""
    
    success: bool
    
    # Topology data (kernel-agnostic representation)
    shell: Optional[ShellTopology]
    
    # Validation results
    is_closed: bool
    is_manifold: bool
    continuity_achieved: ContinuityTarget
    geometry_preserved: bool
    
    # Errors/warnings
    errors: List[TopologyError]
    warnings: List[TopologyWarning]
    
    # Metrics
    face_count: int
    edge_count: int
    vertex_count: int
```

### Builder Interface

```python
class TopologyBuilder(Protocol):
    """Abstract topology builder interface."""
    
    def build(self, request: TopologyRequest) -> TopologyResult:
        """Construct topology from request."""
        ...
    
    def validate(self, topology: ShellTopology) -> ValidationResult:
        """Validate existing topology."""
        ...
    
    def get_capabilities(self) -> BuilderCapabilities:
        """Report what this builder can construct."""
        ...
```

---

## Builder Capabilities

### PROTOTYPE Tier (MRP-5H Target)

| Capability | Status |
|------------|--------|
| Flat extrusion | SUPPORTED |
| Uniform rim depth | SUPPORTED |
| G0 continuity | SUPPORTED |
| Closed shell validation | SUPPORTED |

### PRODUCTION Tier (MRP-5J+ Target)

| Capability | Status |
|------------|--------|
| Tapered rim depth | REQUIRES_LOFT |
| Radiused back | REQUIRES_SURFACE |
| G1 continuity | REQUIRES_KERNEL |
| Manifold validation | REQUIRES_KERNEL |

---

## Topology Construction Strategies

### Strategy 1: Flat Extrusion (Current STEP)

```
Profile (z=0) → Extrude → Shell (z=0 to z=thickness)
```

Supports:
- `body_category: flat_body`
- `side_profile.type: uniform`
- `plate_relationship: flat/flat`

### Strategy 2: Variable Extrusion (Future)

```
Profile (z=0) → Per-point depth → Shell with variable z_max
```

Supports:
- `body_category: acoustic_flat_top`
- `side_profile.type: tapered`
- `plate_relationship: flat/flat`

### Strategy 3: Lofted Shell (Future)

```
Profile + depth_profile → Loft interpolation → Shell
Back plate as radiused surface
```

Supports:
- `body_category: acoustic_flat_top`
- `side_profile.type: tapered`
- `plate_relationship: flat/radiused`

### Strategy 4: Carved Surfaces (Research Only)

```
Profile + arch_profiles → NURBS surface → Shell
```

Supports:
- `body_category: archtop`
- Complex arch profiles

---

## Validation Requirements

### PROTOTYPE Tier

| Check | Requirement |
|-------|-------------|
| Shell closure | All edges have 2 adjacent faces |
| No gaps | Edge gap < 0.01mm |
| Geometry preservation | BOE points within 0.001mm |

### PRODUCTION Tier

| Check | Requirement |
|-------|-------------|
| Shell closure | Verified by kernel |
| Manifold | No non-manifold edges |
| No self-intersection | Kernel verified |
| Continuity | G1 within 1° at junctions |
| Geometry preservation | All BOE points in output |

---

## Kernel Adapter Pattern

### Why Adapter?

```
Topology Builder
      │
      │ calls
      ▼
┌─────────────────────┐
│   Kernel Adapter    │  ← Abstract interface
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
OpenCascade   CadQuery
  Adapter      Adapter
```

Benefits:
- Kernel selection doesn't affect builder interface
- Testing can use mock kernel
- Kernel can be swapped without topology logic changes
- Failure isolation — kernel crash doesn't corrupt state

### Adapter Interface

```python
class KernelAdapter(Protocol):
    """Abstract CAD kernel adapter."""
    
    def create_face(self, points: List[Point3D]) -> FaceHandle:
        ...
    
    def create_shell(self, faces: List[FaceHandle]) -> ShellHandle:
        ...
    
    def loft(self, profiles: List[WireHandle]) -> ShellHandle:
        ...
    
    def validate_closed(self, shell: ShellHandle) -> bool:
        ...
    
    def export_step(self, shell: ShellHandle) -> bytes:
        ...
```

---

## Error Handling

### Builder Errors (Blocking)

| Error | Cause | Action |
|-------|-------|--------|
| `OpenShellError` | Failed to close shell | REJECT |
| `GeometryMutationError` | BOE point not in output | REJECT |
| `ContinuityFailure` | Cannot achieve target | REJECT |
| `SelfIntersectionError` | Topology self-intersects | REJECT |

### Builder Warnings

| Warning | Cause | Action |
|---------|-------|--------|
| `ContinuityDegraded` | G1 requested, G0 achieved | LOG + CONTINUE |
| `LowResolutionInput` | Few profile points | LOG + CONTINUE |

---

## MRP-5H Validation Plan

### Prototype Scope

1. Implement flat extrusion builder
2. Validate BOE geometry preservation
3. Validate closed shell output
4. Demonstrate translator consumption

### Success Criteria

- [ ] Builder produces valid topology from semantic input
- [ ] Translator serializes builder output without modification
- [ ] BOE coordinates verifiable in final output
- [ ] Clear error on invalid input

---

## Related Documents

- `TOPOLOGY_AUTHORITY_CHAIN.md` — Authority hierarchy
- `ACOUSTIC_TOPOLOGY_RUNTIME_RULES.md` — Runtime constraints
- `TOPOLOGY_FAILURE_CLASSIFICATION.md` — Error classification
- `CAD_KERNEL_BOUNDARY_ANALYSIS.md` — Kernel evaluation
