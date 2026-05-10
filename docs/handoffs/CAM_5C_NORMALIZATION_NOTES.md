# CAM Dev Order 5C — Fret Slot Preview Normalization Notes

**Date:** 2026-05-09  
**Author:** Claude (CAM Dev Order 5C)  
**Status:** COMPLETE

---

## Summary

Normalized the fret slot preview endpoint (`/api/cam/fret_slots/preview`) to comply with governed preview standards without breaking existing frontend consumers.

**Approach:** Additive normalization — all new standard fields added alongside existing legacy fields.

---

## What Changed

### File: `app/cam/routers/fret_slots_router.py`

Added governed preview standard types:
- `CamGate` enum (green/yellow/red)
- `CamIssue` structured issue model
- `CoordinateSystem` metadata model
- `PreviewMetadata` generator provenance model
- `FRET_SLOT_COORDINATE_SYSTEM` constant

Updated `FretSlotsPreviewResponse` with new fields:
- `operation`: "fret_slot_preview"
- `status`: "preview"
- `gate`: derived from messages
- `units`: "mm"
- `coordinate_system`: spatial reference
- `canonical_toolpath`: wrapper for slots
- `warnings`: list of warning strings
- `errors`: list of error strings
- `issues`: structured CamIssue array
- `metadata`: generator info

Added helper functions:
- `_derive_gate_from_messages()`: Maps severity → gate (error→RED, warning→YELLOW)
- `_messages_to_issues()`: Converts RmosMessageOut to CamIssue
- `_normalize_statistics()`: Adds core statistics fields

### File: `tests/cam/test_fret_slots_preview_normalization.py`

Created 32 new tests covering:
- Governed preview fields presence
- Legacy field preservation
- Gate derivation logic
- Statistics normalization
- Issues structure validation
- Coordinate system documentation
- Fan-fret mode compatibility

---

## Coordinate System Documentation

The coordinate system constant was derived from reading actual code behavior in `fret_slots_cam.py`:

```python
FRET_SLOT_COORDINATE_SYSTEM = CoordinateSystem(
    units="mm",
    origin="nut_edge",
    x_axis="scale_length_direction",   # Position along neck
    y_axis="bass_to_treble",           # Across fretboard
    z_axis="depth_into_fretboard",     # Cutting depth (negative)
    z_zero="top_of_fretboard",
    handedness="right_handed",
    frame="local_part",
)
```

Source: Line 161-162 of fret_slots_cam.py:
> "Slots generated bass-to-treble (left-to-right in standard orientation)"

---

## Gate Derivation Logic

Gate is derived from existing RMOS messages (v1 approach):

```python
def _derive_gate_from_messages(messages):
    gate = GREEN
    for msg in messages:
        if msg.severity == "error":
            return RED  # Terminal
        if msg.severity == "warning":
            gate = YELLOW
    return gate
```

Gate escalation only — never de-escalates within a single evaluation.

---

## What Was Preserved (Frontend Compatibility)

All legacy fields remain in the response:
- `model_id`
- `fret_count`
- `slots` (array of FretSlotOut)
- `messages` (array of RmosMessageOut)
- `statistics` (dict with operation-specific fields)

Frontend code consuming these fields will continue to work without modification.

---

## What Was NOT Changed

Per 5C guardrails:

1. **Route path unchanged** — Still `/api/cam/fret_slots/preview` (not renamed to kebab-case)
2. **No geometry rewrites** — `fret_slots_cam.py` calculator untouched
3. **No G-code changes** — Machine output generation unchanged
4. **No frontend changes required** — Additive fields only

---

## Manifest Updates

Updated `cam_preview_standard_manifest.json`:

| Module | Status Before | Status After | Compliance |
|--------|---------------|--------------|------------|
| fret_slots_cam | candidate (45%) | governed_preview (95%) | +50% |
| fret_slots_fan_cam | candidate (40%) | governed_preview (95%) | +55% |

Remaining work for 100%: Route rename to `/fret-slot/preview` (deferred, non-breaking).

---

## Test Results

```
32 passed in 25.66s
Coverage: 23.04% (threshold: 20%)
```

All normalization tests pass. Legacy functionality unaffected.

---

## Future Work (Not 5C Scope)

1. **Route rename** — `/fret_slots/preview` → `/fret-slot/preview` (CAM_PREVIEW_ROUTE_CONVENTIONS.md)
2. **Native gate logic** — Replace message-derived gate with dedicated validation like nut_slot_cam
3. **Additional gate conditions** — Slot depth vs stock thickness, spacing checks

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_PREVIEW_CONTRACT_STANDARD.md` | Response shape spec |
| `CAM_GATE_SEMANTICS_STANDARD.md` | Gate derivation rules |
| `CAM_PREVIEW_METADATA_STANDARD.md` | Statistics requirements |
| `cam_preview_standard_manifest.json` | Compliance tracking |
| `test_fret_slots_preview_normalization.py` | Test coverage |

---

*5C normalization complete: 2026-05-09*
