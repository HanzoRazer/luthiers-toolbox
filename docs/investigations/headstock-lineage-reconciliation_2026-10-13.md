# Headstock Lineage Reconciliation (MAINT-DEFER-010)

**Date:** 2026-10-13
**Type:** evidence only. No source file is moved, deleted or edited by this document.
**Measured against:** `origin/main` @ `2a2f3924`
**Subject:** `packages/client/src/views/cam/headstock/` (`ConfiguratorView`, `ImportView`, `ParametricView`, `WorkspaceView`)

## 0. Verdict

| Question | Answer |
|---|---|
| Classification | **PRESERVE_PENDING_FEATURE_RECONCILIATION** |
| Cause | **Partial import of an in-progress feature.** It is **not** namespace-collision debris: no collision record mentions these files, and the blobs were already malformed before the April rewrite, which only carried them forward. |
| Are they duplicates of the archive? | **No** for the March *Headstock Generator* bundle. They are the **last iterations** of the same suite, and byte-identical copies exist only in the later *Neck and Cam* bundle folders and in `docs/archive/photo_vectorizer_patches/`. |
| Unique capability vs the routed headstock feature? | **Yes, substantial** (§4). Nothing routed today provides it. |
| Recoverable? | **Partly.** Of the 11 missing modules, 3 are in the archive, 3 are live at another path, and **5 exist nowhere in git or under Downloads** (§3). |
| Is the removal decision still standing? | **No.** PR #308 (deletion) shows MERGED but never reached `main` (§2). The owner's 2026-10-13 instinct to preserve this work is supported by the evidence and supersedes the plan to re-land #308. |

## 1. Provenance: one suite, built in one day

The headstock, neck and CAM modules are **one suite** ("Production Shop" / `ps-vue`). It was generated in a
claude.ai session on **2026-03-17 between 03:53 and 22:42**, and its output folder was
`/mnt/user-data/outputs/ps-vue/src/`. The timestamped download folders preserve its evolution:

| Time (03-17) | Folder (`archive/experimental/2026-03/…`) | View blob | Notes |
|---|---|---|---|
| 09:14 | `Interactive_Headstock_Generator/files - …091407.113` | ImportView `c7cf5834`, WorkspaceView `d496ab7c` | first Vue port |
| 09:27 | `…092736.563` | ParametricView `755e25e6` | `INTEGRATION.md`: "drop the `ps-vue/src/` subtree", which includes `stores/headstock.ts`, `types/headstock.ts`, `assets/data/headstockData.ts`, `composables/useHeadstock.ts`, `useParametric.ts` |
| 17:27 | `Interactive_Neck and Cam _Modules/files - …172741.143` | WorkspaceView **`80a5ed54`** | `WORKSPACE_CAM_INTEGRATION` applied (CAM overlay, wood grain, DXF) |
| 18:15 | `…181515.994` | ImportView **`3580af7e`** | |
| 18:22 | `…182228.919` | ConfiguratorView **`4c3ac93b`** | customer configurator added |
| 22:38–22:42 | `…223828.607` and later | `CamWorkspaceView` `bfbc33ba` | the CAM workspace; harvested and routed (now `views/cam/CamWorkspaceView.vue`) |

Blob history of the four `src` views:

| View | pre-rewrite `8c553069` (03-18) | April root `8d91c4c7` (04-05) | `main` today | identical copy in archive |
|---|---|---|---|---|
| ConfiguratorView | `4c3ac93b` | `4c3ac93b` | `4c3ac93b` | 18:22 folder; `photo_vectorizer_patches/` |
| ImportView | `3580af7e` | **`674d3fde`** | `674d3fde` | 18:15 folder holds the *pre*-edit blob |
| ParametricView | `755e25e6` | `755e25e6` | `755e25e6` | 09:27 folder; `photo_vectorizer_patches/` |
| WorkspaceView | `80a5ed54` | `80a5ed54` | **`3be10a9e`** | 17:27 folder holds the pre-#430 blob |

