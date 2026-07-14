# SPINE-004 — Project-Centric Manufacturing Artifact Adoption

**Status:** Implemented (held draft PR)
**Scope:** Associate manufacturing planning artifacts (RMOS run artifacts) with the
canonical project record, making them first-class members of the instrument's engineering
history — without changing CAM computation, RMOS orchestration, or manufacturing authority.
**Depends on:** ADR-002; SPINE-002 (Analyzer→Project edge); SPINE-003 (Project→CAM edge);
existing RMOS `runs_v2` artifact persistence.

---

## The gap this closes

After SPINE-003, CAM can *consume* a project, but the manufacturing artifacts it produces
(RMOS run artifacts — toolpaths, feasibility, decision) had **no link back to the project**.
Investigation confirmed: a `RunArtifact` carries no `project_id`, and the only project→run
reference anywhere was analyzer-only (`AnalyzerObservation.run_id`). So a project's
manufacturing history was invisible from the project record. SPINE-004 adds the missing
back-reference — association only, never ownership.

## What changed

| File | Kind | Role |
|------|------|------|
| `app/schemas/instrument_project.py` | modified (additive) | New `ProjectArtifactRef` sub-schema + append-only `InstrumentProjectData.manufacturing_artifacts: List[ProjectArtifactRef]`. |
| `app/projects/project_artifact_service.py` | new | The single canonical association service: `validate_project_artifact`, `build_artifact_ref_from_run`, `merge_artifact_refs`, `associate_artifact_with_project`, `retrieve_project_artifacts`. |
| `app/projects/router.py` | modified | `POST /api/projects/{project_id}/artifacts` (row-locked, owner-auth); and `PUT /design-state` now append-merges `manufacturing_artifacts` (data-loss guard, mirroring `analyzer_observations`). |
| `tests/projects/test_project_artifact_association.py` | new | Unit + service + API + boundary + negative-path coverage. |
| `ci/router_count_baseline.json` | modified | Ratchet: `route_decorators` 1226→1227 for the one new endpoint (no new router file). |
| `tests/test_technical_debt_gates.py` | modified | `TARGET_MAX_ENDPOINTS` 1223→1224 for the one new endpoint. |
| `docs/adr/ADR-002-...md` | modified | Non-normative implementation-status note. |

## What a "manufacturing artifact" is here

An RMOS **run artifact** (`app.rmos.runs_v2`), identified by `run_id` — e.g. the run
persisted by the adaptive planner (`tool_id="adaptive:plan"`). Existence is checked via
`rmos.runs_v2.store_api.get_run(run_id)`. The project stores a `ProjectArtifactRef`:
`run_id` (+ `tool_id`, `mode`, `event_type`, `status`, `risk_level`, `artifact_created_at`,
`feasibility_sha256`, `toolpaths_sha256`) plus association metadata (`associated_at`,
`project_revision`). **No toolpath/move/gcode payload is copied** — references and integrity
anchors only.

## Endpoint

```
POST /api/projects/{project_id}/artifacts
  auth:  owner of project (_get_project_or_404) + SELECT ... FOR UPDATE row lock
  body:  { run_id (required), expected_tool_id?, expected_feasibility_sha256? }
  200:   DesignStateResponse (updated canonical state, incl. manufacturing_artifacts)
  404:   referenced RMOS artifact does not exist
  403:   caller does not own the project
  409:   run_id already associated with DIFFERENT artifact provenance (integrity conflict)
  422:   provenance mismatch (expected_* != actual), or uninitialized project
         (no design state AND no declared instrument_type — no fabricated default)
```

Retrieval piggybacks on the existing `GET /api/projects/{id}/design-state` (the
`manufacturing_artifacts` field is included); `retrieve_project_artifacts` is also exposed
as a service function. No separate GET route was added, to keep the router-count delta at +1.

## Boundaries honored

- **Association only — RMOS/CAM authority unchanged.** RMOS remains sole owner of artifact
  generation + persistence; CAM sole owner of planning. The project records a reference.
- **No artifact duplication.** The ref carries identifiers + hashes, never the payload
  (a test asserts no `moves`/`toolpaths`/`gcode` fields on the ref).
- **Reference built from the real artifact, never fabricated.** Every provenance field is
  read from the fetched `RunArtifact`; the caller supplies only `run_id` (+ optional
  `expected_*` assertions). A non-existent artifact is a 404, not a dangling reference.
- **Read-then-associate.** The service generates no artifacts; it reads an existing one and
  is read-only against it (a test asserts the artifact object is never mutated).
- **Single canonical association service.** All Project↔artifact associations pass through
  `associate_artifact_with_project` / `merge_artifact_refs`; `PUT /design-state` reuses the
  same merge. No inline project updates.
- **Append-only + idempotent by `run_id`.** Re-associating the same run is a no-op (original
  `associated_at` preserved). Because the ref is derived from the immutable artifact, the
  idempotency comparison ignores association metadata; a genuine provenance divergence on an
  existing `run_id` is surfaced as 409, never silently overwritten.
- **Explicit project identity.** `project_id` is required in the URL; no implicit association.
- **No authority promotion.** Association touches only `manufacturing_artifacts`; it does
  not set `manufacturing_state`, approve production, or alter any other field (regression-
  tested).
- **Concurrency-safe.** The write is a row-locked (`SELECT ... FOR UPDATE`) read-modify-write
  of `Project.data`, matching the SPINE-002 hardening; `PUT /design-state` protects
  `manufacturing_artifacts` from loss the same way it protects `analyzer_observations`.

## Schema change (additive, migration-safe)

`manufacturing_artifacts` defaults to `[]` (`default_factory=list`); old projects read back
with an empty list (`InstrumentProjectData` has `extra="allow"`), so no migration is needed
and `CURRENT_SCHEMA_VERSION` is unchanged. No existing field is altered or removed.

## Remaining adoption work (each a separate order)

- Auto-association hook (associate the run a project-driven CAM execution just produced).
- NC/g-code export keyed off associated artifacts.
- Build-history / provenance reporting views over `manufacturing_artifacts`.
- Phase-5/6 Project Spine work (store retirement, utilities) — unrelated edges.

## Verification

- `py -3.11 -m pytest tests/projects/test_project_artifact_association.py` → **29 passed**
- Regression: `tests/test_analyzer_project_observation.py`, `tests/cam/test_project_cam_execution.py` green
- Governance: `ci/router_count_gate.py` PASS; `tests/test_technical_debt_gates.py` endpoint/duplicate gates PASS
- CBSP21 patch-input + coverage gates (`.cbsp21/patches/spine-004-project-artifacts.json`)
