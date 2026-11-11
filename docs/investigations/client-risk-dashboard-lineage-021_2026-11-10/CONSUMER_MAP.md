# Consumer map

Search commands run from the repository root against `packages/client/src`:

```bash
rg -n "views/art/composables|views/art/risk-dashboard" packages/client/src
rg -n "useRiskBuckets|useRiskExport|useRiskExports|useRiskBucketDetails" packages/client/src
rg -n "risk-dashboard|RiskDashboard" packages/client/src
```

No production caller imports the characterization specs. The specs import the composables and do not mount either Vue dashboard.

## Intended consumers

| Caller | Reachable | Cluster imported | Return shape | Unfinished decomposition | Tests before this order |
|---|---|---|---|---|---|
| `packages/client/src/views/art/RiskDashboardCrossLab.vue` | Not mounted. `packages/client/src/router/index.ts` has no import and no `/lab/risk-dashboard` route. | February 22 barrel `./risk-dashboard` | Matches. The view passes filter refs into `useRiskBuckets`, `jobFilter` into details and navigation, and `setError` into exports. `setError` writes `bucketEntriesError`. | Yes. Filter edits use `v-model` and the February 22 watches. Quick range and lane preset call the composable directly, with no `onFiltersChanged` callback. Explicit Refresh, Clear, and Apply still clear details and refresh. | None |
| `packages/client/src/views/art/RiskDashboardCrossLabV2.vue` | Not mounted. No router entry. | February 19 barrel `./composables` | Matches. The view calls `filteredBuckets(lane, preset)`, `refresh(since, until)`, `loadBucketDetails(bucket, jobFilter)`, `goToLab(bucket, jobFilter)`, and the export functions with arguments. | The February 19 commit added this copy and did not edit `RiskDashboardCrossLab.vue`. Its watches clear details, and the date watch also refreshes. | None |
| `packages/client/src/views/art/composables/index.ts` | Re-exports the February 19 modules. | February 19 | Barrel only. | None by itself. | None |
| `packages/client/src/views/art/risk-dashboard/index.ts` | Re-exports the February 22 modules, formatters, filters, and navigation. | February 22 | Barrel only. | None by itself. | None |

## Not a caller of either cluster

`packages/client/src/views/CAMDashboard.vue` advertises a card whose path is `/lab/risk-dashboard`. That path is not registered. The registered risk route is `/lab/risk-timeline`, which does not import these composables.

`packages/client/src/composables/useSavedViews.ts` mentions `RiskDashboardCrossLab` in a comment and formats saved-view timestamps with its own `formatMetaTime`. It does not import either risk cluster.

## Reachability

No router entry imports either dashboard. No caller found for a route is evidence that the screens are not reachable. It is not permission to delete either cluster.

The February 22 view is the in-place decomposition of the original dashboard. The February 19 view is a parallel copy whose return shape matches the February 19 composables. Each consumer matches its own cluster. Neither consumer matches the other cluster's function signatures.