- **Entry:** commit `8c553069` (2026-03-18). Its title is the unrelated "feat(materials): add E_C_gpa cross-grain modulus". It added only the four views, at `views/cam/headstock/`, and not at the path `INTEGRATION.md` prescribed (`modules/cam/headstock/`). None of the supporting `ps-vue/src` modules came with them.
- **April rewrite:** `8d91c4c7` is a parentless root commit (4,553 files). It **carried the files forward unchanged except `ImportView`**, which gained a 27-line photo "extraction method" selector (`auto/silhouette/blueprint/photo/ai`) feeding `loadFromPhoto(file, { sourceType })`. That edit was made in the repo during the 03-18 → 04-05 window. The history for that window was not preserved, so the edit cannot be attributed to a commit. **It is evidence of active development on these views after import.**
- **Since then:** the only change is `WorkspaceView` 3-line handler extraction in #430 (behavior-preserving).

## 2. Why the files are still on `main`

PR #308 ("remove orphaned cam/headstock views; ceiling 150 → 87") shows **MERGED**, but its base was
`ci/client-type-check-ratchet` (#306), not `main`. #306 merged to `main` at 2026-08-19 22:03Z, and #308 merged into
#306's branch at 02:23Z the next day. Merge commit `f8f5a568` is **not an ancestor of `main`**. I checked eight other
PRs from that period and all are on `main`, so this is specific to #308. SPRINTS.md still lists MAINT-DEFER-010 as DEFERRED.
**The stranding preserved the files.** Given §4, that outcome is useful, not harmful.

## 3. The 11 missing modules

| Imported as | Status | Where it lives |
|---|---|---|
| `@/composables/useCamSpec` | live, **byte-identical**, other path | `design-utilities/lutherie/neck/useCamSpec.ts` (`8a5fa2e0`) |
| `@/composables/drawCamOverlay` | live, **byte-identical**, other path | `design-utilities/lutherie/neck/drawCamOverlay.ts` (`6a970f47`) |
| `@/components/CamSpecPanel.vue` | live, **byte-identical**, other path | `components/cam/neck/` and `components/neck/` (`348e6dd9`) |
| `@/stores/variants` | **archive only** | `photo_vectorizer_patches/variants.ts` (`288c47a6`) |
| `@/components/VariantLibraryPanel.vue` | **archive only** | `photo_vectorizer_patches/VariantLibraryPanel.vue` (`f73a4b2d`) |
| `@/components/WoodGrainPanel.vue` | **archive only** | `photo_vectorizer_patches/WoodGrainPanel.vue` (`6979c276`) |
| `@/stores/headstock` | **lost** | in no ref, no archive, and nowhere under `Downloads/` |
| `@/types/headstock` | **lost** | in no ref, no archive, and nowhere under `Downloads/` |
| `@/composables/useHeadstock` | **lost** | logic partly present in prototypes (below) |
| `@/composables/useParametric` | **lost** | logic partly present in prototypes (below) |
| `@/assets/data/headstockData` | **lost** | data partly present in prototypes (below) |

The four imports that do resolve (`useKonvaCanvas`, `useWoodGrain`, `useDxfImport`, `useExportDxf`) are live.
`useExportDxf` is byte-identical to the suite's version.

**What the HTML prototypes hold** (`Interactive_Headstock_Generator/*.html`). Each symbol the views import was looked for by name:
`HS_MODELS` is in `ps-suite.html`, and `buildTunerPositions`, `runGates` and `CORPUS` are in `ps-parametric.html`. The other 13 symbols are **not found**,
including `drawHeadstock`, `createInlayGroup`, `buildParametricPath`, `scoreNovelty`, `TIP_STYLE_NAMES`, `TUNER_PATTERNS` and `PARAM_RANGES`.
The prototypes are therefore a partial reconstruction source, not the lost modules.

**The authoritative recovery source is the 2026-03-17 claude.ai conversation** that wrote `/mnt/user-data/outputs/ps-vue/src/`.
`docs/archive/photo_vectorizer_patches/BACKLOG.md` (NECK-001, HEADSTOCK-001, VECTORIZER-001) records the copy-out lists from that
session. The neck items were copied in; the headstock store, types, data and composables were never listed and never copied.
Only the owner can check whether that conversation and its files are still available.

## 4. Capability matrix

Routed today: `/art-studio/headstock` → `HeadstockDesignerView.vue`. It is form-based and calls `/api/instruments/guitar/headstock-inlay/*`.
`views/art/art_studio_headstock/ArtStudioHeadstock.vue` exists but is **not routed**.

| Capability | Orphaned views | Routed `HeadstockDesignerView` |
|---|---|---|
| Interactive canvas (Konva) | yes (all four) | no |
| Headstock model presets | yes (`HS_MODELS`) | style templates via API |
| Inlay placement: drag, scale, rotate, flip, delete | yes (Workspace) | inlay design fields only |
| Snap and boundary constraints, 80-step undo | yes (Workspace) | no |
| CAM overlay (truss rod and related spec) | yes (Workspace, via live `useCamSpec`) | no |
| Wood-grain texture by species | yes (Workspace, Configurator) | no |
| Variant library (save and load designs) | yes (Workspace) | no |
| Parametric outline generator (body, shoulder and tuner params; tip styles; tuner patterns) | yes (Parametric) | tuner hole diameter and spacing only |
| Corpus overlay of known headstocks, **novelty scoring**, gates | yes (Parametric) | no |
| DXF/photo import with raw-vs-normalized view and vectorizer source-type selector | yes (Import) | no |
| SVG export | yes | limited |
| DXF export with **veneer, binding and material cost** (`/headstock-dxf`, `/preview`, `/cost`) | yes (Workspace, via live `useExportDxf`) | no (uses the inlay API) |
| **Customer configurator**: 4-step public wizard that queues a variant for the shop | yes (Configurator) | no |
| AI inlay prompt generation | no | yes |

**Corollary:** the backend `/headstock-dxf`, `/headstock-dxf/preview` and `/headstock-dxf/cost` routes
(`routers/headstock/dxf_export.py`, with `VeneerSpec`/`BindingSpec` from BACKLOG HEADSTOCK-001) are live, but
**the orphaned `WorkspaceView` is their only UI caller**. `CamSpecPanel` mentions `useExportDxf` in a comment only.
Retiring the views would leave that backend capability with no UI.

## 5. Dispositions offered (owner to choose)

| Option | What it does | Type-check effect |
|---|---|---|
| **A. Preserve out of compilation** (recommended interim) | `git mv` the four views, byte-identical, to a documented research location (e.g. `archive/experimental/2026-03/headstock-suite-refined/`) with a README pointing here. Copy the 3 archive-only modules beside them. Leave src untouched otherwise. | ceiling falls by the views' 63 errors; re-measure, don't assume |
| B. Exclude in place | Keep the files where they are and add a `tsconfig` `exclude` with the reason recorded | same as A, but the code stays in `src/` and is easy to forget |
| C. Reconstruct on an isolated branch | Rebuild the 5 lost modules from the 03-17 conversation (if recoverable) or from the HTML prototypes, then evaluate against §4 | none until merged |
| D. Harvest into the routed feature | Port chosen capabilities from §4 into `/art-studio/headstock` deliberately, one at a time | per increment |

These options are not exclusive: A first (secure preservation, then lower the ceiling), then C or D under separate orders.
**Do not lower the ceiling before preservation is merged.**

## 6. Out of scope, flagged

- `views/art/art_studio_headstock/ArtStudioHeadstock.vue` and its composables are unrouted too. That is a second headstock lineage that
  this document did not reconcile.
- `docs/archive/photo_vectorizer_patches/` is misnamed: it holds the whole `ps-vue` suite, not vectorizer patches.
- The 03-18 → 04-05 history was not preserved by the April rewrite, so in-repo work from that window (e.g. the `ImportView` edit)
  cannot be attributed to a commit.

## Method (reproducible)

- Blob comparison: `git rev-parse <commit>:<path>` for each view at `8c553069`, `8d91c4c7`, `2b4c0033~1`, `d3035e19`, `origin/main`, plus `git ls-tree -r` over `archive/experimental/2026-03/` and `docs/archive/photo_vectorizer_patches/`.
- Missing modules: `git log --all -- <path>` for each import, `git ls-tree` basename search on `main`, and a `find` over `Downloads/` (depth 7) for `headstockData*`, `useHeadstock.ts`, `useParametric.ts` and `ps-vue/`.
- #308: `gh pr view 308` (base `ci/client-type-check-ratchet`), `git merge-base --is-ancestor f8f5a568 origin/main` → false. The same check for #305, #306, #307, #309, #312, #320, #340 and #370 → all on `main`.
- Collision records: `git grep -il "namespace collision"` over `docs/`, then searched each hit for `headstock`, `views/cam` and `ps-vue`. The only hit was an acoustics inventory that mentions headstocks in an unrelated context.
- Capabilities: read each view's header and controls, and searched the routed view for each capability keyword.
