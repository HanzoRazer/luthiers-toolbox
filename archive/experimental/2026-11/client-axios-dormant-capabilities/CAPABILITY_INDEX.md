# Axios dormant capability index

Order: CLIENT-AXIOS-DORMANT-PRESERVATION-024.
Source commit: `cfaf07751110d99b3539647e877c2ffd80f4f29c`.
Production Axios importers: 17. Effective UNRESOLVED rows: 0.
Axios remains declared at `^1.21.0`. Removal is not authorized.
DORMANT_PRESERVE does not mean safe to delete. A cluster that has a copy may stay in production.
The four CANONICAL_BUT_UNROUTED importers stay in production. This copy does not retire them.

## ai-advisory

POST /ai/advisories/request, with the Pinia store and the dormant AiAdvisoryPanel. The renderer tree does not call this client.

Disposition: DORMANT_PRESERVE.
Next adjudication: Decide later whether to mount AiAdvisoryPanel. Do not remove the client or the dependency in this preservation order.

Archived files:

- `packages/client/src/components/ai/AiAdvisoryPanel.vue` (panel). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/ai/aiAdvisoryApi.ts` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/stores/aiAdvisoryStore.ts` (caller). binding_reachable=false, evaluated_reachable=false.

## art-presets-jobs

Preset selector, preset CRUD, job detail, and the job timeline. One commercial/art workflow. The timeline's reports_index GET stays here and is not a risk-dashboard /api/compare/risk_* call.

Disposition: DORMANT_PRESERVE.
Next adjudication: Decide later whether to adopt the selector, the manager, job detail, or the timeline. The art component barrel was not archived because it also re-exports live studio components.

Archived files:

- `packages/client/src/components/art/ArtPresetSelector.vue` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/ArtJobDetail.vue` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/ArtJobTimeline.vue` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/ArtPresetManager.vue` (importer). binding_reachable=false, evaluated_reachable=false.

Left in production, with a reason:

- `packages/client/src/components/art/index.ts` (caller). Only direct caller of ArtPresetSelector.vue, and it also re-exports ArtStudioRosette, ArtStudioInlay, ArtStudioBracing, ConfidenceBadge, and ConfidenceDetails. Those exports are not this workflow. The selector source is archived.
- `packages/client/src/composables/useConfirm.ts` (dependency). Shared confirm dialog used by live screens. ArtPresetManager.vue is archived. The helper is not an art-preset contract.

## cam-insights

GET /api/cam/job_log/insights list client, archived beside the competing per-job api() client. The two URLs are not interchangeable.

Disposition: DORMANT_PRESERVE.
Next adjudication: Keep the list GET and the per-job api() client distinct. Do not delete either because the other exists.

Archived files:

- `packages/client/src/components/cam/CamJobInsightsPanel.vue` (competing-client). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/cam/CamJobInsightsSummaryPanel.vue` (importer). binding_reachable=false, evaluated_reachable=false.

Left in production, with a reason:

- `packages/client/src/services/apiBase.ts` (dependency). Shared api() helper imported by CamJobInsightsPanel.vue. The panel is archived so the per-job URL stays next to the list client. The helper is live infrastructure.

## cam-utility-clients

Four dormant CAM utility clients. They share a preservation cluster and stay separate endpoint families. Preserving them together is not one deletion.

Disposition: DORMANT_PRESERVE.
Next adjudication: Review n15, n16, sawLab, and job_int separately before any removal. /cam/adaptive2 is not /api/cam/adaptive2. /api/cam/job-int/favorites is not /api/jobint/favorites. sawLab is not the live GET /api/joblog/saw_runs store.

Archived files:

- `packages/client/src/api/job_int.ts` (importer). binding_reachable=false, evaluated_reachable=true.
- `packages/client/src/api/n15.ts` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/api/n16.ts` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/api/sawLab.ts` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/cam/composables/jobIntHistoryTypes.ts` (type-caller). binding_reachable=false, evaluated_reachable=true.
- `packages/client/src/components/cam/composables/useJobIntHistoryActions.ts` (caller). binding_reachable=false, evaluated_reachable=true.
- `packages/client/src/components/cam/composables/useJobIntHistoryLoad.ts` (caller). binding_reachable=false, evaluated_reachable=true.
- `packages/client/src/components/toolbox/AdaptiveBench.vue` (caller). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/toolbox/BackplotGcode.vue` (caller). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/saw_lab_dashboard/TelemetryMetricsPanel.vue` (type-caller). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/saw_lab_dashboard/composables/sawRiskStyles.ts` (type-caller). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/saw_lab_dashboard/composables/useSawDashboard.ts` (caller). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/saw_lab_dashboard/composables/useSawDashboardFilters.ts` (type-caller). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/saw_lab_dashboard/composables/useSawDashboardModals.ts` (type-caller). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/saw_lab_dashboard/composables/useSawRiskActions.ts` (type-caller). binding_reachable=false, evaluated_reachable=false.

