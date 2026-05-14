# Translator Layer Rules

**Date:** 2026-05-14  
**Sprint:** MRP-4A  
**Status:** ACTIVE

---

## Core Principle

**All translators consume canonical Export Objects. No translator defines canonical semantics.**

---

## Authority Boundaries

### Export Object Authority

The Export Object is the canonical manufacturing representation. It contains:

- Geometry (coordinates, bounds, entities)
- Validation (gate status, checks performed)
- Metadata (export_id, provenance, timestamps)
- Intent (operation type, finish requirements)
- Extensions (IBG context, optional enrichment)

**Export Objects define semantics. Translators serialize semantics.**

### Translator Authority

Translators are authorized to:

- Read Export Object data
- Serialize to target format
- Embed provenance where supported
- Report statistics and warnings

Translators are NOT authorized to:

- Create new semantic meaning
- Modify input geometry
- Interpret missing data as present
- Skip validation gates
- Generate machine-executable output (G-code, toolpaths)

---

## Execution States

| State | Meaning | Execution | Machine Output |
|-------|---------|-----------|----------------|
| validation_only | Can validate, not execute | No | No |
| governed_execution | Full execution authorized | Yes | No |
| experimental | Under development | Limited | No |
| execution_disabled | Explicitly disabled | No | No |
| deprecated | Scheduled for removal | No | No |

Only `governed_execution` translators may produce artifacts.

---

## Gate Enforcement

| Gate | Translator Behavior |
|------|---------------------|
| GREEN | Translation proceeds |
| YELLOW | Translation proceeds with warnings |
| RED | Translation blocked (must return error) |

**Red gate rejection is mandatory at the translator layer.**

---

## Deterministic Requirements

Translators MUST produce deterministic output when:

1. Same Export Object input
2. Same translator options
3. Provenance embedding disabled

Acceptable variance:
- Timestamp in provenance (when enabled)

Unacceptable variance:
- Random IDs
- Non-deterministic ordering
- Platform-dependent encoding

---

## Provenance Requirements

Translators SHOULD embed provenance where format supports it:

**Required fields:**
- export_id
- translator_id
- translator_version
- translated_at (ISO 8601)

**Optional fields:**
- source_hash
- ibg_session_id
- instrument_spec

**Format-specific embedding:**
- DXF: TEXT entities on PROVENANCE layer
- SVG: XML comment at document start
- STEP: Header metadata
- PDF: Document properties

---

## Geometry Invariants

Translators MUST NOT:

- Modify input points
- Reorder vertices
- Change winding direction
- Merge or split entities
- Add or remove geometry
- Apply transformations not specified in options

Translators MAY:

- Round coordinates to specified precision
- Convert coordinate system for target format
- Apply deterministic transformations explicitly requested

---

## Error Handling

Translators MUST:

- Use standard TranslatorErrorCode values
- Include descriptive error messages
- Reference entity_id when error is entity-specific
- Return partial results when safe to do so

Translators MUST NOT:

- Swallow errors silently
- Return success with empty output
- Produce malformed output on error

---

## Registration Requirements

All translators MUST:

1. Implement ExportTranslator protocol
2. Register with TranslatorRegistry
3. Declare TranslatorCapabilities
4. Appear in capability matrix

Unregistered translators are not authorized for execution.

---

## Backward Compatibility

MRP-3A imports continue to work:

```python
from app.cam.translators.base import ExportTranslator, BaseTranslator
```

MRP-4A imports are preferred:

```python
from app.cam.translators import (
    resolve_translator,
    get_translator_registry,
    TranslatorCapabilities,
)
```

---

## References

- `docs/governance/MULTI_TARGET_TRANSLATOR_POLICY.md`
- `docs/governance/DXF_TRANSLATOR_SERIALIZATION_POLICY.md`
- `docs/handoffs/MRP_4A_MULTI_TARGET_TRANSLATOR_HANDOFF.md`
