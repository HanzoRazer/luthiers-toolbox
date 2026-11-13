# CLIENT-RISK-DASHBOARD-RECONCILE-022

Closed reconciliation of the Risk Dashboard. February 22 is canonical. The dashboard stays unrouted. This record grants no CAM or manufacturing authority.

## Base

- Base SHA: `eb24a99c7014cd03f2093db05e0b27bd03ebb344`
- Outcome B authority: PR #478, merged at `e976aea5`
- Historical ruling: `docs/investigations/client-risk-dashboard-lineage-021_2026-11-10/DECISION.md`
- Machine record: `RECONCILIATION.json`

PR #478 named February 22 as the target baseline and withheld canonical status until `RISK-L01`, `RISK-L02`, and `RISK-L03` were ported. The 63-row matrix in that record still classifies the pre-reconciliation state.

## Canonical declaration

`packages/client/src/views/art/risk-dashboard/` is the canonical Risk Dashboard implementation. `RiskDashboardCrossLab.vue` is its view. Neither file is registered in the client router.

Axios stays a direct dependency at `^1.21.0`. This order does not migrate or remove it. The three February 22 Axios importers are canonical and unrouted. The two Rosette Compare importers remain unresolved.

## Behavior that was restored

`RISK-L01`. `syncFiltersToQuery()` in `packages/client/src/views/art/risk-dashboard/useRiskFilters.ts` trims `lane`, `preset`, `job_hint`, `since`, and `until`, omits a value that is empty after trimming, and leaves the filter refs unchanged. The query object still replaces the five known keys.

`RISK-L02`. One watcher in `RiskDashboardCrossLab.vue` clears the selected bucket when lane, preset, or job hint changes. That edit does not request `/api/compare/risk_aggregate`.

`RISK-L03`. The same watcher clears the selected bucket and calls `refresh()` once when `since` or `until` changes. Quick range, a lane preset that sets dates, clearing an active date window, and applying a saved view that changes the window each produce one aggregate request. Mount applies the URL and a default saved view before the watcher accepts edits, so initialization stays at one request. The Refresh button still clears the selection and requests once.

Witnesses:

- `packages/client/src/views/art/risk-dashboard/__tests__/riskDashboardDecomposed.spec.ts`
- `packages/client/src/views/art/__tests__/RiskDashboardCrossLab.spec.ts`

The five `/api/compare/risk_*` operations, export bytes, filenames, and `Failed to download bucket JSON report.` are unchanged.

## Files changed

- `packages/client/src/views/art/risk-dashboard/useRiskFilters.ts`
- `packages/client/src/views/art/RiskDashboardCrossLab.vue`
- `packages/client/src/views/art/risk-dashboard/__tests__/riskDashboardDecomposed.spec.ts`
- `packages/client/src/views/art/__tests__/RiskDashboardCrossLab.spec.ts`
- `scripts/ci/test_client_risk_dashboard_lineage.py`
- `scripts/ci/test_client_axios_reachability.py`
- `docs/investigations/client-risk-dashboard-lineage-021_2026-11-10/DECISION.md` (closure appended)
- `docs/investigations/client-axios-reachability-020_2026-11-10/POST_AUDIT_RETIREMENTS.json`
- `SPRINTS.md`

## Files removed

The February 19 cluster is preserved by the SHA-256 values in `RECONCILIATION.json`, by the hashes in the PR #478 evidence file, and by Git history. The bytes were not copied into another executable directory.

- `packages/client/src/views/art/RiskDashboardCrossLabV2.vue`
- `packages/client/src/views/art/composables/index.ts`
- `packages/client/src/views/art/composables/useRiskBuckets.ts`
- `packages/client/src/views/art/composables/useRiskExport.ts`
- `packages/client/src/views/art/composables/useRiskFilters.ts`
- `packages/client/src/views/art/composables/__tests__/riskDashboardLegacy.spec.ts`

No remaining source under `packages/client/src` imports that cluster.

## Authority

Display and investigation code only. No route was added. No API route changed. No manufacturing or CAM authority was added.
