# CI-RED-015-L - IBG Sandbox Landmark Candidate Intake Bridge

**Status:** Dev-ready scope  
**Created:** 2026-07-03  
**Baseline surveyed:** `luthiers-toolbox` `origin/main` at `53bbf1a2`; `vectorizer-sandbox` local branch `feature/ibg-kb-facts-ci-guard` at `d688084`  
**Recommended branch:** `fix/ci-red-015l-ibg-sandbox-landmark-intake`  
**Owner lane:** CI-RED-015 / IBG-body-solver alignment  

---

## Purpose

Connect the developmental IBG sandbox to `luthiers-toolbox` in the narrowest safe way: import
`vectorizer-sandbox` landmark candidate records as non-authoritative, review-required
`BodyEvidenceCandidate` objects.

This is not an authority ruling and does not unblock IBG DXF export. It gives luthiers a concrete,
typed intake bridge for the evidence the sandbox is already producing, so future governance decisions
and CI-red remediation can line up around the same object shape instead of loose prose.

---

## Grounding

The sandbox now produces IBG landmark facts:

```text
vectorizer-sandbox/governance/geo_acquisition/geometry_facts/
  melody_maker_body.landmarks.json
  jazzmaster62_body.landmarks.json
```

These files use:

```text
schema_version: ibg-landmark-candidate.v1
status: landmark_candidate
coordinate_space: pixel-space; body-relative norms included; NO mm
```

They carry:

- source filename and source SHA256,
- POS-003 admissibility verdict and P1-P5 measurements,
- upper bout / waist / lower bout landmark candidates,
- body pixel metrics and ratios,
- extraction confidence,
- offset/body-ordering caveats.

`luthiers-toolbox` already has the correct landing zone:

```text
services/api/app/instrument_geometry/body/ibg/body_evidence_candidate.py
services/api/app/instrument_geometry/body/ibg/ibg_intake_gate.py
services/api/app/instrument_geometry/body/ibg/body_grid/body_grid_schema.py
services/api/app/governance/provenance_attachment.py
services/api/app/governance/authority_metadata.py
services/api/app/governance/confidence_envelope.py
docs/governance/coordination/GAMS_GEOMETRY_AUTHORITY_MAPPING_SPEC.md
```

The missing connection is an adapter from sandbox landmark candidate JSON into luthiers'
constitutional intake model.

---

## Core Decision

Treat sandbox landmark candidates as **evidence geometry**, not authority geometry.

Implementation labels to carry in metadata:

```json
{
  "geometry_role": "evidence",
  "authority_state": "governed_evidence_candidate",
  "authority_source": "vectorizer_sandbox:ibg_geo_acquisition",
  "promotion_mechanism": "human_review_and_governance_ratification",
  "export_format_authority": "none"
}
```

The adapter must preserve provenance and caveats, then fail closed under `IBGIntakeGate` until a
human/governance promotion path exists.

---

## Non-Goals

- Do not make sandbox output authoritative.
- Do not convert pixel landmarks to mm without calibration.
- Do not feed these records into `solve-from-landmarks`.
- Do not unblock IBG DXF export or change `BLOCKED_PROVENANCE`.
- Do not change C2 geometry-origin authority.
- Do not add a route or user-facing API in this slice.
- Do not depend on a live checkout of `vectorizer-sandbox` at runtime.

---

## File-by-File Patch Plan

### `services/api/app/instrument_geometry/body/ibg/body_grid/body_grid_schema.py`

Add a source enum value:

```python
IBG_SANDBOX_LANDMARK_CANDIDATE = "ibg_sandbox_landmark_candidate"
```

This lets luthiers distinguish sandbox landmark evidence from DXF, photo extraction, user input, and
spec defaults without pretending it is one of those existing sources.

### New file: `services/api/app/instrument_geometry/body/ibg/morphology_harvest/sandbox_landmark_candidate_adapter.py`

Add a small adapter with no external dependencies beyond the existing luthiers models.

Responsibilities:

- load and validate `ibg-landmark-candidate.v1` JSON,
- reject malformed records with clear errors,
- map records into `BodyEvidence`,
- create a `BodyEvidenceCandidate`,
- preserve source SHA, POS-003 facts, landmark widths, ratios, and caveats in candidate metadata,
- set `geometry_role` and authority metadata per GAMS,
- keep authority at advisory/non-authoritative state,
- run `IBGIntakeGate` and return a review-ready result,
- explicitly block mm landmark conversion unless calibration metadata is present.

Suggested public functions/classes:

```python
class SandboxLandmarkCandidateError(ValueError): ...
class CalibrationRequiredError(SandboxLandmarkCandidateError): ...

def load_sandbox_landmark_candidate(path: Path | str) -> dict: ...
def candidate_to_body_evidence(record: dict) -> BodyEvidence: ...
def candidate_to_body_evidence_candidate(record: dict) -> BodyEvidenceCandidate: ...
def adapt_sandbox_landmark_candidate(record: dict) -> SandboxLandmarkAdapterResult: ...
```

Mapping guidance:

