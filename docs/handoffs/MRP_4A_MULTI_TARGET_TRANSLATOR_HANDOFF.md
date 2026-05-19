# MRP-4A: Multi-Target Translator Architecture

**Date:** 2026-05-14  
**Sprint:** MRP-4A  
**Status:** COMPLETE

---

## Executive Summary

MRP-4A generalizes the governed DXF translator (MRP-3A/3B) into a multi-target translator platform. Multiple serialization targets now consume the same Export Object canonically through a shared abstraction layer.

**DXF becomes the reference implementation, not the architecture itself.**

---

## Architecture Achievement

```
Export Object (canonical)
    │
    └── Translator Abstraction Layer
            │
            ├── DXF R12 Translator  → .dxf (LINE entities)
            ├── DXF R2000 Translator → .dxf (LWPOLYLINE)
            └── SVG Translator       → .svg (styled paths)
            
            Future:
            ├── STEP Translator      → .step
            ├── PDF Translator       → .pdf
            └── RMOS Artifact        → archival
```

---

## Key Principle

**All translators consume canonical Export Objects. No translator defines canonical semantics.**

---

## Files Created

### Abstraction Layer (`app/cam/translators/base/`)

| File | Purpose |
|------|---------|
| `__init__.py` | Package exports |
| `contracts.py` | ExportTranslator Protocol, BaseTranslator ABC, result types |
| `capabilities.py` | TranslatorCapabilities, categories, maturity levels |
| `registry.py` | TranslatorRegistry, discovery, registration |
| `negotiation.py` | resolve_translator(), target/version resolution |

### SVG Translator (`app/cam/translators/svg/`)

| File | Purpose |
|------|---------|
| `__init__.py` | Package exports |
| `translator.py` | BodyOutlineSvgTranslator implementation |

### Multi-Target API

| File | Purpose |
|------|---------|
| `app/routers/export/translate_router.py` | `/api/translate/{target}` endpoint |

### Governance Documents

| File | Purpose |
|------|---------|
| `docs/governance/TRANSLATOR_LAYER_RULES.md` | Core translator rules |
| `docs/governance/DXF_TRANSLATOR_SERIALIZATION_POLICY.md` | DXF-specific policy |
| `docs/governance/MULTI_TARGET_TRANSLATOR_POLICY.md` | Multi-target policy |

### Tests

| File | Purpose |
|------|---------|
| `tests/mrp_spine_verification/standalone_multitarget_verify.py` | Standalone verification |

---

## Files Modified

| File | Change |
|------|--------|
| `app/cam/translators/base.py` | Now compatibility shim re-exporting from base/ |
| `app/cam/translators/__init__.py` | Updated exports for MRP-4A |
| `app/cam/translators/dxf/body_outline_translator.py` | Backward-compat options handling |
| `app/router_registry/manifests/cam_manifest.py` | Added translate_router |

---

## Translator Registry

```python
from app.cam.translators import get_translator_registry

registry = get_translator_registry()

# Discovery
registry.list_targets()          # ['dxf', 'svg']
registry.list_all()              # ['body_outline_dxf_r12', ...]
registry.list_governed()         # Governed translators only

# Lookup
translator = registry.get("body_outline_svg")
cap = registry.get_capabilities("body_outline_dxf_r12")
```

---

## Target Negotiation

```python
from app.cam.translators import resolve_translator

# Default version
translator = resolve_translator("dxf")

# Specific version
translator = resolve_translator("dxf", "r2000")

# With governance check
translator = resolve_translator("svg", require_governed=True)
```

---

## API Endpoints

### List Targets

```
GET /api/translate/targets

Response: { "targets": ["dxf", "svg"] }
```

### Target Info

```
GET /api/translate/targets/dxf

Response: {
  "target": "dxf",
  "supported": true,
  "versions": ["r12", "r2000"],
  "default_version": "r12",
  "translator_ids": ["body_outline_dxf_r12", "body_outline_dxf_r2000"]
}
```

### Translate

```
POST /api/translate/{target}?version={version}

Body: BodyExportObject JSON
Response: Translated artifact bytes

Headers:
  X-Export-ID: {export_id}
  X-Target-Format: {target}
  X-Translator-ID: {translator_id}
```

### Metadata Only

```
POST /api/translate/{target}/metadata

Response: Translation statistics without artifact bytes
```

---

## Capability Matrix

| Translator | Target | Version | Execution | Deterministic | Provenance |
|------------|--------|---------|-----------|---------------|------------|
| body_outline_dxf_r12 | dxf | R12 | governed | yes | yes |
| body_outline_dxf_r2000 | dxf | R2000 | governed | yes | yes |
| body_outline_svg | svg | 1.1 | governed | yes | yes |

---

## Verification Results

```
registry:            VERIFIED
target_negotiation:  VERIFIED
svg_translation:     VERIFIED
multitarget_api:     VERIFIED
deterministic_output: VERIFIED
no_geometry_mutation: VERIFIED
```

All 6 tests pass via `standalone_multitarget_verify.py`.

---

## Backward Compatibility

MRP-3A/3B imports continue to work:

```python
# MRP-3A style (still works)
from app.cam.translators.base import ExportTranslator, BaseTranslator

# MRP-4A style (preferred)
from app.cam.translators import (
    resolve_translator,
    TranslatorRegistry,
    TranslatorCapabilities,
)
```

The existing `/api/export/translate/dxf` endpoint remains functional (deprecated in favor of `/api/translate/dxf`).

---

## SVG Output Example

```svg
<!--
Provenance:
  export_id: EXP-BODY-20260514-test
  translator: body_outline_svg v1.0.0
  translated_at: 2026-05-14T12:00:00Z
-->
<svg xmlns="http://www.w3.org/2000/svg" 
     viewBox="-110 -10 220 220" 
     width="220mm" height="220mm">
  <g id="body-outline" transform="scale(1,-1)...">
    <path id="outer" d="M -100 0 L 100 0..." 
          fill="none" stroke="#0066CC" stroke-width="1.5"/>
  </g>
</svg>
```

---

## Governance Invariants

| Invariant | Status |
|-----------|--------|
| Export Object remains canonical | VERIFIED |
| Translators consume, not create semantics | VERIFIED |
| Red gate blocks all translation | VERIFIED |
| No geometry mutation | VERIFIED |
| Deterministic output (sans timestamp) | VERIFIED |
| Registry governs execution authorization | VERIFIED |

---

## Deprecation Path

Existing ad hoc DXF generators should migrate to translator consumption:

**Before:**
```python
doc = ezdxf.new()
# ... direct manipulation
```

**After:**
```python
translator = resolve_translator("dxf", "r12")
result = translator.translate(export_object)
```

---

## Next Steps (MRP-4B+)

1. **STEP Translator**: 3D CAD interchange format
2. **PDF Translator**: Print-ready documentation
3. **Batch Translation**: Multiple targets in single request
4. **Streaming**: Large file support
5. **Migration Tooling**: Migrate remaining ad hoc DXF generators

---

## References

- `docs/handoffs/MRP_3A_DXF_TRANSLATOR_ARCHITECTURE_HANDOFF.md`
- `docs/handoffs/MRP_3B_DXF_TRANSLATOR_API_ENDPOINT_HANDOFF.md`
- `docs/governance/TRANSLATOR_LAYER_RULES.md`
- `docs/governance/MULTI_TARGET_TRANSLATOR_POLICY.md`

---

*MRP-4A complete. Multiple serialization targets now consume Export Objects canonically through a governed abstraction layer.*
