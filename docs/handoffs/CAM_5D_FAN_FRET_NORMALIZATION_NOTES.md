# CAM Dev Order 5D — Fan Fret Preview Normalization Notes

**Date:** 2026-05-09  
**Author:** Claude (CAM Dev Order 5D)  
**Status:** COMPLETE

---

## Summary

Normalized fan fret preview mode to comply with governed preview standards while preserving inheritance compatibility with fret slot CAM (5C).

**Key achievement:** Validates inheritance-aware governed preview normalization.

---

## Corrected Provenance Issue

**Discovery:** During 5D implementation, audit revealed that the router endpoint accepted `mode="fan_fret"` but **did not call the fan fret generator**. It silently ran standard fret slot generation regardless of mode.

**Root cause:** The router only imported and called `generate_fret_slot_toolpaths`, not `generate_fan_fret_cam`.

**Fix:** Wired `mode="fan_fret"` to the actual fan fret generator in `fret_slots_fan_cam.py`.

**Impact:** Without this fix, the governed preview metadata would have been misleading — claiming fan fret operation while producing standard geometry.

---

## Pre-existing Bug Fix

**Issue:** `fret_slots_fan_cam.py` passed `scale_length_reference_mm` to `compute_fan_fret_positions()`, but the function signature uses `_scale_length_reference_mm` (private/deprecated parameter).

**Fix:** Removed the unnecessary argument since it defaults to None.

**Note:** This was a minimal fix to make existing code work, not a geometry rewrite.

---

## What Changed

### File: `app/cam/routers/fret_slots_router.py`

**New imports:**
```python
from app.calculators.fret_slots_fan_cam import generate_fan_fret_cam
```

**Extended models:**
- `CoordinateSystem`: Added `notes` and `coordinate_confidence` optional fields
- `PreviewMetadata`: Added `mode` field

**New constant:**
```python
FAN_FRET_COORDINATE_SYSTEM = CoordinateSystem(
    units="mm",
    origin="nut_edge",
    x_axis="scale_length_direction",
    y_axis="bass_to_treble",
    z_axis="depth_into_fretboard",
    z_zero="top_of_fretboard",
    handedness="right_handed",
    frame="local_part",
    notes="Fan fret slots are angled; each slot has separate bass and treble X positions. "
          "Perpendicular fret is marked with is_perpendicular=true.",
    coordinate_confidence="documented_from_current_code",
)
```

**Endpoint changes:**
- Branch on `mode` to call appropriate generator
- Mode-aware `operation` field: `"fan_fret_preview"` vs `"fret_slot_preview"`
- Mode-aware `coordinate_system`: Fan fret gets notes about angled slots
- Mode-aware `generator_id` in metadata
- Mode field in metadata
- Fan-specific fields in `canonical_toolpath`: bass_scale_mm, treble_scale_mm, perpendicular_fret
- Validation for missing fan fret parameters (returns RED gate with error)

### File: `app/calculators/fret_slots_fan_cam.py`

**Bug fix:** Removed invalid `scale_length_reference_mm` argument from `compute_fan_fret_positions()` call.

### File: `tests/cam/test_fan_fret_preview_normalization.py`

Created 25 new tests covering:
- Governed preview fields for fan fret mode
- Legacy field preservation
- Fan fret generator wiring (angled slots verification)
- Standard mode unchanged
- Gate inheritance
- Statistics normalization
- Issues structure

---

## Mode-Aware Behavior

| Aspect | Standard Mode | Fan Fret Mode |
|--------|---------------|---------------|
| operation | `fret_slot_preview` | `fan_fret_preview` |
| generator_id | `fret_slots_cam` | `fret_slots_fan_cam` |
| coordinate_system.notes | null | Angled slot documentation |
| canonical_toolpath | slots, slot_count, mode | + bass_scale_mm, treble_scale_mm, perpendicular_fret |
| statistics | Standard fields | + mode, bass_scale_mm, treble_scale_mm, max_angle_deg |

---

## Shared Infrastructure Reuse

5D maximizes reuse of 5C infrastructure:

| Component | Reused from 5C |
|-----------|----------------|
| `CamGate` enum | Yes |
| `CamIssue` model | Yes |
| `PreviewMetadata` model | Extended (added mode) |
| `CoordinateSystem` model | Extended (added notes, confidence) |
| `_derive_gate_from_messages()` | Yes |
| `_messages_to_issues()` | Yes |
| `_normalize_statistics()` | Yes |

---

## Fan Fret Coordinate Semantics

Documented from `fret_slots_fan_cam.py` line 164-165:
```python
bass_pt = (fret_point.bass_pos_mm, fret_point.center_y + half_width)
treble_pt = (fret_point.treble_pos_mm, fret_point.center_y - half_width)
```

Key differences from standard mode:
- Slots have **different X positions** for bass and treble endpoints
- `angle_rad` field contains the slot angle
- `is_perpendicular` flag marks the neutral fret
- Statistics include `max_angle_deg`

Confidence: `documented_from_current_code`

---

## Test Results

```
tests/cam/test_fret_slots_preview_normalization.py: 32 passed
tests/cam/test_fan_fret_preview_normalization.py: 25 passed
Total: 57 tests, 0 failures
Coverage: 23.04%
```

---

## What Was NOT Changed

Per 5D guardrails:
1. **No geometry rewrite** — Fan fret math in `fret_slots_fan_cam.py` unchanged (except bug fix)
2. **No scale interpolation changes** — Dual scale calculation unchanged
3. **No G-code changes** — Machine output generation unchanged
4. **No route splitting** — Single endpoint serves both modes
5. **Standard mode unchanged** — All 5C tests still pass

---

## Future Work (Not 5D Scope)

1. **Fan-specific gate rules** — Could add validation for scale length differential, angle limits
2. **Perpendicular fret validation** — Could warn if perpendicular fret is at extremes
3. **Route separation** — Could split to `/fret-slot/preview` and `/fan-fret/preview` if needed

---

## Strategic Outcome

After 5D:
- The governed preview normalization pipeline supports **inheritance-aware** CAM systems
- Fan fret mode now uses the **actual fan fret generator** (corrected provenance)
- Both modes share gate derivation, statistics normalization, and metadata patterns

This validates that 5C's additive normalization approach extends cleanly to dependent modules.

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_5C_NORMALIZATION_NOTES.md` | Base normalization pattern |
| `CAM_PREVIEW_CONTRACT_STANDARD.md` | Response shape spec |
| `CAM_GATE_SEMANTICS_STANDARD.md` | Gate derivation rules |
| `test_fan_fret_preview_normalization.py` | Test coverage |

---

*5D normalization complete: 2026-05-09*
