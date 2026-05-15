# Acoustic Runtime Limitations

**Sprint:** MRP-5F  
**Status:** ACTIVE  
**Authority:** CAD Translation Governance

---

## Purpose

Document explicit runtime limitations for acoustic semantic configurations. These limitations prevent false CAD confidence by ensuring unsupported operations fail clearly rather than silently degrading.

---

## Current Runtime Support

### Supported (MRP-5F)

| Category | Operation | Runtime |
|----------|-----------|---------|
| `flat_body` | Uniform extrusion | SUPPORTED |
| DXF export | 2D profile only | SUPPORTED |
| SVG export | 2D profile only | SUPPORTED |

### Semantic Only (No Topology)

| Category | Semantics | Topology |
|----------|-----------|----------|
| `acoustic_flat_top` | Valid schema | NOT GENERATED |
| `acoustic_arched_top` | Valid schema | NOT GENERATED |
| `hollow_electric` | Valid schema | NOT GENERATED |
| `archtop` | Valid schema | NOT GENERATED |

### Unsupported

| Category | Status |
|----------|--------|
| `resonator` | Not planned |
| `unknown` | Fallback only |

---

## Explicit Non-Goals (MRP-5F)

The following are explicitly NOT implemented:

### 1. Acoustic STEP Generation

```
NO: Tapered rim solid
NO: Radiused back surface
NO: Arched top surface
NO: Shell topology
NO: G1 continuity at junctions
```

### 2. Lofting / Surface Generation

```
NO: Loft from profile to depth profile
NO: NURBS surface generation
NO: B-spline interpolation
NO: Variable-depth extrusion
```

### 3. CAD Kernel Integration

```
NO: CadQuery integration
NO: OpenCASCADE direct calls
NO: Parametric surface construction
NO: Fillet/chamfer operations
```

### 4. Assembly Semantics

```
NO: Multi-body export
NO: Top/back/side as separate bodies
NO: Bracing topology
NO: Binding/purfling geometry
```

---

## Translator Rejection Behavior

### STEP Translator

When acoustic topology is required:

```python
# CORRECT: Clear rejection
return TranslatorResult(
    success=False,
    error_classification="UNSUPPORTED_TOPOLOGY_RUNTIME",
    message="Acoustic topology generation not supported",
)

# WRONG: Silent fallback
# DO NOT fall back to flat extrusion
# DO NOT generate incorrect geometry
```

### DXF/SVG Translators

```python
# CORRECT: Ignore acoustic semantics safely
# Proceed with 2D profile extraction only
# No error, no warning — acoustic semantics are irrelevant

# WRONG: Attempt to interpret acoustic depth
# WRONG: Modify profile based on side_depth_mm
```

---

## Safe Rejection Protocol

### Step 1: Detect Unsupported Configuration

```python
def can_translate(semantics: CadSemantics) -> bool:
    if semantics.body_category == BodyCategory.FLAT_BODY:
        return True
    if semantics.requires_acoustic_topology():
        return False
    return False
```

### Step 2: Generate Clear Error

```python
def reject_unsupported(semantics: CadSemantics) -> TranslatorResult:
    return TranslatorResult(
        success=False,
        error_classification="UNSUPPORTED_TOPOLOGY_RUNTIME",
        message=f"Cannot generate topology for {semantics.body_category.value}",
        runtime_support=semantics.get_runtime_support().value,
        requires_acoustic_topology=semantics.requires_acoustic_topology(),
    )
```

### Step 3: Preserve Semantics in Error

Error response should include:
- Body category
- Runtime support classification
- Specific unsupported features
- No partial/degraded output

---

## Future Sprint Enablement

### MRP-5G: Side/Rim Topology

```
ENABLE: Tapered rim generation
ENABLE: Variable depth extrusion
REQUIRE: CAD kernel evaluation complete
```

### MRP-5H: CAD Kernel Integration

```
ENABLE: CadQuery/OCC integration
ENABLE: NURBS surface construction
REQUIRE: Kernel selection approved
```

### MRP-5I: Acoustic STEP Prototype

```
ENABLE: Acoustic body STEP export
ENABLE: G1 continuity at junctions
REQUIRE: Side/rim topology working
```

---

## Why No Fallback?

### Problem: False Confidence

If STEP translator silently falls back to flat extrusion:

```
User expects: Dreadnought acoustic body (tapered sides, radiused back)
User receives: Flat rectangular extrusion

Result: User believes they have acoustic CAD
Reality: They have incorrect geometry
Consequence: Manufacturing errors, wasted material, lost trust
```

### Solution: Clear Failure

```
User requests: Dreadnought acoustic body
System responds: "Acoustic topology not supported (SEMANTIC_ONLY)"
User knows: They need to wait for MRP-5I or use alternative workflow
Result: No false confidence, clear expectations
```

---

## Semantic Value Without Runtime

Acoustic semantics provide value even without topology:

1. **Schema Validation** — Validates acoustic configurations before runtime
2. **Documentation** — Records design intent in Export Object
3. **Future Compatibility** — Ready for future translator implementation
4. **API Consistency** — Uniform semantic interface across body types
5. **Regression Testing** — Test fixtures validate semantic evolution

---

## Monitoring Unsupported Requests

### Telemetry Events

```python
# Log when acoustic topology is requested but unavailable
logger.info(
    "acoustic_topology_requested",
    body_category=semantics.body_category.value,
    runtime_support=semantics.get_runtime_support().value,
    requires_topology=semantics.requires_acoustic_topology(),
)
```

### Metrics

Track:
- Count of `UNSUPPORTED_TOPOLOGY_RUNTIME` rejections
- Body category distribution of rejections
- User progression from semantic to runtime requests

---

## Related Documents

- `ACOUSTIC_CAD_SEMANTIC_EXTENSION_MODEL.md` — Schema structure
- `ACOUSTIC_SEMANTIC_VALIDATION_RULES.md` — Validation rules
- `CAD_TRANSLATOR_PROMOTION_THRESHOLDS.md` — Translator maturity
- `THICKNESS_HIERARCHY_MODEL.md` — Thickness levels
