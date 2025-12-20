# Architecture Cleanup Master Report

**Luthier's Toolbox - Code Quality Initiative**
**Date:** December 20, 2025
**Principle:** "All math operations must be in their own subroutines" (Fortran Rule, c. 1980)

---

## The Journey: From Router Sprawl to Clean Architecture

This report documents a comprehensive architectural cleanup that began with a simple task and evolved into a fundamental improvement of the codebase structure.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE TRANSFORMATION JOURNEY                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   PHASE 1              PHASE 2              PHASE 3              PHASE 4   │
│   Router               Bug                  Module                Math      │
│   Consolidation        Discovery            Cleanup               Audit     │
│                                                                             │
│   ┌─────────┐         ┌─────────┐         ┌─────────┐         ┌─────────┐ │
│   │ Fret    │         │ /api/api│         │ Delete  │         │ Find    │ │
│   │ Endpoints│   →    │ Double  │   →     │ Shims   │   →     │ All     │ │
│   │ Scattered│        │ Prefix  │         │ Update  │         │ Stray   │ │
│   │ (12+)   │         │ Bug (36)│         │ Imports │         │ Math    │ │
│   └─────────┘         └─────────┘         └─────────┘         └─────────┘ │
│        │                   │                   │                   │       │
│        ▼                   ▼                   ▼                   ▼       │
│   ┌─────────┐         ┌─────────┐         ┌─────────┐         ┌─────────┐ │
│   │ Created │         │ Fixed   │         │ Clean   │         │ 18+     │ │
│   │ fret_   │         │ 11      │         │ Module  │         │ Router  │ │
│   │ router  │         │ Router  │         │ Structure│        │ Violations│
│   │ (13 ep) │         │ Regs    │         │ (7 files)│        │ Documented│
│   └─────────┘         └─────────┘         └─────────┘         └─────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Fret Router Consolidation

**Problem:** Fret calculation endpoints were scattered across 4 routers.

**Actions:**
- Removed 12+ duplicate endpoints from:
  - `instrument_router.py` (3 endpoints)
  - `instrument_geometry_router.py` (6 endpoints)
  - `ltb_calculator_router.py` (2 endpoints)
  - `temperament_router.py` (1 endpoint)
- Created consolidated `fret_router.py` with 13 focused endpoints

**E2E Testing:** Found and fixed 4 parameter mismatch bugs.

**Governance:** Created `COMPONENT_ROUTER_RULE_v1.md` and CI tests.

**Detailed Report:** `FRET_ROUTER_CONSOLIDATION_EXECUTIVE_SUMMARY.md`

---

## Phase 2: Double Prefix Bug Discovery

**Discovery:** CI governance tests caught 36 routes with `/api/api/` malformed paths.

**Root Cause:** Routers with own `/api` prefix registered with additional `prefix="/api"`.

**Fix:** Updated 11 router registrations in `main.py` to use `prefix=""`.

**Lesson:** Governance tests pay immediate dividends.

---

## Phase 3: Instrument Geometry Module Cleanup

**Question:** "Is bridge math, neck math, etc. all in their own directory?"

**Answer:** Partially. Migration was incomplete with orphaned shim files.

**Actions:**
| Action | Files |
|--------|-------|
| Deleted backup | `fret_math.py.bak` |
| Deleted duplicate logic | `scale_intonation.py` |
| Deleted shims | `bridge_geometry.py`, `fretboard_geometry.py`, `scale_length.py`, `radius_profiles.py`, `profiles.py` |
| Updated imports | `instrument_router.py`, `test_instrument_geometry.py`, `__init__.py` |

**Result:** 34 tests passing, clean module structure.

**Detailed Report:** `INSTRUMENT_GEOMETRY_AUDIT.md`

---

## Phase 4: Codebase-Wide Math Audit (Sanity Check)

**Question:** "Can we now say this repo follows the Fortran Rule?"

**Answer:** **Not yet.** Significant violations remain.

### Violations Found

| Category | Count | Status |
|----------|-------|--------|
| `instrument_geometry/` | 0 | ✅ CLEAN |
| `cam/` core modules | 0 | ✅ CLEAN |
| `routers/` with inline math | 18+ | ❌ VIOLATIONS |
| `generators/` with inline math | 2 | ❌ VIOLATIONS |
| Duplicate calculator functions | 3 | ⚠️ DUPLICATES |
| Hardcoded Pi (`3.14159`) | 20+ | ⚠️ INCONSISTENT |

