# CAD Extension Compatibility Policy

**Date:** 2026-05-14  
**Sprint:** MRP-5B  
**Status:** PROPOSAL

---

## Purpose

Defines compatibility requirements for CAD semantic extensions to ensure:
- Backward compatibility with existing Export Objects
- Forward compatibility with future extensions
- Translator isolation from schema evolution

---

## Core Compatibility Principles

### Principle 1: Optional by Default

All CAD semantic fields MUST be optional.

```python
class CadSemantics(BaseModel):
    # CORRECT: Optional with default
    uniform_thickness_mm: Optional[float] = None
    
    # FORBIDDEN: Required field
    # thickness_mm: float  # NO — breaks existing Export Objects
```

### Principle 2: Additive Evolution

Schema evolution MUST be additive.

```python
# Version 1.0.0
class CadSemantics_v1(BaseModel):
    uniform_thickness_mm: Optional[float] = None

# Version 1.1.0 (compatible)
class CadSemantics_v1_1(BaseModel):
    uniform_thickness_mm: Optional[float] = None
    top_thickness_mm: Optional[float] = None  # NEW — optional, additive
    
# FORBIDDEN: Removing fields
# class CadSemantics_v2(BaseModel):
#     top_thickness_mm: float  # Required + old field removed = BREAKING
```

### Principle 3: Graceful Degradation

Translators MUST handle missing/unknown extensions gracefully.

```python
def translate(self, export_object):
    cad = getattr(export_object.extensions, 'cad_semantics', None)
    
    if cad is None:
        # Graceful: Clear error for STEP, ignore for DXF
        if self.requires_cad_semantics:
            return self._missing_extension_error()
        else:
            return self._translate_without_cad()
    
    # Handle unknown fields (forward compatibility)
    thickness = getattr(cad, 'uniform_thickness_mm', None)
```

---

## Backward Compatibility

### Existing Export Objects

Export Objects created before CAD semantics:

```python
# Old Export Object (no cad_semantics)
{
    "schema_version": "1.0.0",
    "export_id": "EXP-BODY-...",
    "extensions": {
        "ibg_morphology": {...}
        # NO cad_semantics
    }
}
```

| Translator | Behavior |
|------------|----------|
| DXF R12 | Works — ignores missing extension |
| DXF R2000 | Works — ignores missing extension |
| SVG | Works — ignores missing extension |
| STEP | Fails gracefully with clear error |

### Translator Compatibility Matrix

| Export Object Version | DXF | SVG | STEP |
|-----------------------|-----|-----|------|
| 1.0.0 (no cad_semantics) | ✓ | ✓ | ✗ (requires extension) |
| 1.0.0 (with cad_semantics) | ✓ | ✓ | ✓ |
| Future (additional fields) | ✓ | ✓ | ✓ |

---

## Forward Compatibility

### Unknown Field Handling

Translators MUST ignore unknown fields in `cad_semantics`.

```python
# Future Export Object with new field
{
    "extensions": {
        "cad_semantics": {
            "uniform_thickness_mm": 45.0,
            "future_field_xyz": "unknown"  # Future addition
        }
    }
}

# Current translator (does not know future_field_xyz)
def translate(self, export_object):
    cad = export_object.extensions.cad_semantics
    
    # Use known fields
    thickness = cad.uniform_thickness_mm
    
    # Ignore unknown fields (Pydantic extra='ignore' or explicit skip)
```

### Schema Version Handling

```python
class CadSemantics(BaseModel):
    schema_version: str = "1.0.0"
    
    class Config:
        extra = 'ignore'  # Ignore unknown fields for forward compatibility
```

Translators check schema version:

```python
def translate(self, export_object):
    cad = export_object.extensions.cad_semantics
    
    if cad.schema_version.startswith("2."):
        # Major version mismatch — warn but attempt
        logger.warning(f"CAD semantics version {cad.schema_version} may have incompatibilities")
    
    # Proceed with best-effort translation
```

---

## Extension Isolation

### DXF/SVG Isolation

2D translators MUST NOT:
- Require `cad_semantics`
- Fail if `cad_semantics` present
- Interpret thickness as geometry modification

