# CLIENT-AXIOS-REACHABILITY-020

Evidence record for the client Axios import audit. This increment does not retire Axios.

## Authority

Maintenance evidence only. This record grants no production authority, no CAM authority, and no manufacturing authority. Merge is not authorized. No API route, payload, authentication, timeout, cancellation, download, or error behavior was changed.

## Base

- Repository: `HanzoRazer/luthiers-toolbox`
- Branch: `cursor/client-axios-reachability-020-b509`
- Base commit: `93c69e26da887fecec272245a04dc5ba7c39aa88` (merge of PR #472, 2026-11-09 1:09 AM America/Chicago)
- Merge base equals `origin/main` at that commit
- Client lint warning ceiling on that commit: 6,979. Type-check ceiling: 87. Neither baseline is edited here.

## PR #470

**Update 2026-11-10:** PR #470 was merged by the owner as `c6542957`, after this audit; main now declares `"axios": "^1.21.0"`. Axios still ships zero bytes in the production bundle, so no finding below changes. The rest of this section is as observed at the audit base.

At the audit base, PR #470 was open and unmerged. Its head is `dependabot/npm_and_yarn/packages/client/axios-1.21.0`. It changes `packages/client/package.json`, `packages/client/package-lock.json`, and adds `.cbsp21/patches/axios-1.21.0-bump.json` on that branch. That manifest is not on `main`. This branch does not modify #470.

This audit did not retire Axios because no retirement reached green. That decision is independent of the 1.20.0 -> 1.21.0 bump in #470.

Open PRs #473, #474, #475, and #476 also touch `packages/client/package.json` and the lockfile. None of them edit the 20 Axios importers. This branch does not edit the package manifest or the lockfile, so it does not take those dependency bumps.

## Importers

The scanner found these 20 files, and no others, under `packages/client/src`:

- `packages/client/src/api/n16.ts`
- `packages/client/src/api/n15.ts`
- `packages/client/src/api/sawLab.ts`
- `packages/client/src/api/job_int.ts`
- `packages/client/src/components/ai/aiAdvisoryApi.ts`
- `packages/client/src/components/cam/CamJobInsightsSummaryPanel.vue`
- `packages/client/src/views/ArtJobDetail.vue`
- `packages/client/src/views/ArtJobTimeline.vue`
- `packages/client/src/views/ArtPresetManager.vue`
- `packages/client/src/components/art/ArtPresetSelector.vue`
- `packages/client/src/components/art/RosetteComparePanel.vue`
- `packages/client/src/components/art/rosette-compare/useRosetteCompareApi.ts`
- `packages/client/src/views/art/composables/useRiskExport.ts`
- `packages/client/src/views/art/composables/useRiskBuckets.ts`
- `packages/client/src/views/art/risk-dashboard/useRiskBuckets.ts`
- `packages/client/src/views/art/risk-dashboard/useRiskExports.ts`
- `packages/client/src/views/art/risk-dashboard/useRiskBucketDetails.ts`
- `packages/client/src/views/rosette_compare/composables/useRosetteCompareHistory.ts`
- `packages/client/src/views/rosette_compare/composables/useRosetteCompareActions.ts`
- `packages/client/src/components/art/rosette_compare_history/composables/useRosetteCompareActions.ts`

## Methodology

`scripts/investigations/client_axios_reachability.py` enumerates static Axios imports, resolves relative and `@/` specifiers, follows static imports, `import()`, and Vue script imports, and separates type-only imports from runtime imports. It reports two closures from `main.ts`, `App.vue`, and `router/index.ts`:

- `binding_reachable`: a value binding demanded by an entrypoint. This is the bundler approximation. Unused `export *` names are not followed.
- `evaluated_reachable`: language-level evaluation. Once a module is reached, its `export *` targets are included.

The tool also reports unresolved relative or `@/` specifiers and namespace imports. It does not assign a disposition and it does not delete anything. Writes go only to an explicit `--output` or `--csv` path.

Dispositions were assigned by reading callers, router records, the typed SDK and `api()` helpers, backend route tests, and `git log --follow`. Unrouted is not treated as disposable. A file that is the only client of a live backend route is not an orphan.

## Aggregate result

| Disposition | Count |
|---|---|
| `LIVE_REPLACE` | 0 |
| `DORMANT_PRESERVE` | 13 |
| `SUPERSEDED_REMOVE` | 0 |
| `ORPHAN_REMOVE` | 0 |
| `UNRESOLVED` | 7 |

No importer is `binding_reachable` from the application entries. `api/job_int.ts` is `evaluated_reachable` because `CamPipelineRunner.vue` imports other names from `components/cam/composables/index.ts`, and that barrel `export *`s the job-int composables. Rollup does not keep that unused re-export: the production bundle contains no Axios source. The job-int request functions are unused. The module still exports types and a favorite POST that no reached caller uses. The file stays.

The seven `UNRESOLVED` rows are the two risk-dashboard decompositions and the rosette-compare panel plus its extracted composable. See `CAPABILITY_DISPOSITION.md`.

## Dependency disposition

Axios remains a direct dependency. Observed at the audit base `93c69e26` (main declares `^1.21.0` since `c6542957`):

- `packages/client/package.json`: `"axios": "^1.20.0"`
- `npm ls axios --all`: `axios@1.20.0` from the client package only
- `npm explain axios`: required by the root project at `^1.20.0`
- No production source import was removed
- No client test imports Axios
- `FENCE_REGISTRY.json` still forbids raw `axios.get/post/put/delete` in favor of typed SDK helpers. That fence stays because Axios stays.

Retirement is blocked by the `UNRESOLVED` rows and by dormant modules that are the only client of live backend routes. No archive copy was made. The rollout stops before preservation copies, migration, and dependency removal when any row is unresolved.

## Build comparison

Both builds were `npm run build` in `packages/client` on this branch. No file under `packages/client` differs from `93c69e26`. The two outputs are byte-identical: 199 files, 4,117,422 bytes. A search of `dist/` found no `axios` string and no `isAxiosError`, `AxiosHeaders`, or `axios/lib` marker. Per-file SHA-256 values are in `dist-manifest.sha256` and `evidence.json`.

That reproduces the earlier finding that the shipped bundle does not contain Axios. It is not permission to delete the importers.

## Scanner noise that is not an Axios disposition

On this tree the scanner reports 42 unresolved local specifiers, mostly missing design-utility modules, and 2 namespace imports (`sdk/endpoints/cam/__tests__/cam.endpoints.test.ts`, `stores/useRosetteWheelStore.ts`). None of those specifiers are the 20 Axios files. They are reported and left alone.

## Explicit non-authority statement

This directory is an investigation record. It does not approve a design, a toolpath, a cut, a job, or a dependency upgrade. It did not act on PR #470, which the owner merged separately as `c6542957`. The next decision, which this increment does not authorize, is an owner choice of the surviving risk-dashboard and rosette-compare implementations. Until that choice exists, Axios and the 20 importers stay in the production tree.
