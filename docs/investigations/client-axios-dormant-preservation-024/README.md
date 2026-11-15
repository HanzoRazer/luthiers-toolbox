# CLIENT-AXIOS-DORMANT-PRESERVATION-024

Preservation and classification of the remaining dormant Axios capabilities. Not dependency removal. Not feature activation.

## Census

Recorded from fetched `origin/main` after PR #482.

| Fact | Value |
| --- | --- |
| Merge commit | `cfaf07751110d99b3539647e877c2ffd80f4f29c` |
| PR head | `d1b7daf89385d2873fc07b72716220acc47f0fba` |
| Production Axios importers | 17 |
| Effective UNRESOLVED rows | 0 |
| Axios declaration | `^1.21.0` |
| Canonical Rosette client | `packages/client/src/components/art/rosette-compare/useRosetteCompareApi.ts` (unrouted) |

The original 20-row inventory is unchanged. Later dispositions stay in `docs/investigations/client-axios-reachability-020_2026-11-10/POST_AUDIT_RETIREMENTS.json`. This order adds a preservation block there. It does not mark production files retired.

## Archive

`archive/experimental/2026-11/client-axios-dormant-capabilities/`

Sixty-four production files, copied byte-for-byte, plus the manifest, capability index, and endpoint matrix. Each copied file records its original path, blob hash, source commit, cluster, callers, endpoints, and reachability.

Ledger: `PRESERVATION_LEDGER.csv` (one row per production importer).

## Clusters

Nine clusters. These are separate adjudication units. Preserving them in one order does not make them one deletion. `cam-utility-clients` is a preservation umbrella only: `n15`, `n16`, `sawLab`, and `job_int` are still adjudicated one at a time.

| Cluster | Importers | Disposition |
| --- | --- | --- |
| `cam-utility-clients` | `api/n15.ts`, `api/n16.ts`, `api/sawLab.ts`, `api/job_int.ts` | `DORMANT_PRESERVE` |
| `ai-advisory` | `components/ai/aiAdvisoryApi.ts` | `DORMANT_PRESERVE` |
| `art-presets` | `ArtPresetSelector.vue`, `ArtPresetManager.vue` | `DORMANT_PRESERVE` |
| `art-jobs` | `ArtJobDetail.vue`, `ArtJobTimeline.vue` | `DORMANT_PRESERVE` |
| `cam-insights` | `CamJobInsightsSummaryPanel.vue` | `DORMANT_PRESERVE` |
| `rosette-compare-history` | `components/art/rosette_compare_history/composables/useRosetteCompareActions.ts` (`GET /api/compare/history`) | `DORMANT_PRESERVE` |
| `art-rosette-job-history` | `views/rosette_compare/composables/useRosetteCompareActions.ts`, `useRosetteCompareHistory.ts` (`/api/art/rosette/*`) | `DORMANT_PRESERVE` |
| `rosette-compare-canonical` | `useRosetteCompareApi.ts` | `DORMANT_PRESERVE — CANONICAL_BUT_UNROUTED` |
| `risk-dashboard-canonical` | `useRiskBuckets.ts`, `useRiskExports.ts`, `useRiskBucketDetails.ts` | `DORMANT_PRESERVE — CANONICAL_BUT_UNROUTED` |

`/api/compare/lab`, Rosette baseline/diff, `/api/compare/history`, and the `/api/art/rosette/*` job history stay distinct contracts, each in its own cluster. The lab client is `packages/client/src/composables/useCompareState.ts`.

## Callers left in production

A direct caller that is not in the archive has a reason in the manifest. The closures that needed an exclusion:

- **cam-utility-clients.** `ArtStudioCAM.vue` is an unmounted shell that also mounts other toolbox tools. The CAM composables barrel also re-exports the live pipeline. `useJobIntHistoryClone.ts`, `useJobIntHistoryState.ts`, and `useJobIntHistoryStats.ts` import history types and do not call `api/job_int.ts`. The saw composables barrel and `RunDetailModal.vue` do not import `api/sawLab.ts`. `sdk/rmos/runs.ts` is the live RMOS SDK used by `useSawRiskActions.ts`.
- **art-presets.** `components/art/index.ts` re-exports the selector together with live studio components. `useConfirm.ts` is a shared dialog.
- **art-jobs.** No exclusion needed. Job detail and the timeline have no caller or dependency outside the cluster.
- **cam-insights.** `services/apiBase.ts` is the live `api()` helper. `CamJobInsightsPanel.vue` itself is archived so the per-job URL stays visible beside the list GET.
- **rosette-compare-history and rosette-compare-canonical.** `ArtStudioUnified.vue` mounts both the history view and the canonical panel. Archiving that shell in either cluster would mix the contracts. `utils/downloadBlob.ts` is a shared helper. Characterization specs mock Axios and are not production capabilities.
- **art-rosette-job-history.** No exclusion needed. `ArtStudioRosetteCompare.vue` and `views/rosette_compare/**` have no caller or dependency outside the cluster.
- **risk-dashboard-canonical.** Characterization specs, plus `utils/downloadBlob.ts` and `components/ui/index.ts`, which are shared production helpers. The February 22 composables, the unrouted view, and the Bucket types are archived.

## What this order does not do

No file under `packages/client/src` changes. `package.json` and the lockfile stay. The router stays. No dormant component becomes routed. No backend route, CAM authority, readiness state, or manufacturing behavior changes.

Axios removal remains unauthorized. The owner still reviews the cluster boundaries before any later merge of a removal.
