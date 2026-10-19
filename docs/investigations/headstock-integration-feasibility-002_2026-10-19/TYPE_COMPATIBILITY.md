# Type compatibility

The recovered `ps-vue-src/types/headstock.ts` is the standalone app's type set. It is not the set the live composables were written against.

## Measurement

Scratch only. The file was copied into `packages/client/src/types/headstock.ts`, two aliases were appended, `vue-tsc --noEmit` was run with the client toolchain already installed (vue-tsc 3.3.12, TypeScript 6.0.3), and the scratch file was deleted. Nothing in that path is part of this change.

```ts
export type ParametricParams = HeadstockParams
export type ImportedPath = RawPath
```

Result: **94** errors. That matches the count recorded when PR #443 measured `main` at `703694c1` (87 without the file, 94 with it). The aliases clear the missing-name errors for `ParametricParams` and `ImportedPath`. They expose the 11 errors below. `useCamSpec.ts` imports `ParametricParams` and does not read fields from it, so the alias adds no error there.

## The 11 errors

| # | File | Line | Code | What the recovered type lacks |
|---|---|---|---|---|
| 1 | `useDxfImport.ts` | 124 | TS2339 | `NormalizeOptions.pad`. The recovered field is `padding`. |
| 2 | `useDxfImport.ts` | 168 | TS2769 | The object passed to `NormalizeOptions` uses `pad` and sets `flipY` to a boolean. The recovered `flipY` is `'auto' \| 'yes' \| 'no'`. |
| 3 | `useDxfImport.ts` | 180 | TS2353 | `RawPath.type`, on an SVG element name. |
| 4 | `useDxfImport.ts` | 198 | TS2353 | `RawPath.type`, value `'SPLINE'`. |
| 5 | `useDxfImport.ts` | 207 | TS2353 | `RawPath.type`, the DXF entity type. |
| 6–11 | `useExportDxf.ts` | 34, 37, 38, 39, 40, 74 | TS2339 | `InlayLayer.node`. The exporter reads `children`, `x()`, `y()`, `scaleX()`, and `rotation()` from it. |

Placing the recovered types into `packages/client/src` would raise the type-check count. This order does not do that.

Errors that remain because other modules are still missing, and that the aliases do not create, include `KonvaCanvas` (not exported by the live `useKonvaCanvas.ts`), `./useParametric`, and `@/assets/data/headstockData`.

## Adapters

An adapter may re-export symbols that exist. It may not claim to be the historical module.

### `headstockData`

Status: **incomplete**.

Symbols that exist today:

| Symbol | File |
|---|---|
| `HS_MODELS`, `PARAM_DEFS`, `TIP_STYLE_LABELS`, `TUNER_PATTERNS` | `ps-vue-src/components/headstock/constants.ts` |
| `MM` (`0.215`), `buildHeadstockPath`, `buildTunerPositions` | `ps-vue-src/composables/useHeadstockPath.ts` |

The archived views import `HS_MODELS` and `MM` from `@/assets/data/headstockData`. Those two names exist, in two files. The original file that combined them was not recovered, so a module placed at that import path would be a new boundary. `MM` is the scale the DXF exporter multiplies into millimetres. Re-exporting it into a design preview is allowed only if the preview does not emit a manufacturing file. See the manufacturing boundary in [RECOMMENDATION.md](RECOMMENDATION.md).

### `useParametric`

Status: **infeasible as a drop-in**.

`useHeadstockPath.ts` exports `buildHeadstockPath`, `buildTunerPositions`, and `useHeadstockPath`. `useScoring.ts` exports `computeNovelty`, `computeGates`, and `useScoring`. Those are the recovered names.

The March lineage note looked for `buildParametricPath` and `scoreNovelty` in the HTML prototypes and did not find them. Inventing those aliases would assert a historical export list that no file shows. A later change may import the recovered names directly. It may not add a `useParametric.ts` that pretends to be the lost module.
