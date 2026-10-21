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

## Implementation status

Appended after the order above. The order text is unchanged. This section records what the production branch actually shipped.

- Base: `origin/main` `5bb4614224bd7632cc7badcf873235231064f45e`. PR #450 is an ancestor. Open pull requests at branch cut: none.
- Branch: `cursor/headstock-parametric-outline-preview-003`
- Draft pull request: https://github.com/HanzoRazer/luthiers-toolbox/pull/452 against `main`. Merge is not authorized.
- Client type-check stayed at 87. No baseline was raised.

### Delivered

- `packages/client/src/design-utilities/lutherie/headstock/parametricOutline.ts` is the production kernel. It ports `buildHeadstockPath` and the BODY and SHOULDER defaults and ranges. It does not import `archive/`. It does not apply `MM`. Coordinates stay in the 200×320 model space and are labeled outline units.
- `packages/client/src/components/art-studio/headstock/HeadstockParametricOutlinePreview.vue` renders that closed SVG path for Rounded, Squared, Pointed, and Scroll, with independent controls, validation, and reset.
- `HeadstockDesignerView.vue` mounts that panel under `/art-studio/headstock`. Template loading, millimeter fields, the prompt payload, and `generateHeadstockPrompt` are unchanged.

### Adjustments

- The kernel lives at the path named in the 003 file plan, under `design-utilities/lutherie/headstock/`, rather than in a module beside the view.
- The kernel's provenance comment names `useHeadstockPath.ts` and PR #443. It does not repeat the suite directory slug. `test_client_does_not_import_the_archived_suite` treats that slug, in any client `.ts` or `.vue` text, as an import. The full archive path stays in the order section above.
- No designer test existed. Regression coverage was added once, at `packages/client/src/views/art-studio/__tests__/HeadstockDesignerView.spec.ts`.
- Client tests run with `npm test` (`vitest run`). The client package has no `test:unit` script.
- Recovered pointed geometry can use a negative model-space Y. The default pointed tip includes `100.00,-5.00`. That is the archived formula, left in place.
- `(taper || 0) / 2` is kept. Validation already rejects non-finite taper before that expression runs.

### Still excluded

Tuner placement, novelty scoring, interactive inlay, variants, wood-grain rendering, DXF import and export, G-code, CAM, downloads, persistence, backend changes, `useHeadstock`, and any change to `ArtStudioHeadstock.vue`.

## Disposition after review

Status of this increment:

`PRODUCTION_DESIGN_CAPABILITY — NON_DIMENSIONAL — NON_MANUFACTURING — NOT_IN_MVS_CRITICAL_PATH`

It is a recovered design preview. It is not the manufacturing verification standard, and it does not move the critical path. That path remains Grounding Agent recovery, workflow harness completion, the validated-package contract, the guided beginner interface, deterministic gates, and the physical MVS witness, returning through `LTB-G1-002`.

### Viewport

The recovered path is unchanged, including pointed `Y = -5.00`. The SVG display window is no longer `0 0 200 320`. It is the padded bounds of every control point on the valid parameter-range corners, `13.00 -89.00 164.00 389.00`, so the displayed curve includes the whole valid envelope. Path hashes are the same.

### Separate maintenance

- `MAINT-DEFER-017` — the committed production `VITE_API_BASE` omits `/api`. Prompt construction in this increment is source-compatible. The Generate Preview browser witness used an uncommitted API-base override and does not prove the stock production bundle. Repair stays out of PR #452.
- `MAINT-DEFER-018` — the archive-suite test rejects the directory slug in any client text. Narrowing it to import declarations stays out of PR #452. The full archive path remains in the order section above.
