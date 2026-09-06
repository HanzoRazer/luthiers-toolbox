# CLAIM RECORD — Investigation 035 (EQ-A01)

Every material finding uses:

```text
STATEMENT
INSTRUMENT
OBSERVATION
SUPPORTED INFERENCE
SCOPE
LIMITATION
FALSIFIER / CONTROL
EVIDENCE
```

Claims below Phase 5 are **baseline / predecessor / selection** only.
Runtime D-status claims are added only after witnesses are frozen.

---

## EQ-A01-035-01 — Production baseline SHA

```text
STATEMENT
  Current origin/main of HanzoRazer/luthiers-toolbox at Phase 0 is
  cab91edacaedc66a0492c35275ce2c255935bf8e.

INSTRUMENT
  git fetch origin main; git rev-parse origin/main

OBSERVATION
  Local HEAD and origin/main both resolve to
  cab91edacaedc66a0492c35275ce2c255935bf8e
  (Merge pull request #353 manufacturing-spine-001 profiling witness).

SUPPORTED INFERENCE
  Investigation 035 repository-production baseline is that SHA.
  It is not independently witnessed as a deployed-production SHA.

SCOPE
  git remote origin of this environment's luthiers-toolbox clone.

LIMITATION
  No deployment SHA was queried.

FALSIFIER / CONTROL
  A later fetch of origin/main yielding a different SHA would supersede
  this as current, without rewriting this Phase 0 freeze.

EVIDENCE
  EXPERIMENTS.md Phase 0; git log -1 origin/main
```

---

## EQ-A01-035-02 — Historical comparator equals current SHA

```text
STATEMENT
  The historical comparator SHA from the 033 census
  (cab91edacaedc66a0492c35275ce2c255935bf8e) is the same commit as current
  origin/main at Phase 0.

INSTRUMENT
  Handoff-stated comparator vs git rev-parse origin/main

OBSERVATION
  Exact match.

SUPPORTED INFERENCE
  Current vs historical SHA identity does not make count series comparable.
  PR #17 census artifacts are not present in this environment.

SCOPE
  SHA identity only.

LIMITATION
  No PR #17 count tables available here to compare instrumentation.

FALSIFIER / CONTROL
  Discovery of PR #17 artifacts with documented instrument identity would
  allow a normalized comparison; until then: comparison not normalized.

EVIDENCE
  SCOPE.md; EXPERIMENTS.md Phase 0
```

---

## EQ-A01-035-03 — Investigation number 035 is free in this tree

```text
STATEMENT
  This luthiers-toolbox tree has no investigations/035-* directory prior
  to this packet. Lab main was not fetchable in this environment.

INSTRUMENT
  glob investigations/** ; gh/repo search for Lab

OBSERVATION
  No investigations/ tree existed on production main. Consolidation Lab
  repository is not in the cloud-agent repo list.

SUPPORTED INFERENCE
  Number 035 is used here. Collision with a Lab-only 035 cannot be
  disproven without Lab access.

SCOPE
  This clone + GitHub search visible to this token.

LIMITATION
  Lab main not fetched. Predecessor 033 directories live in Lab, not here.

FALSIFIER / CONTROL
  A Lab clone showing investigations/035-* already claimed would collide.

EVIDENCE
  README.md Lab placement note; EXPERIMENTS.md Phase 0–1
```

---

## EQ-A01-035-04 — Current Toolbox Vectorizer is a control, not the seed failure

```text
STATEMENT
  Production mounts POST /api/blueprint/vectorize on
  app.routers.blueprint.vectorize_router.vectorize_blueprint, which
  delegates to BlueprintOrchestrator.process_file.

INSTRUMENT
  Static read of vectorize_router.py and blueprint package __init__
  include_router(vectorize_router). Predecessor 033 lineage ruling (handoff).

OBSERVATION
  Router docstring: single production endpoint, thin wrapper over orchestrator.
  Lab 033 Vectorizer lineage correction is cited by handoff as merged; Lab
  files were not re-read here.

SUPPORTED INFERENCE
  IW-03 may use this route as a negative control. This investigation does
  not treat current Toolbox Vectorizer as the original sandbox seam/gap
  failure.

SCOPE
  Static wiring of the blueprint vectorize route on current SHA.

LIMITATION
  Runtime control is a separate claim (IW-03), recorded after witness.

FALSIFIER / CONTROL
  Runtime POST that reaches a different orchestrator or never calls
  vectorize_blueprint.

EVIDENCE
  services/api/app/routers/blueprint/vectorize_router.py
  services/api/app/routers/blueprint/__init__.py
```

