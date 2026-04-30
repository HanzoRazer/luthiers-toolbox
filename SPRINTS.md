# Sprint Backlog

## Completed

### Sprint FRET-A — Fretboard Ecosphere API

**Status:** COMPLETED (Phase 7)
**Tag:** v2.5.0-alpha.1-phase7
**Completed:** 2026-04-29
**Branch:** sprint/fret-ecosphere-a

Canonical Pydantic-validated fretboard geometry with honest temperament math
and full nine-layer DXF projection verified through GRBL pipeline.

**Phase summary:**
  - Phase 1: Schema (FretboardInput, FretboardEcosphere, FretLine, StringPath)
  - Phase 1.5: Math kernel honesty refactor (real N-TET, Pythagorean, Scala)
  - Phase 2: FastAPI router (/compute, /dxf, /scala, /presets, /schema)
  - Phase 7: Nine-layer DXF projection with R2000 LWPOLYLINE CAM verification

**Phase 7 verification results (R2000):**

| Layer | Entities | Notes |
|-------|----------|-------|
| FRET_SLOTS | 22 LWPOLYLINE | Closed rectangles, CAM-ready |
| FRETS | 22 LINE | Bass-to-treble per fret |
| STRINGS | 6 LINE | Nut-to-bridge per string |
| NUT | 1 LINE + 6 CIRCLE | Nut line + string slot markers |
| BRIDGE | 1 LINE | Theoretical saddle position |
| FRETBOARD_OUTLINE | 1 LWPOLYLINE | Closed 4-point contour |
| ANNOTATIONS | 23 TEXT | 22 fret numbers + scale label |
| BRIDGE_COMPENSATED | 0 | Empty (no offsets in test) |
| HARMONICS_OVERLAY | 0 | Empty (future Sprint FRET-D) |

GRBL pipeline test confirms closed LWPOLYLINE emission avoids the 2-point
loop-assembly gap identified in cam_pipeline_r2000_compat 2026-04-29.

**Remaining sprints (separate):**
  - Phase 8 (FRET-B): Frontend wire-up
  - Sprint FRET-D: Harmonics overlay (Zone-Tritone integration)
  - Fusion add-in: Standalone sprint

---

## Backlog

### Orphaned curvature test file

**Status:** Backlog
**Priority:** Cleanup — non-blocking
**Discovered:** 2026-04-29 during FRET-A baseline capture
**File:** services/api/tests/test_layer_builder_curvature.py

The test file imports three symbols that don't exist in the codebase:
  - _is_curvature_body_candidate
  - curvature_body_promotion_enabled
  - CURVATURE_PROFILER_AVAILABLE

**Origin:** Commit 944aefc6 (2026-04-19 05:17:58) added curvature_profiler.py,
curvature_correction.py, and this test file together. The test imports symbols
for layer_builder integration (`_is_curvature_body_candidate`, etc.) that were
never implemented — the test was written for planned integration that didn't ship.

This is **case B** (speculative test), not case A (removed implementation).

Currently skipped at module level pending triage. Resolution options:

  A. Implement the layer_builder integration the test expects.
  B. Delete test file — the planned integration was abandoned.

Recommend option B unless curvature-based body promotion is on the roadmap.

Not blocking FRET-A. Triage in next layer-builder cleanup sprint.

### FRET-A schema/kernel math duplication

**Status:** RESOLVED (Phase 1.5)
**Priority:** Technical debt — blocking alt-temperament feature
**Discovered:** 2026-04-29 during FRET-A Phase 1 retrospective
**Resolved:** 2026-04-29 in Phase 1.5
**File:** services/api/app/instrument_geometry/neck/fretboard_ecosphere.py

~~The FretboardEcosphere schema implements `_fret_position_temperament()`
internally, duplicating ~30 lines of math from `fret_math.py`.~~

**Resolution (Path 1 executed):**
  1. Extended alternative_temperaments.py with resolve_temperament_ratios()
  2. Created scala_loader.py for .scl parsing
  3. Refactored schema methods to delegate to the kernel

All temperaments now produce mathematically correct positions:
  - Equal temperaments (12/19/24/31-TET): true N-TET math
  - Non-equal temperaments (Pythagorean, Just, Meantone): real ratio math
  - Custom Scala: parsed and applied via scala_loader

Round-trip tests confirm compute → scala → parse → compute identity
within 1e-3 mm tolerance (accounts for Scala format precision).
