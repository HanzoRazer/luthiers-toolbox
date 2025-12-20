# Instrument Geometry Module Audit

**Date:** December 20, 2025
**Status:** ✅ CLEANUP COMPLETE

---

## Executive Summary

The `instrument_geometry/` module has been **fully organized**. All compatibility shims have been removed and imports updated to use canonical locations.

| Status | Description |
|--------|-------------|
| ✅ **Complete** | Core math in `neck/`, `bridge/`, `body/` subdirectories |
| ✅ **Complete** | All imports use canonical paths |
| ✅ **Removed** | `scale_intonation.py` deleted (was duplicate logic) |
| ✅ **Removed** | `.bak` files deleted |
| ✅ **Removed** | All shim files deleted (bridge_geometry.py, fretboard_geometry.py, scale_length.py, radius_profiles.py, profiles.py) |

---

## Directory Structure (Post-Cleanup)

```
instrument_geometry/
├── neck/                         # ✅ CANONICAL - Fret & Neck Math
│   ├── __init__.py
│   ├── fret_math.py             # Core fret calculations (620+ lines)
│   ├── neck_profiles.py         # Neck specs, FretboardSpec
│   └── radius_profiles.py       # Compound radius calculations
│
├── bridge/                       # ✅ CANONICAL - Bridge Math
│   ├── __init__.py
│   ├── compensation.py          # Intonation compensation
│   ├── geometry.py              # Bridge location, saddle positions
│   └── placement.py             # Bridge placement calculations
│
├── body/                         # ✅ CANONICAL - Body/Fretboard Geometry
│   ├── __init__.py
│   ├── fretboard_geometry.py    # Outline, slots, width calculations
│   ├── outlines.py              # Body outline catalog
│   └── detailed_outlines.py     # Extended outline data
│
├── bracing/                      # ✅ CANONICAL - Bracing Math
├── guitars/                      # ✅ Model-specific data
├── models/                       # ✅ Model definitions (JSON specs)
├── specs/                        # ✅ Specifications
│
├── __init__.py                   # ✅ Re-exports from canonical locations
├── dxf_loader.py                 # DXF file loading
├── dxf_registry.py               # DXF registry management
├── fan_fret_guard.py             # Fan fret validation
├── model_registry.py             # Model registry
├── model_spec.py                 # Model spec utilities
├── models.py                     # Model enums
└── spacing.py                    # String spacing calculations
```

---

## Function Mapping

### Fret Calculations (Canonical: `neck/fret_math.py`)

| Function | Location | Status |
|----------|----------|--------|
| `compute_fret_positions_mm` | `neck/fret_math.py:135` | ✅ Canonical |
| `compute_fret_spacing_mm` | `neck/fret_math.py:182` | ✅ Canonical |
| `compute_compensated_scale_length_mm` | `neck/fret_math.py:225` | ✅ Canonical |
| `compute_fret_to_bridge_mm` | `neck/fret_math.py:253` | ✅ Canonical |
| `compute_multiscale_fret_positions_mm` | `neck/fret_math.py:281` | ✅ Canonical |
| `compute_fan_fret_positions` | `neck/fret_math.py:523` | ✅ Canonical |
| `validate_fan_fret_geometry` | `neck/fret_math.py:616` | ✅ Canonical |

### Bridge Calculations (Canonical: `bridge/`)

| Function | Location | Status |
|----------|----------|--------|
| `compute_bridge_location_mm` | `bridge/geometry.py:34` | ✅ Canonical |
| `compute_saddle_positions_mm` | `bridge/geometry.py:50` | ✅ Canonical |
| `compute_bridge_height_profile` | `bridge/geometry.py:77` | ✅ Canonical |
| `compute_compensation_estimate` | `bridge/geometry.py:166` | ✅ Canonical |
| `compute_compensated_bridge` | `bridge/compensation.py:42` | ✅ Canonical |
| `compute_bridge_placement` | `bridge/placement.py:38` | ✅ Canonical |

### Radius Calculations (Canonical: `neck/radius_profiles.py`)

| Function | Location | Status |
|----------|----------|--------|
| `compute_compound_radius_at_fret` | `neck/radius_profiles.py:40` | ✅ Canonical |
| `compute_radius_arc_points` | `neck/radius_profiles.py:74` | ✅ Canonical |
| `compute_radius_drop_mm` | `neck/radius_profiles.py:127` | ✅ Canonical |
| `generate_compound_radius_profile` | `neck/radius_profiles.py:204` | ✅ Canonical |

### Fretboard Geometry (Canonical: `body/fretboard_geometry.py`)

| Function | Location | Status |
|----------|----------|--------|
| `compute_fretboard_outline` | `body/fretboard_geometry.py:20` | ✅ Canonical |
| `compute_fret_slot_lines` | `body/fretboard_geometry.py:106` | ✅ Canonical |
| `compute_width_at_position_mm` | `body/fretboard_geometry.py:73` | ✅ Canonical |
| `compute_string_spacing_at_position` | `body/fretboard_geometry.py:149` | ✅ Canonical |

---

## Issues Found & Resolved

### 1. ✅ RESOLVED: Duplicate Logic in `scale_intonation.py`

**Previous State:** This file had duplicate fret math logic and was not a pure shim.

**Resolution:** File deleted. Similar compensation functions already exist in `bridge/compensation.py`.

### 2. ✅ RESOLVED: Backup File Deleted

**Previous State:** `instrument_geometry/neck/fret_math.py.bak` existed.

**Resolution:** File deleted.

### 3. ✅ RESOLVED: All Shims Removed

**Previous State:** 5 shim files existed for backward compatibility.

**Resolution:** All imports updated to canonical locations. Shims deleted:
- `bridge_geometry.py`
- `fretboard_geometry.py`
- `scale_length.py`
- `radius_profiles.py`
- `profiles.py`

---

## Related Modules

### `calculators/` Directory

| File | Purpose | Relation to instrument_geometry |
|------|---------|--------------------------------|
| `alternative_temperaments.py` | Just intonation, Pythagorean | Uses fret_math indirectly |
| `fret_slots_cam.py` | CAM toolpath generation | Consumes fret positions |
| `fret_slots_export.py` | G-code export | Consumes fret positions |
| `inlay_calc.py` | Fretboard inlay positions | Uses fret positions |

### `ltb_calculators/` Directory

| File | Purpose | Status |
|------|---------|--------|
| `luthier_calculator.py` | LTBLuthierCalculator class | Has own fret_position method |

**Note:** `LTBLuthierCalculator.fret_position()` duplicates `compute_fret_positions_mm` logic.

---

## Recommendations

### ✅ Completed (December 20, 2025)

1. ✅ **Deleted** `neck/fret_math.py.bak`
2. ✅ **Searched & documented** all usages of shim files
3. ✅ **Deleted** `scale_intonation.py` (was duplicate logic)
4. ✅ **Removed shims** after updating all imports
5. ✅ **Updated** `__init__.py` re-exports for clean public API

### Remaining (Low Priority)

- **Consolidate** `LTBLuthierCalculator.fret_position()` to call `fret_math.py`

---

## Verification

All 34 instrument_geometry tests pass after cleanup:
- `test_instrument_geometry.py` - 32 tests PASSED
- `test_instrument_geometry_imports.py` - 2 tests PASSED

---

*Audit performed by: Claude Opus 4.5*
*Session: Fret Router Consolidation + Geometry Audit*
*Cleanup completed: December 20, 2025*