- Use the sandbox `body_metrics_px.centerline_x_px` and each landmark `y_px` as raw pixel coordinates.
- Use `NormalizedPoint.x_norm = 0.0` for centerline landmark records; the landmark width remains metadata,
  because the sandbox record has width-at-y, not a left/right point.
- Use `NormalizedPoint.y_norm` from the sandbox landmark.
- Set raw coordinate space to `RAW_PIXEL`.
- Set `BodyEvidence.source_type` to `IBG_SANDBOX_LANDMARK_CANDIDATE`.
- Store `body_bbox_px_xywh`, `body_metrics_px`, `ordering_ok`, `non_degenerate`,
  `bout_ordering_lower_ge_upper`, and `scope_note` in `candidate.metadata`.

Do not invent `outline_points` if the sandbox record does not include an outline.

### New fixtures:

```text
services/api/tests/fixtures/ibg_sandbox_landmarks/melody_maker_body.landmarks.json
services/api/tests/fixtures/ibg_sandbox_landmarks/jazzmaster62_body.landmarks.json
```

Copy the two number-only sandbox facts from:

```text
C:\Users\thepr\Downloads\vectorizer-sandbox\governance\geo_acquisition\geometry_facts\
```

These are numbers, source filenames, and source SHA values only. Do not copy licensed image/PDF/DXF
derivatives into luthiers.

### New test file:

```text
services/api/tests/test_ibg_sandbox_landmark_candidate_adapter.py
```

Test the bridge directly with the fixtures.

### Optional docs update:

```text
SPRINTS.md
```

Only update after implementation lands. Suggested note: CI-RED-015-L adds a review-only sandbox IBG
landmark intake bridge and does not close C2/R1 authority questions.

---

## Test Cases

### 1. Melody Maker candidate adapts as review-required evidence

Expected:

- adapter succeeds,
- candidate has provenance,
- `candidate.authority_state` is not approved,
- `candidate.review_required is True`,
- `candidate.approved_for_ibg_memory is False`,
- metadata includes `geometry_role="evidence"`,
- metadata includes source repo/subsystem,
- gate result is not valid because human review/authority is missing.

### 2. Provenance and sandbox facts are preserved

Expected:

- `source_sha256` remains the exact 64-character sandbox value,
- `admissibility.verdict == "ADMISSIBLE"`,
- `P1_P5` remains present,
- `coordinate_space` still says no mm,
- `scope_note` is preserved.

### 3. Pixel facts do not become mm landmarks

Expected:

- calling any helper that would produce `LandmarkInput` or solver-ready landmarks without calibration
  raises `CalibrationRequiredError`,
- no test calls `InstrumentBodyGenerator.complete_from_landmarks` with pixel-derived values.

### 4. Jazzmaster offset caveat survives intake

Expected:

- `non_degenerate is True`,
- `width_structure_resolved is True`,
- `bout_ordering_lower_ge_upper is False`,
- `ordering_ok is False`,
- `extraction_confidence == "medium"`,
- the record is not rejected as malformed just because it is an offset body.

### 5. Malformed schema fails loudly

Expected failures:

- wrong `schema_version`,
- missing `provenance.source_sha256`,
- missing required landmark,
- invalid confidence label,
- missing `coordinate_space`.

### 6. Existing IBG blocked-provenance guards still pass

Run existing relevant tests after adding the bridge:

```text
python -m pytest services/api/tests/test_ibg_intake_gate.py
python -m pytest services/api/tests/test_ibg_constitutional_integration.py
python -m pytest tests/governance/test_provenance_attachment_draft.py
python -m pytest tests/test_ibg_provenance_ratification_docs.py
```

---

## Rollout Order

1. Sync an isolated `luthiers-toolbox` worktree from current `origin/main`.
2. Copy the two sandbox landmark JSON fixtures into luthiers test fixtures.
3. Add the `EvidenceSource` enum value.
4. Add the sandbox landmark candidate adapter.
5. Add adapter tests.
6. Run the new adapter test.
7. Run the existing IBG intake/provenance guard tests listed above.
8. If those pass, run the normal API test slice used by the CI-RED-015 lane.
9. Open a PR titled around "IBG sandbox landmark candidate intake bridge".
10. Do not mark any human-approval issue resolved; mark only the connection/readiness work complete.

---

## Acceptance Criteria

The work is complete when luthiers can ingest a sandbox `ibg-landmark-candidate.v1` fixture into a
review-ready `BodyEvidenceCandidate` while preserving:

- source provenance,
- POS-003 admissibility facts,
- pixel/ratio coordinate caveats,
- offset-body caveats,
- GAMS role/authority labels,
- fail-closed intake behavior.

The work is not complete if:

- pixel widths are treated as millimeters,
- the adapter feeds the solver,
- the candidate can populate IBG memory without human review,
- `BLOCKED_PROVENANCE` export guards are loosened,
- or DXF/SVG/file format is used to imply authority.

---

## Human Approval Boundary

No direct human governance approval is needed to implement this bridge because it does not promote
authority. Human approval is still required for:

- authoritative geometry-origin decisions,
- IBG memory promotion,
- IBG DXF export ratification,
- C2/C3 governance enforcement,
- treating sandbox facts as canonical geometry.

This bridge should make those approval needs cleaner, not bypass them.

