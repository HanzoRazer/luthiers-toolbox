# EXPERIMENTS

Accepted runs only in the “Accepted” sections. Voided runs are labeled VOIDED
and are not mixed into accepted results.

## Phase 0 — baseline (accepted)

```text
git fetch origin main
git rev-parse HEAD
git rev-parse origin/main
```

Result:

```text
LAB BASE SHA            (this clone / feature branch parent) cab91edacaedc66a0492c35275ce2c255935bf8e
PRODUCTION BASE SHA     cab91edacaedc66a0492c35275ce2c255935bf8e
HISTORICAL COMPARATOR   cab91edacaedc66a0492c35275ce2c255935bf8e
isolated specimen       git worktree add --detach /tmp/ltb-prod-specimen <SHA>
```

Lab main was not fetched: Consolidation Lab is not in this environment.

## Phase 1 — predecessor verification (accepted)

Lab main 033 lineage-correction files are **not present** in this clone.

Static production check (SKIP EDIT):

- `POST /api/blueprint/vectorize` → `vectorize_blueprint` → `BlueprintOrchestrator.process_file`
- Handoff treats Investigation 033 Legacy Wiring (PR #17) as having already
  corrected the sandbox vs Toolbox Vectorizer conflation.

```text
PREDECESSOR STATUS
  033 MS-A01 merged          (Lab PR #16; not re-read here)
  033 Legacy Wiring merged   (Lab PR #17; not re-read here)
  034 claimed by VEC-SIMPLE-LINEAGE-001 (Lab PR #18)
  SKIP EDIT
```

## Phase 2 — current census refresh

Command (Lab-side; does not write production metrics/):

```text
PYTHONPATH=services/api:investigations/035-legacy-wiring-runtime-verification/artifacts/tools
python investigations/035-legacy-wiring-runtime-verification/artifacts/tools/census_refresh.py
```

`dump_and_assert_routes.py` is imported as-is for `collect_routes()`. The
production `main()` write to `services/api/metrics/live_routes.json` is **not**
invoked (Lab-side workaround). Gate result is recorded under
`artifacts/census/CURRENT_CENSUS_SUMMARY.json`.

```text
ROUTE-TRUTH DEFECT TOUCHED? = NO
```

(Phase 2 output filled after the accepted census run.)

## Phase 3 — candidate selection (accepted, frozen before runtime)

See `artifacts/CANDIDATE_SELECTION.md`.

```text
S1 CAM SimLab FE URL
S2 Soundhole POST dual mount
S3 Polygon offset NC collision
S4 CurveMath DXF legacy export
S5 Fret slots CAM preview
```

## Phase 4 — instrument controls

```text
PYTHONPATH=investigations/035-legacy-wiring-runtime-verification/artifacts/tools
pytest investigations/035-legacy-wiring-runtime-verification/tests/test_instrument_controls.py -v
```

IW-03 (optional Vectorizer control) is a specimen runner in
`runtime_reachability_witness.py` (`iw03`), not the unit-fixture file.

If IW-03 or IW-01/IW-02 fail unexpectedly: STOP before trusting S1–S5.

(Phase 4 output filled after accepted control run.)

## Phases 5–9 — specimens

Each specimen is a separate accepted run of:

```text
PYTHONPATH=services/api:investigations/035-legacy-wiring-runtime-verification/artifacts/tools
python .../runtime_reachability_witness.py sN
```

If the severe stop rule fires, remaining specimen commands are not run.

(Filled after each accepted witness.)

## Phase 10 — test/runtime comparison

```text
python .../test_runtime_compare.py
```

## Phase 11–12 — adjudication / recommendation

See FINDINGS.md and RESULTS.md. Assigned only after runtime evidence is frozen.

## Voided runs

None yet.
