# Pending Patches

Tracking patches in development that require follow-up.

---

## PATCH-001: Fret Math Intonation Model + CAM Manufacturability

**Status**: COMPLETED
**Created**: 2026-01-23
**Completed**: 2026-01-23
**Owner**: User + Claude

### Summary

Tighten fret design architecture:
- Default CAM fret-slot export stays **12-TET** (unchanged behavior)
- Add explicit **opt-in** `intonation_model="custom_ratios"` path
- Use existing ratio infrastructure only when explicitly requested
- Add **manufacturability validation** (min spacing + edge margins)

### Changes Made

#### `services/api/app/schemas/cam_fret_slots.py`
- Added `IntonationModel` type alias: `Literal["equal_temperament_12", "custom_ratios"]`
- Added `intonation_model` field to `FretSlotExportRequest` (default: `"equal_temperament_12"`)
- Added `ratio_set_id` field for named ratio sets (JUST_MAJOR, PYTHAGOREAN, MEANTONE)
- Added `ratios` field for explicit per-fret frequency ratios
- Added `@model_validator` to enforce custom_ratios requirements

#### `services/api/app/calculators/alternative_temperaments.py`
- Added `NAMED_RATIO_SETS` dict for CAM export
- Added `get_ratio_set(ratio_set_id, fret_count)` to generate per-fret ratios
- Added `compute_fret_positions_from_ratios_mm(scale_length_mm, ratios)` for ratio → position conversion
- Added `list_named_ratio_sets()` helper

#### `services/api/app/calculators/fret_slots_export.py`
- Added `validate_fret_positions_for_machining()` for manufacturability checks
- Modified `compute_slot_geometry()` to accept pre-computed `fret_positions` parameter
- Modified `export_fret_slots()` to branch on `intonation_model`
- Added warning for custom_ratios usage

### Contract

- `intonation_model="equal_temperament_12"` (default): Uses `compute_fret_positions_mm()` (unchanged)
- `intonation_model="custom_ratios"`: Requires `ratios[]` or `ratio_set_id`
  - `ratios[]` must have `len == fret_count` with all values `> 1.0`
  - Named ratio sets are expanded to per-fret ratios automatically

### Manufacturability Validation

Applies to ALL intonation models:
- Fret positions must be within bounds (0 < pos < scale_length)
- Adjacent frets must be spaced >= `slot_width_mm * 1.25`
- First fret must be >= 1mm from nut
- Last fret must be >= 1mm from bridge

### Backwards Compatibility

**100% backwards compatible.** All existing calls use default `intonation_model="equal_temperament_12"` which produces identical output to pre-patch behavior.

---

## PATCH-002: Archtop/Smart Guitar Router Design Fix

**Status**: In Development
**Created**: 2026-01-23
**Owner**: User

### Context

During the Option C migration, the following routers were removed and replaced with legacy 308 redirects:

- `archtop_router.py` → `instruments/guitar/archtop_instrument_router.py` + `cam/guitar/archtop_cam_router.py`
- `smart_guitar_router.py` → `instruments/guitar/smart_instrument_router.py` + `cam/guitar/smart_cam_router.py`

### Issue

Design issues identified in the original router implementations that need addressing in the new Option C structure.

### Files to Review

- `services/api/app/routers/instruments/guitar/archtop_instrument_router.py`
- `services/api/app/routers/instruments/guitar/smart_instrument_router.py`
- `services/api/app/routers/cam/guitar/archtop_cam_router.py`
- `services/api/app/routers/cam/guitar/smart_cam_router.py`

### Related

- `docs/ROUTER_INVENTORY_AND_DEPRECATION_PLAN.md`
- `services/api/app/ci/deprecation_registry.json`

---

*Add new patches below this line*
