# MRP Dev Order 5F — Acoustic Semantic Extension Handoff

**Date:** 2026-05-14  
**Dev Order:** MRP-5F  
**Status:** COMPLETE

---

## Summary

MRP-5F implemented governed acoustic semantic extensions for the morphology spine:

1. **CadSemantics Schema** — Modular schema with flat-body and acoustic extensions
2. **Level 2 Thickness Semantics** — Component thickness (top/back/side)
3. **Side/Rim Descriptors** — Profile type, taper, continuity targets
4. **Validation Rules** — Blocking errors vs. warnings, field constraints
5. **Acoustic Fixture Corpus** — 4 semantic-only fixtures
6. **Runtime Limitations** — Clear UNSUPPORTED_TOPOLOGY_RUNTIME rejection

**Sprint Type:** Schema implementation + validation (no acoustic topology runtime)

---

## Deliverables

### 1. CadSemantics Schema

**Location:** `services/api/app/export/cad_semantics.py`

**Structure:**
```
CadSemantics
├── schema_version: str
├── body_category: BodyCategory
├── flat_body: Optional[FlatBodySemantics]
├── acoustic: Optional[AcousticSemantics]
└── uniform_thickness_mm: Optional[float] (legacy)
```

**Enums Defined:**
- `BodyCategory`: flat_body, acoustic_flat_top, acoustic_arched_top, hollow_electric, archtop, resonator, unknown
- `SideProfileType`: uniform, tapered
- `ContinuityTarget`: G0, G1
- `PlateType`: flat, radiused, arched
- `RuntimeSupport`: supported, semantic_only, unsupported

### 2. Level 2 Thickness Semantics

**Location:** `ThicknessSemantics` class

**Fields:**
| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `top_thickness_mm` | float | 0.1-50.0 | Soundboard thickness |
| `back_thickness_mm` | float | 0.1-50.0 | Back plate thickness |
| `side_depth_mm` | float | 1.0-500.0 | Side/rim depth |

### 3. Side/Rim Semantic Descriptors

**SideProfileSemantics:**
```python
type: SideProfileType  # uniform | tapered
taper_axis: str        # "tail_to_neck"
max_depth_mm: float    # Depth at butt
min_depth_mm: float    # Depth at shoulder
```

**RimSemantics:**
```python
continuity_target: ContinuityTarget  # G0 | G1
closure_type: ClosureType            # closed_rim | cutaway
```

### 4. Validation Rules

**Implemented in:** `validate_acoustic_semantics()`

**Blocking Errors:**
- Negative/zero thickness values
- Taper min > max
- Invalid enum values

**Warnings:**
- Incomplete taper profile
- Radiused back without radius
- Category/semantic mismatch

### 5. Acoustic Fixture Corpus

**Location:** `services/api/tests/cam/fixtures/acoustic/`

**Fixtures:**
| Fixture | Body Category | Features |
|---------|---------------|----------|
| dreadnought_semantic | acoustic_flat_top | Tapered sides, radiused back |
| jumbo_semantic | acoustic_flat_top | Larger dimensions |
| parlor_semantic | acoustic_flat_top | Uniform sides, smaller |
| hollowbody_semantic | hollow_electric | Shallow, uniform |

**Classification:** SEMANTIC_ONLY (no runtime topology)

### 6. Translator Awareness

**Runtime Support:**
| Category | Support |
|----------|---------|
| flat_body | SUPPORTED |
| acoustic_flat_top | SEMANTIC_ONLY |
| hollow_electric | SEMANTIC_ONLY |
| archtop | SEMANTIC_ONLY |
| resonator | UNSUPPORTED |

**Rejection Behavior:**
```python
if semantics.requires_acoustic_topology():
    return TranslatorResult(
        success=False,
        error_classification="UNSUPPORTED_TOPOLOGY_RUNTIME",
    )
```

---

## Files Created

### Source Code

| File | Purpose |
|------|---------|
| `services/api/app/export/cad_semantics.py` | CAD semantic schema |
| `services/api/tests/cam/fixtures/acoustic/__init__.py` | Fixture package |
| `services/api/tests/cam/fixtures/acoustic/fixture_generator.py` | Fixture generation |

### Tests

