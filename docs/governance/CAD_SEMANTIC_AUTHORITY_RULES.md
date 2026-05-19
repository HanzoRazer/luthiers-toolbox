# CAD Semantic Authority Rules

**Date:** 2026-05-14  
**Sprint:** MRP-5B  
**Status:** PROPOSAL

---

## Purpose

Defines ownership and authority boundaries for CAD semantic extensions to ensure they extend—not override—the established morphology/manufacturing authority model.

---

## Authority Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│ TIER 1: GEOMETRY AUTHORITY                                      │
│                                                                 │
│   Owner: BOE (Body Outline Editor)                              │
│   Scope: 2D profile coordinates, contour closure, winding       │
│   Status: IMMUTABLE by downstream systems                       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ TIER 2: MORPHOLOGY AUTHORITY                                    │
│                                                                 │
│   Owner: IBG (Image Body Generator)                             │
│   Scope: side_heights, radii_by_zone, constraint parameters     │
│   Status: ADVISORY enrichment (not manufacturing specification) │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ TIER 3: MANUFACTURING AUTHORITY                                 │
│                                                                 │
│   Owner: Export Object                                          │
│   Scope: intent, validation, provenance, operation semantics    │
│   Status: CANONICAL for downstream translators                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ TIER 4: CAD SEMANTIC AUTHORITY (NEW)                            │
│                                                                 │
│   Owner: extensions.cad_semantics                               │
│   Scope: thickness, extrusion hints, profile classification     │
│   Status: OPTIONAL enrichment for CAD-grade translators         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ TIER 5: SERIALIZATION AUTHORITY                                 │
│                                                                 │
│   Owner: Translators (DXF, SVG, STEP)                           │
│   Scope: Format-specific output, topology construction          │
│   Status: ISOLATED per-format                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Semantic Ownership Matrix

| Semantic | Authority Owner | Can Be Overridden By | Notes |
|----------|-----------------|---------------------|-------|
| Profile coordinates (x, y) | BOE | NONE | Immutable |
| Contour closure | BOE + Validation | NONE | Verified at validation |
| Winding direction | BOE | NONE | ccw outer, cw voids |
| Side heights | IBG | User override in BOE | Advisory morphology |
| Back radius | IBG | User override in BOE | Advisory morphology |
| Thickness value | CAD Semantics | User specification | Manufacturing input |
| Extrusion direction | CAD Semantics | Default from coord sys | Derived hint |
| Body type | CAD Semantics | User specification | Classification |
| Face topology | STEP Translator | N/A | Constructed, not stored |
| BREP solid | STEP Translator | N/A | Constructed, not stored |

---

## Authority Conflict Resolution

### Rule 1: Geometry Authority is Final

```
IF conflict between BOE geometry and any downstream system:
    BOE geometry WINS
    Downstream system must adapt or fail
```

Example: If CAD semantics imply a profile modification, reject the semantics.

### Rule 2: Morphology is Advisory

```
IF IBG morphology conflicts with user-specified CAD semantics:
    User-specified CAD semantics WIN
    IBG data is enrichment, not mandate
```

Example: User specifies `uniform_thickness_mm=45`, IBG has variable side_heights. User value takes precedence for flat extrusion.

### Rule 3: CAD Semantics are Optional

```
IF cad_semantics extension is absent:
    DXF/SVG translators: proceed normally
    STEP translator: require explicit thickness or fail with clear error
```

Example: Export Object without `cad_semantics` → DXF works, STEP fails gracefully.

### Rule 4: Translators May Not Store

```
Translators may CONSTRUCT topology for output.
Translators may NOT persist topology to Export Object.
```

Example: STEP translator builds BREP internally, emits STEP file, does not mutate Export Object.

---

## CAD Semantics Governance

### What CAD Semantics MAY Do

| Action | Allowed | Example |
|--------|---------|---------|
| Add thickness value | YES | `uniform_thickness_mm=45.0` |
| Classify body type | YES | `body_type="flat"` |
| Hint extrusion direction | YES | `extrusion_direction="positive_z"` |
| Reference IBG data | YES | `use_ibg_side_heights=True` |
| Override IBG with user value | YES | User thickness vs IBG side_heights |

### What CAD Semantics MAY NOT Do

