# CLIENT-ROSETTE-COMPARE-RECONCILE-023

Rosette Compare was the remaining unresolved Axios-lineage cluster after PR #481. This order makes `packages/client/src/components/art/rosette-compare/useRosetteCompareApi.ts` the single baseline/diff client used by `packages/client/src/components/art/RosetteComparePanel.vue`.

The feature stays **unrouted**. `ArtStudioUnified.vue` still imports the panel, and neither that view nor `CamProductionView.vue` is registered in `packages/client/src/router`. Axios stays declared at `^1.21.0`. This removes one direct importer. It does not remove the dependency.

## Chosen baseline

`useRosetteCompareApi.ts` is the canonical client. The panel stays the presentation and integration layer: selected baseline, both canvases, the baseline-name / job-id / preset form, `localStorage` key `ltb:compare:lastJobId`, and the `update:job-id` emit.

The panel and the composable already used the same four backend calls. Adoption did not need a backend change. `/api/compare/lab` is a different contract (lab baseline store, no lane, no job/preset logging) and is not a replacement.

## Network surface

| Operation | Method | URL | Body / query |
| --- | --- | --- | --- |
| `loadBaselines` | GET | `/api/compare/baselines` | `lane=rosette` |
| `saveBaseline` | POST | `/api/compare/baselines` | `name`, `lane`, `geometry` (name not trimmed). Then reloads the list and returns `id`. |
| `loadBaselineGeometry` | GET | `/api/compare/baselines/{id}` | Id is `encodeURIComponent`'d. Stores `geometry`. |
| `runDiff` | POST | `/api/compare/diff` | `baseline_id`, `lane`, `current_geometry`. Blank `job_id` and `preset` omitted. Nonblank values trimmed. |

A later response for an older list, save, geometry, or diff request does not overwrite the newer state, error, or loading flag. Clearing the selected id invalidates a pending geometry response. `saveBaseline`'s nested reload does not clear `loading` while the save is still in flight.

A comparison belongs to one baseline and one current geometry. Requesting another baseline (or clearing the selection) drops a pending diff, removes the shown statistics, and removes the previous baseline's geometry at once, so a late diff cannot leave statistics for a baseline that is no longer selected. When the current geometry changes, the panel calls `clearDiff()`, which does the same and restores the plain baseline geometry in place of the diff coloring. A diff that lands while the same baseline's plain geometry is still loading keeps its colored geometry. A null geometry now clears its canvas instead of leaving the previous drawing.

Errors are owned per operation. Starting an operation clears only its own error, and a stale request is judged only against its own operation's generation, so a newer request of one kind can neither erase nor suppress another kind's failure. `error` shows the most recent failure that is still standing.

## Importers

| | Count | Notes |
| --- | --- | --- |
| Before | 18 | Panel and composable both imported Axios. |
| After | 17 | Panel import retired in the overlay. Composable reclassified as canonical but unrouted. |

The original 20-row `AXIOS_IMPORT_INVENTORY.csv` is unchanged. Status changes are only in `POST_AUDIT_RETIREMENTS.json`. Axios consolidation remains incomplete because dormant-preserve importers still exist.

## Non-goals

No Axios removal, no archive copy, no Risk Dashboard edit, no new route, no backend contract change, no `/api/compare/lab` migration, and no CAM, readiness, approval, or manufacturing authority.

## Commands

```bash
cd packages/client
npx vitest run src/components/art/rosette-compare/__tests__/useRosetteCompareApi.spec.ts src/components/art/__tests__/RosetteComparePanel.spec.ts
npm test
npm run build
NODE_OPTIONS=--max-old-space-size=6144 npm run type-check
npm run lint:report -- --output-file /tmp/eslint.json
python3 ../scripts/ci/check_client_type_check_ratchet.py --log /tmp/vue-tsc.log --baseline ../scripts/ci/client_type_check_baseline.json
python3 ../scripts/ci/check_client_lint_ratchet.py --report /tmp/eslint.json --baseline ../scripts/ci/client_lint_baseline.json

cd ..
python3 -m pytest scripts/ci/test_client_rosette_compare_lineage.py scripts/ci/test_client_axios_reachability.py -q
python3 scripts/ci/check_cbsp21_gate.py --changed-files $(git diff --name-only origin/main...HEAD)
python3 scripts/ci/check_cbsp21_patch_input.py --base origin/main --head HEAD
```

Machine-readable matrix, hashes, and results: `RECONCILIATION.json` in this directory.
