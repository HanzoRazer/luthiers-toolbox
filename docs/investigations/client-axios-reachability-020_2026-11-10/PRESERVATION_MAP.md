# Preservation map

Archive copies were not written. Seven importers are `UNRESOLVED`, and the rollout stops before the copy step. Each `DORMANT_PRESERVE` file remains the production-tree source of record. The preservation target for every row below is that original path. A later increment may copy a file only after an owner closes the unresolved rows and names the destination.

No production file imports an archive. There is no archive directory for this order.

## packages/client/src/api/n16.ts

- Why it matters: only Axios client of POST `/cam/adaptive2/offset_spiral.svg` and `/cam/adaptive2/trochoid_corners.svg`, with SVG text responses. The unmounted `useAdaptiveBenchActions.ts` sibling uses `/api/cam/adaptive2` and is not the same URL.
- Origin: `ca9b12ef`, 2025-12-07 5:38 PM America/Chicago, "Phase 4: Migrate remaining orphan files".
- Dependencies: `axios`. Caller `components/toolbox/AdaptiveBench.vue`, which `ArtStudioCAM.vue` imports. Neither view is routed.
- Completeness: the two POST helpers and their request types are complete. There is no bench-timing call.
- Preservation destination: remain at `packages/client/src/api/n16.ts`.
- Later integration: an owner has to decide whether `/cam/adaptive2` or `/api/cam/adaptive2` is the contract, then either point `AdaptiveBench.vue` at the existing `api()` helper or delete the unused copy. This record does not make that choice.

## packages/client/src/api/n15.ts

- Why it matters: only client of POST `/api/cam/gcode/plot.svg`, `/api/cam/gcode/estimate`, and `/api/cam/gcode/save_temp`.
- Origin: `ca9b12ef`, 2025-12-07 5:38 PM America/Chicago.
- Dependencies: `axios`. Caller `components/toolbox/BackplotGcode.vue` via unmounted `ArtStudioCAM.vue`.
- Completeness: three functions plus `BackplotRequest` and `SimulateResponse`. `saveGcodeTemp` returns `{ gcode_key }`.
- Preservation destination: remain at `packages/client/src/api/n15.ts`.
- Later integration: confirm the three routes are still mounted, then move the caller to `api()` with the same SVG text and JSON decoding. `CamBackplotViewer` and `/api/cam/gcode/simulate` do not replace this.

## packages/client/src/api/sawLab.ts

- Why it matters: typed client for the saw dashboard, job-log status and telemetry, and live-learn ingest. `useJobLogStore.ts` covers only GET `/api/joblog/saw_runs`.
- Origin: `ca9b12ef`, 2025-12-07 5:38 PM America/Chicago.
- Dependencies: `axios`. Value caller `views/saw_lab_dashboard/composables/useSawDashboard.ts`. Other saw-dashboard files import types only. `SawLabDashboard.vue` is not routed. `SawLabView.vue` is the routed screen and does not import this module.
- Completeness: dashboard, job-log CRUD-ish status updates, telemetry, and learn health are implemented in this file. The dashboard view uses `getDashboardRuns` only.
- Preservation destination: remain at `packages/client/src/api/sawLab.ts`.
- Later integration: decide whether the routed Saw Lab screen should absorb this client. Do not drop the telemetry and learn calls because the list GET already exists on `api()`.

## packages/client/src/api/job_int.ts