---

## EQ-A01-035-05 — Current census (Lab workaround vs dump as-is)

```text
STATEMENT
  On SHA cab91eda, Lab-workaround live route walk yields 1157 routes.
  dump_and_assert_routes.collect_routes() yields 10 routes.
  Collision count under Lab walk is 15.
  FE API literals 276; 137 absent from live table.
  Historical PR #17 counts are not available here.

INSTRUMENT
  artifacts/tools/census_refresh.py importing dump_and_assert_routes as-is
  plus included-router walk.

OBSERVATION
  artifacts/census/CURRENT_CENSUS_SUMMARY.json collected 2026-09-06T04:19:01Z.
  gate_exit=1 FAIL MVP uniqueness; missing_mvp_exact includes
  /api/rmos/wrap/mvp/dxf-to-grbl and /api/v1/fretboard/dxf.
  Divergence note: FastAPI 0.137 _IncludedRouter has no .path.

SUPPORTED INFERENCE
  Current candidate population exists for manual selection.
  dump-as-is 10 vs workaround 1157 is instrumentation divergence, not a
  production patch. Comparison with PR #17 is not normalized.

SCOPE
  Investigation 035 census files only. Production metrics/ not written.

LIMITATION
  Workaround walk is Lab-side. Production collector was not repaired.

FALSIFIER / CONTROL
  A later collect_routes() on the same SHA returning 1157 would mean the
  FastAPI object model changed or the defect was repaired elsewhere.

EVIDENCE
  artifacts/census/CURRENT_CENSUS_SUMMARY.json
  EXPERIMENTS.md Phase 2
```

---

## EQ-A01-035-06 — IW-03 Vectorizer control reaches intended handler

```text
STATEMENT
  POST /api/blueprint/vectorize on the current app reaches
  vectorize_blueprint (APIRoute.handle spy count = 1).

INSTRUMENT
  runtime_reachability_witness.py iw03
  spy: fastapi.routing.APIRoute.handle keyed by (module, name)

OBSERVATION
  HTTP 200; expected_vectorize_route=1; tiny PNG fails extraction.
  Collected 2026-09-06T04:22:24Z. VOIDED prior run used route.endpoint wrap
  and returned HTTP 422.

SUPPORTED INFERENCE
  Current Toolbox Vectorizer production path is wired to the intended
  route function. Extraction quality of the tiny PNG is out of scope.
  S1–S5 handler-identity spies using the same hook are trusted.

SCOPE
  Handler identity for this control request only.

LIMITATION
  Orchestrator.process_file was not separately counted (bound method).

FALSIFIER / CONTROL
  Repeat POST with expected_vectorize_route=0 would invalidate the hook.

EVIDENCE
  artifacts/census/WITNESS_IW03.json
  artifacts/RUNTIME_WITNESSES.md IW-03
```

---

## EQ-A01-035-07 — S1 SimLab FE URL is not mounted

```text
STATEMENT
  POST /api/cam/simulate_gcode returns HTTP 404. No spied simulation
  handler ran. Intended simulate_gcode_json lives at POST /api/cam/sim/gcode.

INSTRUMENT
  runtime_reachability_witness.py s1 + APIRoute.handle

OBSERVATION
  status 404 {"detail":"Not Found"}; expected_sim_json=0;
  alternate_sim_legacy_under_sim_prefix=0;
  alternate_gcode_consolidated_simulate=0.
  Collected 2026-09-06T04:22:43Z.

SUPPORTED INFERENCE
  The SimLab FE contract URL is not a live mount. App tests of
  /api/cam/sim/gcode do not witness this FE path (relation DIFFERENT).

SCOPE
  This request body and SHA. Does not prove /api/cam/sim/gcode works.

LIMITATION
  Disabled package simulation_router=None was not imported.

FALSIFIER / CONTROL
  A 2xx from POST /api/cam/simulate_gcode on this SHA would falsify.

EVIDENCE
  artifacts/census/WITNESS_S1.json
  artifacts/RUNTIME_WITNESSES.md S1
```

