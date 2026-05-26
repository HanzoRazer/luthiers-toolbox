# DXF Lifecycle Sprint — Developer Plan

**Date:** 2026-05-25  
**Namespace:** Phase 1E → 2A → 2B → 2C → 2D → 2F → 2G → 3A+  
**Status:** Phase 3A-3 COMPLETE — Phase 3A-4 READY

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
| 3A-3 / 3A-4 | PENDING | `layered_dxf_writer`; read-modify-save pair |
| 3B | PENDING | Orchestrator integration candidates (3 paths) |
| R1+ | BLOCKED | IBG provenance ratification (5 paths) |

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
| 2F | `cam/dxf_consolidator.py` | runtime_service |

### Phase 2G Decision

**DxfWriter cannot be guarded internally.**

Reason: DxfWriter lacks caller context (`source_module`, `runtime_callable`, `authority_context`). A guard with synthetic values is worse than no guard.

**Resolution:** Callers must supply lifecycle context at their own save boundaries.

---

## Remaining Work

### Phase 3A — Group B Guard Candidates (batched)

**Priority:** P2  
**Prerequisite:** Phase 2G complete  
**Estimated effort:** 1-2 days total (4 sub-PRs)

| File | Lifecycle Status | Callable | Batch | Status |
|------|------------------|----------|-------|--------|
| `cam/archtop_bridge_generator.py` | COMPAT_ONLY | runtime_service | 3A-1 | GUARD_ADDED |
| `cam/archtop_saddle_generator.py` | COMPAT_ONLY | runtime_service | 3A-1 | GUARD_ADDED |
| `cam/archtop/archtop_surface_tools.py` | COMPAT_ONLY | runtime_service | 3A-1 | GUARD_ADDED |
| `cam/archtop/archtop_contour_generator.py` | COMPAT_ONLY | runtime_service | 3A-1 | GUARD_ADDED |
| `instrument_geometry/body/smart_guitar_dxf.py` | COMPAT_ONLY | runtime_service | 3A-2 | GUARD_ADDED |
| `instrument_geometry/soundhole/spiral_geometry.py` | COMPAT_ONLY | runtime_service | 3A-2 | GUARD_ADDED |
| `generators/bezier_body.py` | COMPAT_ONLY | runtime_service | 3A-2 | GUARD_ADDED |
| `services/layered_dxf_writer.py` | COMPAT_ONLY | runtime_service | 3A-3 | GUARD_ADDED |
| `cam/line_deduplicator.py` | DIRECT_SAVE_GAP | runtime_service | 3A-4 | Pending |
| `services/text_reinsertion.py` | DIRECT_SAVE_GAP | runtime_service | 3A-4 | Pending |

**Pattern:** Same as Phase 2A — `assert_dxf_lifecycle_context()` before save.

---

### Phase 3B — Orchestrator Candidates (3 paths)

**Priority:** P3  
**Prerequisite:** Phase 3A complete  
**Estimated effort:** 2-3 days

| File | Current Status | Target |
|------|----------------|--------|
| `routers/blueprint_cam/dxf_preprocessor.py` | COMPAT_ONLY | LIFECYCLE_GOVERNED |
| `routers/blueprint_cam/contour_reconstruction.py` | COMPAT_ONLY | LIFECYCLE_GOVERNED |
| `routers/blueprint_cam/dxf_geometry_correction.py` | DIRECT_SAVE_GAP | LIFECYCLE_GOVERNED |

**Scope:** Full `export_lifecycle_orchestrator` adoption with gate validation.

---

### R Namespace — IBG Provenance (5 paths)

**Priority:** P1 after R1 ratification  
**Prerequisite:** R1 governance ratification session  
**Status:** BLOCKED

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
    provenance_status="NOT_ATTACHED",
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
    provenance_status="NOT_ATTACHED",
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
| `provenance_status` | YES | `NOT_ATTACHED`, `BLOCKED`, `ATTACHED` |

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

## Sprint Execution Order

### Immediate (No Blockers)

```
Phase 3A: Group B guard candidates
├── cam/line_deduplicator.py
├── cam/archtop_*.py (4 files)
├── instrument_geometry/body/smart_guitar_dxf.py
├── instrument_geometry/soundhole/spiral_geometry.py
├── generators/bezier_body.py
├── services/layered_dxf_writer.py
└── services/text_reinsertion.py
```

### After Phase 3A

```
Phase 3B: Orchestrator candidates
├── routers/blueprint_cam/dxf_preprocessor.py
├── routers/blueprint_cam/contour_reconstruction.py
└── routers/blueprint_cam/dxf_geometry_correction.py
```

### After R1 Ratification

```
R2: IBG provenance guards
├── instrument_geometry/body/ibg/body_contour_solver.py (2 paths)
└── instrument_geometry/body/ibg/arc_reconstructor.py (3 paths)
```

---

## Metrics

### Current State (after 3A-3)

| Status | Count |
|--------|-------|
| GUARD_ADDED | 18 |
| GUARD_CANDIDATE | 2 |
| ORCHESTRATOR_CANDIDATE | 3 |
| BLOCKED_PROVENANCE | 5 |
| REQUIRES_CALLER_CONTEXT | 1 |
| NOT_APPLICABLE | 26 |
| **Total paths** | **55** |

### Target State (After Phase 3A-4)

| Status | Count |
|--------|-------|
| GUARD_ADDED | 20 |
| LIFECYCLE_GOVERNED | 3 |
| GUARD_CANDIDATE | 0 |
| BLOCKED_PROVENANCE | 5 |
| REQUIRES_CALLER_CONTEXT | 1 |
| NOT_APPLICABLE | 26 |

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/governance/DXF_SAVE_LIFECYCLE_GUARD_PLAN.md` | Full guard plan |
| `docs/governance/EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` | Path classification |
| `docs/governance/RUNTIME_BOUNDARY_INVENTORY.md` | Boundary inventory |
| `docs/governance/IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` | IBG timeline |
| `docs/handoffs/DO_75_DXF_LIFECYCLE_PHASE_3A2.md` | Phase 3A-2 dev order (instrument geometry) |

---

## Acceptance Criteria

### Phase 3A Complete When

- [ ] All 10 Group B candidates have guards
- [ ] Tests pass for each new guard
- [ ] Matrix updated with `GUARD_ADDED` status
- [ ] No behavior changes to DXF output

### Phase 3B Complete When

- [ ] All 3 orchestrator candidates use `export_lifecycle_orchestrator`
- [ ] Full gate validation active
- [ ] Matrix updated with `LIFECYCLE_GOVERNED` status

### R2 Complete When

- [ ] R1 ratification approved
- [ ] All 5 IBG paths have provenance-aware guards
- [ ] Matrix updated: `BLOCKED_PROVENANCE` → `COMPAT_ONLY` or `LIFECYCLE_GOVERNED`

---

*Developer Plan version: 2026-05-25*
