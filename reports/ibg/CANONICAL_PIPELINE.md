# Instrument Body Generator — file list

Verified against live code at `2646992fc294a904438042d529b939ec6db80662` (`origin/main`).

IBG is **Instrument Body Generator**: a parametric body completor. It consumes DXF / landmarks. It does not process images.

`vectorizer-sandbox` is out of scope. `services/api/app/ibg_repository/` is a **repository-proposal** package, not this geometry pipeline. It is not in the zip.

Do not copy-paste these files. Use the zip (see `HOW_TO_DOWNLOAD.md`).

> **Source of truth.** This document and the zip beside it are a **snapshot**, verified at
> the commit named above. The canonical source is the repository at that commit — not this
> file, and not the zip. The source files keep changing; when they do, this snapshot goes
> stale and nothing here will announce it. **If a path below disagrees with the repository,
> the repository is right.**
>
> Every path listed here is a real repository path, so any entry can be checked directly
> against `main`. Governance for this pipeline lives in
> `docs/governance/IBG_ROLE_DEFINITION.md`, which is authoritative over this list on any
> question of what IBG is permitted to do.

---

## Path A — Body Solver HTTP (production intake)

```
hostinger/body-outline-editor.html
    → POST /api/body/solve-from-landmarks   (BOE "Solve Outline"; auth required)
    → services/api/app/routers/body_solver_router.py
    → InstrumentBodyGenerator.complete_from_landmarks()

POST /api/body/solve-from-dxf
    → same router
    → InstrumentBodyGenerator.complete_from_dxf()
    → ConstraintExtractor (DXF landmarks)
    → optional LayerConsolidator
    → BodyContourSolver.solve()
```

BOE does **not** call `solve-from-dxf`. That endpoint exists on the same router.

```
complete_from_dxf / complete_from_landmarks / generate_from_defaults
    → services/api/app/instrument_geometry/body/ibg/instrument_body_generator.py
    → constraint_extractor.py
    → body_contour_solver.py
         → arc_reconstructor.py  (fit_circle_3pts, falloff, Sevy/Mottola helpers)
    → outline_to_dxf() → cam/dxf_writer.py + util/ibg_dxf_export_lifecycle.py
```

| File | Role |
|------|------|
| `hostinger/body-outline-editor.html` | BOE UI. Calls `/body/solve-from-landmarks`. |
| `services/api/app/routers/body_solver_router.py` | `POST /api/body/solve-from-dxf`, `solve-from-landmarks`, session GET/PUT. |
| `services/api/app/instrument_geometry/body/ibg/__init__.py` | Public exports. |
| `services/api/app/instrument_geometry/body/ibg/instrument_body_generator.py` | `InstrumentBodyGenerator` + `INSTRUMENT_SPECS`. |
| `services/api/app/instrument_geometry/body/ibg/constraint_extractor.py` | Landmarks from DXF. |
| `services/api/app/instrument_geometry/body/ibg/body_contour_solver.py` | `BodyContourSolver`, `SolvedBodyModel`, `outline_to_dxf`. |
| `services/api/app/instrument_geometry/body/ibg/arc_reconstructor.py` | Arc / gap helpers used by the solver. |
| `services/api/app/instrument_geometry/body/ibg/session_store.py` | Session store for the HTTP API. |
| `services/api/app/instrument_geometry/body/ibg/reference_outline_bridge.py` | Optional import from `arc_reconstructor.py`. |
| `services/api/app/cam/layer_consolidator.py` | Optional LINE→polyline step before extract. |
| `services/api/app/cam/dxf_writer.py` | R12 writer used by `outline_to_dxf()`. |
| `services/api/app/util/ibg_dxf_export_lifecycle.py` | Fail-closed IBG DXF save gate. |
| `services/api/app/util/dxf_compat.py` | Used by `layer_consolidator.py`. |
| `services/api/app/util/dxf_lifecycle_guard.py` | Lifecycle context for the save gate. |
| `services/api/app/governance/ibg_export_provenance.py` | Attachment from `BodyEvidenceCandidate` on save. |
| `services/api/app/governance/provenance_attachment.py` | Draft / exportability. |
| `services/api/app/governance/provenance_record.py` | Provenance record type. |
| `services/api/app/governance/authority_state.py` | Authority states used by candidates. |
| `services/api/app/governance/confidence_declaration.py` | Confidence types. |
| `services/api/app/governance/review_enforcement.py` | Review gate types. |

Open on GitHub (one file at a time):

- https://github.com/HanzoRazer/luthiers-toolbox/blob/main/services/api/app/instrument_geometry/body/ibg/instrument_body_generator.py
- https://github.com/HanzoRazer/luthiers-toolbox/blob/main/services/api/app/instrument_geometry/body/ibg/body_contour_solver.py
- https://github.com/HanzoRazer/luthiers-toolbox/blob/main/services/api/app/routers/body_solver_router.py
- https://github.com/HanzoRazer/luthiers-toolbox/blob/main/hostinger/body-outline-editor.html

---

## Path B — Evidence / workflow (same IBG package, not the HTTP default)

These live under `ibg/` and are imported by harvest / workflow code. The body-solver router does **not** call them.

| Area | Files |
|------|--------|
| Intake object | `body_evidence_candidate.py`, `ibg_intake_gate.py` |
| Body grid | `body_grid/*.py` |
| Workflow 1A | `workflow/ibg_workflow_pipeline.py` and siblings |
| Harvest | `morphology_harvest/*.py` (outputs/ omitted) |

`instrument_body_generator.analyze_morphology()` optionally imports `body_grid.morphology_descriptor`. That is not on `complete_from_dxf` / `complete_from_landmarks`.

---

## Not in this zip

| Path | Why |
|------|-----|
| `services/api/app/ibg_repository/` | Code-change proposal pipeline. Not the body generator. |
| `sandbox/arc_reconstructor/` | Removed from this tree; production copy is `ibg/arc_reconstructor.py`. |
| Vectorizer files | Upstream DXF producer. Separate zip (PR #334). |
| `morphology_harvest/outputs/` | Generated validation dumps. |

---

## Zip contents

`canonical_ibg_pipeline.zip` has Path A + Path B Python (and BOE HTML), with repo paths preserved. Start with `CANONICAL_PIPELINE.md` inside the zip.