---

## EQ-A01-035-08 — S2 first-match is instrument_router, same facade

```text
STATEMENT
  POST /api/instrument/soundhole first-match is
  instrument_router.get_soundhole_spec, which called bound
  compute_soundhole_spec. Geometry calculate_soundhole did not run.
  Source-module facade spy was 0 (IW-02). HTTP 200 spiral spec.

INSTRUMENT
  runtime_reachability_witness.py s2

OBSERVATION
  expected_geometry_router=0; alternate_legacy_instrument_router=1;
  legacy_router_bound_facade=1; geometry_router_bound_compute=0;
  shared_facade_source_namespace=0.
  diameter_mm=49.9; P:A note Williams 0.143. Collected 2026-09-06T04:22:47Z.

SUPPORTED INFERENCE
  HTTP ownership is the legacy instrument_router, not the geometry split
  router. Physics is the shared facade, not an obsolete calculator.

SCOPE
  This spiral POST on this SHA.

LIMITATION
  Does not rank which router “should” own the URL; that is owner policy.

FALSIFIER / CONTROL
  expected_geometry_router=1 with alternate=0 on the same POST.

EVIDENCE
  artifacts/census/WITNESS_S2.json
```

---

## EQ-A01-035-09 — S3 OffsetLab NC URL executes N17, not governed NC

```text
STATEMENT
  POST /api/cam/polygon_offset.nc with OffsetLab-shaped JSON
  (stepover=0.4, tool_dia=6, link_mode=arc, units=mm) executed
  utility polygon_offset (N17), not governed polygon_offset_nc.
  G-code pass insets step by 0.4 mm, not 0.4×6 mm.

INSTRUMENT
  runtime_reachability_witness.py s3 + APIRoute.handle

OBSERVATION
  HTTP 200 text/plain; expected_governed_nc=0; alternate_utility_n17=1.
  Banner "(N17 Polygon Offset — arcs + feed floors)".
  Pass starts 99.600, 99.200, 98.800, 98.400.
  Collected 2026-09-06T04:22:51Z.

SUPPORTED INFERENCE
  Runtime-confirmed wrong/unintended implementation for this FE contract.
  Manufacturing G-code; stepover unit mismatch is a material consequence.
  Severe-stop predicates all three hold.

SCOPE
  This NC URL + this JSON. Preview URL not invoked.

LIMITATION
  OVERLAP.md records parallel mounts; n17_n18.ts also posts this URL.
  Ownership policy is owner adjudication, not this packet.

FALSIFIER / CONTROL
  Same POST yielding expected_governed_nc=1 and N17 banner absent.

EVIDENCE
  artifacts/census/WITNESS_S3.json
  artifacts/RUNTIME_WITNESSES.md S3 severe-stop freeze
```

---

## EQ-A01-035-10 — S4 CurveMath hits legacy polyline DXF, not governed translate

```text
STATEMENT
  POST /exports/polyline_dxf dispatched export_polyline_dxf.
  Governed translate_to_dxf did not run. HTTP 500.

INSTRUMENT
  runtime_reachability_witness.py s4

OBSERVATION
  actual_legacy_handler=1; expected_governed_translate=0;
  helper source spies 0. Collected 2026-09-06T04:22:56Z.
  Logs showed ezdxf R12 dictionary activity before 500.

SUPPORTED INFERENCE
  FE CurveMath entrypoint is the legacy router, not the governed translator.
  Handler identity is established. Cause of HTTP 500 is not fully isolated.

SCOPE
  This polyline JSON on this SHA. Collected after S3 severe condition.

LIMITATION
  Helper spies were source-module (IW-02). 500 may be history_store or
  response assembly, not “legacy cannot emit DXF.”

FALSIFIER / CONTROL
  expected_governed_translate=1 on this URL, or actual_legacy_handler=0.

EVIDENCE
  artifacts/census/WITNESS_S4.json
```

