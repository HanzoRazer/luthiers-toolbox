# Dev Order 78–79: IBG Provenance R Namespace (R1 + R2)

**Sprint:** DXF Lifecycle — IBG blocked paths  
**Orders:** DO 78 (R1 governance) · DO 79 (R2 implementation)  
**Status:** R2 code on branch `feat/ibg-provenance-r2-export-wrapper` — **team handoff:** [DO_80](DO_80_IBG_PROVENANCE_R2_ROLLOUT_ANNOTATED_HANDOFF.md)  
**Date:** 2026-05-19 (reconciled 2026-05-26)  
**Prerequisite:** Phase 3B merged (PR #44, `main` @ `225b1fd7`)  
**Parent sprint:** DXF Lifecycle complete for non-IBG paths (DO 75–77)  
**Canonical sequencing:** Aligned with [DO_80](DO_80_IBG_PROVENANCE_R2_ROLLOUT_ANNOTATED_HANDOFF.md) — see § Sequencing (R1 vs R2 merge)

---

## Executive Summary

All **non-IBG** DXF lifecycle work is complete (`GUARD_ADDED: 20`, `LIFECYCLE_GOVERNED: 3`, `ORCHESTRATOR_CANDIDATE: 0`). Five IBG save points on **`main`** remain bare `writer.saveas` with matrix **`BLOCKED_PROVENANCE`** until the R2 wrapper merges and R1 ratification unlocks export.

This handoff defines the **only remaining DXF lifecycle dev orders** in two gated phases:

| Phase | Dev order | Type | Outcome |
|-------|-----------|------|---------|
| **R1** | DO 78 | Governance session (not a code sprint) | Signed ratification; **production export** authorization |
| **R2** | DO 79 / DO 80 | Engineering (branch → PR) | Provenance-aware save wrapper; guard wiring; matrix guard column |

### Sequencing (R1 vs R2 merge) — canonical

| Action | Requires signed R1? | Why |
|--------|---------------------|-----|
| Open / merge **R2 PR** (wrapper on branch) | **No** | Wrapper is fail-closed; every save uses blocked draft → `IbgDxfExportBlockedError` until `RATIFIED` |
| **Production IBG DXF export** (`save_dxf`, API base64) | **Yes** | Needs R1 + Phase D/E (DO 80) |
| Matrix: `GUARD_ADDED` column | **No** | Documents guard wiring; does not imply export enabled |
| Matrix: export-enabled / `COMPAT_ONLY` lifecycle | **Yes** | Governance PR after R1 |
| Phase D caller bridge (`BodyEvidenceCandidate`) | **Yes** | Field contract frozen at R1 |

> **Operational note (post–R2 merge):** `POST /api/body/*` paths that call `gen.save_dxf()` will **fail DXF export by design** until R1 + ratified attachment. This is correct fail-closed posture, not a regression to “fix” by removing the wrapper.

**Fail-closed rule (precise):** No **export authorization** or matrix promotion that implies CAM-ready IBG output until R1 exit criteria are met. **R2 code may land on `main` before R1** because the wrapper blocks all non-`RATIFIED` saves.

---

## Blocked inventory (verified on `main` @ PR #44)

Line numbers are a **baseline** — re-verify on your branch with `rg` before editing (see DO 80 Phase A).

| File | Lines (`main`) | Callable context | Save API |
|------|----------------|------------------|----------|
| `instrument_geometry/body/ibg/body_contour_solver.py` | 777, 808 | `outline_to_dxf()` — empty-outline path (~777) and full outline (~808) | `DxfWriter.saveas` |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1116 | `chains_to_dxf()` | `DxfWriter.saveas` |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1279, 1303 | `create_visual_test_dxf()`, `create_simple_gap_test_dxf()` | `DxfWriter.saveas` |

**Matrix:** `EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` §3 — all five rows `BLOCKED_PROVENANCE` on `main`.

**R2 branch (`feat/ibg-provenance-r2-export-wrapper`):** replaces bare `saveas` with `governed_ibg_writer_saveas` — verify on branch, not visible on `main` until merged.

**Epistemic default until ratified:** `PREDICTED` / `HEURISTIC` — not production OBSERVED/DERIVED authority.

---

## DO 78 — Phase R1: Governance ratification session

### Intent

Ratify authority semantics and required fields at the IBG DXF save boundary. R1 decides **what may be exported**, not how to refactor IBG solvers.

### Session inputs (already prepared — MRP-6C)

| Document | Role |
|----------|------|
| `docs/governance/IBG_PROVENANCE_RATIFICATION_PACKET.md` | Required fields, schema layers |
| `docs/governance/IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md` | Per-field save-boundary requirements |
| `docs/governance/IBG_DXF_LIFECYCLE_MAPPING_ADDENDUM.md` | Transition rules (no skip to LIFECYCLE_GOVERNED) |
| `docs/governance/IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` | Phase R0–R3 timeline |
| `docs/governance/CANONICAL_PROVENANCE_MODEL.md` | Taxonomy (draft → ratify or supersede) |
| `docs/governance/IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md` | IBG runtime provenance shape |
| `docs/governance/CROSS_REPO_AUTHORITY_CROSSWALK.md` | tap_tone ↔ luthiers epistemic alignment |

### R1 agenda (minimum)

1. Ratify canonical provenance taxonomy (`CANONICAL_PROVENANCE_MODEL.md` or superseding record).
2. Ratify IBG constitutional runtime foundation authority tier.
3. Approve `IBGProvenanceAttachment` / `ProvenanceAttachmentDraft` export contract (field list from packet §Required Provenance Attachment Fields).
4. Sign lifecycle transition rules: `BLOCKED_PROVENANCE → COMPAT_ONLY` only after R2; **forbidden** `BLOCKED_PROVENANCE → LIFECYCLE_GOVERNED` direct jump.
5. Record signed governance artifact (meeting notes + decision ID stored under `docs/governance/` or ADR).

### R1 deliverables (documentation only)

| Deliverable | Notes |
|-------------|-------|
| Signed ratification record | Updates matrix blocking condition from “awaiting ratification” → “implementation approved” |
| `ProvenanceAttachmentStatus.RATIFIED` policy | When `export_authorized` may become true |
| DO 79 / DO 80 Phase D–E unlocked | Caller bridge + ratified export (not R2 merge itself) |

### R1 exit criteria

- [ ] Governance owner sign-off with date and decision ID
- [ ] Required field list frozen (no “TBD” on mandatory save-boundary fields)
- [ ] Explicit approval for R2 minimal wrapper scope (validation-only at save; no DXF geometry changes)
- [ ] No open objection to epistemic posture (`PREDICTED`/`HEURISTIC` at export)

### R1 — out of scope

| Item | Reason |
|------|--------|
| Editing `body_contour_solver.py` / `arc_reconstructor.py` | R2 only |
| Adding `assert_dxf_lifecycle_context` that implies production legitimacy | False confidence |
| Promoting matrix rows to `LIFECYCLE_GOVERNED` | Requires orchestrator + provenance; later |
| MRP-6D / MRP-5X capability audits | Redundant; do not staff |
| Vectorizer / blueprint_cam lifecycle work | Complete (DO 77) |

### R1 — existing code (read-only reference)

`services/api/app/governance/provenance_attachment.py` — draft structures exist (`create_ibg_provenance_draft`, `IBG_DEFAULT_STATUS = BLOCKED`). **Do not wire to DXF export in R1.**

---

## DO 79 — Phase R2: Minimal IBG export wrapper (implementation)

**Prerequisite (code merge):** Branch from `main` @ PR #44 — **R1 signature not required to merge R2** (wrapper is inert/fail-closed).  
**Prerequisite (production export):** DO 78 R1 exit criteria met + DO 80 Phase D–E.

**Branch:** `feat/ibg-provenance-r2-export-wrapper` from current `main` (`918f84d9` on branch)  
**Estimated effort:** 2–4 days  
**PR title (suggested):** `feat(ibg): wire provenance-aware DXF save wrapper (R2)`

### Intent

Replace bare `writer.saveas(output_path)` at five sites with a **minimal provenance wrapper** that:

1. Validates ratified provenance context (fail closed if missing or non-exportable status).
2. Asserts DXF lifecycle context per `test_dxf_lifecycle_guard.py::test_blocked_provenance_pattern` during transition, then **`COMPAT_ONLY`** once attachment is wired.
3. Does **not** change geometry bytes or layer semantics.

### Allowed lifecycle transition (post-R2)

```text
BLOCKED_PROVENANCE  →  (R1 + R2)  →  COMPAT_ONLY
                                      provenance_status: ATTACHED (or ratified equivalent)
                                      lifecycle_status: COMPAT_ONLY
```

**Forbidden in R2:**

```text
BLOCKED_PROVENANCE → LIFECYCLE_GOVERNED   # Rule 1, lifecycle addendum
```

Future promotion `COMPAT_ONLY → LIFECYCLE_GOVERNED` is a **separate** dev order after full orchestrator adoption.

### Proposed implementation shape

**New module (suggested):** `services/api/app/util/ibg_dxf_export_lifecycle.py`

```python
# Pseudocode — implement per ratified field matrix after R1
def assert_ibg_dxf_export_allowed(*, attachment: ProvenanceAttachmentDraft, ...) -> None:
    if attachment.status in NON_EXPORTABLE_STATUSES or not attachment.export_authorized:
        raise IbgExportBlockedError(...)
    assert_dxf_lifecycle_context(DxfLifecycleContext(
        source_module=...,
        export_type="dxf-create-save",
        dxf_version="R12",  # from DxfWriter
        lifecycle_status="COMPAT_ONLY",  # after R2 — not BLOCKED_PROVENANCE
        runtime_callable="runtime_service",
        authority_context="pipeline_stage",
        provenance_status="ATTACHED",  # per ratified contract
    ))

def governed_ibg_writer_saveas(writer, path: str, *, attachment: ProvenanceAttachmentDraft, ...) -> None:
    assert_ibg_dxf_export_allowed(attachment=attachment, ...)
    writer.saveas(path)
```

**Call sites (5):** replace `writer.saveas(output_path)` in:

- `body_contour_solver.py` — ~777, ~808
- `arc_reconstructor.py` — ~1116, ~1279, ~1303

Callers must obtain or construct `ProvenanceAttachmentDraft` (or ratified type) from `BodyEvidenceCandidate` / workflow context per field matrix. If attachment cannot be built, **raise** — do not save.

**Reuse:** `app/governance/provenance_attachment.py`, `authority_metadata.py` (IBG defaults). Extend only as required by R1 ratified schema.

### Guard / lifecycle context reference

Until R2 ships, blocked pattern (validation-only reference):

```python
DxfLifecycleContext(
    lifecycle_status="BLOCKED_PROVENANCE",
    provenance_status="BLOCKED",
    runtime_callable="runtime_service",
    authority_context="pipeline_stage",
    export_type="dxf-create-save",
)
```

See `services/api/tests/test_dxf_lifecycle_guard.py::test_blocked_provenance_pattern`.

### Tests (R2)

**Add:** `services/api/tests/test_dxf_lifecycle_ibg_provenance_guards.py`

| Test | Requirement |
|------|-------------|
| Source inspection | No bare `writer.saveas` at five matrix lines; wrapper precedes save |
| Fail closed | Save rejected when attachment missing / `BLOCKED` / non-exportable status |
| Success path | Save allowed with ratified fixture attachment; one guard invocation |
| Context fields | Post-R2: `COMPAT_ONLY`, `provenance_status` per ratified enum |

**Regression:**

```bash
cd services/api
pytest tests/test_dxf_lifecycle_guard.py tests/test_dxf_lifecycle_ibg_provenance_guards.py -q
# Existing IBG unit tests if present — no DXF byte diffs on golden fixtures
```

### R2 deliverables

| Deliverable | Path |
|-------------|------|
| IBG export wrapper | `app/util/ibg_dxf_export_lifecycle.py` (or ratified name) |
| Five save-site wiring | `body_contour_solver.py`, `arc_reconstructor.py` |
| Tests | `tests/test_dxf_lifecycle_ibg_provenance_guards.py` |
| Matrix update | 5 rows: `BLOCKED_PROVENANCE` → `COMPAT_ONLY`, Guard `GUARD_ADDED` or `LIFECYCLE_GOVERNED` per R1 decision |
| Plan update | `DXF_LIFECYCLE_SPRINT_DEVELOPER_PLAN.md` — R2 complete |
| Ratification cross-link | Reference R1 decision ID in PR body |

### R2 acceptance criteria

- [ ] All five saves go through provenance wrapper
- [ ] Export fails without ratified provenance context
- [ ] No change to DXF entity output on controlled fixtures
- [ ] Matrix reflects `COMPAT_ONLY` (not `LIFECYCLE_GOVERNED`) unless separate governance PR approves jump
- [ ] `BLOCKED_PROVENANCE` count → **0** in sprint metrics
- [ ] CI: lifecycle guard tests pass

### R2 — out of scope

| Item | Reason |
|------|--------|
| `LIFECYCLE_GOVERNED` promotion | Separate order; needs orchestrator |
| Provenance in DXF file bytes | Attachment is boundary metadata unless R1 mandates embedding |
| IBG solver algorithm changes | Orthogonal |
| Audit lanes (MRP-6D, CAM-8A closure-only) | Not blocking native work |

---

## Metrics

### Current (after DO 77 / PR #44)

| Status | Count |
|--------|-------|
| GUARD_ADDED | 20 |
| LIFECYCLE_GOVERNED | 3 |
| ORCHESTRATOR_CANDIDATE | 0 |
| **BLOCKED_PROVENANCE** | **5** |

### Target (after DO 79 R2)

| Status | Count |
|--------|-------|
| BLOCKED_PROVENANCE | **0** |
| GUARD_ADDED | 25 (20 + 5 IBG) — or per matrix guard status label post-R1 |
| COMPAT_ONLY (IBG) | 5 |

---

## Developer workflow (recommended)

1. **R2 branch / PR** — `feat/ibg-provenance-r2-export-wrapper`; run DO 80 Phase A `VERIFY` on **the branch** (not `main` alone).
2. **Merge R2** — Allowed before R1; PR body must state: *IBG DXF export disabled in production until R1 + Phase D*.
3. **Schedule R1** — Governance session in parallel; produce signed `IBG_R1_RATIFICATION_RECORD_*.md`.
4. **Phase D–E** — Caller provenance bridge + ratified export — **only after R1**.
5. **Matrix** — `GUARD_ADDED` with R2 merge; lifecycle export-enabled promotion only after R1 governance PR.

---

## Reference documents

| Document | Purpose |
|----------|---------|
| `docs/handoffs/DO_77_DXF_LIFECYCLE_PHASE_3B.md` | Prior phase (complete) |
| `docs/plans/DXF_LIFECYCLE_SPRINT_DEVELOPER_PLAN.md` | Sprint roadmap § R Namespace |
| `docs/governance/EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` | §3 blocked rows |
| `docs/governance/RUNTIME_BOUNDARY_INVENTORY.md` | Phase 2 IBG attachment |
| `docs/governance/DXF_SAVE_LIFECYCLE_GUARD_PLAN.md` | Guard disposition history |
| PR #44 | Phase 3B merge reference |

---

## Anti-patterns (do not repeat)

- Staffing audit-only lanes (MRP-6D ≈ MRP-6A) instead of R1/R2
- Adding lifecycle guards before R1 that imply CAM-ready exports
- Skipping provenance attachment while changing `lifecycle_status` in matrix
- Using `rank_score` or solver success as export authorization

---

*DO 78–79 — Spec. Execution checklist: [DO_80_IBG_PROVENANCE_R2_ROLLOUT_ANNOTATED_HANDOFF.md](DO_80_IBG_PROVENANCE_R2_ROLLOUT_ANNOTATED_HANDOFF.md).*