| File | Test Count | Coverage |
|------|------------|----------|
| `services/api/tests/cam/test_acoustic_semantic_validation.py` | ~40 | Schema validation |
| `services/api/tests/cam/test_acoustic_semantic_compatibility.py` | ~25 | Backward compatibility |

### Documentation

| File | Purpose |
|------|---------|
| `docs/architecture/ACOUSTIC_CAD_SEMANTIC_EXTENSION_MODEL.md` | Schema structure |
| `docs/governance/ACOUSTIC_SEMANTIC_VALIDATION_RULES.md` | Validation rules |
| `docs/governance/ACOUSTIC_RUNTIME_LIMITATIONS.md` | Runtime constraints |
| `docs/handoffs/MRP_5F_ACOUSTIC_SEMANTIC_EXTENSION_HANDOFF.md` | This document |

---

## What Was NOT Built (By Design)

Explicitly excluded per dev order:

- **Acoustic STEP generation** — No solid topology
- **Lofting/NURBS** — No surface generation
- **Shell topology** — No multi-wall solids
- **G1 runtime continuity** — Semantic target only
- **CAD kernel calls** — No CadQuery/OCC
- **Assembly semantics** — Single body only
- **Silent fallback** — No degraded output

---

## Integration Points

### Export Object Extension

```python
from app.export.body_export_bridge import ExportExtensions
from app.export.cad_semantics import CadSemantics

extensions = ExportExtensions(
    cad_semantics=CadSemantics(
        body_category=BodyCategory.ACOUSTIC_FLAT_TOP,
        acoustic=AcousticSemantics(...),
    ),
)
```

### Validation

```python
from app.export.cad_semantics import validate_acoustic_semantics

result = validate_acoustic_semantics(semantics)
if not result.valid:
    raise ValidationError(result.blocking_errors)
```

### Runtime Check

```python
if semantics.requires_acoustic_topology():
    # Reject with UNSUPPORTED_TOPOLOGY_RUNTIME
    pass
```

---

## Authority Boundaries Preserved

| Authority | Role | MRP-5F Impact |
|-----------|------|---------------|
| BOE | Geometry approval | NO CHANGE |
| IBG | Morphology advisory | NO CHANGE |
| cad_semantics | CAD hints | EXTENDED (acoustic fields) |
| Translator | Topology construction | AWARE (safe rejection) |

**Key Rule Verified:**
> Acoustic semantic descriptors may enrich approved geometry context, but may not invent or reinterpret approved geometry.

---

## Test Summary

| Category | Tests | Status |
|----------|-------|--------|
| Valid semantics | 4 | Defined |
| Invalid thickness | 6 | Defined |
| Taper consistency | 4 | Defined |
| Enum validation | 4 | Defined |
| Runtime classification | 6 | Defined |
| Topology detection | 5 | Defined |
| Effective thickness | 3 | Defined |
| Backward compatibility | 4 | Defined |
| No geometry mutation | 3 | Defined |
| Authority boundary | 3 | Defined |
| Fixture integration | 3 | Defined |

---

## Next Steps (Not in MRP-5F Scope)

| Sprint | Focus | Enables |
|--------|-------|---------|
| MRP-5G | Side/rim topology prototype | Tapered rim generation |
| MRP-5H | CAD kernel evaluation | CadQuery/OCC selection |
| MRP-5I | Acoustic STEP prototype | Acoustic body export |
| MRP-5J | Carved-top research | Archtop semantics |

---

## Definition of Done

✅ CadSemantics schema implemented  
✅ Level 2 thickness semantics implemented  
✅ Side/rim semantic descriptors implemented  
✅ Validation rules operational  
✅ Acoustic fixture corpus exists  
✅ Translator runtime awareness documented  
✅ Unsupported configurations reject safely  
✅ Backward compatibility preserved  
✅ Authority boundaries preserved  
✅ Documentation complete  
✅ Handoff exists

---

## Related Documents

- `MRP_5E_ACOUSTIC_BODY_SEMANTIC_RESEARCH.md` — Research foundation
- `ACOUSTIC_BODY_SEMANTIC_MODEL.md` — Semantic vocabulary
- `THICKNESS_HIERARCHY_MODEL.md` — Thickness levels
- `ACOUSTIC_CAD_SEMANTIC_RULES.md` — Authority rules
- `CAD_TRANSLATOR_PROMOTION_THRESHOLDS.md` — Translator maturity
