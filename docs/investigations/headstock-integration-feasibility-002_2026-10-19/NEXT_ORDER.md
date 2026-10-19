# Next order: HEADSTOCK-PARAMETRIC-OUTLINE-PREVIEW-003

This file is the order. It is not the implementation. Do not start it from the feasibility branch.

## Outcome

`HeadstockDesignerView.vue` shows a parametric headstock outline from `buildHeadstockPath`.

## Source that may be copied

Copy the pure function and its parameter type. Do not import the archive tree from the client, and do not edit the archive bytes.

- `buildHeadstockPath` from `archive/experimental/2026-03/headstock-suite-refined/ps-vue-src/composables/useHeadstockPath.ts`
- `HeadstockParams` and `TipStyle` from `ps-vue-src/types/headstock.ts`
- The `BODY` and `SHOULDER` groups of `PARAM_DEFS` from `ps-vue-src/components/headstock/constants.ts`

Leave `buildTunerPositions`, `MM`, `HS_MODELS`, and the `TUNER` parameter group out. They are the hole-schedule side of the same files.

## Destination

`packages/client/src/views/art-studio/HeadstockDesignerView.vue` and a small module next to it for the pure function. The route stays `/art-studio/headstock`.

The existing template list and prompt button may remain. The new preview is additional. It is drawn in the suite path space (200 by 320, nut at y=298). The view states that this preview is not a cutting file.

## Forbidden in that order

- `ArtStudioHeadstock.vue`, and any merge of the two views
- `useHeadstock`, `createInlayGroup`, `drawHeadstock`, `drawBackground`, `exportWorkspaceSVG`
- `useExportDxf`, `useCamSpec`, `drawCamOverlay`
- `POST /api/export/headstock-dxf`, `/preview`, and `/cost`
- `POST /api/dxf/spline/evaluate`
- File download, G-code, DXF, and any control that admits the path to manufacturing
- Editing files under `archive/experimental/2026-03/headstock-suite-refined/`
- Placing the recovered `types/headstock.ts` onto the live composables

## Tests that order should add

- `buildHeadstockPath` on the default `PARAM_DEFS` values returns one closed path (`M` and a final `Z`)
- Changing `nutWidth` or `tipWidth` changes the path string
- The designer renders that path as an SVG path element
- The designer module does not call `fetch` on `/api/export/headstock-dxf`

## Still unscheduled after that order

Novelty scoring is the strongest leftover design cluster. It is not part of 003.