### Top Violations

1. **`neck_router.py:86-97`** - Reimplements `compute_fret_positions_mm()`
2. **`parametric_guitar_router.py`** - 120+ lines of bezier/ellipse math
3. **`cam_post_v155_router.py`** - 300+ lines of biarc math
4. **`luthier_calculator.py`** - Duplicates fret_math functions
5. **`fret_slots_cam.py` + `fret_slots_export.py`** - Two G-code generators

**Detailed Report:** `CODEBASE_MATH_AUDIT.md`

---

## Summary: Fortran Rule Compliance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    "ALL MATH IN SUBROUTINES" COMPLIANCE                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Section                          Before          After           Status   │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  instrument_geometry/             Partial         Complete        ✅       │
│    └── neck/fret_math.py         ✓               ✓                        │
│    └── bridge/geometry.py        ✓               ✓                        │
│    └── body/fretboard_geometry   ✓               ✓                        │
│    └── [6 shim files]            Present         DELETED                   │
│                                                                             │
│  cam/ core modules                                                ✅       │
│    └── adaptive_core*.py         ✓               ✓                        │
│    └── feedtime*.py              ✓               ✓                        │
│    └── trochoid_l3.py            ✓               ✓                        │
│                                                                             │
│  routers/                         18+ violations  Documented      ❌       │
│    └── neck_router.py            Fret math       NEEDS FIX                │
│    └── parametric_guitar_router  Bezier math     NEEDS FIX                │
│    └── cam_post_v155_router.py   Biarc math      NEEDS FIX                │
│                                                                             │
│  calculators/                     Duplicates      Documented      ⚠️       │
│    └── fret_slots_*.py           2 versions      NEEDS MERGE              │
│    └── luthier_calculator.py     Duplicates      NEEDS DELEGATE           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 5: Fortran Rule Compliance Fixes (COMPLETED)

**Session:** December 20, 2025 (Continuation)

Following the audit, these Priority 1-3 items were addressed:

### ✅ Completed Fixes

| Item | Action | Result |
|------|--------|--------|
| `neck_router.py` | Removed inline `calculate_fret_positions()`, delegates to `fret_math.py` | FIXED |
| `luthier_calculator.py` | Refactored `fret_position()`, `fret_spacing()` to delegate to `fret_math.py` | FIXED |
| Hardcoded Pi values | Replaced 20+ occurrences of `3.14159` with `math.pi` across 8 files | FIXED |
| Fret slot calculators | Audited - confirmed as complementary modules, not duplicates | CLARIFIED |
| `parametric_guitar_router.py` | Extracted 120+ lines of bezier/ellipse math to `body/parametric.py` | FIXED |
| `cam_post_v155_router.py` | Extracted fillet/arc math to `cam/biarc_math.py` | FIXED |

### New Modules Created

| Module | Purpose | Functions |
|--------|---------|-----------|
| `instrument_geometry/body/parametric.py` | Parametric body generation | `generate_body_outline()`, `cubic_bezier()`, `ellipse_point()` |
| `cam/biarc_math.py` | Arc and fillet calculations | `fillet_between()`, `arc_tessellate()`, `arc_center_from_radius()` |

### Files Modified for Pi Replacement

- `calculators/fret_slots_cam.py` (6 occurrences)
- `calculators/service.py` (3 occurrences)
- `rmos/feasibility_scorer.py` (5 occurrences)
- `rmos/feasibility_fusion.py` (1 occurrence)
- `saw_lab/risk_evaluator.py` (2 occurrences)
- `saw_lab/calculators/saw_heat.py` (1 occurrence)
- `routers/fret_router.py` (1 occurrence)
- `_experimental/cnc_production/feeds_speeds/core/deflection_model.py` (1 occurrence)

### Remaining Router Violations (Lower Priority) - NOW FIXED

These routers have been updated to use the new `geometry/arc_utils.py` module:

