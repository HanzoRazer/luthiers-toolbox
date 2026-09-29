# Candidate Ledger (human-readable mirror)

Base SHA: `5258d4c6754c122fcdad65df2019c9f7c11eaffe`. Evidence-only. Runtime reachability is primary authority.

**This Markdown mirrors `CANDIDATE_LEDGER.json` exactly** (same candidate IDs). The JSON is canonical; a validation test asserts ID-set and disposition-vocabulary parity.

Total candidates: **28** (target 20–30, hard ceiling 40). Overflow backlog: **8** (not adjudicated this increment).

## Disposition summary

| Disposition | Count |
|---|---|
| BUILT_DISCONNECTED | 4 |
| DEAD_CONFIRMED | 1 |
| DEFERRED_AUTHORIZED | 1 |
| DORMANT_UNRESOLVED | 3 |
| DUPLICATE_SUPERSEDED | 5 |
| LIVE_INCOMPLETE | 11 |
| PROTOTYPE_EXPLICIT | 3 |

## Candidates

| ID | Feature | Disposition | Conf | Jan | Introduced | Recommended action |
|---|---|---|---|---|---|---|
| `CF2-01-GEOMETRY-EXPORT` | Geometry G-code/bundle export: POST /api/geometry/export_bun | LIVE_INCOMPLETE | high | n | 2026-02-10 | Contain export_bundle + export_bundle_multi behind RMOS authority mirr |
| `CF2-02-POLYGON-OFFSET-DRAFT` | Polygon-offset NC draft lane: POST /api/cam/polygon_offset.n | DEFERRED_AUTHORIZED | high | n | 2025-12-13 | Treat as intentional draft/preview lane; document, do not contain in C |
| `CF2-03-SAW-TOOLPATHS` | Saw Lab toolpaths from decision: POST /api/saw/batch/toolpat | LIVE_INCOMPLETE | high | n | 2025-12-26 | Contain both behind RMOS authority via the shared service, mirroring t |
| `CF2-04-RMOS-TOOLPATHS` | RMOS generic toolpaths: POST /api/rmos/toolpaths (generate_t | LIVE_INCOMPLETE | medium | n | 2025-12-04 | Assess whether this generic entrypoint should be governed or is supers |
| `CF2-05-RMOS-WRAP-DXF-GRBL` | RMOS wrap MVP: POST /api/rmos/wrap/mvp/dxf-to-grbl (inline G | LIVE_INCOMPLETE | medium | n | unverified | Classify MVP status; contain or mark prototype after confirming consum |
| `CF2-06-VISION-PHOTO-GCODE` | Vision photo-to-gcode: POST /api/vision/photo-to-gcode (inli | LIVE_INCOMPLETE | medium | n | unverified | Contain or defer pending Vision Beta maturity decision. |
| `CF2-07-RADIUS-DISH` | Acoustic radius-dish G-code: POST /api/acoustics/radius-dish | LIVE_INCOMPLETE | high | n | 2026-03-21 | Contain behind RMOS authority (single-route increment). |
| `CF2-08-INLAY-EXPORT` | Art Studio inlay G-code export: POST /api/art-studio/inlay/e | LIVE_INCOMPLETE | high | n | 2026-03-10 | Contain behind RMOS authority (single-route increment). |
| `CF2-09-FRET-SLOTS-PREVIEW` | Fret slot CAM preview: POST /api/cam/fret_slots/preview (gen | DORMANT_UNRESOLVED | medium | n | 2025-12-09 | Determine whether 'preview' is a program emitter requiring containment |
| `CF2-10-HEADSTOCK-TRANSITION` | Headstock transition G-code: POST /api/headstock/transition/ | LIVE_INCOMPLETE | high | n | 2026-03-18 | Contain behind RMOS authority (single-route increment). |
| `CONS-01-CAM-ASSIST-ROUTER` | CAM Assist / cognition (30 routes) | BUILT_DISCONNECTED | high | n | 2026-05-20 | Decide mount-or-retire; strong retirement candidate pending owner ruli |
| `CONS-02-RMOS-OPERATIONS-ROUTER` | RMOS Operations lane (/api/rmos/operations) | BUILT_DISCONNECTED | high | n | 2025-12-31 | Mount-or-retire ruling; confirm intended consumer. |
| `CONS-03-CAMCORE-SAWLAB-DUP` | cam_core Saw Lab router (duplicate mount surface) | DUPLICATE_SUPERSEDED | high | n | 2025-12-14 | Retire after import/build proof; canonical survivor = app.saw_lab. |
| `CONS-04-RMOS-FEASIBILITY-HTTP-DUP` | RMOS feasibility HTTP router (duplicate of api_routes /feasi | DUPLICATE_SUPERSEDED | high | n | 2025-12-04 | Retire the unused HTTP surface only; keep the library. Requires care ( |
| `CONS-05-CORE-FEATURES-REGISTRY` | Legacy parallel feature loader register_all_features / FEATU | DUPLICATE_SUPERSEDED | medium | n | 2026-02-09 | Confirm no dynamic caller, then retire; canonical survivor = router_re |
| `CONS-06-COMPARE-AUTOMATION` | Compare automation sub-router | DORMANT_UNRESOLVED | high | n | 2025-12-20 | Determine intended automation feature; wire or remove the gated block. |
| `CONS-07-RMOS-ACOUSTICS-AGGREGATOR` | RMOS acoustics aggregator shell | DUPLICATE_SUPERSEDED | medium | n | 2025-12-26 | Retire unmounted aggregator after confirming submodules are reached vi |
| `CONS-08-INSTRUMENT-GEOMETRY-MONOLITH` | Instrument-geometry monolith router (pre-split) | DUPLICATE_SUPERSEDED | high | n | 2025-12-07 | Retire the monolith after parity confirmation with the split package. |
| `CONS-09-ART-DESIGN-FIRST-WORKFLOW` | Art Studio design-first workflow (client SDK/store/panels pr | BUILT_DISCONNECTED | high | n | unverified | Either implement the backend contract to connect the existing client a |
| `CONS-10-APERTURE-WORKSPACE-SHELL` | Aperture beta consolidation shell mounting canonical spiral  | LIVE_INCOMPLETE | high | n | unverified | Complete parity verification then converge, or keep dual until parity  |
| `CONS-11-FEEDBACK-TRAININGDATA` | Vectorizer user-correction feedback + training-data retraini | DEAD_CONFIRMED | high | n | unverified | Retain as governed-dead (a gate already enforces it) OR retire with ow |
| `CONS-12-CALIBRATION-INTEGRATION` | Vectorizer calibration integration | DORMANT_UNRESOLVED | medium | n | unverified | Determine intended wiring or defer; CLAUDE.md flags it for wiring. |
| `CONS-13-PHASE4-DIMENSION-LINKER` | Blueprint phase4 dimension linker | PROTOTYPE_EXPLICIT | medium | n | unverified | Keep as tested prototype; integration is a separate future decision. |
| `CONS-14-VECTORIZER-THREELOOP-AGE` | Vectorizer three-loop feedback + AGE architecture | PROTOTYPE_EXPLICIT | high | n | unverified | No action; explicitly out of runtime scope per CLAUDE.md. Do not treat |
| `CONS-15-CAM-ROSETTE-PROTOTYPES` | Rosette CAM parametric prototypes (17 modules) | PROTOTYPE_EXPLICIT | high | n | 2026-03-12 | Keep as isolated prototypes; do not retire on age alone. |
| `CONS-16-CLIENT-ORPHAN-DASHBOARDS` | Dashboard/index shells not registered in the client router | BUILT_DISCONNECTED | high | n | 2025-12-07 | Route or retire the named orphan dashboards after confirming they are  |
| `CONS-17-API-V1-DUAL-SURFACE` | Parallel /api/v1/* API surface (fretboard, dxf, frets) | LIVE_INCOMPLETE | high | n | 2026-02-12 | Adjudicate the dual-API story; document canonical vs v1 boundaries (no |
| `CONS-18-AI-CONTEXT-ADAPTER` | AI context adapter routes (advisory) | LIVE_INCOMPLETE | medium | Y | 2026-01-14 | Assess completeness of AI advisory adapter; likely non-manufacturing,  |

## Evidence & rationale (per candidate)

### `CF2-01-GEOMETRY-EXPORT` — Geometry G-code/bundle export: POST /api/geometry/export_bundle, /api/geometry/export_bundle_multi, /api/geometry/export_gcode
- Paths: `services/api/app/routers/geometry/bundle_router.py`, `services/api/app/routers/geometry/export_router.py`
- Disposition: **LIVE_INCOMPLETE** (confidence high); January provenance: False; introduced 2026-02-10 (`b9948d09`)
- Backend routes: ['/api/geometry/export_bundle', '/api/geometry/export_bundle_multi', '/api/geometry/export_gcode']; client consumers: ['packages/client/src DXF/geometry export flows']; manufacturing-output: LIVE_UNGOVERNED
  - evidence: Inventory rows LIVE_UNGOVERNED for all three
  - evidence: export_gcode has a governed sibling export_gcode_governed (FAIL_CLOSED, RUNTIME_PROVED) at export_router.py:209 -> a proven in-repo containment template
  - evidence: export_bundle/export_bundle_multi have NO governed sibling
- Recommended action: Contain export_bundle + export_bundle_multi behind RMOS authority mirroring export_gcode_governed; reconcile the export_gcode draft/governed split.
- Future increment: OPTION A alternative (geometry export containment, 13->10)

### `CF2-02-POLYGON-OFFSET-DRAFT` — Polygon-offset NC draft lane: POST /api/cam/polygon_offset.nc
- Paths: `services/api/app/routers/polygon_offset_router.py`
- Disposition: **DEFERRED_AUTHORIZED** (confidence high); January provenance: False; introduced 2025-12-13 (`c0187479`)
- Backend routes: ['/api/cam/polygon_offset.nc', '/api/cam/polygon_offset_governed.nc']; client consumers: ['SVG debug panel (preview)']; manufacturing-output: LIVE_UNGOVERNED
  - evidence: polygon_offset_router.py:126 docstring: 'For governed execution ... use /polygon_offset_governed.nc'
  - evidence: governed sibling /api/cam/polygon_offset_governed.nc is FAIL_CLOSED (RUNTIME_PROVED)
- Recommended action: Treat as intentional draft/preview lane; document, do not contain in CF2 unless policy requires draft-lane governance.
- Future increment: none (deferred; governed path already exists)

### `CF2-03-SAW-TOOLPATHS` — Saw Lab toolpaths from decision: POST /api/saw/batch/toolpaths/from-decision, /api/saw/compare/toolpaths
- Paths: `services/api/app/services/saw_lab_toolpaths_from_decision_service.py`
- Disposition: **LIVE_INCOMPLETE** (confidence high); January provenance: False; introduced 2025-12-26 (`d235453e`)
- Backend routes: ['/api/saw/batch/toolpaths/from-decision', '/api/saw/compare/toolpaths']; client consumers: ['Saw Lab client flows']; manufacturing-output: LIVE_UNGOVERNED
  - evidence: Both rows LIVE_UNGOVERNED and share generate_toolpaths_from_decision in saw_lab_toolpaths_from_decision_service.py
  - evidence: No governed sibling exists (unlike geometry/polygon draft lanes)
- Recommended action: Contain both behind RMOS authority via the shared service, mirroring the Rosette pattern.
- Future increment: OPTION A (recommended: saw toolpaths containment, 13->11)

### `CF2-04-RMOS-TOOLPATHS` — RMOS generic toolpaths: POST /api/rmos/toolpaths (generate_toolpaths_for_design)
- Paths: `services/api/app/rmos/api_contracts.py`
- Disposition: **LIVE_INCOMPLETE** (confidence medium); January provenance: False; introduced 2025-12-04 (`1bc1023c`)
- Backend routes: ['/api/rmos/toolpaths']; client consumers: ['unverified']; manufacturing-output: LIVE_UNGOVERNED
  - evidence: Inventory row LIVE_UNGOVERNED; generate_toolpaths_for_design is a shared multi-mode generator (saw/rosette/vcarve) already used by governed routes
- Recommended action: Assess whether this generic entrypoint should be governed or is superseded by mode-specific governed routes.
- Future increment: candidate for a later CF2 or convergence increment

### `CF2-05-RMOS-WRAP-DXF-GRBL` — RMOS wrap MVP: POST /api/rmos/wrap/mvp/dxf-to-grbl (inline G-code)
- Paths: `services/api/app/rmos/mvp_router.py`
- Disposition: **LIVE_INCOMPLETE** (confidence medium); January provenance: False; introduced unverified (`unverified`)
- Backend routes: ['/api/rmos/wrap/mvp/dxf-to-grbl']; client consumers: ['unverified']; manufacturing-output: LIVE_UNGOVERNED
  - evidence: Inventory row LIVE_UNGOVERNED, implementation_symbol=inline; handler in app/rmos/mvp_router.py
  - evidence: 'mvp' naming suggests minimum-viable/prototype lineage
- Recommended action: Classify MVP status; contain or mark prototype after confirming consumers.
- Future increment: later CF2 increment (needs consumer confirmation)

### `CF2-06-VISION-PHOTO-GCODE` — Vision photo-to-gcode: POST /api/vision/photo-to-gcode (inline G-code)
- Paths: `services/api/app/vision/router.py`
- Disposition: **LIVE_INCOMPLETE** (confidence medium); January provenance: False; introduced unverified (`unverified`)
- Backend routes: ['/api/vision/photo-to-gcode']; client consumers: ['vision client flows (Beta per README)']; manufacturing-output: LIVE_UNGOVERNED
  - evidence: Inventory row LIVE_UNGOVERNED, implementation_symbol=inline; Vision Engine is marked Beta in README
  - evidence: 7 incompleteness markers in app/vision per recon
- Recommended action: Contain or defer pending Vision Beta maturity decision.
- Future increment: later CF2 increment (Beta subsystem)

### `CF2-07-RADIUS-DISH` — Acoustic radius-dish G-code: POST /api/acoustics/radius-dish/generate-gcode
- Paths: `services/api/app/routers/radius_dish_router.py`
- Disposition: **LIVE_INCOMPLETE** (confidence high); January provenance: False; introduced 2026-03-21 (`3215ef9b`)
- Backend routes: ['/api/acoustics/radius-dish/generate-gcode']; client consumers: ['acoustics client flows']; manufacturing-output: LIVE_UNGOVERNED
  - evidence: Inventory row LIVE_UNGOVERNED; single dedicated handler generate_radius_dish_gcode
- Recommended action: Contain behind RMOS authority (single-route increment).
- Future increment: small standalone CF2 increment

### `CF2-08-INLAY-EXPORT` — Art Studio inlay G-code export: POST /api/art-studio/inlay/export-gcode
- Paths: `services/api/app/art_studio/_inlay_gcode_addon.py`
- Disposition: **LIVE_INCOMPLETE** (confidence high); January provenance: False; introduced 2026-03-10 (`bec7b24a`)
- Backend routes: ['/api/art-studio/inlay/export-gcode']; client consumers: ['Art Studio inlay flows']; manufacturing-output: LIVE_UNGOVERNED
  - evidence: Inventory row LIVE_UNGOVERNED; dedicated addon handler generate_inlay_gcode
- Recommended action: Contain behind RMOS authority (single-route increment).
- Future increment: small standalone CF2 increment

### `CF2-09-FRET-SLOTS-PREVIEW` — Fret slot CAM preview: POST /api/cam/fret_slots/preview (generate_fret_slot_toolpaths)
- Paths: `services/api/app/calculators/fret_slots_cam.py`
- Disposition: **DORMANT_UNRESOLVED** (confidence medium); January provenance: False; introduced 2025-12-09 (`25378c11`)
- Backend routes: ['/api/cam/fret_slots/preview']; client consumers: ['fret calculator client flows']; manufacturing-output: LIVE_UNGOVERNED
  - evidence: Row is a 'preview' endpoint (name) emitting toolpaths; unclear whether preview should be governed like a program emitter
- Recommended action: Determine whether 'preview' is a program emitter requiring containment or a non-emitting preview; classify accordingly.
- Future increment: classification precedes any containment

### `CF2-10-HEADSTOCK-TRANSITION` — Headstock transition G-code: POST /api/headstock/transition/gcode
- Paths: `services/api/app/routers/neck/headstock_transition_export.py`
- Disposition: **LIVE_INCOMPLETE** (confidence high); January provenance: False; introduced 2026-03-18 (`8c553069`)
- Backend routes: ['/api/headstock/transition/gcode']; client consumers: ['neck/headstock client flows']; manufacturing-output: LIVE_UNGOVERNED
  - evidence: Inventory row LIVE_UNGOVERNED; dedicated handler build_transition_gcode
- Recommended action: Contain behind RMOS authority (single-route increment).
- Future increment: small standalone CF2 increment

### `CONS-01-CAM-ASSIST-ROUTER` — CAM Assist / cognition (30 routes)
- Paths: `services/api/app/routers/cam/cam_assist_router.py`, `services/api/app/cam/cam_cognition_task.py`
- Disposition: **BUILT_DISCONNECTED** (confidence high); January provenance: False; introduced 2026-05-20 (`d5033799`)
- Backend routes: ['defined APIRouter, NOT mounted']; client consumers: none found; manufacturing-output: None
  - evidence: In manifest_discipline_baseline; no RouterSpec in cam_manifest.py; `rg cam_assist_router` -> router file + metrics/docs only, no include_router
  - evidence: docs/handoffs/CAM_BUILD_WORKFLOW_DISCOVERY_DEV_HANDOFF.md marks it dead
  - evidence: no tests (`rg cam_assist services/api/tests` -> none)
- Recommended action: Decide mount-or-retire; strong retirement candidate pending owner ruling.
- Future increment: OPTION C member (retirement) or explicit mount

### `CONS-02-RMOS-OPERATIONS-ROUTER` — RMOS Operations lane (/api/rmos/operations)
- Paths: `services/api/app/rmos/operations/router.py`
- Disposition: **BUILT_DISCONNECTED** (confidence high); January provenance: False; introduced 2025-12-31 (`1653c699`)
- Backend routes: ['declares prefix /api/rmos/operations, NOT mounted']; client consumers: none found; manufacturing-output: None
  - evidence: exported as operations_router in operations/__init__.py only; `rg operations_router` -> __init__ only; no manifest; no tests
  - evidence: module docstring references OPERATION_EXECUTION_GOVERNANCE_v1.md only
- Recommended action: Mount-or-retire ruling; confirm intended consumer.
- Future increment: OPTION B (resume) or OPTION C (retire)

### `CONS-03-CAMCORE-SAWLAB-DUP` — cam_core Saw Lab router (duplicate mount surface)
- Paths: `services/api/app/cam_core/api/saw_lab_router.py`
- Disposition: **DUPLICATE_SUPERSEDED** (confidence high); January provenance: False; introduced 2025-12-14 (`7c1e0d25`)
- Backend routes: ['exported from cam_core/api/__init__.py, never manifest-mounted']; client consumers: none found; manufacturing-output: None
  - evidence: Canonical live Saw Lab is app.saw_lab.__init_router__ (RouterSpec in cam_manifest.py); this cam_core copy is never mounted
- Recommended action: Retire after import/build proof; canonical survivor = app.saw_lab.
- Future increment: OPTION C member

### `CONS-04-RMOS-FEASIBILITY-HTTP-DUP` — RMOS feasibility HTTP router (duplicate of api_routes /feasibility)
- Paths: `services/api/app/rmos/api/rmos_feasibility_router.py`
- Disposition: **DUPLICATE_SUPERSEDED** (confidence high); January provenance: False; introduced 2025-12-04 (`1bc1023c`)
- Backend routes: ["@router.post('/feasibility') defined but feasibility_router never include_router'd"]; client consumers: none found; manufacturing-output: None
  - evidence: Public HTTP /feasibility served by app.rmos.api_routes via rmos_router; this router's HTTP surface never mounted; the module's LIBRARY function compute_feasibility_internal is the live authority (do NOT retire the library, only the dead HTTP surface)
- Recommended action: Retire the unused HTTP surface only; keep the library. Requires care (module also hosts the live evaluator).
- Future increment: OPTION C member (surgical, library-preserving)

### `CONS-05-CORE-FEATURES-REGISTRY` — Legacy parallel feature loader register_all_features / FEATURES
- Paths: `services/api/app/core/features.py`
- Disposition: **DUPLICATE_SUPERSEDED** (confidence medium); January provenance: False; introduced 2026-02-09 (`92e1b6d9`)
- Backend routes: none found; client consumers: none found; manufacturing-output: None
  - evidence: `rg register_all_features app` -> defined only in features.py, not called from main.py; router_registry is the live loader
- Recommended action: Confirm no dynamic caller, then retire; canonical survivor = router_registry.
- Future increment: OPTION C member

### `CONS-06-COMPARE-AUTOMATION` — Compare automation sub-router
- Paths: `services/api/app/compare/routers/aggregator.py`
- Disposition: **DORMANT_UNRESOLVED** (confidence high); January provenance: False; introduced 2025-12-20 (`86d0a12b`)
- Backend routes: ['automation_router = None; include block gated off']; client consumers: none found; manufacturing-output: None
  - evidence: aggregator.py sets automation_router = None so the automation sub-router is never mounted
- Recommended action: Determine intended automation feature; wire or remove the gated block.
- Future increment: needs owner intent

### `CONS-07-RMOS-ACOUSTICS-AGGREGATOR` — RMOS acoustics aggregator shell
- Paths: `services/api/app/rmos/acoustics/router.py`
- Disposition: **DUPLICATE_SUPERSEDED** (confidence medium); January provenance: False; introduced 2025-12-26 (`c7be7456`)
- Backend routes: ['composes router_import/router_zip_export but not referenced by manifests']; client consumers: none found; manufacturing-output: None
  - evidence: Wave 22 uses runs_v2/acoustics_router.py + direct imports from router_import; this aggregator is not mounted
- Recommended action: Retire unmounted aggregator after confirming submodules are reached via runs_v2.
- Future increment: OPTION C member

### `CONS-08-INSTRUMENT-GEOMETRY-MONOLITH` — Instrument-geometry monolith router (pre-split)
- Paths: `services/api/app/routers/instrument_geometry_router.py`
- Disposition: **DUPLICATE_SUPERSEDED** (confidence high); January provenance: False; introduced 2025-12-07 (`8b708410`)
- Backend routes: ['commented out in business_manifest.py']; client consumers: none found; manufacturing-output: None
  - evidence: Canonical split package app.routers.instrument_geometry is mounted; monolith commented out in business_manifest.py; tests skip monolith-only endpoints
- Recommended action: Retire the monolith after parity confirmation with the split package.
- Future increment: OPTION C member

### `CONS-09-ART-DESIGN-FIRST-WORKFLOW` — Art Studio design-first workflow (client SDK/store/panels present; backend HTTP contract absent)
- Paths: `packages/client/src/sdk/endpoints/artDesignFirstWorkflow*.ts`, `packages/client/src/stores (artDesignFirstWorkflowStore)`, `services/api/app/workflow`
- Disposition: **BUILT_DISCONNECTED** (confidence high); January provenance: False; introduced unverified (`unverified`)
- Backend routes: ["none (tests skipped with reason 'Routes ... not implemented')"]; client consumers: ['artDesignFirstWorkflow SDK; unwired DesignFirstWorkflowPanel(V2)']; manufacturing-output: None
  - evidence: `rg design-first-workflow services/api/app` -> tests only, skipped
  - evidence: client SDK + store + panels exist but panels have zero imports outside themselves
- Recommended action: Either implement the backend contract to connect the existing client assets, or retire the client SDK/store/panels.
- Future increment: OPTION B (resume dormant feature) primary candidate

### `CONS-10-APERTURE-WORKSPACE-SHELL` — Aperture beta consolidation shell mounting canonical spiral designer
- Paths: `packages/client/src (ApertureWorkspace.vue, SpiralSoundholeDesigner.vue)`
- Disposition: **LIVE_INCOMPLETE** (confidence high); January provenance: False; introduced unverified (`unverified`)
- Backend routes: ['/api/instrument/soundhole* (governed elsewhere)']; client consumers: ['ApertureWorkspace mounts SpiralSoundholeDesigner']; manufacturing-output: None
  - evidence: Per FEATURE_PARITY_MIGRATION_POLICY.md: ApertureWorkspace.vue = beta consolidation shell (State 3); SpiralSoundholeDesigner.vue = canonical
  - evidence: parity not yet verified -> migration incomplete
- Recommended action: Complete parity verification then converge, or keep dual until parity is proven; do not remove canonical.
- Future increment: OPTION B alternative (parity completion)

### `CONS-11-FEEDBACK-TRAININGDATA` — Vectorizer user-correction feedback + training-data retraining
- Paths: `services/blueprint-import/vectorizer_phase3.py (FeedbackSystem, TrainingDataCollector)`
- Disposition: **DEAD_CONFIRMED** (confidence high); January provenance: False; introduced unverified (`unverified`)
- Backend routes: ['no API']; client consumers: none found; manufacturing-output: None
  - evidence: Module docstring + check_feedback_correction_calls.py + test_governance_compliance.py prove submit_correction is DEAD (never wired); no API, no consumer
  - evidence: CLAUDE.md lists FeedbackSystem/TrainingDataCollector as 'exist but NEVER CALLED'
- Recommended action: Retain as governed-dead (a gate already enforces it) OR retire with owner approval; do NOT wire without an owner decision (CLAUDE.md).
- Future increment: OPTION C alternative (governed-dead retirement) — needs owner ruling

### `CONS-12-CALIBRATION-INTEGRATION` — Vectorizer calibration integration
- Paths: `services/blueprint-import/calibration_integration.py`
- Disposition: **DORMANT_UNRESOLVED** (confidence medium); January provenance: False; introduced unverified (`unverified`)
- Backend routes: ['no production call chain to integrate_with_vectorizer']; client consumers: none found; manufacturing-output: None
  - evidence: Lazy import only; no production call to integrate_with_vectorizer outside blueprint-import; CLAUDE.md: 'exists but NEVER CALLED, wire to pipeline'
- Recommended action: Determine intended wiring or defer; CLAUDE.md flags it for wiring.
- Future increment: needs owner intent

### `CONS-13-PHASE4-DIMENSION-LINKER` — Blueprint phase4 dimension linker
- Paths: `services/blueprint-import/phase4/dimension_linker.py`
- Disposition: **PROTOTYPE_EXPLICIT** (confidence medium); January provenance: False; introduced unverified (`unverified`)
- Backend routes: ['not wired as a primary API path']; client consumers: none found; manufacturing-output: None
  - evidence: Complete + unit-tested but standalone; CLAUDE.md: 'complete but standalone, integrate after Loop 1/2'
- Recommended action: Keep as tested prototype; integration is a separate future decision.
- Future increment: deferred (documented in CLAUDE.md)

### `CONS-14-VECTORIZER-THREELOOP-AGE` — Vectorizer three-loop feedback + AGE architecture
- Paths: `docs/audit-sources (external vectorizer-sandbox); docs/forensics/THREE_LOOP_*`
- Disposition: **PROTOTYPE_EXPLICIT** (confidence high); January provenance: False; introduced unverified (`unverified`)
- Backend routes: none found; client consumers: none found; manufacturing-output: None
  - evidence: No src/incubation/agentic_supervisor.py present; CLAUDE.md corrections state it is experimental/sandboxed, not runtime; the shipped runtime guardrail (validate_scale_before_export) is separate and LIVE
- Recommended action: No action; explicitly out of runtime scope per CLAUDE.md. Do not treat validate_scale_before_export as part of it.
- Future increment: none (sandbox-owned)

### `CONS-15-CAM-ROSETTE-PROTOTYPES` — Rosette CAM parametric prototypes (17 modules)
- Paths: `services/api/app/cam/rosette/prototypes`
- Disposition: **PROTOTYPE_EXPLICIT** (confidence high); January provenance: False; introduced 2026-03-12 (`f65931d6`)
- Backend routes: none found; client consumers: none found; manufacturing-output: None
  - evidence: Under a prototypes/ directory, separate from production rosette CAM/manufacturing routes; no manifest mount
- Recommended action: Keep as isolated prototypes; do not retire on age alone.
- Future increment: none (isolated)

### `CONS-16-CLIENT-ORPHAN-DASHBOARDS` — Dashboard/index shells not registered in the client router
- Paths: `packages/client/src/views/LabsIndex.vue`, `packages/client/src/views/CAMDashboard.vue`, `packages/client/src/views/SawLabDashboard.vue`, `packages/client/src/views/ArtStudioDashboard.vue`
- Disposition: **BUILT_DISCONNECTED** (confidence high); January provenance: False; introduced 2025-12-07 (`cb781ce0`)
- Backend routes: none found; client consumers: ['not routed']; manufacturing-output: None
  - evidence: `rg LabsIndex|CAMDashboard packages/client/src/router` -> no matches; ~109 of 183 view files are not top-level router entries (many are legitimately nested panels, so this candidate is scoped to the named orphan dashboards)
- Recommended action: Route or retire the named orphan dashboards after confirming they are not nested-only.
- Future increment: OPTION C alternative (client) — needs per-file confirmation

### `CONS-17-API-V1-DUAL-SURFACE` — Parallel /api/v1/* API surface (fretboard, dxf, frets)
- Paths: `services/api/app/api_v1`
- Disposition: **LIVE_INCOMPLETE** (confidence high); January provenance: False; introduced 2026-02-12 (`88aa2052`)
- Backend routes: ['/api/v1/*']; client consumers: ['client wizards use /api/v1/fretboard, /api/v1/dxf, etc.']; manufacturing-output: None
  - evidence: main.py: app.include_router(api_v1_router) -> LIVE, parallel to registry routes; a dual API story (v1 vs registry) with live client dependence
- Recommended action: Adjudicate the dual-API story; document canonical vs v1 boundaries (not a removal candidate — client depends on it).
- Future increment: documentation/convergence increment

### `CONS-18-AI-CONTEXT-ADAPTER` — AI context adapter routes (advisory)
- Paths: `services/api/app/ai_context_adapter`
- Disposition: **LIVE_INCOMPLETE** (confidence medium); January provenance: True; introduced 2026-01-14 (`d5ac968c`)
- Backend routes: ['ai_context_adapter/routes.py']; client consumers: ['AI advisory UI']; manufacturing-output: None
  - evidence: Introduced 2026-01-14 (January provenance); mounted; advisory-layer feature with incompleteness markers per recon
  - evidence: adjacent ai_context (2026-01) also January-era
- Recommended action: Assess completeness of AI advisory adapter; likely non-manufacturing, lower priority.
- Future increment: later, non-manufacturing

## Overflow backlog (recorded, not adjudicated)

| Path | Discovery signal | Reason deferred |
|---|---|---|
| services/api/app/export/dxf_translate_router.py vs translate_router (/ | cam_manifest.py comment marks dxf_translate DEPRECATED | duplicate/deprecated; lower risk; adjudicate in a translate- |
| services/api/app/routers/legacy_dxf_exports_router.py | mounted via business_manifest; 'legacy' naming; introduced 2 | live legacy surface; needs consumer census before dispositio |
| services/api/app/agentic/router.py + client CoachBubble | system_manifest mounted; App.vue imports agentic UI | live advisory; completeness assessment deferred |
| services/api/app/misc_stub_routes.py | 'stub' filename; mounted; proxies AI advisory | mounted proxy; low risk; name suggests interim |
| packages/client/src (~109 non-router-entry views) | basename diff vs router/index.ts | most are legitimate nested panels; requires per-file nesting |
| services/api/scripts/manifest_discipline_baseline.txt (103 unmanifeste | check_manifest_discipline.py baseline | meta-debt tracker; most entries are composed into manifested |
| docs/rosette-prototypes/jsx/*, docs/archive/rosette_designer_history/* | documentation/prototype snapshots | DOC_ONLY; non-runtime; retain as history |
| services/api/app/sandboxes (Jan 2026 adds) | git adds in Jan 2026 but directory absent on current tree | already removed from main; nothing to adjudicate on this bas |

