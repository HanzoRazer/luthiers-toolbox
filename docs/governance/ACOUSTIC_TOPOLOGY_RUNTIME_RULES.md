# Acoustic Topology Runtime Rules

**Sprint:** MRP-5G  
**Status:** ACTIVE  
**Authority:** CAD Topology Governance

---

## Purpose

Define runtime rules for acoustic topology generation. These rules extend the semantic governance from MRP-5E/5F with runtime-specific constraints and two-tier (PROTOTYPE/PRODUCTION) requirements.

---

## Reference Documents

This document extends:
- `ACOUSTIC_TOPOLOGY_CONTINUITY_MODEL.md` (MRP-5E) — Continuity theory
- `ACOUSTIC_CAD_SEMANTIC_RULES.md` (MRP-5F) — Semantic authority
- `ACOUSTIC_RUNTIME_LIMITATIONS.md` (MRP-5F) — Current limitations

---

## Two-Tier Requirements

### Tier 1: PROTOTYPE

**Purpose:** Safe experimentation with acoustic topology.

**Characteristics:**
- Relaxed continuity enforcement
- Basic validation only
- Clear "prototype" marking in output
- Not for manufacturing

**Use Cases:**
- Algorithm development
- Visualization
- Design iteration
- Feasibility testing

### Tier 2: PRODUCTION

**Purpose:** Manufacturing-ready acoustic topology.

**Characteristics:**
- Strict continuity enforcement
- Full validation suite
- Kernel-verified geometry
- Manufacturing tolerance compliance

**Use Cases:**
- CNC toolpath generation
- Manufacturing documentation
- Customer deliverables

---

## Continuity Requirements by Tier

### Junction: Rim ↔ Top Plate

| Tier | Target | Tolerance | Failure Action |
|------|--------|-----------|----------------|
| PROTOTYPE | G0 acceptable | 0.1mm gap | WARNING |
| PRODUCTION | G1 required | 1° angle | BLOCKING |

### Junction: Rim ↔ Back Plate

| Tier | Target | Tolerance | Failure Action |
|------|--------|-----------|----------------|
| PROTOTYPE | G0 acceptable | 0.1mm gap | WARNING |
| PRODUCTION | G1 required | 1° angle | BLOCKING |

### Junction: Neck Transition

| Tier | Target | Tolerance | Failure Action |
|------|--------|-----------|----------------|
| PROTOTYPE | G0 | 0.5mm gap | WARNING |
| PRODUCTION | G0 | 0.1mm gap | BLOCKING |

### Junction: Cutaway (Future)

| Tier | Target | Tolerance | Failure Action |
|------|--------|-----------|----------------|
| PROTOTYPE | G0 | 1.0mm gap | WARNING |
| PRODUCTION | G1 | 1° angle | BLOCKING |

---

## Shell Closure Requirements

### PROTOTYPE Tier

```
All edges must have exactly 2 adjacent faces.
Gaps up to 0.1mm allowed with warning.
Self-intersection check recommended but not required.
```

Validation:
```python
def validate_prototype_shell(shell):
    for edge in shell.edges:
        if edge.adjacent_face_count != 2:
            warnings.append(f"Edge {edge.id} has {edge.adjacent_face_count} faces")
    
    max_gap = max(edge.gap_mm for edge in shell.edges)
    if max_gap > 0.1:
        return ValidationResult(valid=False, error="Gap exceeds prototype tolerance")
    
    return ValidationResult(valid=True, warnings=warnings)
```

### PRODUCTION Tier

```
All edges must have exactly 2 adjacent faces.
No gaps (kernel-verified watertight).
No self-intersection (kernel-verified).
Manifold topology required.
```

Validation:
```python
def validate_production_shell(shell, kernel):
    # Kernel verification required
    if not kernel.is_closed(shell):
        return ValidationResult(valid=False, error="Shell not closed")
    
    if not kernel.is_manifold(shell):
        return ValidationResult(valid=False, error="Non-manifold topology")
    
    if kernel.has_self_intersection(shell):
        return ValidationResult(valid=False, error="Self-intersection detected")
    
    return ValidationResult(valid=True)
```

---

## Geometry Preservation Rules

### Rule: No Coordinate Mutation

```
For all points P in BOE-approved outline:
    There must exist point Q in topology output
    Where distance(P, Q) < 0.001mm
```

### PROTOTYPE Tier

- Verification recommended
- Warning on drift > 0.001mm
- Error on drift > 0.01mm

### PRODUCTION Tier

- Verification required
- Error on drift > 0.001mm
- No tolerance relaxation

