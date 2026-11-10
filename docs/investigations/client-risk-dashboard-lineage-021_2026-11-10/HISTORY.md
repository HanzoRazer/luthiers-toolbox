# History

Times below are America/Chicago.

## Pre-split dashboard

`f563d7f56d5022277e01cea1594934249143caa9` is the parent of the February 22 decomposition. `RiskDashboardCrossLab.vue` at that commit still contains the aggregate, detail, export, and navigation logic inline.

That file trims query values in `syncFiltersToQuery` (`val.trim()`). Its lane/preset/job watch syncs the URL and clears the selected bucket. Its since/until watch updates the quick-range mode, syncs the URL, clears the selected bucket, and calls `refresh()`. `downloadBucketJson` assigns `bucketEntriesError` to `Failed to download bucket JSON report.` and also calls `console.error`. `syncFiltersToQuery` copies `route.query` before replacing the five known keys, so unrelated query keys survive.

## February 19 copy

`d594fd96a1925343997df651d157c36a79e1dd80`, 2026-02-19, 11:17 AM, message `refactor(ui): decompose RiskDashboardCrossLab.vue (948→268 LOC, 72% reduction)`.

The commit adds five files and does not modify `RiskDashboardCrossLab.vue`:

- `RiskDashboardCrossLabV2.vue`
- `composables/index.ts`
- `composables/useRiskBuckets.ts`
- `composables/useRiskExport.ts`
- `composables/useRiskFilters.ts`

The new filter composable still trims. It does not watch. The V2 view watches: lane/preset/job syncs and clears details; since/until syncs, clears details, and refreshes. `downloadBucketJson` in the extracted export composable only calls `console.error`. The extracted `syncFiltersToQuery` builds a new query object and does not copy unrelated keys.

## February 22 in-place decomposition

`7d1a82aed2cf12fdc6e1a38ab48292ad52c2550f`, 2026-02-22, 6:01 AM, message `refactor(ui): decompose RiskDashboardCrossLab.vue (948→276 lines)`.

This commit rewrites `RiskDashboardCrossLab.vue` and adds `risk-dashboard/`: filters, formatters, buckets, details, exports, and navigation. The view's `setError` callback writes `bucketEntriesError`, preserving the pre-split report-download error. The filter composable's watches only sync the URL. They do not trim, do not clear the selected bucket, and do not refresh. The replacement query object still drops unrelated keys. The commit message does not discuss those drops. The parent file is the evidence for what the decomposition was taking apart.

## Later edits that touch both export paths

`9a8d0423a87b5ab8bdbdfa0222fa38a8863834cb`, 2026-02-25, 2:00 PM, `Phase 6: consolidate download/CSV utilities into shared downloadBlob`.

Both `useRiskExport.ts` and `useRiskExports.ts` lose their private `csvEscape`, `downloadBlob`, and timestamp helpers and import them from `packages/client/src/utils/downloadBlob.ts`. The escaping rule and the timestamp pattern stay the same. Both clusters now use the shared helper, which revokes the object URL on a timer. That is a shared later edit, not a difference between the clusters.

`1643142f` (2026-03-03, 12:19 PM) and `672dd100` (2026-10-13, 10:07 AM) reformat `RiskDashboardCrossLabV2.vue` and replace an inline bucket type with `RiskBucket`. They do not change the composable requests.

The comparison in this record is of the current bytes on `93c69e26`, not a claim that those bytes are identical to the introducing commits. `evidence.json` records the current SHA-256 values.

## PR #477

Draft PR #477 (`cursor/client-axios-reachability-020-b509`) was open at adjudication. Its inventory has 20 unique rows. These five files are `UNRESOLVED` there:

- `packages/client/src/views/art/composables/useRiskBuckets.ts`
- `packages/client/src/views/art/composables/useRiskExport.ts`
- `packages/client/src/views/art/risk-dashboard/useRiskBuckets.ts`
- `packages/client/src/views/art/risk-dashboard/useRiskExports.ts`
- `packages/client/src/views/art/risk-dashboard/useRiskBucketDetails.ts`

No open pull request in that set edits those source files. This branch is cut from `main`, not stacked on #477. Axios migration stays in that later consolidated change, after Risk Dashboard and Rosette Compare each have a canonical baseline.
