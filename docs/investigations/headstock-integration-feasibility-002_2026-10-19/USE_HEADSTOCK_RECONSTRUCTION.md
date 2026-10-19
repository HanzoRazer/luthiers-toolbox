# useHeadstock reconstruction

Classification of the module: **NOT_RECOVERED_GENERATION_UNKNOWN**.

Whether a session generated `composables/useHeadstock.ts` is not known. No source for it was found. The four names below are a call-site contract, read from the archived views. They are not a recovered implementation.

Restoring the archived application as-is is ruled out. The rest of this investigation continues.

## Preflight, then stop

Searches were limited to the surfaces named in the order. They were not expanded into another repository census.

| Search | Result |
|---|---|
| `SPRINTS.md` | Names `useHeadstock` as one of five lost imports. It does not paste `drawBackground`, `drawHeadstock`, `createInlayGroup`, or `exportWorkspaceSVG`. |
| `docs/archive/photo_vectorizer_patches/BACKLOG.md` and `INTEGRATION.md` | Path references to `/mnt/user-data/outputs/ps-vue/src/` and a tree diagram that lists `useHeadstock.ts`. No function body. |
| `docs/investigations/march-2026-consolidation-recovery-census/` | `useHeadstock` recorded as `SOURCE_UNAVAILABLE` / `LOST_REFERENCE_ONLY`. |
| `git log --all -- '*useHeadstock.ts'` | No commit. |
| `git grep function drawHeadstock` on every commit from `git rev-list --all` | No match. |
| `git grep drawBackground` on history | Call sites in archived views and their earlier copies. One unrelated minified rosette bundle also contains the substring. No `useHeadstock.ts`. |
| `git fsck --full --no-reflogs --unreachable` | Empty. This clone has no unreachable objects to inspect. |
| `git stash list`, `git worktree list`, `*.bundle` | No stash. One worktree (this checkout). No bundle file other than the clone pack. |
| Reflog | This clone only. |
| Filenames under `archive/experimental/2026-03` | `useHeadstockPath.ts` and `useHeadstockTransition.ts`. No `useHeadstock.ts`, `headstockData.ts`, or `useParametric.ts`. |
| March 15–20 download folders already in `archive/experimental/2026-03` | HTML prototypes and the view copies. No Vue module for the four exports. |

## Call-site contract

Taken from `WorkspaceView.vue`, `ParametricView.vue`, and `ConfiguratorView.vue` under `archive/experimental/2026-03/headstock-suite-refined/`.

| Export | Calls that exist | Body |
|---|---|---|
| `drawBackground(layer, canvas, showGrid)` | Workspace passes the grid flag. Parametric passes `true`. Configurator passes `false`. | Not recovered |
| `drawHeadstock(hsLayer, guideLayer \| null, canvas, hs, showCenterline, showNut)` | Workspace passes the guide layer and both flags. Configurator passes `null`, `false`, `false`. | Not recovered |
| `createInlayGroup(type, cx, cy, inlayLayer, canvas, snap, boundary, hs, onSelect, onChange)` | Workspace and Configurator. The return value is stored and later read as `.node` and `.id()`. | Not recovered |
| `exportWorkspaceSVG(hs, modelKey, inlays, canvas)` | Workspace only. The return value is saved as an `.svg` download. | Not recovered |

`exportWorkspaceSVG` writes a file in the browser. That download stays outside the recommended implementation cluster.

## What is only a partial input

`packages/client/src/composables/useKonvaCanvas.ts` creates one stage and one layer and returns `{ addLayer, W, H }`. It does not export the four functions, coordinate conversion, or a `stage` ref. `addLayer` returns the same layer on every call. The archived views call `addLayer` once per layer and then use `canvas.stage`, `canvas.c2px`, and `canvas.p2cx`. The live composable does not implement that contract.

`ps-vue-src/composables/useKonvaCanvas.ts` creates a stage and a named layer map, plus `makeCoordHelpers` (`p2cx`, `p2cy`, `c2px`, `c2py`, `fitScale`) for a 200 by 320 path space. It still does not export the four functions. Its signature is `(container, layerNames)`, which matches `ps-vue-src` `ParametricCanvas.vue` and does not match `WorkspaceView.vue`.

Classification of both Konva files: **PARTIAL_RECONSTRUCTION_INPUT**. They are not a substitute for `useHeadstock`.

The HTML prototypes are the same class of input:

| Prototype function | File | Relation to the missing export |
|---|---|---|
| `drawGrid`, `drawBg` | `headstock-designer.html`, `ps-import-normalize.html` | Grid and paper background. Not `drawBackground`. |
| `drawHS` | `headstock-designer.html` | Draws one preset path, tuner dots, centerline, and nut. Not `drawHeadstock`. |
| `makeInlay` | `headstock-designer.html` | Builds a draggable Konva group for eight inlay types. Not `createInlayGroup`. |
| none found | | No function returns the workspace SVG string. |

Those HTML functions show that a canvas of this kind was drawn in a prototype. They do not supply the Vue module, and this order does not rewrite them into one.

`ps-vue-src/components/headstock/parametric/ParametricCanvas.vue` draws its own background and the parametric path with `buildHeadstockPath`. That file does not import `useHeadstock`. It is evidence for the outline cluster below, not a recovery of the four exports.
