# Capability disposition

Outcome: **evidence**. Axios stays. No importer was edited, moved, or deleted.

`LIVE_REPLACE` would require a reached behavior and a contract-equivalent move onto the existing `api()` helper or typed SDK. No importer is a used binding from `main.ts`, `App.vue`, or `router/index.ts`. The SDK does not already implement these calls. Migrating an unmounted Axios client onto `api()` would still be a behavior edit of code the running app does not call, and it is stopped while any row is `UNRESOLVED`.

`ORPHAN_REMOVE` and `SUPERSEDED_REMOVE` were not used. The June 21, 2026 conflation audit lists `ArtJobDetail` and `SawLabDashboard` among views with zero routes. That audit is evidence that those views are unrouted. It is not a deletion authority under this order. Several of those views are the only client of a backend route that still has tests.

## Unresolved clusters

### Risk dashboards

Two decompositions of `RiskDashboardCrossLab.vue` both still call the compare risk endpoints:

| Path | Introduced | Mount |
|---|---|---|
| `views/art/composables/useRiskBuckets.ts` and `useRiskExport.ts` | `d594fd96`, 2026-02-19 11:17 AM America/Chicago, "decompose RiskDashboardCrossLab.vue" | `views/art/RiskDashboardCrossLabV2.vue`, not in the router |
| `views/art/risk-dashboard/useRiskBuckets.ts`, `useRiskExports.ts`, `useRiskBucketDetails.ts` | `7d1a82ae`, 2026-02-22 6:01 AM America/Chicago, a second "decompose RiskDashboardCrossLab.vue" | `views/art/RiskDashboardCrossLab.vue`, not in the router |

Both sides GET `/api/compare/risk_aggregate`, `/api/compare/risk_bucket_detail`, `/api/compare/risk_bucket_export` (CSV and JSON blobs), `/api/compare/risk_bucket_report`, and `/api/compare/risk_snapshot`. V1 keeps bucket detail in its own composable. V2 folds detail into `useRiskBuckets.ts`. `docs/archive/2026/remediation/CODE_QUALITY_EXECUTION_PLAN.md` already records that the two `useRiskBuckets.ts` files serve V1 and V2. A May 2026 handoff said the original view was superseded by V2. The June 2026 audit treats the unrouted art views as retireable. Those notes disagree, and neither view is mounted. Directory shape is not a disposition. All five files are `UNRESOLVED`.

`composables/useSavedViews.ts` mentions the dashboard in comments and does not import these Axios modules. It is not a canonical replacement.

### Rosette compare baselines

`components/art/RosetteComparePanel.vue` (`3a73a2d8`, 2025-12-07 2:32 PM America/Chicago) still performs the Axios calls. `components/art/rosette-compare/useRosetteCompareApi.ts` (`b4d60cab`, 2026-02-24 7:20 PM America/Chicago, "extract rosette-compare composables for future adoption") repeats GET/POST `/api/compare/baselines` and POST `/api/compare/diff`. The panel was not switched over to the composable. `useRosetteCompareCanvas.ts` only type-imports `GeometryPayload`.

The panel is mounted by `views/ArtStudioUnified.vue`, which is mounted by `views/CamProductionView.vue`. The router mounts `CncProductionView.vue`, not `CamProductionView.vue`. The June 2026 audit calls `CamProductionView` corrupt and orphaned. Nothing else imports the extracted composable's functions.

`components/compare/CompareBaselinePicker.vue` and `composables/useCompareState.ts` call `/api/compare/lab/baselines` and `/api/compare/lab/diff` through `fetch`. That is a different path prefix, so it is not a drop-in canonical equivalent. Both Axios files are `UNRESOLVED`.

## Dormant modules kept in place

Preservation copies were not made. The stop happens before that step. Each dormant file remains at its original path. Details are in `PRESERVATION_MAP.md`.

### API modules

`api/n16.ts` posts `/cam/adaptive2/offset_spiral.svg` and `/cam/adaptive2/trochoid_corners.svg`. Its only caller is `components/toolbox/AdaptiveBench.vue`, which is only imported by unmounted `ArtStudioCAM.vue`. `components/toolbox/adaptive-bench/useAdaptiveBenchActions.ts` posts the same bodies to `/api/cam/adaptive2/...` through `api()`, and adds `/api/cam/adaptive2/bench`. That sibling is only used by `AdaptiveBenchLab.vue`, which the router also does not mount. The URL prefix differs, so the sibling is not treated as equivalent. `n16.ts` stays.

