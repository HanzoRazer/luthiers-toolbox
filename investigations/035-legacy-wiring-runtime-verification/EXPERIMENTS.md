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

## Phase 2 — current census refresh (accepted)

Command (Lab-side; does not write production metrics/):

```text
PYTHONPATH=services/api:investigations/035-legacy-wiring-runtime-verification/artifacts/tools
/tmp/ltb-035-venv/bin/python \
  investigations/035-legacy-wiring-runtime-verification/artifacts/tools/census_refresh.py
```

Collected at `2026-09-06T04:19:01Z`. Output under `artifacts/census/` only.

```text
CURRENT live routes (Lab workaround)     1157
dump_and_assert_routes.collect_routes()    10
collisions                                 15
name-hint modules                          23
FE API literals                           276
FE literals absent from live              137
test files                                455 (185 TestClient)
gate_exit                                   1  FAIL: MVP-path uniqueness gate
missing_mvp_exact  /api/rmos/wrap/mvp/dxf-to-grbl
                   /api/v1/fretboard/dxf
ROUTE-TRUTH DEFECT TOUCHED? = NO
```

`dump_and_assert_routes.py` is imported as-is for `collect_routes()`. The
production `main()` write to `services/api/metrics/live_routes.json` is **not**
invoked. Divergence: FastAPI 0.137 `_IncludedRouter` has no `.path`, so the
production collector returned 10 rows; Lab workaround walked included routers.

Historical PR #17 counts are unavailable here. Comparison not normalized.

## Phase 3 — candidate selection (accepted, frozen before runtime)

See `artifacts/CANDIDATE_SELECTION.md`.

```text
S1 CAM SimLab FE URL
S2 Soundhole POST dual mount
S3 Polygon offset NC collision
S4 CurveMath DXF legacy export
S5 Fret slots CAM preview
```

## Phase 4 — instrument controls (accepted)

```text
PYTHONPATH=investigations/035-legacy-wiring-runtime-verification/artifacts/tools
/tmp/ltb-035-venv/bin/python -m pytest \
  investigations/035-legacy-wiring-runtime-verification/tests/test_instrument_controls.py -v
```

```text
test_iw01_bound_name_spy_fires                                    PASSED
test_iw02_wrong_namespace_spy_may_not_fire                        PASSED
test_iw04_fail_closed_guard_is_not_automatically_defect           PASSED
test_iw05_placeholder_substitution_distinguished_from_intended    PASSED
test_call_counter_wraps_original_return                           PASSED
5 passed
```

IW-03 (optional Vectorizer control) is a specimen runner in
`runtime_reachability_witness.py` (`iw03`), not the unit-fixture file.

Accepted IW-03 (after VOIDED wrap of `route.endpoint`; see Voided runs):

```text
PYTHONPATH=services/api:services/blueprint-import:investigations/035-legacy-wiring-runtime-verification/artifacts/tools
/tmp/ltb-035-venv/bin/python \
  investigations/035-legacy-wiring-runtime-verification/artifacts/tools/runtime_reachability_witness.py iw03
```

```text
HTTP 200  expected_vectorize_route=1
tiny PNG fails extraction; intended route still fires
spy method: fastapi.routing.APIRoute.handle keyed by (endpoint.__module__, endpoint.__name__)
```

Harness control passed. S1–S5 handler-identity spies using the same hook are
trusted. Source-module patches remain IW-02 controls and may stay at 0.

## Phases 5–9 — specimens (accepted)

Each specimen:

```text
PYTHONPATH=services/api:services/blueprint-import:investigations/035-legacy-wiring-runtime-verification/artifacts/tools
/tmp/ltb-035-venv/bin/python \
  investigations/035-legacy-wiring-runtime-verification/artifacts/tools/runtime_reachability_witness.py sN
```

S4 and S5 were launched in the same batch as S3 before S3 was inspected.
Severe-stop is recorded from S3; S4/S5 remain frozen extra evidence.

### Phase 5 — S1 (accepted)

