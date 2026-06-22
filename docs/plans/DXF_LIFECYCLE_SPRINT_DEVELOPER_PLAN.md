# DXF Lifecycle Sprint — Developer Plan

**Date:** 2026-05-25 (reconciled 2026-05-19)  
**Namespace:** Phase 1E → 2A → 2B → 2C → 2D → 2F → 2G → 3A → 3B → R  
**Status:** Phases 2A–3B COMPLETE on `main` (PR #40–#44) — next: DO 78 R1 / DO 79 R2 (IBG)  
**Verified against:** `origin/main` @ `225b1fd7` (merge PR #44)

---

## Executive Summary

The DXF Lifecycle Sprint establishes validation-only guards at all DXF save/write boundaries. Guards ensure export context is present but do not mutate output or authorize execution.

| Phase | Status | Scope |
|-------|--------|-------|
| 1E | COMPLETE | Guard plan drafted |
| 2A | COMPLETE | Core guard infrastructure |
| 2B | COMPLETE | Rollout readiness / status tracking |
| 2C | COMPLETE | Neck router guards (3 paths) |
| 2D | COMPLETE | Remaining router guards (3 paths) |
| 2F | COMPLETE | Runtime service guards (3 paths) |
| 2G | COMPLETE | DxfWriter assessment (no guard) |
| 3A-1 | COMPLETE | Archtop CAM batch (4 paths, PR #40) |
| 3A-2 | COMPLETE | Instrument geometry batch (3 paths, DO 75) |
| 3A-3 | COMPLETE | `layered_dxf_writer.py` (PR #42) |
| 3A-4 | COMPLETE | read-modify-save pair (`DO_76`) |
| 3B | COMPLETE | Blueprint CAM orchestrator adoption (3 paths, DO 77) |
| R2 | IN PROGRESS | IBG wrapper on branch; merge + R1 gate (DO 80) |
| R1+ | BLOCKED | IBG production export until R1 + Phase E |

---

## Completed Work (Phase 2A-2G)

### Infrastructure Created

| File | Purpose |
|------|---------|
| `app/util/dxf_lifecycle_guard.py` | Core guard module |
| `DxfLifecycleContext` | Export context dataclass |
| `validate_dxf_lifecycle_context()` | Validation function |
| `assert_dxf_lifecycle_context()` | Assertion wrapper |
| `DxfLifecycleGuardError` | Guard exception |

### Paths Guarded (10 total)

| Phase | File | Callable |
|-------|------|----------|
| 2A | `routers/instruments/guitar/smart_guitar_dxf_router.py` | router_endpoint |
| 2C | `routers/neck/neck_profile_export.py` | router_endpoint |
| 2C | `routers/neck/headstock_transition_export.py` | router_endpoint |
| 2C | `routers/neck/export.py` | router_endpoint |
| 2D | `routers/headstock/dxf_export.py` | router_endpoint |
| 2D | `routers/export/curve_export_router.py` | router_endpoint |
| 2D | `routers/dxf_preflight_router.py` | router_endpoint |
| 2F | `cam/unified_dxf_cleaner.py` | runtime_service |
| 2F | `cam/layer_consolidator.py` | runtime_service |
| 2F | `cam/dxf_consolidator.py` | runtime_service — RETIRED (dead, superseded by `layer_consolidator`; BACKLOG item 9) |

### Phase 2G Decision

**DxfWriter cannot be guarded internally.**

Reason: DxfWriter lacks caller context (`source_module`, `runtime_callable`, `authority_context`). A guard with synthetic values is worse than no guard.

**Resolution:** Callers must supply lifecycle context at their own save boundaries.

---

## Completed Work (Phase 3A — Group B guards)

| File | Lifecycle Status | Batch | Merge |
|------|------------------|-------|-------|
| `cam/archtop_bridge_generator.py` | COMPAT_ONLY | 3A-1 | PR #40 |
| `cam/archtop_saddle_generator.py` | COMPAT_ONLY | 3A-1 | PR #40 |
| `cam/archtop/archtop_surface_tools.py` | COMPAT_ONLY | 3A-1 | PR #40 |
| `cam/archtop/archtop_contour_generator.py` | COMPAT_ONLY | 3A-1 | PR #40 |
| `instrument_geometry/body/smart_guitar_dxf.py` | COMPAT_ONLY | 3A-2 | PR #41 |
| `instrument_geometry/soundhole/spiral_geometry.py` | COMPAT_ONLY | 3A-2 | PR #41 |
| `generators/bezier_body.py` | COMPAT_ONLY | 3A-2 | PR #41 |
| `services/layered_dxf_writer.py` | COMPAT_ONLY | 3A-3 | PR #42 |
| `cam/line_deduplicator.py` | DIRECT_SAVE_GAP | 3A-4 | PR #43 |
| `services/text_reinsertion.py` | DIRECT_SAVE_GAP | 3A-4 | PR #43 |

**Pattern:** `assert_dxf_lifecycle_context()` immediately before each `saveas` (or DxfWriter `saveas`).

---

## Completed Work (Phase 3B — Blueprint CAM orchestrator)

| File | Target status | Module | Merge |
|------|---------------|--------|-------|
| `routers/blueprint_cam/dxf_preprocessor.py` | LIFECYCLE_GOVERNED | `governed_doc_saveas` | PR #44 |
| `routers/blueprint_cam/contour_reconstruction.py` | LIFECYCLE_GOVERNED | `governed_doc_saveas` | PR #44 |
| `routers/blueprint_cam/dxf_geometry_correction.py` | LIFECYCLE_GOVERNED | `governed_doc_saveas` | PR #44 |

**Helper:** `app/util/blueprint_dxf_export_lifecycle.py` — not the CAM G-code `export_lifecycle_orchestrator`.

---

## Remaining Work

### R Namespace — IBG Provenance (5 paths)

**Priority:** P1 — execution via DO 80  
**Prerequisite:** R1 for **production export**; R2 PR may merge earlier (fail-closed wrapper)  
**Status:** R2 on branch `feat/ibg-provenance-r2-export-wrapper`; not on `main` until merged  
**Handoff:** `docs/handoffs/DO_80_IBG_PROVENANCE_R2_ROLLOUT_ANNOTATED_HANDOFF.md`

| File | Line | Status |
|------|------|--------|
| `instrument_geometry/body/ibg/body_contour_solver.py` | 777 | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/body_contour_solver.py` | 808 | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1116 | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1279 | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1303 | BLOCKED_PROVENANCE |

**Do not add guards until R1 ratification completes.**

---

## Developer Guide

### Adding a Guard (Standard Pattern)

```python
from app.util.dxf_lifecycle_guard import (
    DxfLifecycleContext,
    assert_dxf_lifecycle_context,
)

# Create context
context = DxfLifecycleContext(
    source_module=__name__,
    export_type="dxf-create-save",
    dxf_version=doc.dxfversion,
    lifecycle_status="COMPAT_ONLY",
    runtime_callable="runtime_service",  # or "router_endpoint"
    authority_context="user_request",    # or "pipeline_stage"
    provenance_status="NO",
)

# Assert before save
assert_dxf_lifecycle_context(context)

# Then save
doc.saveas(path)  # or doc.write(buf)
```

### Adding a Guard (Read-Modify-Write Pattern)

```python
# For DIRECT_SAVE_GAP paths
context = DxfLifecycleContext(
    source_module=__name__,
    export_type="dxf-read-modify-save",  # Different export type
    dxf_version=doc.dxfversion,
    lifecycle_status="DIRECT_SAVE_GAP",  # Different status
    runtime_callable="runtime_service",
    authority_context="pipeline_stage",
    provenance_status="NO",
)

assert_dxf_lifecycle_context(context)
doc.saveas(path)
```

### Context Field Reference

| Field | Required | Values |
|-------|----------|--------|
| `source_module` | YES | `__name__` |
| `export_type` | YES | `dxf-create-save`, `dxf-read-modify-save`, `dxf-create-only`, `dxf-preview` |
| `dxf_version` | YES | `doc.dxfversion` (e.g., "AC1009", "AC1015") |
| `lifecycle_status` | YES | `LIFECYCLE_GOVERNED`, `COMPAT_ONLY`, `DIRECT_SAVE_GAP` |
| `runtime_callable` | YES | `router_endpoint`, `runtime_service`, `script_only` |
| `authority_context` | OPTIONAL | `user_request`, `pipeline_stage`, `batch_operation`, `preview_only` |
| `provenance_status` | YES | `NO`, `YES`, `BLOCKED`, `N/A` (see `dxf_lifecycle_guard.py`) |

---

## Guard Behavior

### What Guards Do

- Validate export context exists
- Validate declared export type
- Validate DXF version known
- Validate caller/source module known
- Optionally emit audit/log record

### What Guards Do NOT Do

- Mutate document output
- Block valid exports
- Authorize machine execution
- Attach provenance metadata
- Replace orchestrator validation

---

## Test Requirements

### For Each New Guard

```python
def test_guard_fires_before_save():
    """Guard is called before save operation."""
    
def test_guard_does_not_block_valid_export():
    """Valid context allows export to complete."""
    
def test_guard_rejects_missing_source():
    """Missing source_module raises DxfLifecycleGuardError."""
    
def test_output_unchanged():
    """Guard does not alter DXF output."""
```

### Run Guard Tests

```bash
pytest tests/test_dxf_lifecycle_guard.py -v
pytest tests/governance/test_dxf_lifecycle_*.py -v
```

---

## Excluded Paths (No Guard Needed)

| Category | Count | Reason |
|----------|-------|--------|
| Test fixtures | 9 | `TEST_ONLY` — ezdxf.new allowed |
| Scripts | 1 | `R_AND_D_EXCLUDED` — CLI utility |
| Blueprint-import | 4 | `R_AND_D_EXCLUDED` — Import surface |
| Photo-vectorizer | 9 | `R_AND_D_EXCLUDED` — R&D sandbox |
| Create-only | 2 | Caller saves, no local save |
| Preview-only | 1 | No save operation |

---

## Repo verification (run before trusting this plan)

From repo root on current `main`:

```bash
# 20 path-owner modules + 1 orchestrator helper = 21 production files (excludes guard.py, tests)
rg -l "assert_dxf_lifecycle_context" services/api/app --glob "*.py" \
  | rg -v "dxf_lifecycle_guard.py|/tests/"

# Phase 3B orchestrator (must exist post–PR #44)
test -f services/api/app/util/blueprint_dxf_export_lifecycle.py
rg "governed_doc_saveas" services/api/app/routers/blueprint_cam --glob "*.py"

# IBG still blocked (no guards until R2)
rg "assert_dxf_lifecycle_context|governed_doc_saveas" \
  services/api/app/instrument_geometry/body/ibg --glob "*.py"
# expect: no matches
```

**Expected counts (2026-05-19):** 21 files with `assert_dxf_lifecycle_context` in `app/`; 3 blueprint_cam routers using `governed_doc_saveas`; 0 IBG guard wiring.

**Before guarding any new path:** open the file and confirm the actual save pattern (`create-save` vs `read-modify-save`) matches `EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` for that row.

---

## Sprint Execution Order

### Complete (merged PR #40–#44)

Phases 3A-1 through 3B — see tables above.

### Next — after R1 ratification (DO 78)

```
R2: IBG provenance guards
├── instrument_geometry/body/ibg/body_contour_solver.py (2 paths)
└── instrument_geometry/body/ibg/arc_reconstructor.py (3 paths)
```

---

## Metrics

### Current State (after 3B)

| Status | Count |
|--------|-------|
| GUARD_ADDED | 20 |
| LIFECYCLE_GOVERNED | 3 |
| ORCHESTRATOR_CANDIDATE | 0 |
| BLOCKED_PROVENANCE | 5 |
| REQUIRES_CALLER_CONTEXT | 1 |
| NOT_APPLICABLE | 26 |
| **Total paths** | **55** |

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/governance/DXF_SAVE_LIFECYCLE_GUARD_PLAN.md` | Full guard plan |
| `docs/governance/EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` | Path classification |
| `docs/governance/RUNTIME_BOUNDARY_INVENTORY.md` | Boundary inventory |
| `docs/governance/IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` | IBG timeline |
| `docs/handoffs/DO_75_DXF_LIFECYCLE_PHASE_3A2.md` | Phase 3A-2 dev order (instrument geometry) |
| `docs/handoffs/DO_76_DXF_LIFECYCLE_PHASE_3A4.md` | Phase 3A-4 dev order (read-modify-save) |
| `docs/handoffs/DO_77_DXF_LIFECYCLE_PHASE_3B.md` | Phase 3B dev order (blueprint_cam orchestrator) |
| `docs/handoffs/DO_78_IBG_PROVENANCE_R_NAMESPACE_HANDOFF.md` | DO 78 (R1) + DO 79 (R2) IBG provenance spec |
| `docs/handoffs/DO_80_IBG_PROVENANCE_R2_ROLLOUT_ANNOTATED_HANDOFF.md` | **Dev-ready** R2 rollout + R1 gate + caller bridge (annotated) |

---

## Acceptance Criteria

### Phase 3A Complete When

- [x] All 10 Group B candidates have guards (PR #40–#43)
- [x] Tests pass for each new guard (`test_dxf_lifecycle_*_guards.py`)
- [x] Matrix updated with `GUARD_ADDED` status
- [x] No behavior changes to DXF output

### Phase 3B Complete When

- [x] All 3 orchestrator candidates use `blueprint_dxf_export_lifecycle.governed_doc_saveas` (PR #44)
- [x] `LIFECYCLE_GOVERNED` guard context at every blueprint_cam save boundary
- [x] Matrix updated with `LIFECYCLE_GOVERNED` status

### R2 Complete When (DO 79 — proposed)

- [ ] R1 ratification approved
- [ ] All 5 IBG paths have provenance-aware guards
- [ ] Matrix updated: `BLOCKED_PROVENANCE` → `COMPAT_ONLY` or `LIFECYCLE_GOVERNED`

---

*Developer Plan version: 2026-05-25 — reconciled against `main` @ PR #44*
