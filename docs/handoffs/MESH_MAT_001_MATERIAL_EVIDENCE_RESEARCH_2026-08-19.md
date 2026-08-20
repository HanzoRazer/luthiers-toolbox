# MESH-MAT-001 — Material Evidence Integration (research increment)

**Status:** ACTIVE research surface on current `main`  
**Date:** 2026-08-19  
**Namespace:** `services/api/app/mesh/materials/`  
**Authority:** Research-only sidecars; no `qa_core` / `cam_policy` mutation

## Amended grounding (binding)

| Q | Ruling |
|---|--------|
| Q1 | Current `main` only. Do **not** restore deleted `fields/` / `retopo/` (`ee36ddf1`). Mesh Pipeline v0.1.0 tag is design ancestry, not the active code base. |
| Q2 | Proceed now, **fixture-only**. DO-103 Stage 3 provenance adapter deferred. No caller-supplied `HARDWARE=true`. |
| Q3 | Package under `app/mesh/materials/` — not `app/materials/` (tonewood registry). |
| Q4 | Wrap existing `rayleigh_ritz.OrthotropicPlate` with explicit inputs. No `from_wood()` default path. No `inverse_solver`. No thickness recommendation surface. |
| Q5 | ToolBox-local `MaterialEvidenceBundle`; Tap Tone adapters later. |
| Q6 | ADR-0012 `EpistemicStatus` only. UNKNOWN = absence. ASSUMED = `ModelAssumption`, not epistemic enum. |
| Q7 | Research sidecars only (`material_evidence` / `material_prediction` / `prediction_residual`). |

## Pipeline

```text
fixture / imported artifact
        ↓
ADR-0012 epistemic status
        ↓
MaterialEvidenceBundle  (app.mesh.materials.evidence)
        ↓
OrthotropicMaterialState + ModelAssumption serialization
        ↓
OrthotropicPlate (explicit ctor) → solve_rayleigh_ritz
        ↓
PredictedPlateResponse  (epistemic_status=predicted, research_only=true)
        ↓
PredictionResidualReport
```

Future DO-103 Stage 3 maps into the same ToolBox evidence model via an adapter seam; internal representation should not need to change.

## Explicit non-goals (this sprint)

- Restoring Mesh Pipeline v0.1 scaffold modules
- Consuming unfinished Stage 3 HARDWARE contracts
- Mixing specimen evidence into `app.materials` tonewood APIs
- Mutating `qa_core` or `cam_policy`
- Inventing missing `E_C` (fail closed)

## Contracts

- `contracts/material_evidence.schema.json`
- `contracts/material_prediction.schema.json`
- `contracts/prediction_residual.schema.json`

## Tests

```bash
cd services/api && pytest tests/mesh/materials/ -q
```

## Historical note

Tag `toolbox-mesh-pipeline-v0.1.0` remains architectural input / evidence of prior scaffold intent. Any later decision to rebuild field/retopo layers is deliberate and out of scope for MESH-MAT-001.