```text
POST /api/cam/simulate_gcode  →  HTTP 404 {"detail":"Not Found"}
expected_sim_json=0
alternate_sim_legacy_under_sim_prefix=0
alternate_gcode_consolidated_simulate=0
collected 2026-09-06T04:22:43Z
```

### Phase 6 — S2 (accepted)

```text
POST /api/instrument/soundhole  spiral payload  →  HTTP 200
expected_geometry_router=0
alternate_legacy_instrument_router=1
legacy_router_bound_facade=1
geometry_router_bound_compute=0
shared_facade_source_namespace=0
collected 2026-09-06T04:22:47Z
```

### Phase 7 — S3 (accepted; severe stop)

```text
POST /api/cam/polygon_offset.nc  stepover=0.4 tool_dia=6  →  HTTP 200
expected_governed_nc=0
alternate_utility_n17=1
G-code banner: (N17 Polygon Offset — arcs + feed floors)
pass insets 99.600, 99.200, 98.800, 98.400
collected 2026-09-06T04:22:51Z
SEVERE STOP TRIGGERED = YES
```

### Phase 8 — S4 (accepted; collected in same batch as S3)

```text
POST /exports/polyline_dxf  →  HTTP 500
actual_legacy_handler=1
legacy_ezdxf_helper=0
legacy_ascii_r12_fallback=0
expected_governed_translate=0
collected 2026-09-06T04:22:56Z
```

### Phase 9 — S5 (accepted; collected in same batch as S3)

```text
POST /api/cam/fret_slots/preview  →  HTTP 200
expected_preview_handler=1
expected_standard_generator=0
alternate_fan_generator=0
gate=yellow
collected 2026-09-06T04:23:00Z
```

JSON frozen at `artifacts/census/WITNESS_S1.json` … `WITNESS_S5.json`,
`WITNESS_IW03.json`, `WITNESS_BUNDLE.json`. Narrative:
`artifacts/RUNTIME_WITNESSES.md`.

## Phase 10 — test/runtime comparison (accepted)

```text
/tmp/ltb-035-venv/bin/python \
  investigations/035-legacy-wiring-runtime-verification/artifacts/tools/test_runtime_compare.py
```

```text
S1 DIFFERENT
S2 PARTIAL
S3 DIFFERENT
S4 DIFFERENT
S5 PARTIAL
```

Machine extraction: `artifacts/census/TEST_RUNTIME_COMPARISON.json`.
Narrative: `artifacts/TEST_RUNTIME_COMPARISON.md`.

## Phase 11–12 — adjudication / recommendation (accepted)

Assigned only after runtime evidence freeze. See FINDINGS.md and RESULTS.md.

```text
D2=3 D5=1 D6=1
RECOMMENDATION = TARGET_SPECIFIC_FAILURE_CLASS
```

## Voided runs

### VOIDED — IW-03 first attempt (route.endpoint wrap)

```text
VOIDED
instrument   runtime_reachability_witness.py iw03
fault        wrapping APIRoute.endpoint after include_router broke FastAPI
             signature inspection
result       HTTP 422 missing query args/kwargs
disposition  not used as IW-03 evidence; spy method replaced with
             fastapi.routing.APIRoute.handle
```

Wrapping `dependant.call` / `route.app` also showed 0 calls and is not an
accepted IW-03 result. Those probes informed spy-location design only.

No other voided specimen runs.

## Phase 13 — draft PR / CI declaration (accepted)

Draft PR: https://github.com/HanzoRazer/luthiers-toolbox/pull/356

Required CBSP21 Patch Manifest Gate failed because this PR brought no owned
manifest (CBSP21-NOBORROW-001). Follow-up (not a CBSP21 policy change): add
`.cbsp21/patches/legacy-wiring-035-runtime-verification.json` declaring the
Investigation 035 packet. Checker scripts, schema, and thresholds are
unmodified.

```text
ROUTE-TRUTH DEFECT TOUCHED? = NO
CBSP21 CHECKERS MODIFIED? = NO
PRODUCTION MODIFIED? = NO
```
