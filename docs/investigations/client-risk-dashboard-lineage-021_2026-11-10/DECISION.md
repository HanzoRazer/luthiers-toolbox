# Decision

Outcome B. The February 22 directory is the target baseline. It is not yet canonical.

```text
TARGET_BASELINE:
packages/client/src/views/art/risk-dashboard/

CANONICAL_STATUS:
withheld until RISK-L01, RISK-L02, and RISK-L03 are ported
and the combined characterization tests pass

DISPOSITION:
February 19 cluster remains in place.
Removal is withheld until that later PR.
```

The five `/api/compare/risk_*` operations are equivalent: method, URL, params object, absence of body and headers, response mapping, client sort and filter predicate, empty payload, and the shared catch path for 404, 422, and network failure. `goToLab` in `useRiskNavigation.ts` uses the same route table as the February 19 function. CSV and JSON bytes and filenames match. Import issues no request. One explicit action issues one request.

Argument lists became refs and computeds. `RiskDashboardCrossLab.vue` already calls that shape. That interface split is an intentional decomposition, not a different HTTP contract.

## Later-only behavior that stays

`downloadBucketJson` in the February 22 cluster calls `setError('Failed to download bucket JSON report.')` after `console.error`. The February 19 export only writes to the console. The pre-split view at `f563d7f5` assigned `bucketEntriesError` to that same string. `RiskDashboardCrossLab.vue` wires `setError` to `bucketEntriesError`. This behavior is complete and is kept.

`formatMetaTime` and `formatRelativeMetaTime` are exported from `riskFormatters.ts` and have no importer in `packages/client/src`. They do not change the risk requests. They stay until an owner decides they are unused display helpers.

## Missing behavior

```text
RISK-L01 — restore trimmed URL query values
RISK-L02 — clear the selected bucket when lane, preset, or job changes
RISK-L03 — clear the selected bucket and refresh once when since or until changes
```

`RISK-L01`. `composables/useRiskFilters.ts` and the pre-split view trim each query value and omit a blank result. `risk-dashboard/useRiskFilters.ts` writes the raw string, including whitespace. `applyQueryToFilters` reads that query back, so a later refresh can send different `since`, `until`, `lane`, `preset`, or `job_hint` values.

`RISK-L02`. The February 22 watch on lane, preset, and job only calls `syncFiltersToQuery`. `RiskDashboardCrossLabV2.vue` and the pre-split view also clear the selected bucket. The February 22 dashboard binds those fields with `v-model`, so a lane edit leaves the previous bucket open.

`RISK-L03`. The February 22 watch on since and until updates `quickRangeMode` and the URL. It does not clear the selection and does not call `refresh`. The February 19 view and the pre-split view do both. Quick range and lane preset on `RiskDashboardCrossLab.vue` call the composable directly and do not pass `onFiltersChanged`, so those buttons also skip the aggregate reload. The February 19 view can issue two aggregate requests for one quick-range click because the handler and the watch both refresh. The repair should issue one request for that action.

Both decompositions build a fresh query object and drop unrelated query keys. The pre-split view copied `route.query` first. That shared omission is not a difference between the two clusters and is not part of `RISK-L01`.

## Why not the other outcomes

Outcome A is not available. February 19 filter and watch behavior is still missing, so the February 22 directory is not a complete refactor.

Outcome C does not fit. The two clusters are two decompositions of the same dashboard, not two jobs. Their endpoints overlap because they were extracted from the same view.

Outcome D does not fit. The parent file at `f563d7f5` shows the trim, the clear, and the refresh. The February 22 commit message does not discuss dropping them, and the parent implementation is enough to name the missing behavior.

## Later implementation PR

After this adjudication is merged, a separate PR can:

1. Port `RISK-L01`, `RISK-L02`, and `RISK-L03` into `packages/client/src/views/art/risk-dashboard/`.
2. Update the February 22 characterization tests so the ported behavior is the one they pin.
3. Point any remaining February 19 consumer at the combined interface.
4. Preserve the February 19 source bytes and the hashes in this directory.
5. Remove the superseded February 19 production files only after those tests pass.
6. Confirm no source import still points at the removed paths.
7. Leave Axios on the current client dependency. Migrate it only in the later consolidated Axios change, after Risk Dashboard and Rosette Compare both have canonical baselines.

This branch stops before that PR.