| Router | Fix Applied |
|--------|-------------|
| `adaptive_router.py` | Delegates arc tessellation to `tessellate_arc_radians()` |
| `geometry_router.py` | Delegates arc discretization to `tessellate_arc_radians()` |
| `art_studio_rosette_router.py` | Delegates circle generation to `generate_circle_points()` |
| `sim_validate.py` | Delegates arc math to `arc_center_from_endpoints()`, `compute_arc_length()` |
| `rmos_saw_ops_router.py` | Delegates circumference to `circle_circumference()`, `arc_length_from_angle()` |

---

## Phase 6: Low-Priority Router Cleanup (COMPLETED)

**Session:** December 20, 2025 (Continuation)

Created new `geometry/arc_utils.py` module with comprehensive arc/circle utilities:

### New Module: `geometry/arc_utils.py`

| Function | Purpose |
|----------|---------|
| `generate_circle_points()` | Generate points around a circle |
| `tessellate_arc()` | Convert arc to line segments (degrees) |
| `tessellate_arc_radians()` | Convert arc to line segments (radians) |
| `arc_center_from_endpoints()` | Calculate arc center from start/end + radius |
| `arc_signed_sweep()` | Calculate signed sweep angle |
| `arc_length()` | Calculate arc length from center + endpoints |
| `arc_length_from_angle()` | Calculate arc length from radius + angle |
| `circle_circumference()` | Calculate circle circumference |
| `nearest_point_distance()` | Find minimum distance to point cloud |
| `trapezoidal_motion_time()` | Calculate motion time with accel profile |

---

## Metrics Summary

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Fret endpoints (scattered) | 12+ | 0 | -100% |
| Fret endpoints (consolidated) | 0 | 13 | NEW |
| Routes with double prefix | 36 | 0 | -100% |
| Shim files | 6 | 0 | -100% |
| Governance tests | 0 | 6 | NEW |
| **Hardcoded Pi values** | 20+ | 0 | **-100%** |
| **Routers with duplicate math** | 18+ | ~10 | **-44%** |
| **New math modules created** | 0 | 2 | **NEW** |
| Duplicate fret implementations | 3 | 0 | -100% |

---

## Documents Created

| Document | Purpose |
|----------|---------|
| `COMPONENT_ROUTER_RULE_v1.md` | Prevent future endpoint sprawl |
| `FRET_ENDPOINT_MIGRATION.md` | Frontend migration guide |
| `INSTRUMENT_GEOMETRY_AUDIT.md` | Module structure audit |
| `FRET_ROUTER_CONSOLIDATION_EXECUTIVE_SUMMARY.md` | Phase 1-2 summary |
| `CODEBASE_MATH_AUDIT.md` | Math violations catalog |
| `ARCHITECTURE_CLEANUP_MASTER_REPORT.md` | This unified report |
| `test_route_governance.py` | CI enforcement tests |

---

## Recommended Next Phase

### ✅ Completed (Phase 5)

1. ~~**`neck_router.py`** - Delete inline fret function, import from `fret_math.py`~~ **DONE**
2. ~~**Replace `3.14159`** - Search/replace with `math.pi` across codebase~~ **DONE**
3. ~~**`luthier_calculator.py`** - Delegate fret methods to `fret_math.py`~~ **DONE**
4. ~~**Extract parametric geometry** - Create `body/parametric.py`~~ **DONE**
5. ~~**Extract biarc math** - Create `cam/biarc_math.py`~~ **DONE**

### Remaining Work (Lower Priority)

6. **Add CI lint rule** - Prevent `import math` in router files
7. **Consolidate CAM version routers** - v155, v160, v161 → single versioned file
8. **Extract remaining arc math** - Circle generation, arc discretization utilities

---

## The Fundamental Principle

Your Fortran/Basic professors from 45 years ago were right:

> **"All math operations must be in their own subroutine"**

This is not old-fashioned thinking. It's timeless architecture wisdom that modern software engineering has simply renamed:

| 1980 Term | 2025 Term |
|-----------|-----------|
| Subroutine | Pure Function |
| "Keep math separate" | Separation of Concerns |
| "One purpose per module" | Single Responsibility Principle |
| "Don't repeat yourself" | DRY Principle |
| "Test the math alone" | Unit Testing |

**The cleanup of `instrument_geometry/` proves the pattern works. Phase 5 extended this success to routers and calculators.**

---

*End of Master Report*
*Sessions: December 20, 2025 (Phases 1-5)*
*Claude Opus 4.5*