- Why it matters: exported log types, plus POST `/api/cam/job-int/favorites/{runId}`. List and detail GETs overlap separate live `api()` callers. The routed CNC favorite call uses `/api/jobint/favorites/{runId}`, a different path. The file is in the evaluation closure of the CAM barrel and is absent from the production bundle.
- Origin: `ca9b12ef`, 2025-12-07 5:38 PM America/Chicago.
- Dependencies: `axios`. Value callers `useJobIntHistoryLoad.ts` and `useJobIntHistoryActions.ts`. Type caller `jobIntHistoryTypes.ts`. Those feed `JobIntHistoryPanel.vue`, which has no importer. The barrel `components/cam/composables/index.ts` re-exports them beside the pipeline composables that `CamPipelineRunner.vue` actually uses.
- Completeness: list, detail, and favorite functions are complete. Only the unmounted panel calls the favorite function.
- Preservation destination: remain at `packages/client/src/api/job_int.ts`.
- Later integration: keep the types if the history panel is adopted. Reconcile `/api/cam/job-int/favorites` with `/api/jobint/favorites` before any rewrite. Do not delete the module because its Axios functions tree-shake.

## packages/client/src/components/ai/aiAdvisoryApi.ts

- Why it matters: only client of POST `/ai/advisories/request`. The backend route in `misc_stub_routes.py` delegates to the RMOS advisory service.
- Origin: `042999f9`, 2026-01-23 12:42 AM America/Chicago, "feat(ai): integrate AI advisory frontend bundles".
- Dependencies: `axios`. Caller `stores/aiAdvisoryStore.ts`, used by `components/ai/AiAdvisoryPanel.vue`. Nothing imports the panel. `main.ts` does not start that store.
- Completeness: one POST helper and the `AIContextPacket` type.
- Preservation destination: remain at `packages/client/src/components/ai/aiAdvisoryApi.ts`.
- Later integration: if the panel is mounted, move the POST to the existing helper and preserve the packet body and error text. Do not mount it in this order.

## packages/client/src/components/cam/CamJobInsightsSummaryPanel.vue

- Why it matters: only client of GET `/api/cam/job_log/insights` with query params. Backend smoke tests still call that list route.
- Origin: `cb781ce0`, 2025-12-07 1:00 PM America/Chicago, "Phase 1-2: Migrate Toolbox calculators + orphan components".
- Dependencies: `axios` and the Vue single-file component. No importer.
- Completeness: the panel loads the list and renders a summary. It does not call the per-job detail URL.
- Preservation destination: remain at `packages/client/src/components/cam/CamJobInsightsSummaryPanel.vue`.
- Later integration: a mounted insights screen can call `api()` for the list. `CamJobInsightsPanel.vue` is a different, also unmounted, detail client and is not a substitute for the list.

## packages/client/src/views/ArtJobDetail.vue

- Why it matters: only client of GET `/api/art/jobs/{jobId}`. `root_art_router.py` still implements the route, and `tests/test_art_job_detail.py` calls it.
- Origin: `cb781ce0`, 2025-12-07 1:00 PM America/Chicago.
- Dependencies: `axios`. No importer. The June 2026 conflation audit lists the view as unrouted.
- Completeness: one GET by id.
- Preservation destination: remain at `packages/client/src/views/ArtJobDetail.vue`.
- Later integration: mount or fold into the routed art studio only under a separate order. Until then the backend route keeps this client.

## packages/client/src/views/ArtJobTimeline.vue

- Why it matters: client of GET `/api/art/jobs` and GET `/api/cam/risk/reports_index`. The jobs list route is live.
- Origin: `cb781ce0`, 2025-12-07 1:00 PM America/Chicago.
- Dependencies: `axios`. No importer.
- Completeness: both GETs are in the view.
- Preservation destination: remain at `packages/client/src/views/ArtJobTimeline.vue`.
- Later integration: same as the job detail view. `reports_index` needs its own route check before anyone treats the timeline as disposable.

## packages/client/src/views/ArtPresetManager.vue

- Why it matters: GET, POST, and DELETE `/api/art/presets`. Backend tests create and delete presets. `ArtPresetCompareAB.vue` calls the aggregate route, not this one.
- Origin: `cb781ce0`, 2025-12-07 1:00 PM America/Chicago.
- Dependencies: `axios`. No importer.
- Completeness: list, create, and delete are present.
- Preservation destination: remain at `packages/client/src/views/ArtPresetManager.vue`.
- Later integration: the selector below is read-only and does not replace this screen.