```python
class BodyOutlineDxfTranslator(BaseTranslator):
    def translate(self, export_object):
        # Ignore cad_semantics entirely
        # Use only geometry.entities for 2D output
        pass
```

### STEP Isolation

CAD translators MUST NOT:
- Modify Export Object
- Persist constructed topology
- Leak CAD assumptions to Export Object schema

```python
class BodyOutlineStepTranslator(BaseTranslator):
    def translate(self, export_object):
        # READ cad_semantics
        # CONSTRUCT topology internally
        # EMIT STEP file
        # DO NOT MUTATE export_object
        pass
```

---

## Compatibility Testing Requirements

### Backward Compatibility Tests

```python
def test_dxf_without_cad_semantics():
    """DXF translation works without cad_semantics."""
    export_object = create_minimal_export_object()
    assert export_object.extensions.cad_semantics is None
    
    result = dxf_translator.translate(export_object)
    assert result.success

def test_step_requires_cad_semantics():
    """STEP translation requires cad_semantics."""
    export_object = create_minimal_export_object()
    
    result = step_translator.translate(export_object)
    assert not result.success
    assert "cad_semantics" in result.error_message
```

### Forward Compatibility Tests

```python
def test_translator_ignores_unknown_fields():
    """Translator handles future schema fields gracefully."""
    export_object = create_export_object_with_cad()
    
    # Inject unknown future field
    export_object.extensions.cad_semantics.__dict__['future_field'] = "test"
    
    result = step_translator.translate(export_object)
    assert result.success  # Should not fail on unknown field
```

---

## Breaking Change Policy

### What Constitutes a Breaking Change

| Change | Breaking? | Action |
|--------|-----------|--------|
| Add optional field | NO | Allowed |
| Add required field | YES | Requires major version |
| Remove field | YES | Requires deprecation period |
| Change field type | YES | Requires major version |
| Change field semantics | MAYBE | Requires governance review |
| Rename field | YES | Add alias, deprecate old |

### Deprecation Process

1. **Mark deprecated** — Add deprecation notice in docstring
2. **Provide alias** — Old field maps to new field
3. **Emit warning** — Log deprecation when old field used
4. **Remove in major version** — After deprecation period (2 minor versions)

```python
class CadSemantics(BaseModel):
    # New field name
    uniform_thickness_mm: Optional[float] = None
    
    # Deprecated alias
    @property
    def thickness_mm(self) -> Optional[float]:
        """DEPRECATED: Use uniform_thickness_mm instead."""
        warnings.warn("thickness_mm is deprecated, use uniform_thickness_mm", DeprecationWarning)
        return self.uniform_thickness_mm
```

---

## Version Migration Guide

### From 0.x to 1.0 (Initial Release)

No migration needed — first release.

### From 1.0 to 1.1 (Level 2 Thickness)

```python
# 1.0 Export Object (uniform only)
{
    "extensions": {
        "cad_semantics": {
            "uniform_thickness_mm": 45.0
        }
    }
}

# 1.1 Export Object (component thickness)
{
    "extensions": {
        "cad_semantics": {
            "uniform_thickness_mm": 45.0,  # Still works
            "top_thickness_mm": 3.0,       # Optional new field
            "back_thickness_mm": 3.5       # Optional new field
        }
    }
}
```

1.0 translators reading 1.1 Export Objects: Work (ignore new fields)
1.1 translators reading 1.0 Export Objects: Work (new fields absent/None)

---

## Governance Checklist

Before adding new CAD semantic field:

- [ ] Field is optional with sensible default
- [ ] Field does not modify geometry authority
- [ ] Field has documented owner
- [ ] Backward compatibility verified
- [ ] Forward compatibility verified
- [ ] Deprecation path documented (if replacing field)
- [ ] Test coverage added
- [ ] Governance review approved

---

## References

- `docs/architecture/CAD_SEMANTIC_EXTENSION_MODEL.md`
- `docs/governance/CAD_SEMANTIC_AUTHORITY_RULES.md`
- `docs/governance/CAD_TRANSLATOR_GOVERNANCE_RULES.md`
- Pydantic schema evolution best practices
