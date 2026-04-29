# Sprint Backlog

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

**Status:** Active (Path 1) or Backlog (Path 2)
**Priority:** Technical debt — blocking alt-temperament feature
**Discovered:** 2026-04-29 during FRET-A Phase 1 retrospective
**File:** services/api/app/instrument_geometry/neck/fretboard_ecosphere.py

The FretboardEcosphere schema implements `_fret_position_temperament()`
internally, duplicating ~30 lines of math from `fret_math.py::
compute_fret_positions_mm()`. Schema also exposes 19-TET, 24-TET, 31-TET
as supported temperaments but the underlying math is 12-TET-only
(all use `divisions` variable but same formula).

Resolution path (Path 1):
  1. Extend fret_math.py with temperament parameter (true N-TET support)
  2. Create scala_loader.py for .scl parsing
  3. Refactor schema methods to delegate to the kernels

Resolution path (Path 2):
  Document the limitation in API responses; refactor in a later sprint
  before exposing alt-temperament support publicly.

Current state: 19/24/31-TET enum values exist but produce mathematically
correct N-TET positions (the formula `1 - 2^(-n/divisions)` is correct
for any equal temperament). The limitation is that non-equal temperaments
(Pythagorean, Just, Meantone) fall back to 12-TET silently.
