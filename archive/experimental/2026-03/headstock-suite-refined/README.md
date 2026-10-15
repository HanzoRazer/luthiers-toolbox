# Headstock Suite — refined views (preserved)

**Status:** PRESERVED, pending feature reconciliation. Not compiled, not routed, not shipped.
**Moved here from:** `packages/client/src/views/cam/headstock/` on 2026-10-13. The files are **byte-identical** to `main` at `2a2f3924`, and still are at `b5e61805` (after #437).
**Evidence:** `docs/investigations/headstock-lineage-reconciliation_2026-10-13.md` (PR #437)
**Ledger:** SPRINTS.md MAINT-DEFER-010

## What these are

These four views are the **final iterations** of the headstock half of the `ps-vue` "Production Shop" suite.
That suite was generated in a claude.ai session on 2026-03-17. The neck and CAM halves of it were integrated into the client
on 2026-03-18 and are live: `design-utilities/lutherie/neck/`, `components/cam/neck/`, `views/cam/NeckView.vue`
and `views/cam/CamWorkspaceView.vue`. The headstock half was not integrated. These views were copied in without their store, types, data
or composables, so they never compiled or ran. They were moved here, not deleted, because they carry capability that the
routed `/art-studio/headstock` feature does not have (see the evidence document, section 4).

| File | Blob | What it is |
|---|---|---|
| `WorkspaceView.vue` | `3be10a9e` | Interactive Konva workspace: model presets, inlay drag/scale/rotate/flip, snap and boundary, undo, wood grain, CAM overlay, variant library, SVG export and DXF export via `/headstock-dxf` (veneer, binding, cost) |
| `ParametricView.vue` | `755e25e6` | Parametric outline generator: body, shoulder and tuner params, tip styles, tuner patterns, corpus overlay, novelty scoring, gates |
| `ImportView.vue` | `674d3fde` | DXF/photo import with raw-vs-normalized canvases and a vectorizer source-type selector |
| `ConfiguratorView.vue` | `4c3ac93b` | Public 4-step customer configurator that queues a variant for the shop |

`WorkspaceView.vue` differs from its 2026-03-17 original (`80a5ed54`) only by #430's behavior-preserving
handler extraction. `ImportView.vue` differs from its original (`3580af7e`) by an in-repo edit that added the source-type selector
before the April 2026 history rewrite.

## What they import, and where it is

The `@/` imports are left as written. Here is where each import resolves today:

| Import | Status |
|---|---|
| `@/composables/useKonvaCanvas`, `useWoodGrain` | live in `packages/client/src/composables/` |
| `@/composables/useDxfImport`, `useExportDxf` | **present but broken** in `packages/client/src/composables/`: they import the lost `@/types/headstock` and `headstockData` (4 of the 5 type errors that stay in `src/`) |
| `@/composables/useCamSpec`, `@/composables/drawCamOverlay` | live, byte-identical, at `design-utilities/lutherie/neck/` (`useCamSpec.ts` also imports the lost `@/types/headstock`: the 5th remaining error) |
| `@/components/CamSpecPanel.vue` | live, byte-identical, at `components/cam/neck/` |
| `@/stores/variants`, `@/components/VariantLibraryPanel.vue`, `@/components/WoodGrainPanel.vue` | archive only: `docs/archive/photo_vectorizer_patches/` |
| `@/stores/headstock`, `@/types/headstock` | **recovered source** in `ps-vue-src/` (2026-10-15; see below). Not placed in `src/` |
| `@/assets/data/headstockData`, `@/composables/useParametric` | **reconstruction input only.** The content is in `ps-vue-src/`, split across other files. An adapter would have to be written; none exists |
| `@/composables/useHeadstock` | **still lost**: in no git ref, no archive and not in `ps-vue-src/`. Partial logic exists in `../Interactive_Headstock_Generator/ps-suite.html` and `ps-parametric.html` |

## Recovered source: `ps-vue-src/` (2026-10-15)

The 2026-03-17 session's standalone app output was recovered from claude.ai and is kept, as delivered, in
`ps-vue-src/`. That folder's README has the hashes, the module-to-file map, and what was and wasn't checked.
`services/api/tests/test_headstock_ps_vue_src_preserved.py` fails if any of those files changes.

| Lost import | What `ps-vue-src/` holds | Kind |
|---|---|---|
| `@/types/headstock` | `types/headstock.ts` | direct recovery |
| `@/stores/headstock` | `stores/headstock.ts` | direct recovery |
| `@/assets/data/headstockData` | `components/headstock/constants.ts` (`HS_MODELS`, `PARAM_DEFS`, …) + `MM` in `composables/useHeadstockPath.ts` | reconstruction input: the original module boundary is unknown |
| `@/composables/useParametric` | `composables/useHeadstockPath.ts` + `composables/useScoring.ts` | reconstruction input: split across two files |
| `@/composables/useHeadstock` | nothing (`drawBackground`, `drawHeadstock`, `createInlayGroup`, `exportWorkspaceSVG`) | still lost |

**No production functionality is restored, and no recovered file is manufacturing-qualified.**

**Measured, not assumed:** this `types/headstock.ts` does **not** fix the type errors in `src/`. Even with
`ParametricParams` and `ImportedPath` aliases, vue-tsc goes from 87 to 94. The live composables use fields
it doesn't declare. Details are in `ps-vue-src/README.md`.

## Why moving them out of `src/` is safe

Preserving these views and moving them out of `src/` do not conflict. Preservation is about keeping the work;
`src/` is only for code that compiles and ships. These files can't compile in `src/` (5 of their imports are lost)
and nothing in the app reaches them, so moving them changes the type-check count and nothing else.
You can re-run every check below:

| Check | Command | Result (merged with `main` `b5e61805`) |
|---|---|---|
| Nothing imports or routes them | `git grep -nE "headstock/(Configurator\|Import\|Parametric\|Workspace)View" -- packages/ services/` | no matches |
| No code path names the old folder | `git grep -l "views/cam/headstock" -- packages services scripts .github` | only the ratchet's baseline (5 per-file keys, removed by the ceiling follow-up) and synthetic fixtures in `scripts/ci/test_client_type_check_ratchet.py` (11 passed) |
| Moved byte-identical | `git rev-parse HEAD:<new path>` vs `git rev-parse b5e61805:<old path>` | 4 of 4 equal |
| Type-check ratchet | `npm run type-check > log; python scripts/ci/check_client_type_check_ratchet.py --log log --baseline scripts/ci/client_type_check_baseline.json` | `vue-tsc errors: 87 \| baseline ceiling: 150`: falls by exactly the views' 63 |
| Build | `npm run build` | passes; the views were never in the module graph |

## Rules for this folder

- Keep these files byte-identical. Record any recovered module **beside** them with its source, and do not edit the views to fit it.
- Keep `ps-vue-src/` as delivered. An adapter or reconstruction goes in its own folder and its own order, never into `ps-vue-src/`.
- Do not move them back into `packages/client/src/` piecemeal. Reconstruction (rebuilding the 5 lost modules) or harvest (porting
  capabilities into `/art-studio/headstock`) each need their own order and their own branch.
