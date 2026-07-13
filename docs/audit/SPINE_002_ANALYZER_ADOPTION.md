# SPINE-002 — Analyzer Observation Adoption

**Status:** Implemented (held draft PR)
**Scope:** First read/write adoption edge of the ADR-002 Instrument Project Graph —
Analyzer → `AnalyzerObservation` → canonical project state.
**Depends on:** ADR-002 (Instrument Project Graph, Accepted); LAB-021 (spine recovery,
WP-PS-3 identified this edge as unbuilt).

---

## Why this exists

ADR-002 locks the decision (#6) that *"the Analyzer enriches project state with
`AnalyzerObservation`; it never overrides `bridge_state`, `material_selection`, or
`spec`."* The Lab recovery (LAB-021) found that while `InstrumentProjectData` and its
persistence are built (Phases 1–5), the Analyzer edge that decision assumes **was never
wired** — an `AnalyzerObservation` was constructed nowhere in the codebase. The project
spine was a *partial island*: the storage existed, but this producer was not connected.

SPINE-002 connects exactly that one edge — no more. It is deliberately the smallest
adoption increment that turns a locked-but-unbuilt decision into a working read/write
path, so the remaining edges (CAM validated reads, store retirement) can follow as
separate orders against a now-proven pattern.

## What changed

| File | Kind | Role |
|------|------|------|
| `app/analyzer/project_observation.py` | new | Pure mapping/validation: `InterpretationResult` (+ explicit `run_id`) → `AnalyzerObservation`. No persistence, no HTTP. |
| `app/analyzer/schemas.py` | modified | Add `AppendObservationRequest` (wraps the interpretation + explicit `run_id`, optional `wsi`/`interpretation_confidence`). |
| `app/analyzer/router.py` | modified | Add `POST /api/analyzer/projects/{project_id}/observations`. |
| `app/projects/service.py` | modified | Add canonical `merge_analyzer_observations` (append-only by `run_id`) and `append_analyzer_observation` (project-state write). |
| `app/projects/router.py` | modified | `PUT /design-state` now uses the shared `merge_analyzer_observations` instead of an inline copy of the same merge. |
| `tests/test_analyzer_project_observation.py` | new | Unit + router-integration coverage of the new edge. |
| `docs/adr/ADR-002-...md` | modified | Non-normative implementation-status note. |

## Design boundaries honored

- **Uses the existing spine.** No `app.project` / `ProjectSpine` / `ProjectObservationV2`
  was created. State lives where ADR-002 put it: `InstrumentProjectData.analyzer_observations`
  persisted in `Project.data`. No new table, no parallel authority.
- **Ownership split.** The Analyzer owns *interpretation* (content, confidence, run
  identity, evidence). The Project Spine owns *association, append-only storage, and
  canonical serialization*. The mapping module contains no persistence; the service
  contains no interpretation.
- **Append-only + idempotent.** Observations are keyed by the stable, explicit `run_id`.
  Re-posting the same run is a no-op; existing observations are never mutated or replaced.
  The dedup rule has **one** implementation (`merge_analyzer_observations`), now shared by
  both writers, so `PUT /design-state` and the new edge cannot diverge.
- **Advisory only — no authority promotion.** The write touches only
  `analyzer_observations`. It confers no geometry, material, CAM, or RMOS/manufacturing
  authority and never overrides `spec` / `bridge_state` / `material_selection` /
  `manufacturing_state`. A regression test asserts every other serialized field is
  byte-identical across the write.
- **Explicit `project_id`, explicit `run_id`, no fabrication.** The project is addressed
  explicitly in the URL (no inference). `run_id` is supplied by the caller — it is not
  present on `InterpretationResult` and is never invented. Missing required identity
  (`run_id` / `specimen_id` / `interpreted_at`) is a `400`, never a fabricated value.
  Absent optional provenance (`wsi`, `interpretation_confidence`, reference instrument) is
  left empty, not filled in.
- **Schema unchanged.** The existing `AnalyzerObservation` schema was authoritative and
  sufficient; it was not extended.
- **tap_tone_pi boundary intact.** No `tap_tone_pi` import is added. The Analyzer
  continues to consume only `viewer_pack` data; `wsi` is carried through from the caller
  when available.

## Endpoint

```
POST /api/analyzer/projects/{project_id}/observations
  auth:  owner of project (reuses projects._get_project_or_404)
  body:  AppendObservationRequest { interpretation, run_id, wsi?, interpretation_confidence? }
  200:   DesignStateResponse   (the updated canonical project state)
  400:   missing/blank required identity in the interpretation or run_id
  403:   caller does not own the project
  404:   project not found / archived
  422:   request schema violation (e.g. run_id field absent)
```

## Non-goals (explicitly deferred to later orders)

CAM/RMOS migration; Pinia-store retirement (Phase 7); Art Studio; Phase 6 utilities;
an event bus. These are separate adoption edges and each warrants its own order.

## Verification

- `py -3.11 -m pytest tests/test_analyzer_project_observation.py -q`
- CBSP21 patch-input + coverage gates (see
  `.cbsp21/patches/spine-002-analyzer-observation-adoption.json`).