---

## EQ-A01-035-11 — S5 preview URL reaches preview_fret_slots

```text
STATEMENT
  POST /api/cam/fret_slots/preview reached preview_fret_slots and returned
  HTTP 200 preview JSON (gate=yellow). Fan generator did not run.
  Source-module generate_fret_slot_toolpaths spy was 0 (IW-02).

INSTRUMENT
  runtime_reachability_witness.py s5

OBSERVATION
  expected_preview_handler=1; expected_standard_generator=0;
  alternate_fan_generator=0. operation=fret_slot_preview.
  Collected 2026-09-06T04:23 (WITNESS_S5.json).

SUPPORTED INFERENCE
  At the HTTP layer this specimen is the intended preview handler.
  Yellow gate / missing-model default is not automatically D3 (IW-04).
  Ecosphere DXF sibling was not posted.

SCOPE
  This preview POST. Collected after S3 severe condition.

LIMITATION
  Generator body not counted at bound-name namespace.

FALSIFIER / CONTROL
  expected_preview_handler=0 on this URL.

EVIDENCE
  artifacts/census/WITNESS_S5.json
```

---

## EQ-A01-035-12 — Spy location: APIRoute.handle vs source-module patch

```text
STATEMENT
  After FastAPI include_router, patching the source module name often
  reports 0 calls (IW-02). Handler identity for S1–S5 used
  fastapi.routing.APIRoute.handle.

INSTRUMENT
  tests/test_instrument_controls.py IW-06 / IW-06b / IW-07 (the APIRoute.handle
  hook itself), IW-01 / IW-02 (module patching, the contrasting mechanism),
  voided IW-03 endpoint wrap.

  CORRECTED 2026-09-06: this field previously named only IW-01/IW-02. Those
  validate module-level patching — the mechanism that reads 0 — and said
  nothing about the hook this claim certifies. IW-06 supplies the missing
  positive and negative control on a purpose-built two-route app.

OBSERVATION
  IW-01 bound spy fires; IW-02 source spy does not. endpoint wrap → 422.
  APIRoute.handle spy fired on accepted IW-03 and on S2/S3/S4/S5 handlers.
  IW-06: dispatched endpoint counts 1, mounted-but-undispatched endpoint
  counts 0 in the same request. IW-06b: status and body are byte-identical
  with and without the hook.

SUPPORTED INFERENCE
  Zero on a source-module spy is not proof of non-execution.

SCOPE
  This harness and FastAPI 0.137 in /tmp/ltb-035-venv.

LIMITATION
  Not a general FastAPI version claim.

FALSIFIER / CONTROL
  Module patch after include_router incrementing on a live request.

EVIDENCE
  EXPERIMENTS.md Phase 4 and Voided runs
  tests/test_instrument_controls.py
```

---

## EQ-A01-035-13 — Sample recommendation TARGET_SPECIFIC_FAILURE_CLASS

```text
STATEMENT
  In this five-specimen sample, the repeating mechanism is wire-URL /
  FastAPI first-match among dual mounts or relocated prefixes, not
  “all static candidates are unwired.” Recommendation:
  TARGET_SPECIFIC_FAILURE_CLASS.

INSTRUMENT
  Manual adjudication after frozen witnesses (FINDINGS.md, RESULTS.md)

OBSERVATION
  D2=3 (S2, S3, S4); D5=1 (S5); D6=1 (S1).
  Confirmed false-integration count 3 (S1, S3, S4) with S2 as ownership
  D2 not obsolete calculator. Severe stop S3. S5 correctly wired at HTTP.

SUPPORTED INFERENCE
  Broader audit of all 15 collisions / 137 unmatched FE literals is not
  justified by this sample. Owner adjudication of S3 is the next
  production decision. No production patch is authorized here.

SCOPE
  These five manually selected specimens on SHA cab91eda.

LIMITATION
  Sample is not a repository-wide rate. Human selected high-risk cases.

FALSIFIER / CONTROL
  Re-run of the same five requests on this SHA with different handler
  identity would require re-adjudication.

EVIDENCE
  artifacts/FINDINGS.md; RESULTS.md
```