Left in production, with a reason:

- `packages/client/src/components/toolbox/ArtStudioCAM.vue` (caller). Unmounted shell that mounts BackplotGcode.vue and AdaptiveBench.vue beside other toolbox tools. Those two callers are archived. The shell is not an Axios importer.
- `packages/client/src/views/saw_lab_dashboard/composables/index.ts` (caller). Re-exports the archived saw-dashboard composables and does not import api/sawLab.ts. SawLabDashboard.vue is unmounted and is not an Axios importer.
- `packages/client/src/views/saw_lab_dashboard/RunDetailModal.vue` (caller). Imports TelemetryMetricsPanel.vue for display and does not import api/sawLab.ts. The panel's type import is archived with the saw client.
- `packages/client/src/components/cam/composables/index.ts` (caller). Re-exports the job-int history composables together with CamPipeline and CamIssues composables the pipeline runner evaluates. It adds no Axios call. Copying the barrel would mix live pipeline exports into this archive. The job-int callers are archived.
- `packages/client/src/components/cam/composables/useJobIntHistoryClone.ts` (caller). Imports jobIntHistoryTypes for the clone modal and does not call api/job_int.ts. The Axios callers are useJobIntHistoryLoad.ts and useJobIntHistoryActions.ts.
- `packages/client/src/components/cam/composables/useJobIntHistoryState.ts` (caller). Imports jobIntHistoryTypes for history state and does not call api/job_int.ts.
- `packages/client/src/components/cam/composables/useJobIntHistoryStats.ts` (caller). Imports jobIntHistoryTypes for history stats and does not call api/job_int.ts.
- `packages/client/src/sdk/rmos/runs.ts` (dependency). useSawRiskActions imports addOverride from the live RMOS SDK. The SDK is not the saw Axios client. The composable is archived.

## risk-dashboard-canonical

February 22 risk-dashboard composables. CANONICAL_BUT_UNROUTED. The three Axios clients stay in production. Bucket and BucketEntry live on the dashboard components this view uses.

Disposition: DORMANT_PRESERVE — CANONICAL_BUT_UNROUTED.
Next adjudication: Routing the risk dashboard is a later order. Do not mark the three composables retired. /api/compare/lab is not this contract, and neither is the art timeline reports_index GET.

Archived files:

- `packages/client/src/components/dashboard/BucketDetailsPanel.vue` (type). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/dashboard/BucketsTable.vue` (type). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/dashboard/FiltersBar.vue` (view-part). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/dashboard/index.ts` (type-barrel). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/art/RiskDashboardCrossLab.vue` (view). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/art/risk-dashboard/index.ts` (barrel). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/art/risk-dashboard/riskFormatters.ts` (caller-support). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/art/risk-dashboard/useRiskBucketDetails.ts` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/art/risk-dashboard/useRiskBuckets.ts` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/art/risk-dashboard/useRiskExports.ts` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/art/risk-dashboard/useRiskFilters.ts` (caller-support). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/art/risk-dashboard/useRiskNavigation.ts` (caller-support). binding_reachable=false, evaluated_reachable=false.

Left in production, with a reason:

- `packages/client/src/utils/downloadBlob.ts` (dependency). Shared download helper used by live labs. useRiskExports.ts is archived.
- `packages/client/src/components/ui/index.ts` (dependency). Shared UI barrel. RiskDashboardCrossLab.vue imports SavedViewsPanel from it. The risk Axios composables and the Bucket types are archived. The UI kit is not the risk contract.
- `packages/client/src/views/art/risk-dashboard/__tests__/riskDashboardDecomposed.spec.ts` (caller). Characterization spec. It imports the risk composables and mocks Axios. It is not a production capability and is not one of the 17 importers.
- `packages/client/src/views/art/risk-dashboard/__tests__/riskDashboardRequestOrder.spec.ts` (caller). Characterization spec. It imports the risk composables and mocks Axios. It is not a production capability and is not one of the 17 importers.
- `packages/client/src/views/art/__tests__/RiskDashboardCrossLab.spec.ts` (caller). Characterization spec. It mounts RiskDashboardCrossLab.vue and mocks Axios. It is not a production capability and is not one of the 17 importers.

## rosette-compare-canonical

Canonical baseline and diff client. CANONICAL_BUT_UNROUTED. The panel no longer imports Axios. This is not /api/compare/history and not /api/compare/lab.

Disposition: DORMANT_PRESERVE — CANONICAL_BUT_UNROUTED.
Next adjudication: Routing this client is a later order. The production composable stays. Do not mark it retired because a copy exists.

Archived files:

- `packages/client/src/components/art/RosetteComparePanel.vue` (caller). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette-compare/index.ts` (barrel). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette-compare/useRosetteCompareApi.ts` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette-compare/useRosetteCompareCanvas.ts` (type-caller). binding_reachable=false, evaluated_reachable=false.

