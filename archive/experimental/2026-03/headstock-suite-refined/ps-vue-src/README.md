# ps-vue-src — Headstock Suite Standalone App (2026-03-17)

Recovered 2026-10-15 from `/mnt/user-data/outputs/ps-vue-src/src/` — the
output of the March 17 standalone Vue migration session. The recovering
session reports the files as byte-identical to that output and computed the
hashes below at copy time.

**What was checked on arrival in this repository (2026-10-15):**

- All 14 hashes below match the committed files, and
  `services/api/tests/test_headstock_ps_vue_src_preserved.py` keeps them
  matching.
- The zip's timestamps are all 2026-10-15, so they cannot date the files.
- Two files are independently dated. `composables/useDxfImport.ts` and
  `views/ImportView.vue` are byte-identical (after LF normalization) to the
  copies already archived under
  `../../Interactive_Headstock_Generator/files - 2026-03-17T091407.113/`, a
  2026-03-17 bundle. The other 12 have no independent date.
- This README is a recovery note written 2026-10-15. It is not March output
  and has no hash of its own.

## Purpose

These files are the source record for the five modules that went missing
when the Headstock Suite views were moved to
`archive/experimental/2026-03/headstock-suite-refined/` in PR #437.
Nothing here is placed into production; the archived views are not edited
to fit these files.

## Module-to-file map

| Lost import path             | Status       | File(s) here                                              |
|------------------------------|--------------|-----------------------------------------------------------|
| `@/types/headstock`          | Recovered    | `types/headstock.ts`                                      |
| `@/stores/headstock`         | Recovered    | `stores/headstock.ts`                                     |
| `@/assets/data/headstockData`| Reconstructable¹ | `components/headstock/constants.ts` + `composables/useHeadstockPath.ts` |
| `@/composables/useParametric`| Partial      | `composables/useHeadstockPath.ts` + `composables/useScoring.ts` |
| `@/composables/useHeadstock` | Not found    | — (needs reconstruction from `ps-suite.html`)             |

¹ The standalone app split `headstockData` across two files. `HS_MODELS`,
`PARAM_DEFS`, `TIP_STYLE_LABELS`, and `TUNER_PATTERNS` are in
`constants.ts`; the `MM` conversion factor (0.215) and `buildHeadstockPath`
/ `buildTunerPositions` are in `useHeadstockPath.ts`. A single
`headstockData.ts` re-exporting both would satisfy the live import.

## Type-name gap (relevant if placing into production)

The live composables (`useExportDxf.ts`, `useDxfImport.ts`, `useCamSpec.ts`)
import two names that are absent from `types/headstock.ts` as recovered:

| Live import name  | Recovered equivalent |
|-------------------|----------------------|
| `ParametricParams`| `HeadstockParams`    |
| `ImportedPath`    | `RawPath`            |

> **Corrected 2026-10-15 by measurement.** An earlier version of this note
> said the aliases "would satisfy all 5 active type errors", and the
> recovering session later said 3 of 5. **Neither is true.**

The proposed aliases:

```ts
export type ParametricParams = HeadstockParams
export type ImportedPath = RawPath
```

Measured with the pinned client toolchain (`npm ci`, vue-tsc 3.3.12,
TypeScript 6.0.3, `vue-tsc --noEmit`) in a scratch copy of `main` at
`703694c1`. Nothing was placed in `packages/client/src`:

| Scratch tree | vue-tsc errors | In the three composables |
|---|---|---|
| `main` as is | 87 | 8 |
| + this `types/headstock.ts` | 94 | 15 |
| + this file and the two aliases | 94 | 15 |

The aliases clear the four `@/types/headstock` import errors. They expose 11
new ones: the live composables use fields this file does not declare
(`InlayLayer.node`, `NormalizeOptions.pad`, `RawPath.type`), plus one overload
mismatch. This file is the standalone app's type set. It is not the set the
live composables were written against, and placing it in production would
raise the error count.