`api/n15.ts` is the only client of POST `/api/cam/gcode/plot.svg`, `/api/cam/gcode/estimate`, and `/api/cam/gcode/save_temp`. Caller: `BackplotGcode.vue`, again only through unmounted `ArtStudioCAM.vue`. Routed backplot views pass move arrays into `CamBackplotViewer`. `sdk/endpoints/cam/simulate.ts` calls `/api/cam/gcode/simulate`. Those are different contracts.

`api/sawLab.ts` is the typed client for `/api/dashboard/saw/runs`, `/api/dashboard/saw/health`, `/api/joblog/saw_runs` and its status and telemetry routes, and `/api/learn/ingest` plus `/api/learn/health`. The value caller is `useSawDashboard.ts` inside unmounted `SawLabDashboard.vue`. The routed Saw Lab screen is `SawLabView.vue`, which does not import this module. `stores/useJobLogStore.ts` GETs `/api/joblog/saw_runs` through `api()` and does not cover the dashboard, telemetry, status, or learn calls.

`api/job_int.ts` is the special case. `CamPipelineRunner.vue` is reached from `PipelineLabView.vue` and imports pipeline names from the CAM composables barrel. The barrel also `export *`s the job-int composables, so a full evaluation closure includes `job_int.ts`. The runner does not name those exports, and the production bundle contains no Axios. `fetchJobIntLog` and `getJobIntLogEntry` overlap live `api()` calls in `cnc_production/CompareRunsPanel.vue` and `views/composables/useJobTooltip.ts`. `updateJobIntFavorite` posts `/api/cam/job-int/favorites/{runId}`. The routed CNC screen posts `/api/jobint/favorites/{runId}` instead. The exported `JobIntLogEntry` types are imported only by the unmounted history panel. The file is not deleted, and its Axios functions are not rewritten.

### Single unmounted clients of live routes

`components/ai/aiAdvisoryApi.ts` posts `/ai/advisories/request`. The store and `AiAdvisoryPanel.vue` have no further importer. `services/api/app/routers/misc_stub_routes.py` still serves that route.

`components/cam/CamJobInsightsSummaryPanel.vue` is the only client of GET `/api/cam/job_log/insights`. Nothing imports the panel. `CamJobInsightsPanel.vue` calls `api()` for `/api/cam/job_log/insights/{jobId}` and also has no importer. The list and the detail URL are different operations. Backend smoke tests cover the list route.

`views/ArtJobDetail.vue` is the only client of GET `/api/art/jobs/{jobId}`. `views/ArtJobTimeline.vue` is the client of GET `/api/art/jobs` and GET `/api/cam/risk/reports_index`. `app/routers/art/root_art_router.py` still lists and gets jobs. `views/ArtPresetManager.vue` is the CRUD client of `/api/art/presets`. `components/art/ArtPresetSelector.vue` only GETs that collection and is re-exported from `components/art/index.ts`, which nothing imports. The selector does not replace the manager. `ArtPresetCompareAB.vue` calls `/api/art/presets_aggregate`, a different route. Backend tests still hit `/api/art/jobs` and `/api/art/presets`.

### Rosette history, separate from the unresolved baseline panel

`views/rosette_compare/composables/useRosetteCompareHistory.ts` and `useRosetteCompareActions.ts` were extracted from `ArtStudioRosetteCompare.vue` (`a19854b5`, 2026-02-22 12:20 PM America/Chicago). Nothing imports that view. They call `/api/art/rosette/jobs`, `/api/art/rosette/compare`, `/api/art/rosette/compare/snapshot`, and `/api/art/rosette/compare/snapshots`. The SDK art snapshot helpers document `/api/art/snapshots` and `/api/art/rosette/snapshots`, and `artRosetteWheel.ts` uses `/api/art/rosette-designer`. Those are not these calls.

`components/art/rosette_compare_history/composables/useRosetteCompareActions.ts` (`75620413`, 2026-02-22 3:51 PM America/Chicago) GETs `/api/compare/history` for `RosetteCompareHistory.vue`, which is only mounted by the unmounted `ArtStudioUnified.vue`. A backend smoke test still requests `/api/compare/history`. The shared function name with the view composable is a namespace collision in the file name only. The endpoints differ, so one file does not supersede the other. The history composable is `DORMANT_PRESERVE`. The baseline panel pair stays `UNRESOLVED`.

## What this increment did not do

- No production importer was rewritten to `api()` or the SDK.
- No file was copied to an archive and no production file was deleted.
- `packages/client/package.json` and `package-lock.json` were not edited.
- PR #470's branch was not edited and the PR was not closed.
- `FENCE_REGISTRY.json` was not edited.
- Historical dependency-security notes in `SPRINTS.md` were not rewritten.