## packages/client/src/components/art/ArtPresetSelector.vue

- Why it matters: GET `/api/art/presets` for a picker. It does not create or delete.
- Origin: `cb781ce0`, 2025-12-07 1:00 PM America/Chicago.
- Dependencies: `axios`. Re-exported from `components/art/index.ts`. Nothing imports that barrel or the component.
- Completeness: one list GET and a select UI.
- Preservation destination: remain at `packages/client/src/components/art/ArtPresetSelector.vue`.
- Later integration: can sit beside the manager. It is not a duplicate to delete.

## packages/client/src/views/rosette_compare/composables/useRosetteCompareHistory.ts

- Why it matters: GET `/api/art/rosette/compare/snapshots` and a browser open of `/api/art/rosette/compare/export_csv`. This is the art-rosette job compare history, not `/api/compare/history`.
- Origin: `a19854b5`, 2026-02-22 12:20 PM America/Chicago, extracted from `ArtStudioRosetteCompare.vue`.
- Dependencies: `axios`. Caller `views/ArtStudioRosetteCompare.vue`, which has no importer. The routed rosette designer is `views/art-studio/RosetteWheelView.vue`.
- Completeness: snapshot listing and CSV export URL are in this composable.
- Preservation destination: remain at `packages/client/src/views/rosette_compare/composables/useRosetteCompareHistory.ts`.
- Later integration: adopt it with `ArtStudioRosetteCompare.vue`, or explicitly replace the endpoints with the SDK snapshot helpers after a contract comparison. The SDK paths found in this audit are not the same strings.

## packages/client/src/views/rosette_compare/composables/useRosetteCompareActions.ts

- Why it matters: GET `/api/art/rosette/jobs`, POST `/api/art/rosette/compare`, POST `/api/art/rosette/compare/snapshot`.
- Origin: `a19854b5`, 2026-02-22 12:20 PM America/Chicago.
- Dependencies: `axios`. Same unmounted `ArtStudioRosetteCompare.vue` caller.
- Completeness: job load, compare, and snapshot save.
- Preservation destination: remain at `packages/client/src/views/rosette_compare/composables/useRosetteCompareActions.ts`.
- Later integration: keep it with the history composable. Do not confuse it with the component-level actions file, which calls a different endpoint.

## packages/client/src/components/art/rosette_compare_history/composables/useRosetteCompareActions.ts

- Why it matters: only client of GET `/api/compare/history`. `tests/test_compare_history_smoke.py` still requests that route. The function name matches the view composable; the endpoint does not.
- Origin: `75620413`, 2026-02-22 3:51 PM America/Chicago, "decompose RosetteCompareHistory into composables".
- Dependencies: `axios`. Caller `components/art/RosetteCompareHistory.vue`, imported only by unmounted `ArtStudioUnified.vue`.
- Completeness: one history GET.
- Preservation destination: remain at `packages/client/src/components/art/rosette_compare_history/composables/useRosetteCompareActions.ts`.
- Later integration: if compare history is mounted, move this GET to `api()` and keep the query params. Do not delete it because the art-rosette composable has the same function name.

## Unresolved files, not copied and not removed

These stay in place because no safe disposition was available. They are not `DORMANT_PRESERVE` rows:

- `packages/client/src/components/art/RosetteComparePanel.vue`
- `packages/client/src/components/art/rosette-compare/useRosetteCompareApi.ts`
- `packages/client/src/views/art/composables/useRiskBuckets.ts`
- `packages/client/src/views/art/composables/useRiskExport.ts`
- `packages/client/src/views/art/risk-dashboard/useRiskBuckets.ts`
- `packages/client/src/views/art/risk-dashboard/useRiskExports.ts`
- `packages/client/src/views/art/risk-dashboard/useRiskBucketDetails.ts`
