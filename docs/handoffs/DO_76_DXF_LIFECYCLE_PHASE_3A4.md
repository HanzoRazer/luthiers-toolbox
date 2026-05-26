# Dev Order 76: DXF Lifecycle Guards — Phase 3A-4 (Read-Modify-Save)

**Sprint:** DXF Lifecycle — Runtime Boundary Follow-Through  
**Order:** DO 76 / Phase 3A-4  
**Status:** IMPLEMENTED (Phase 3A-4)  
**Date:** 2026-05-25  
**Prerequisite:** Phase 3A-3 merged (PR #42, `fc55bf2f`)  
**Branch:** `feat/dxf-lifecycle-phase-3a-4` from `main`

---

## Executive Summary

Add **validation-only** DXF lifecycle guards at the save boundary of two **DIRECT_SAVE_GAP** read-modify-save services. Guards assert export context immediately before `doc.saveas()` after `ezdxf.readfile()`. They do **not** change DXF bytes, attach provenance, or authorize machine execution.

This completes Group B guard candidates (last two before Phase 3B orchestrator adoption).

---

## Core Intent (unchanged)

```text
Guards validate context at every production DXF save/write boundary.
Guards do NOT mutate output, attach provenance, or authorize execution.
DxfWriter is NOT guarded internally (Phase 2G) — callers guard at save boundary.
```

---

## Scope

### In scope (2 files, 2 save sites)

| File | Entry function | Save API | Matrix `export_type` | Matrix `lifecycle_status` |
|------|----------------|----------|----------------------|---------------------------|
| `app/cam/line_deduplicator.py` | `deduplicate_parallel_lines()` | `doc.saveas(output_path)` | `dxf-read-modify-save` | `DIRECT_SAVE_GAP` |
| `app/services/text_reinsertion.py` | `append_text_to_existing_dxf()` | `doc.saveas(dxf_path)` | `dxf-read-modify-save` | `DIRECT_SAVE_GAP` |

**Callable:** `runtime_service`  
**Authority context:** `pipeline_stage`  
**Provenance status:** `NO`

**`dxf_version`:** Use the loaded document version at guard time (e.g. `getattr(doc, "dxfversion", "R2010")`). Do not hardcode unless the file has no loaded doc at the guard site.

### Out of scope

| Item | Reason |
|------|--------|
| `text_reinsertion.add_text_layer_to_dxf()` | Uses `DxfWriter` only — no `saveas` in this function |
| Phase 3B (`blueprint_cam` orchestrator paths) | Separate dev order |
| 5 IBG `BLOCKED_PROVENANCE` paths | Blocked until R1 ratification |
| Guard inside `DxfWriter` | Phase 2G rejected |
| `routers/blueprint_cam/dxf_geometry_correction.py` | Orchestrator candidate — 3B |

---

## Implementation Pattern

Read-modify-save uses **`DIRECT_SAVE_GAP`** (not `COMPAT_ONLY`). Reference: `test_dxf_lifecycle_guard.py::test_read_modify_save_pattern`.

```python
from app.util.dxf_lifecycle_guard import (
    DxfLifecycleContext,
    assert_dxf_lifecycle_context,
)

# After ezdxf.readfile(), immediately before doc.saveas():
dxf_version = getattr(doc, "dxfversion", "R2010")
assert_dxf_lifecycle_context(
    DxfLifecycleContext(
        source_module=__name__,
        export_type="dxf-read-modify-save",
        dxf_version=dxf_version,
        lifecycle_status="DIRECT_SAVE_GAP",
        runtime_callable="runtime_service",
        authority_context="pipeline_stage",
        provenance_status="NO",
    )
)
doc.saveas(output_path)
```

Apply at **module level** imports (not inside nested functions) so guard tests can patch `assert_dxf_lifecycle_context` on the module.

---

## Per-File Checklist

- [ ] Guard immediately before save (after read + in-memory edits)
- [ ] `export_type="dxf-read-modify-save"`
- [ ] `lifecycle_status="DIRECT_SAVE_GAP"` (matrix value — not `COMPAT_ONLY`)
- [ ] `dxf_version` from loaded `doc` when available
- [ ] `provenance_status="NO"`
- [ ] Zero change to DXF entity output
- [ ] Matrix row: `GUARD_CANDIDATE` → `GUARD_ADDED`

---

## Tests

**Baseline (must pass before edits):**

```bash
cd services/api
pytest tests/test_dxf_lifecycle_guard.py -v
pytest tests/test_dxf_lifecycle_archtop_guards.py tests/test_dxf_lifecycle_geometry_guards.py tests/test_dxf_lifecycle_layered_writer_guards.py -v
```

**Add:** `services/api/tests/test_dxf_lifecycle_read_modify_save_guards.py`

| Test | Requirement |
|------|-------------|
| Source inspection | Each file: `assert_dxf_lifecycle_context` precedes every `saveas` |
| Runtime hook | Patch module guard; call export with minimal R12 fixture DXF; assert one guard invocation |
| Context fields | `export_type`, `lifecycle_status=DIRECT_SAVE_GAP`, `provenance_status=NO` |

**Fixtures:** Minimal DXF via `ezdxf.new("R12")` + one LINE entity, or use existing test_temp patterns. Skip OCR path in `append_text_to_existing_dxf` by mocking `extract_text_for_reinsertion` to return one text dict if needed.

---

## Deliverables

| Deliverable | Path |
|-------------|------|
| Guard — line deduplicator | `services/api/app/cam/line_deduplicator.py` |
| Guard — text reinsertion | `services/api/app/services/text_reinsertion.py` |
| Tests | `services/api/tests/test_dxf_lifecycle_read_modify_save_guards.py` |
| Matrix update | `docs/governance/EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` (2 rows) |
| Plan status | `docs/plans/DXF_LIFECYCLE_SPRINT_DEVELOPER_PLAN.md` (3A-4 complete note) |

---

## Acceptance Criteria

- [ ] Both paths guarded per matrix field values
- [ ] `pytest tests/test_dxf_lifecycle_guard.py tests/test_dxf_lifecycle_*_guards.py` pass
- [ ] Matrix shows `GUARD_ADDED` for both rows
- [ ] No DXF output diffs on controlled smoke tests
- [ ] PR targets `main` from `feat/dxf-lifecycle-phase-3a-4` only

---

## Metrics (after merge)

| Metric | After 3A-3 (PR #42) | After 3A-4 (this order) |
|--------|---------------------|-------------------------|
| GUARD_ADDED | 18 | **20** |
| GUARD_CANDIDATE | 2 | **0** |
| ORCHESTRATOR_CANDIDATE | 3 | 3 |
| BLOCKED_PROVENANCE | 5 | 5 |

**Next:** Phase **3B** — orchestrator adoption on `routers/blueprint_cam/*` (3 paths → `LIFECYCLE_GOVERNED`).

---

## Suggested PR

**Title:** `feat(dxf): add lifecycle guards to read-modify-save services (Phase 3A-4)`

**Body summary:**
- DIRECT_SAVE_GAP guards on `line_deduplicator`, `text_reinsertion`
- `dxf-read-modify-save` export type; `dxf_version` from loaded doc
- Matrix + tests; no output mutation

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/plans/DXF_LIFECYCLE_SPRINT_DEVELOPER_PLAN.md` | Sprint roadmap |
| `docs/governance/DXF_SAVE_LIFECYCLE_GUARD_PLAN.md` | §2.6 DIRECT_SAVE_GAP services |
| `docs/governance/EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` | Per-path authority |
| `docs/handoffs/DO_75_DXF_LIFECYCLE_PHASE_3A2.md` | Prior batch pattern |
| PR #42 | 3A-3 reference |

---

*Dev Order 76 — DXF Lifecycle Phase 3A-4 — Read-modify-save Group B guards*
