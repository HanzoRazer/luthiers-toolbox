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

### DXF policy compliance gap

**Status:** Backlog
**Priority:** Hygiene — non-blocking
**Discovered:** 2026-04-29 during post-PR-10 audit
**Source:** docs/investigations/dxf_policy_compliance_audit_2026-04-29.md

CLAUDE.md DXF policy requires all DXF generators route through `dxf_compat`.
Repo-wide grep found **35 files** with direct `ezdxf.new()` calls:

  - 21 files in services/api/ (production code, varied versions R12/R2000/R2010)
  - 14 files in services/photo-vectorizer/ (mostly standalone scripts, less critical)

PR #10 refactored 3 critical bypass files. The remaining 32 are pre-existing
violations that predate PR #10 — not regressions from R2000 work.

**Version distribution matters:** Files use R12, R2000, and R2010 for different
reasons (CAM surfaces need LWPOLYLINE → R2010; consumer output → R12). Future
cleanup requires version-per-file decision, not uniform refactor.

Resolution options:

  A. Refactor in batches by priority (production routers first, scripts last)
  B. Tighten CI to reject new `ezdxf.new()` additions, accept existing as debt
  C. Some endpoints may have legitimate need for non-default versions —
     refactor with version awareness

Recommend B + A in batches. Adding a CI check stops the bleed; backfill
happens when team has bandwidth.

Not blocking FRET-A or any current sprint. Triage when DXF hygiene sprint scheduled.