| Action | Forbidden | Reason |
|--------|-----------|--------|
| Modify profile coordinates | YES | BOE authority |
| Change winding direction | YES | Topology semantics |
| Add geometry entities | YES | Geometry authority |
| Override validation gate | YES | Safety invariant |
| Store constructed topology | YES | Translator ephemeral |
| Remove IBG extension | YES | Enrichment preserved |

---

## Future Extension Rules

### Adding New CAD Semantics

New fields in `cad_semantics` must:

1. **Be optional** — Default to `None` or sensible default
2. **Not override geometry** — Cannot change x, y coordinates
3. **Be documented** — Authority owner specified
4. **Pass governance review** — PR approval required
5. **Have backward compatibility** — Old Export Objects still valid

### Governance Checkpoint

```python
# Before adding new cad_semantics field:
assert field_is_optional()
assert does_not_modify_geometry()
assert authority_owner_documented()
assert backward_compatible()
```

### Schema Evolution

```python
class CadSemantics(BaseModel):
    schema_version: str = "1.0.0"  # Increment on breaking changes
    level: int = 1                  # Feature level marker
    
    # Version 1.0.0 fields
    uniform_thickness_mm: Optional[float] = None
    
    # Version 1.1.0 fields (future)
    # graduated_thickness: Optional[List[float]] = None
```

---

## Cross-Authority Data Flow

### IBG → CAD Semantics (Advisory Path)

```
IBG.side_heights_mm (morphology)
    │
    ▼ if use_ibg_side_heights=True
CadSemantics references IBG data
    │
    ▼ confidence check (≥0.7)
STEP Translator consumes for variable extrusion
```

**Authority:** IBG remains morphology owner. CAD semantics reference, not copy.

### User → CAD Semantics (Override Path)

```
User specifies thickness_mm
    │
    ▼
CadSemantics.uniform_thickness_mm = 45.0
    │
    ▼ overrides IBG variable heights
STEP Translator uses uniform extrusion
```

**Authority:** User specification overrides IBG advisory data.

### BOE → Export Object → CAD Semantics (Immutable Path)

```
BOE approves profile
    │
    ▼ LOCKED
Export Object.geometry.entities
    │
    ▼ READ-ONLY
CadSemantics (cannot modify)
    │
    ▼ READ-ONLY
STEP Translator (construct, don't mutate)
```

**Authority:** Profile coordinates flow one-way. No upstream mutation.

---

## Validation Rules

### Pre-Extension Checks

| Check | Requirement | Action on Failure |
|-------|-------------|-------------------|
| Profile closed | Required | Block CAD extension |
| Winding valid | Required | Block CAD extension |
| Gate not RED | Required | Block CAD extension |

### Post-Extension Checks

| Check | Requirement | Action on Failure |
|-------|-------------|-------------------|
| Thickness positive | If specified | Reject value |
| Body type valid | If specified | Reject value |
| IBG confidence | If referencing IBG | Warn if low |

---

## Implementation Guidance

### For Export Object Producers (BOE Bridge)

```python
def create_body_export_object(..., cad_semantics: Optional[CadSemantics] = None):
    # ... existing logic ...
    
    extensions = ExportExtensions(
        ibg_morphology=ibg_ext,
        cad_semantics=cad_semantics,  # NEW — optional
    )
    
    return BodyExportObject(
        # ... existing fields ...
        extensions=extensions,
    )
```

### For Translators (STEP)

```python
def translate(self, export_object):
    # 1. Check gate
    if export_object.validation.gate_status == "red":
        return error("GATE_RED")
    
    # 2. Get CAD semantics (optional)
    cad = export_object.extensions.cad_semantics if export_object.extensions else None
    
    # 3. Require thickness for STEP
    if cad is None or cad.uniform_thickness_mm is None:
        return error("THICKNESS_REQUIRED", "STEP export requires cad_semantics.uniform_thickness_mm")
    
    # 4. Construct topology (internal, not stored)
    solid = self._extrude(export_object.geometry.entities, cad.uniform_thickness_mm)
    
    # 5. Emit STEP (does not mutate Export Object)
    return self._emit_step(solid, export_object.metadata)
```

---

## References

- `docs/governance/CAD_TRANSLATOR_GOVERNANCE_RULES.md`
- `docs/architecture/CAD_SEMANTIC_EXTENSION_MODEL.md`
- `docs/architecture/CAD_TRANSLATOR_BOUNDARY_MODEL.md`
- `docs/governance/TRANSLATOR_LAYER_RULES.md`