Left in production, with a reason:

- `packages/client/src/views/ArtStudioUnified.vue` (caller). Unrouted shell that mounts the canonical panel and RosetteCompareHistory.vue. Archiving it here would mix baseline/diff with /api/compare/history.
- `packages/client/src/components/art/rosette-compare/__tests__/useRosetteCompareApi.spec.ts` (caller). Characterization spec. It imports Axios only to mock the canonical client. It is not a production capability and is not one of the 17 importers.
- `packages/client/src/components/art/__tests__/RosetteComparePanel.spec.ts` (caller). Characterization spec. It mounts RosetteComparePanel.vue and mocks Axios. It is not a production capability and is not one of the 17 importers.

## rosette-history

Two dormant history contracts in one preservation cluster: GET /api/compare/history, and the art-rosette job compare history. Neither is the canonical baseline/diff client.

Disposition: DORMANT_PRESERVE.
Next adjudication: Review /api/compare/history and the art-rosette snapshot history as separate contracts. Do not treat either as useRosetteCompareApi.ts, and do not treat /api/compare/lab as either of them.

Archived files:

- `packages/client/src/components/art/RosetteCompareHistory.vue` (view). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette_compare_history/GlobalSparklines.vue` (view-part). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette_compare_history/HistoryTable.vue` (view-part). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette_compare_history/PairStatsBadges.vue` (view-part). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette_compare_history/PresetSparklines.vue` (view-part). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette_compare_history/composables/index.ts` (barrel). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette_compare_history/composables/rosetteCompareTypes.ts` (type). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette_compare_history/composables/useRosetteCompareActions.ts` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette_compare_history/composables/useRosetteComparePresets.ts` (caller-support). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette_compare_history/composables/useRosetteCompareSparklines.ts` (caller-support). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette_compare_history/composables/useRosetteCompareState.ts` (caller-support). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/components/art/rosette_compare_history/composables/useRosetteCompareStats.ts` (caller-support). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/ArtStudioRosetteCompare.vue` (view). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/rosette_compare/CompareDiffSummary.vue` (view-part). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/rosette_compare/CompareHistorySidebar.vue` (view-part). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/rosette_compare/compare_history/RiskMetricsBar.vue` (view-part). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/rosette_compare/compare_history/SnapshotCard.vue` (view-part). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/rosette_compare/composables/index.ts` (barrel). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/rosette_compare/composables/rosetteCompareTypes.ts` (type). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/rosette_compare/composables/useRosetteCompareActions.ts` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/rosette_compare/composables/useRosetteCompareHelpers.ts` (caller-support). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/rosette_compare/composables/useRosetteCompareHistory.ts` (importer). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/rosette_compare/composables/useRosetteComparePaths.ts` (caller-support). binding_reachable=false, evaluated_reachable=false.
- `packages/client/src/views/rosette_compare/composables/useRosetteCompareState.ts` (caller-support). binding_reachable=false, evaluated_reachable=false.

Left in production, with a reason:

- `packages/client/src/views/ArtStudioUnified.vue` (caller). Unrouted shell that mounts RosetteCompareHistory.vue and the canonical RosetteComparePanel.vue. Archiving it here would mix /api/compare/history with the baseline/diff contract.
- `packages/client/src/utils/downloadBlob.ts` (dependency). Shared download helper used by live labs. The compare-history actions composable is archived.

## Distinct contracts

`/api/compare/lab` is owned by `packages/client/src/composables/useCompareState.ts` and `packages/client/src/components/compare/CompareBaselinePicker.vue`. It is not the Rosette baseline/diff client and not Rosette history.

`/api/compare/baselines` and `/api/compare/diff` belong to `useRosetteCompareApi.ts`.

`/api/compare/history` belongs to `components/art/rosette_compare_history/composables/useRosetteCompareActions.ts`.

The art-rosette job compare history uses `/api/art/rosette/jobs`, `/api/art/rosette/compare`, `/api/art/rosette/compare/snapshot`, `/api/art/rosette/compare/snapshots`, and `/api/art/rosette/compare/export_csv`.
