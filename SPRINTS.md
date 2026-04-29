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
