# Codebase Math Audit: "All Math in Subroutines" Compliance

**Date:** December 20, 2025
**Principle:** All math operations must be in their own subroutines (Fortran/Basic Rule, c. 1980)
**Modern Names:** Separation of Concerns, Single Responsibility Principle, Pure Functions

---

## Executive Summary

This audit follows from the Fret Router Consolidation and Instrument Geometry Cleanup. While `instrument_geometry/` now follows the subroutine principle, **significant violations exist throughout the codebase**, particularly in routers and generators.

| Section | Status | Violations |
|---------|--------|------------|
| `instrument_geometry/` | ✅ CLEAN | 0 (just completed cleanup) |
| `cam/` core modules | ✅ CLEAN | 0 (math properly isolated) |
| `routers/` | ❌ VIOLATIONS | 18+ files with inline math |
| `generators/` | ❌ VIOLATIONS | 2 files with inline math |
| `calculators/` | ⚠️ DUPLICATES | 2 duplicate implementations |
| `ltb_calculators/` | ⚠️ DUPLICATES | 1 duplicate implementation |
| Various files | ⚠️ HARDCODED PI | Using `3.14159` instead of `math.pi` |

---

## Phase 1: Instrument Geometry (COMPLETED)

**Status: ✅ COMPLIANT**

```
instrument_geometry/
├── neck/
│   ├── fret_math.py       ← All fret calculations HERE
│   ├── neck_profiles.py   ← Neck specs
│   └── radius_profiles.py ← Compound radius math
├── bridge/
│   ├── geometry.py        ← Bridge placement math
│   ├── compensation.py    ← Intonation compensation
│   └── placement.py       ← Bridge calculations
├── body/
│   └── fretboard_geometry.py ← Fretboard outline math
└── bracing/               ← Bracing pattern math
```

**Completed Actions:**
- Deleted 7 shim/duplicate files
- Updated imports to canonical locations
- All 34 tests passing

---

## Phase 2: CAM Core Modules (COMPLIANT)

**Status: ✅ PROPERLY ORGANIZED**

The `cam/` directory correctly separates math into dedicated modules:

```
cam/
├── adaptive_core.py       ← Polygon offset math
├── adaptive_core_l1.py    ← L.1 spiralizer algorithms
├── adaptive_core_l2.py    ← L.2 continuous spiral math
├── feedtime.py            ← Feed/time calculations
├── feedtime_l3.py         ← Jerk-aware timing math
├── trochoid_l3.py         ← Trochoidal insertion math
├── energy_model.py        ← Spindle energy calculations
└── helical_core.py        ← Helical bore math
```

These modules are **pure math** with no HTTP/API dependencies. ✅

---

## Phase 3: ROUTER VIOLATIONS

**Status: ❌ 18+ ROUTERS CONTAIN INLINE MATH**

These routers violate the principle by computing math directly instead of calling subroutines:

### Critical Violations (Complete Functions Inline)

| Router | Lines | Violation | Should Move To |
|--------|-------|-----------|----------------|
| `neck_router.py` | 86-97 | `calculate_fret_positions()` - full fret math | `neck/fret_math.py` |
| `parametric_guitar_router.py` | 59-177 | `generate_body_outline()` - bezier curves, ellipses | `body/parametric.py` |
| `cam_post_v155_router.py` | 63-367 | Biarc math, arc fitting, radius calculations | `cam/biarc_math.py` |
| `sim_validate.py` | 83-135 | Arc angle normalization, sweep calculations | `cam/arc_math.py` |

### Moderate Violations (Inline Calculations)

| Router | Line(s) | Violation |
|--------|---------|-----------|
| `adaptive_router.py` | 567-580 | Arc to polyline conversion with sin/cos |
| `geometry_router.py` | 563-590 | Arc discretization with angle math |
| `art_studio_rosette_router.py` | 144-146 | Circle generation with sin/cos |
| `cam_drill_pattern_router.py` | 99-100 | Circle pattern generation |
| `adaptive_preview_router.py` | 128-139 | Sine wave offset calculations |
| `dxf_preflight_router.py` | 730 | Distance calculation `**0.5` |
| `cam_simulate_router.py` | 61 | 3D distance calculation |
| `blueprint_cam_bridge.py` | 916 | 3D path length calculation |
| `cam_metrics_router.py` | 238 | Acceleration formula |
| `archtop_router.py` | 182+ | Bridge fit calculations |
| `rmos_saw_ops_router.py` | 34-39 | Circumference calculations |

### Example: `neck_router.py` (Line 86-97)

```python
# ❌ VIOLATION: Math in router file
def calculate_fret_positions(scale_length: float, num_frets: int = 22) -> List[float]:
    """
    Calculate fret positions using equal temperament formula.
    Returns distance from nut to each fret.
    """
    positions = []
    for n in range(1, num_frets + 1):
        distance = scale_length - (scale_length / (2 ** (n / 12)))
        positions.append(distance)
    return positions
```

**This EXACT function already exists in `neck/fret_math.py`!**

```python
# ✅ CORRECT: Should call the subroutine
from ..instrument_geometry.neck.fret_math import compute_fret_positions_mm
```

---

## Phase 4: GENERATOR VIOLATIONS

**Status: ❌ 2 GENERATORS WITH INLINE MATH**