### Verification Method

```python
def verify_geometry_preservation(approved_points, topology, tier):
    tolerance = 0.001 if tier == PRODUCTION else 0.01
    
    for point in approved_points:
        nearest = topology.find_nearest_vertex(point)
        distance = point.distance_to(nearest)
        
        if distance > tolerance:
            return GeometryMutationError(
                f"Approved point {point} drifted {distance}mm in output"
            )
    
    return None
```

---

## Thickness Application Rules

### Level 1: Uniform Extrusion

```
All profile points extruded to same z_max.
z_max = uniform_thickness_mm
```

Requirements:
- PROTOTYPE: Basic extrusion, gap tolerance 0.1mm
- PRODUCTION: Kernel-verified extrusion, no gaps

### Level 2: Component Thickness

```
Top plate: z from 0 to top_thickness_mm
Back plate: z from -side_depth_mm to -(side_depth_mm - back_thickness_mm)
Rim: connects top edge to back edge
```

Requirements:
- PROTOTYPE: Separate bodies acceptable, gap warnings
- PRODUCTION: Single watertight shell required

### Level 3: Zonal Thickness (Future)

```
Thickness varies by zone.
Interpolation between zone boundaries.
```

Requirements:
- PROTOTYPE: Discrete zones acceptable
- PRODUCTION: Smooth interpolation required

---

## Loft Generation Rules

### When Required

Loft generation required when:
- `side_profile.type == TAPERED`
- `plate_relationship.back_type == RADIUSED`
- Per-point depth profile differs

### PROTOTYPE Tier

```
Linear interpolation acceptable.
Discontinuities at profile points acceptable.
Warning on deviation > 1mm from ideal.
```

### PRODUCTION Tier

```
Spline interpolation required.
C1 continuity along loft path.
Deviation < 0.1mm from ideal.
```

---

## Runtime Error Handling

### Blocking Errors (Both Tiers)

| Error | Condition |
|-------|-----------|
| `OpenShellError` | Cannot close shell |
| `GeometryMutationError` | BOE point not preserved |
| `InvalidInputError` | Malformed semantic input |
| `KernelCrashError` | CAD kernel failed |

### PROTOTYPE-Only Warnings

| Warning | Condition |
|---------|-----------|
| `ContinuityDegraded` | G1 requested, G0 achieved |
| `GapDetected` | Gap < 0.1mm in shell |
| `LowResolution` | Few profile points |

### PRODUCTION Blocking (Would Be Warning in PROTOTYPE)

| Error | Condition |
|-------|-----------|
| `ContinuityFailure` | G1 not achieved |
| `ManifoldViolation` | Non-manifold edge |
| `SelfIntersection` | Topology self-intersects |

---

## Tier Selection

### Automatic Selection

```python
def select_tier(export_object, user_preference=None):
    if user_preference:
        return user_preference
    
    # Default based on gate status
    if export_object.validation.gate_status == "green":
        return Tier.PRODUCTION
    else:
        return Tier.PROTOTYPE
```

### Manual Override

User may explicitly request tier:
```json
{
  "cad_semantics": {
    "topology_tier": "prototype"
  }
}
```

### Tier in Output

Tier must be recorded in output provenance:
```
FILE_DESCRIPTION(
    ('Acoustic body - PROTOTYPE tier - not for manufacturing'),
    '2;1');
```

---

## Promotion: PROTOTYPE → PRODUCTION

### Requirements

- [ ] All PRODUCTION validation passes
- [ ] Kernel verification complete
- [ ] No geometry drift > 0.001mm
- [ ] G1 continuity at all plate-rim junctions
- [ ] Manifold topology verified
- [ ] No self-intersection

### Process

```python
def promote_to_production(prototype_result, kernel):
    # Re-validate at production tier
    production_validation = validate_production_shell(
        prototype_result.shell, kernel
    )
    
    if not production_validation.valid:
        return PromotionResult(
            success=False,
            reason=production_validation.error,
        )
    
    return PromotionResult(
        success=True,
        production_result=prototype_result.with_tier(Tier.PRODUCTION),
    )
```

---

## Related Documents

- `ACOUSTIC_TOPOLOGY_CONTINUITY_MODEL.md` — Continuity definitions
- `TOPOLOGY_FAILURE_CLASSIFICATION.md` — Error classification
- `TOPOLOGY_AUTHORITY_CHAIN.md` — Authority hierarchy
- `ACOUSTIC_TOPOLOGY_BUILDER_MODEL.md` — Builder responsibilities