`useExportDxf.ts` also imports `{ buildTunerPositions }` from
`'./useParametric'` and `{ MM }` from `'@/assets/data/headstockData'` —
both of which are separately missing from the live composables directory.

## SHA-256 hashes (verified 2026-10-15)

```
e1f41b9622ad77297c33f5fc75ac528db52b84f7e1bf06dbf5b8883a035253ee  types/headstock.ts
d62da3602a738434df4e9fce8dd486c0f81ca7c1c4a4b2b3a8f75f7f88f22b62  stores/headstock.ts
176f80d84e845df6d0e1a9e6a347d55ac9011cf0287ad874bee0809a42f264bf  components/headstock/constants.ts
5a0be21190fc07b0dc989353ea97fa7693594d276c780c75d1ac14a87a9d43b6  composables/useHeadstockPath.ts
eb0011c0454134b9aaf08866214a9275ecf7113412b8d0ba9f2cc03b6fa3c440  composables/useScoring.ts
1e981dc54266d2ffbfa8469c067b12a206da45077e67fb56e3931c9e2c05b867  composables/useKonvaCanvas.ts
702abe2b682881be8679370342837f8728a1635558d69a830df7dea0211a7460  composables/useDxfImport.ts
892b77db8135cb86d647c270c5256ed4b7ed2a79f4fc82b6bcbd8f534e8e72b1  components/headstock/HeadstockSuite.vue
de4046639a959bc86cb0a3ed61a096bc59e851001467faa4277b30740d89ee45  components/headstock/parametric/ParametricCanvas.vue
6f6cc42958015dc471eadde49fc6993674420923fa86402c0b4490fca882e96a  components/headstock/parametric/ScorePanel.vue
b5e66eb1ea1cdfed9b2d438d3057699b642c3d9b15bc0fe05197e62e7fc0bf7c  components/headstock/workspace/WorkspaceCanvas.vue
268829eb2030cc2ca797b9083ac236aed9a6ee6dd922e4e721941896fc564994  views/ImportView.vue
3c40015df1c7de4e38e16e835b09a10612f21204e50be3785e599f085fa17bb9  styles/ps-tokens.css
7c98563f010bb82eeabf4c96ec2d288d56e2809a3406daebe85c06995b13db9a  components/headstock/INTEGRATION.md
```

## File inventory

```
ps-vue-src/
├── types/
│   └── headstock.ts           — 14 exported types/interfaces
├── stores/
│   └── headstock.ts           — Pinia store + CORPUS (5 ref vectors)
├── components/headstock/
│   ├── constants.ts           — HS_MODELS, PARAM_DEFS, TIP_STYLE_LABELS, TUNER_PATTERNS
│   ├── HeadstockSuite.vue     — Top-level shell component
│   ├── INTEGRATION.md         — Integration notes from March session
│   ├── parametric/
│   │   ├── ParametricCanvas.vue
│   │   └── ScorePanel.vue
│   └── workspace/
│       └── WorkspaceCanvas.vue
├── composables/
│   ├── useHeadstockPath.ts    — buildHeadstockPath, buildTunerPositions, MM=0.215
│   ├── useScoring.ts          — computeNovelty, computeGates, useScoring
│   ├── useKonvaCanvas.ts      — Konva canvas setup composable
│   └── useDxfImport.ts        — DXF import pipeline (standalone version)
├── views/
│   └── ImportView.vue         — Standalone import view
└── styles/
    └── ps-tokens.css          — Design token stylesheet
```

## What is NOT here

- `@/composables/useHeadstock` — Konva rendering functions (`drawBackground`,
  `drawHeadstock`, `createInlayGroup`, `exportWorkspaceSVG`). Not found in
  any output file. Partial reconstruction may be possible from `ps-suite.html`
  and `ps-parametric.html` in the HTML prototype archive.
- `@/stores/variants`, `@/components/VariantLibraryPanel.vue`,
  `@/components/WoodGrainPanel.vue` — documented in the parent README as
  archive-only; not addressed here.
