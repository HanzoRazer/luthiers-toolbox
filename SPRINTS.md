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

Git history confirms these symbols existed in commit 944aefc6 and were
removed in a later refactor. Test file left behind.

Currently skipped at module level pending triage. Resolution options:

  A. Restore symbols if curvature-based body promotion functionality is needed.
  B. Delete test file if functionality is intentionally gone.

Triage with: `git log --all -S "<symbol_name>" -- services/api/app/`

Not blocking FRET-A. Triage in next layer-builder cleanup sprint.
