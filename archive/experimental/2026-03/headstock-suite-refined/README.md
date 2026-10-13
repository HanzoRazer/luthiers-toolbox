# Headstock Suite — refined views (preserved)

**Status:** PRESERVED, pending feature reconciliation. Not compiled, not routed, not shipped.
**Moved here from:** `packages/client/src/views/cam/headstock/` on 2026-10-13. The files are **byte-identical** to `main` at `2a2f3924`.
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
| `@/composables/useKonvaCanvas`, `useWoodGrain`, `useDxfImport`, `useExportDxf` | live in `packages/client/src/composables/` |
| `@/composables/useCamSpec`, `@/composables/drawCamOverlay` | live, byte-identical, at `design-utilities/lutherie/neck/` |
| `@/components/CamSpecPanel.vue` | live, byte-identical, at `components/cam/neck/` |
| `@/stores/variants`, `@/components/VariantLibraryPanel.vue`, `@/components/WoodGrainPanel.vue` | archive only: `docs/archive/photo_vectorizer_patches/` |
| `@/stores/headstock`, `@/types/headstock`, `@/composables/useHeadstock`, `@/composables/useParametric`, `@/assets/data/headstockData` | **lost**: in no git ref and no archive. Partial logic exists in `../Interactive_Headstock_Generator/ps-suite.html` and `ps-parametric.html`. Recovery is being attempted from the 2026-03-17 claude.ai session's `/mnt/user-data/outputs/ps-vue*/src/` |

## Rules for this folder

- Keep these files byte-identical. Record any recovered module **beside** them with its source, and do not edit the views to fit it.
- Do not move them back into `packages/client/src/` piecemeal. Reconstruction (rebuilding the 5 lost modules) or harvest (porting
  capabilities into `/art-studio/headstock`) each need their own order and their own branch.
