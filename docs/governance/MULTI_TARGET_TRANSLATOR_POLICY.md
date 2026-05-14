# Multi-Target Translator Policy

**Date:** 2026-05-14  
**Sprint:** MRP-4A  
**Status:** ACTIVE

---

## Purpose

Defines policy for multi-target translation from Export Objects to various serialization formats.

---

## Architecture

```
Export Object (canonical)
    │
    ├── resolve_translator("dxf", "r12")  →  DXF R12 File
    ├── resolve_translator("dxf", "r2000") →  DXF R2000 File
    ├── resolve_translator("svg")          →  SVG Image
    ├── resolve_translator("step")         →  STEP File (future)
    └── resolve_translator("pdf")          →  PDF Document (future)
```

---

## Target Categories

### Serialization

Geometry to file format for CAD/CAM interchange.

| Target | Versions | Status |
|--------|----------|--------|
| DXF | R12, R2000 | governed_execution |
| STEP | TBD | future |

### Visualization

Visual output for preview and documentation.

| Target | Versions | Status |
|--------|----------|--------|
| SVG | 1.1 | governed_execution |
| PDF | TBD | future |
| PNG | TBD | future |

### Manufacturing

Machine-ready output (requires additional authorization).

| Target | Status |
|--------|--------|
| G-code | NOT AUTHORIZED |
| Toolpath | NOT AUTHORIZED |

---

## Target Negotiation

### Basic Resolution

```python
translator = resolve_translator("dxf")  # Default version
```

### Version-Specific

```python
translator = resolve_translator("dxf", "r2000")
```

### With Governance Check

```python
translator = resolve_translator(
    target="dxf",
    version="r12",
    require_governed=True  # Default
)
```

---

## API Endpoints

### List Targets

```
GET /api/translate/targets
```

Response:
```json
{
  "targets": ["dxf", "svg"]
}
```

### Target Info

```
GET /api/translate/targets/dxf
```

Response:
```json
{
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
```

---

## Content Types

| Target | Content-Type |
|--------|--------------|
| dxf | application/dxf |
| svg | image/svg+xml |
| step | application/step |
| pdf | application/pdf |

---

## Response Headers

All translation responses include:

```
X-Export-ID: {export_id}
X-Target-Format: {target}
X-Translator-ID: {translator_id}
X-Translator-Version: {version}
X-Governance-Gate: {green|yellow}
```

Optional (if available):

```
X-Provenance-Hash: {hash}
X-IBG-Session-ID: {session_id}
X-Instrument-Spec: {spec}
X-Governance-Warnings: {warnings}  (yellow gate only)
```

---

## Error Responses

### Target Not Supported (400)

```json
{
  "ok": false,
  "error": "TARGET_NOT_SUPPORTED",
  "reasons": ["Target format 'step' is not supported"],
  "supported_targets": ["dxf", "svg"]
}
```

### Version Not Supported (400)

```json
{
  "ok": false,
  "error": "VERSION_NOT_SUPPORTED",
  "reasons": ["Version 'r14' not supported for target 'dxf'"],
  "supported_versions": ["r12", "r2000"]
}
```

### Red Gate (422)

```json
{
  "ok": false,
  "error": "EXPORT_OBJECT_NOT_TRANSLATABLE",
  "gate": "red",
  "reasons": ["Outer contour not closed"]
}
```

---

## Adding New Targets

To add a new translation target:

1. **Create translator** in `app/cam/translators/{target}/`
2. **Register** with TranslatorRegistry
3. **Add mapping** in `negotiation.py` TARGET_TRANSLATOR_MAP
4. **Add tests** in `tests/translators/`
5. **Update docs** — capability matrix, this policy

---

## Capability Matrix

| Translator | Target | Version | Status | Deterministic | Provenance |
|------------|--------|---------|--------|---------------|------------|
| body_outline_dxf_r12 | dxf | R12 | governed | yes | yes |
| body_outline_dxf_r2000 | dxf | R2000 | governed | yes | yes |
| body_outline_svg | svg | 1.1 | governed | yes | yes |

---

## References

- `docs/governance/TRANSLATOR_LAYER_RULES.md`
- `docs/governance/DXF_TRANSLATOR_SERIALIZATION_POLICY.md`
- `docs/handoffs/MRP_4A_MULTI_TARGET_TRANSLATOR_HANDOFF.md`