| Generator | Lines | Violation |
|-----------|-------|-----------|
| `lespaul_body_generator.py` | 193-522 | Arc generation, perimeter calculation, chord math |
| `neck_headstock_generator.py` | 326-338 | Neck profile curves with sin/cos |

These generators should call utility functions from a `geometry/curves.py` module.

---

## Phase 5: CALCULATOR DUPLICATES

**Status: ⚠️ DUPLICATE IMPLEMENTATIONS**

### Fret Slot Calculators (Same Function, Different Files)

| File | Function | Lines | Notes |
|------|----------|-------|-------|
| `fret_slots_cam.py` | `generate_gcode()` | 934 | Full CAM with fan-fret |
| `fret_slots_export.py` | `generate_gcode()` | 367 | Simpler, post-processor templates |

**Both compute fret geometry differently.** Should be ONE source of truth.

### Luthier Calculator (Duplicate of fret_math.py)

| File | Function | Duplicate Of |
|------|----------|--------------|
| `luthier_calculator.py:329` | `fret_position()` | `fret_math.compute_fret_positions_mm()` |
| `luthier_calculator.py:365` | `fret_spacing()` | `fret_math.compute_fret_spacing_mm()` |
| `luthier_calculator.py:384` | `fret_table()` | `fret_math.generate_fret_table()` |
| `luthier_calculator.py:411` | `scale_length_from_frets()` | No canonical version |

---

## Phase 6: HARDCODED PI VALUES

**Status: ⚠️ USING `3.14159` INSTEAD OF `math.pi`**

These files use hardcoded Pi approximations instead of `math.pi`:

| File | Line(s) | Value Used |
|------|---------|------------|
| `feasibility_scorer.py` | 409, 410, 417, 418, 432 | `3.14159` |
| `fret_router.py` | 467 | `3.14159265359` |
| `feasibility_fusion.py` | 434 | `3.14159265359` |
| `fret_slots_cam.py` | 344, 436, 515, 578, 743, 898 | `3.14159` |
| `calculators/service.py` | 315, 393, 399 | `3.14159` |

**Why This Matters:**
- Inconsistent precision across the codebase
- Harder to maintain
- Violation of DRY principle

**Fix:** Replace with `math.pi` or define `PI = math.pi` constant.

---

## Recommended Cleanup Priority

### Tier 1: High Impact (Same Pattern as Instrument Geometry)

1. **`neck_router.py`** - Delete inline `calculate_fret_positions()`, use `fret_math.py`
2. **`luthier_calculator.py`** - Delegate to `fret_math.py` instead of reimplementing
3. **`fret_slots_cam.py` + `fret_slots_export.py`** - Merge into single source

### Tier 2: Medium Impact (Extract to Utility Modules)

4. **`parametric_guitar_router.py`** - Extract `generate_body_outline()` to `body/parametric.py`
5. **`cam_post_v155_router.py`** - Extract biarc math to `cam/biarc_math.py`
6. **`sim_validate.py`** - Extract arc math to `cam/arc_math.py`

### Tier 3: Low Impact (Quick Fixes)

7. **Replace all `3.14159` with `math.pi`** - Search & replace across codebase
8. **Minor router cleanups** - Move small inline calculations to utilities

---

## Verification Commands

```bash
# Find routers with math imports
grep -rn "import math" --include="*_router.py" | grep -v __pycache__

# Find hardcoded Pi values
grep -rn "3\.14159" --include="*.py" | grep -v __pycache__

# Find inline fret calculations (should only be in fret_math.py)
grep -rn "2 \*\* (.*/ 12)" --include="*.py" | grep -v fret_math

# Count violations
grep -rn "import math" services/api/app/routers --include="*.py" | wc -l
```

---

## Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Routers with `import math` | 18+ | 0 |
| Duplicate fret implementations | 3 | 1 |
| Hardcoded Pi occurrences | 20+ | 0 |
| Files with inline geometry math | 20+ | 0 |

---

## The Fortran Rule Applied

Your engineering professors' rule from 45 years ago:

> **"All math operations must be in their own subroutine"**

Applied to this codebase:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CORRECT ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  API LAYER (Routers)           MATH LAYER (Subroutines)        │
│  ─────────────────────         ─────────────────────────        │
│                                                                 │
│  fret_router.py                instrument_geometry/             │
│    │                             └── neck/fret_math.py          │
│    └── calls ──────────────────────► compute_fret_positions_mm  │
│                                                                 │
│  parametric_guitar_router.py   geometry/                        │
│    │                             └── curves.py                  │
│    └── calls ──────────────────────► generate_bezier_curve      │
│                                      generate_ellipse_arc       │
│                                                                 │
│  cam_drill_pattern_router.py   geometry/                        │
│    │                             └── circles.py                 │
│    └── calls ──────────────────────► generate_circle_points     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Immediate:** Fix `neck_router.py` duplicate (10 minutes)
2. **Short-term:** Merge fret slot calculators (1-2 hours)
3. **Medium-term:** Extract geometry math from routers (4-6 hours)
4. **Ongoing:** Add CI lint rule to prevent new violations

---

*This audit continues from FRET_ROUTER_CONSOLIDATION_EXECUTIVE_SUMMARY.md*
*The Fortran Rule (1980) = Separation of Concerns (2025)*
