# SPINE-003 — CAM Project-State Adoption (Validated Read Path)

**Status:** Implemented (held draft PR)
**Scope:** First governed CAM adoption edge of the ADR-002 Instrument Project Graph —
one existing CAM operation now derives its execution inputs from validated
`InstrumentProjectData`.
**Depends on:** ADR-002 (Instrument Project Graph); LAB-021 (spine recovery, WP-PS-4
identified CAM validated reads as the next unbuilt edge); SPINE-002 (Analyzer adoption —
the sibling read/write edge).

---

## Adopted CAM operation

**`adaptive/plan`** — the adaptive-clearing toolpath planner
(`POST /api/cam/pocket/adaptive/plan`, `PlanIn` → `PlanOut`).

**Why this operation.** Of the CAM surface, it uniquely satisfies every selection
criterion in the Dev Order simultaneously:

- **Governed + machine-ready.** Its router (`app/routers/adaptive/plan_router.py:335`)
  enforces feasibility server-side (`_enforce_safety_policy` → HTTP 409 + persisted
  BLOCKED artifact) and persists an RMOS run artifact on success (`_persist_plan_run`).
- **Already RMOS-integrated.** No new RMOS wiring is required (unlike `profiling/gcode`,
  which is the better *semantic* fit for a body-perimeter cut but is **not** currently
  RMOS-governed — adopting it would require RMOS wiring, explicitly out of scope).
- **Lowest-friction, fabrication-free translation.** Its only required geometry is
  `loops`; every other field is a defaulted machining scalar. The project's canonical
  `blueprint_geometry.body_outline_mm` (a `List[(x, y)]` polyline) maps **directly** onto
  `PlanIn.loops[0]`. No geometry is generated or invented.

**Honest semantic framing.** `adaptive/plan` clears the interior of a boundary. Using the
body outline as that boundary means "adaptive clearing bounded by the instrument body
outline." SPINE-003 establishes the **canonical translation + governed execution path**;
it does not claim this is the final manufacturing choice of operation-per-region. A
perimeter/profile adoption (the semantically natural body-outline cut) is deferred until
`profiling` is itself RMOS-governed — a separate future edge.

## New endpoint

```
POST /api/cam/projects/{project_id}/adaptive-plan
  auth:    owner of project (reuses projects._get_project_or_404)
  body:    ProjectAdaptivePlanRequest { tool_d (required), + optional machining overrides }
  200:     PlanOut (existing shape) + headers X-Project-Id / X-Project-Revision / X-Run-Id
  404:     project not found / archived
  403:     caller does not own the project
  422:     project not CAM-ready, or no/invalid body_outline_mm geometry, or missing tool_d
  409:     feasibility block (inherited unchanged from adaptive.plan)
```

## Files changed

| File | Kind | Role |
|------|------|------|
| `app/cam/project_adapter.py` | new | The single canonical Project→CAM translation: `validate_project_cam_inputs` + `build_cam_request_from_project` (state → `PlanIn`). No execution, no persistence. |
| `app/projects/service.py` | modified | Add `load_project_for_cam` — project-level CAM readiness gate; read-only. |
| `app/cam/routers/project_execution.py` | new | The additive endpoint + `ProjectAdaptivePlanRequest`; delegates to the adapter and the existing `adaptive.plan`. |
| `app/cam/routers/aggregator.py` | modified | Register the new router under `/projects` (one import + one `include_router`). |
| `tests/cam/test_project_cam_execution.py` | new | Unit (translation/validation), service, API, parity, provenance, read-only, and regression coverage. |
| `docs/adr/ADR-002-...md` | modified | Non-normative implementation-status note (Project→CAM edge). |

> **File-plan reconciliation.** The Dev Order's plan said "modify one existing CAM router,
> add one endpoint." The repo's CAM surface is composed by a pure-composition aggregator of
> per-category sub-routers (`app/cam/routers/aggregator.py`), so the idiomatic realization
> is a small focused sub-router registered through that existing aggregator — rather than
> placing a fat handler in the composition file. This is one additive endpoint on the
> existing `/api/cam` surface; no existing route changes.

## Boundaries honored

- **Existing CAM architecture governs.** No new execution model. Execution goes through the
  existing `adaptive.plan` function; feasibility and RMOS persistence are inherited, not
  re-implemented. CAM keeps computational authority; RMOS keeps manufacturing authority.
- **Existing Project Spine governs.** Uses `InstrumentProjectData`, the project service,
  and canonical project identity. No `ProjectSpineV2` / `ProjectExecutionModel` / duplicate
  loader. No project-schema change.
- **Single adoption slice.** Exactly one CAM operation adopted. No other CAM operation
  touched.
- **Compatibility first.** The Project-State ingress is purely additive; the existing
  `POST /api/cam/pocket/adaptive/plan` is unchanged (regression-tested).
- **Canonical translation, once.** All Project→CAM translation lives in
  `build_cam_request_from_project`. Machining overrides are restricted to known `PlanIn`
  fields, and any omitted parameter keeps its `PlanIn` default (no default duplication /
  drift).
- **No authority promotion.** Loading a project approves no manufacturing/execution,
  bypasses no feasibility/safety, and does not touch `manufacturing_state`.
- **Explicit project identity.** `project_id` is required in the URL; no implicit
  discovery. Machining parameters (tool, feeds) are supplied by the caller — they are not
  design state and are never fabricated from the project.
- **Provenance preserved.** Project identity + revision (`X-Project-Id` /
  `X-Project-Revision`) and execution/RMOS identity (`X-Run-Id`, plus the persisted run
  artifact + hashes from `adaptive.plan`) are retained — via response headers, with **no**
  CAM/RMOS/project schema modification.
- **Read-only against project state.** The path performs no `commit` and mutates nothing:
  not geometry, not spec, not analyzer observations, not manufacturing history.

## Parity verification

A project-derived `PlanIn` is asserted byte-equal (`model_dump()`) to the equivalent
hand-built `PlanIn` for the same outline + machining parameters — so the project path and
the direct path drive **equivalent execution**
(`tests/cam/test_project_cam_execution.py::TestBuildRequest::test_translation_is_single_and_faithful`).
The API tests additionally execute the real governed path and assert a toolpath is
produced with provenance headers, and that the existing direct endpoint still works.

## Remaining adoption work (each a separate order)

- Perimeter/profile CAM adoption once `profiling` is RMOS-governed.
- Additional CAM operations (neck pocket, cavities) as project state grows to carry their
  geometry.
- Project-centric downloadable NC (`gcode`) path.
- WP-PS-5 store retirement / WP-PS-6 utilities (unrelated edges).

## Verification

- `py -3.11 -m pytest tests/cam/test_project_cam_execution.py`
- CBSP21 patch-input + coverage gates
  (`.cbsp21/patches/spine-003-project-cam-adoption.json`).
