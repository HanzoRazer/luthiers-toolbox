# CLIENT-RISK-DASHBOARD-LINEAGE-021

Evidence-only comparison of the February 19 and February 22 risk-dashboard clusters. This record does not merge the clusters, edit their production modules, mount either dashboard, or change Axios.

Compared on `origin/main` `93c69e26da887fecec272245a04dc5ba7c39aa88` (2026-11-09, 1:09 AM America/Chicago).

## Clusters

February 19, introduced by `d594fd96` (2026-02-19, 11:17 AM America/Chicago):

- `packages/client/src/views/art/composables/useRiskBuckets.ts`
- `packages/client/src/views/art/composables/useRiskExport.ts`

February 22, introduced by `7d1a82ae` (2026-02-22, 6:01 AM America/Chicago):

- `packages/client/src/views/art/risk-dashboard/useRiskBuckets.ts`
- `packages/client/src/views/art/risk-dashboard/useRiskExports.ts`
- `packages/client/src/views/art/risk-dashboard/useRiskBucketDetails.ts`

`useRiskNavigation.ts` holds the February 22 `goToLab`. `useRiskFilters.ts` in each directory feeds the request strings. Both are in the matrix because they change observable dashboard behavior. They were not treated as equivalent just because the names match.

## Ruling

Outcome B. The February 22 directory is the target baseline and is not yet canonical. The five `/api/compare/risk_*` operations agree. Three February 19 behaviors are missing from the February 22 filter layer: `RISK-L01`, `RISK-L02`, and `RISK-L03`. See `DECISION.md`.

## Contents

| File | Role |
|---|---|
| `BEHAVIOR_MATRIX.csv` | Exported symbols, requests, and side effects, with a classification on every row |
| `CONSUMER_MAP.md` | Callers, routes, and expected return shapes |
| `HISTORY.md` | Introducing commits and later shared edits |
| `ENDPOINT_CONTRACTS.md` | Method, URL, params, body, response, and fixture results |
| `DECISION.md` | Outcome B and the missing-behavior list |
| `evidence.json` | Ruling metadata and SHA-256 of the recorded sources |

Characterization tests, which do not declare either cluster correct:

- `packages/client/src/views/art/composables/__tests__/riskDashboardLegacy.spec.ts`
- `packages/client/src/views/art/risk-dashboard/__tests__/riskDashboardDecomposed.spec.ts`
- Shared fixtures: `packages/client/src/views/art/risk-dashboard/__tests__/riskDashboardFixtures.ts`

The evidence gate is `scripts/ci/test_client_risk_dashboard_lineage.py`, pinned from `.github/workflows/core_ci.yml`.

## What this branch does not do

Production composables and both Vue dashboards are unchanged. No route was added. Axios stays on the version already in `main`. Removal of the February 19 files waits for a later PR after this adjudication is merged and `RISK-L01` through `RISK-L03` are ported.
