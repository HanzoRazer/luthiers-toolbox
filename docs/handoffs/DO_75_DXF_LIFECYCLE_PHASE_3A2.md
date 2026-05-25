# Dev Order 75: DXF Lifecycle Guards — Phase 3A-2 (Instrument Geometry)

**Sprint:** DXF Lifecycle — Runtime Boundary Follow-Through  
**Order:** DO 75 / Phase 3A-2  
**Status:** READY FOR IMPLEMENTATION  
**Date:** 2026-05-25  
**Prerequisite:** Phase 3A-1 merged (PR #40, `da7f10b6`)  
**Branch:** `feat/dxf-lifecycle-phase-3a-2` from `main`

---

## Executive Summary

Add **validation-only** DXF lifecycle guards at the save boundary of three **Group B** instrument-geometry generators. Guards assert export context exists immediately before `doc.saveas()` or `writer.saveas()`. They do **not** change DXF bytes, attach provenance, or authorize machine execution.

This continues the original DXF lifecycle sprint stopped at Phase 2G. Phase 3A-1 (archtop CAM batch) is complete; **this order is 3A-2 only**.

---

## Core Intent (unchanged)

```text
Guards validate context at every production DXF save/write boundary.
Guards do NOT mutate output, attach provenance, or authorize execution.
DxfWriter is NOT guarded internally (Phase 2G) — callers guard at save boundary.
```

---

## Scope

### In scope (3 files)

| File | Save API | Matrix `export_type` | Matrix `lifecycle_status` | `dxf_version` |
|------|----------|----------------------|---------------------------|---------------|
| `app/instrument_geometry/body/smart_guitar_dxf.py` | `doc.saveas()` | `dxf-create-save` | `COMPAT_ONLY` | `R2010` (from `create_document`) |
| `app/instrument_geometry/soundhole/spiral_geometry.py` | `writer.saveas()` in `generate_dxf()` | `dxf-create-save` | `COMPAT_ONLY` | `R12` (DxfWriter default) |
| `app/generators/bezier_body.py` | `writer.saveas()` in export method | `dxf-create-save` | `COMPAT_ONLY` | `R12` (DxfWriter default) |

**Callable:** `runtime_service`  
**Authority context:** `pipeline_stage`  
**Provenance status:** `NO` (validation-only; no attachment)

### Out of scope

| Item | Reason |
|------|--------|
| Phase 3A-3 (`layered_dxf_writer.py`) | Separate dev order |
| Phase 3A-4 (`line_deduplicator.py`, `text_reinsertion.py`) | Read-modify-save; separate order |
| Phase 3B orchestrator adoption | After all 3A batches |
| 5 IBG `BLOCKED_PROVENANCE` paths | Blocked until R1 ratification |
| Guard inside `DxfWriter` / `dxf_writer.py` | Phase 2G rejected |
| Provenance attachment (R2) | Separate sprint |
| CamIntent / review queue / MRP-5 governance extensions | Different namespace |

---

## Implementation Pattern

### Standard (`smart_guitar_dxf.py` — `create_document` + `saveas`)

```python
from app.util.dxf_lifecycle_guard import (
    DxfLifecycleContext,
    assert_dxf_lifecycle_context,
)

assert_dxf_lifecycle_context(
    DxfLifecycleContext(
        source_module=__name__,
        export_type="dxf-create-save",
        dxf_version="R2010",
        lifecycle_status="COMPAT_ONLY",
        runtime_callable="runtime_service",
        authority_context="pipeline_stage",
        provenance_status="NO",
    )
)
doc.saveas(output_path)
```

### DxfWriter caller boundary (`spiral_geometry.py`, `bezier_body.py`)

Guard **immediately before** `writer.saveas(...)`, not inside `DxfWriter`:

```python
assert_dxf_lifecycle_context(
    DxfLifecycleContext(
        source_module=__name__,
        export_type="dxf-create-save",
        dxf_version="R12",
        lifecycle_status="COMPAT_ONLY",
        runtime_callable="runtime_service",
        authority_context="pipeline_stage",
        provenance_status="NO",
    )
)
writer.saveas(output_path)
```

---

## Per-File Checklist

- [ ] Guard immediately before save (not at import)
- [ ] `lifecycle_status` matches matrix (`COMPAT_ONLY`)
- [ ] `export_type` matches matrix (`dxf-create-save`)
- [ ] `provenance_status="NO"`
- [ ] Zero change to DXF entity output (diff existing golden if available)
- [ ] Matrix row: `GUARD_CANDIDATE` → `GUARD_ADDED`

---

## Tests

**Baseline (must pass before edits):**

```bash
cd services/api
pytest tests/test_dxf_lifecycle_guard.py -v
pytest tests/test_dxf_lifecycle_archtop_guards.py -v
```

**Add:** `services/api/tests/test_dxf_lifecycle_geometry_guards.py`

| Test | Requirement |
|------|-------------|
| Source inspection | Each file: `assert_dxf_lifecycle_context` precedes every `saveas` |
| Runtime hook (where feasible) | Patch module-local `assert_dxf_lifecycle_context`; call export with minimal fixture; assert one guard invocation |
| Invalid context | Existing guard unit tests cover validation (no duplicate suite) |
| Output unchanged | Export smoke: file size / entity count stable vs pre-guard baseline (optional snapshot) |

**Spiral / bezier note:** If full geometry fixtures are heavy, source-order + mocked guard invocation is sufficient for this order (same bar as 3A-1 archtop tests).

---

## Deliverables

| Deliverable | Path |
|-------------|------|
| Guard — Smart Guitar DXF | `services/api/app/instrument_geometry/body/smart_guitar_dxf.py` |
| Guard — Spiral soundhole DXF | `services/api/app/instrument_geometry/soundhole/spiral_geometry.py` |
| Guard — Bezier body DXF | `services/api/app/generators/bezier_body.py` |
| Tests | `services/api/tests/test_dxf_lifecycle_geometry_guards.py` |
| Matrix update | `docs/governance/EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` (3 rows) |
| Plan status | `docs/plans/DXF_LIFECYCLE_SPRINT_DEVELOPER_PLAN.md` (3A-2 complete note) |

---

## Acceptance Criteria

- [ ] All 3 paths guarded per matrix field values
- [ ] `pytest tests/test_dxf_lifecycle_guard.py tests/test_dxf_lifecycle_*_guards.py` pass
- [ ] Matrix shows `GUARD_ADDED` for all 3 rows
- [ ] No DXF output diffs on controlled export smoke tests
- [ ] PR targets `main` from `feat/dxf-lifecycle-phase-3a-2` only (no CamIntent / governance bundle)

---

## Metrics (after merge)

| Metric | After 3A-1 | After 3A-2 (this order) |
|--------|------------|-------------------------|
| GUARD_ADDED | 14 | **17** |
| GUARD_CANDIDATE | 6 | **3** |
| ORCHESTRATOR_CANDIDATE | 3 | 3 |
| BLOCKED_PROVENANCE | 5 | 5 |

**Remaining Group B:** `layered_dxf_writer.py` (3A-3), `line_deduplicator.py` + `text_reinsertion.py` (3A-4).

---

## Suggested PR

**Title:** `feat(dxf): add lifecycle guards to instrument geometry exports (Phase 3A-2)`

**Body summary:**
- COMPAT_ONLY guards on smart_guitar_dxf, spiral_geometry, bezier_body
- DxfWriter paths guarded at caller save boundary (Phase 2G rule)
- Matrix + tests; no output mutation

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/plans/DXF_LIFECYCLE_SPRINT_DEVELOPER_PLAN.md` | Sprint roadmap |
| `docs/governance/DXF_SAVE_LIFECYCLE_GUARD_PLAN.md` | Group B/C definitions |
| `docs/governance/EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` | Per-path authority |
| `docs/handoffs/DO_75_DXF_LIFECYCLE_PHASE_3A2.md` | This order |
| PR #40 | 3A-1 reference implementation |

---

## Next Orders (not this PR)

| Order | Files |
|-------|-------|
| **3A-3** | `app/services/layered_dxf_writer.py` |
| **3A-4** | `app/cam/line_deduplicator.py`, `app/services/text_reinsertion.py` (read-modify-save template) |
| **3B** | `routers/blueprint_cam/*` (orchestrator adoption) |

---

*Dev Order 75 — DXF Lifecycle Phase 3A-2 — Instrument Geometry Group B guards*
