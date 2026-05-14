# DXF Translator Serialization Policy

**Date:** 2026-05-14  
**Sprint:** MRP-4A  
**Status:** ACTIVE

---

## Purpose

Defines serialization policy for governed DXF translators producing DXF output from Export Objects.

---

## Format Versions

### R12 (AC1009) — Free Tier

- Entity type: LINE (individual segments)
- Maximum compatibility with legacy CAM systems
- Translator ID: `body_outline_dxf_r12`

### R2000 (AC1015) — Paid Tier

- Entity type: LWPOLYLINE (multi-point contours)
- Modern CAM workflow support
- Translator ID: `body_outline_dxf_r2000`

---

## Layer Convention

| Layer Name | Color | Purpose |
|------------|-------|---------|
| BODY_OUTLINE | 5 (Blue) | Outer contours |
| VOID | 1 (Red) | Internal voids |
| PROVENANCE | 8 (Gray) | Metadata text |

**No geometry on layer 0.**

---

## Coordinate Precision

- Default: 3 decimal places
- Configurable via `TranslatorOptions.coordinate_precision`
- Rounding applied consistently to all coordinates

---

## Provenance Embedding

When `embed_provenance=True` (default):

```
TEXT entities on PROVENANCE layer:
  Export ID: EXP-BODY-20260514-xxx
  Translator: body_outline_dxf_r12 v1.0.0
  Translated: 2026-05-14
  IBG Session: ibg-xxx (if present)
  Instrument: dreadnought (if present)
```

Position: Below geometry bounding box (y_min - 15mm)

---

## Contour Handling

- Closed contours: Polyline with `closed=True`
- Open contours: Not currently supported (error)
- Minimum points: 3 per contour

---

## Header Settings

```
$INSUNITS = 4 (mm)
$MEASUREMENT = 1 (metric)
```

Note: R12 does not export $INSUNITS (ezdxf limitation).

---

## Determinism Requirements

Same Export Object + same options → same DXF output

**Except:** Provenance timestamp when `embed_provenance=True`

For strict determinism testing, use `embed_provenance=False`.

---

## Gate Behavior

| Gate | DXF Translator Action |
|------|----------------------|
| GREEN | Generate DXF |
| YELLOW | Generate DXF + warning header |
| RED | Reject with TranslatorErrorCode.GATE_RED |

---

## DXF Writer Governance

All DXF generation routes through:

```
app/cam/dxf_writer.py (PROTECTED)
  └── app/util/dxf_compat.py (PROTECTED)
```

Direct `ezdxf.new()` calls are forbidden outside these modules.

---

## Migration Path

Existing DXF generators should migrate to translator consumption:

**Before (ad hoc):**
```python
doc = ezdxf.new()
# ... direct ezdxf manipulation
```

**After (governed):**
```python
from app.cam.translators import resolve_translator

translator = resolve_translator("dxf", "r12")
result = translator.translate(export_object)
```

---

## References

- `docs/governance/TRANSLATOR_LAYER_RULES.md`
- `CLAUDE.md` — DXF output standard section
- `app/cam/dxf_writer.py` — Protected DXF writer
