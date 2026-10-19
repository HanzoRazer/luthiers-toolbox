# Capability comparison

Three surfaces:

| Surface | Role in this order |
|---|---|
| Archived suite | `archive/experimental/2026-03/headstock-suite-refined/` views, plus `ps-vue-src/` |
| Routed designer | `HeadstockDesignerView.vue` at `/art-studio/headstock`. Also embedded as a stage of `/art-studio/inlay-workspace`. Provisional destination. |
| Engraving view | `ArtStudioHeadstock.vue`. Comparison only. The router does not mount it. |

No shared contract turned up that would justify merging the designer and the engraving view. The designer collects a style, a few millimetre fields, and an inlay prompt. The engraving view runs a CAM pipeline and risk notes. They share a product word and nothing else in code.

| Capability | Recovered implementation | Routed designer | Engraving view | Needs missing `useHeadstock` | Manufacturing output |
|---|---|---|---|---|---|
| Parametric outline | `buildHeadstockPath` and `PARAM_DEFS`. `ParametricCanvas.vue` draws that path with its own `drawBg`. | Length, width, and tuner layout fields. Preview is an empty string. Generate copies a prompt. | No outline editor | No, if the port uses `buildHeadstockPath` and the recovered canvas pattern | No, if the path is not scaled out through `/headstock-dxf` |
| Novelty scoring | `computeNovelty`, `computeGates`, `useScoring`, corpus on the recovered store | None | None | No | No |
| Preset model paths | `HS_MODELS` in `constants.ts` | Template names from the inlay API, mapped onto `3x3`, `6-inline`, `4x2` | None | No | The same objects carry tuner coordinate lists |
| Interactive inlay | Call sites only. `makeInlay` in `headstock-designer.html` is a partial prototype. | Prompt fields `inlay_design: 'dove'` | Pocketing pipeline, not an inlay editor | Yes. `createInlayGroup` and `InlayLayer.node` | Inlay pockets are a DXF layer in `useExportDxf` |
| Import comparison | Live `useDxfImport`, also copied in `ps-vue-src` | Not used by the designer. The inlay shell calls `loadFile`. | None | No | DXF parse and `POST /api/dxf/spline/evaluate` |
| Wood grain | `useWoodGrain` is live. `WoodGrainPanel.vue` is archive-only. | None | None | No | No |
| Variants | Archive-only store and panel. Not in `ps-vue-src`. | None | None | No | A variant payload in the archived workspace includes `camSpec` |
| CAM overlay | `useCamSpec` and `drawCamOverlay` are live and uncalled. Archived workspace wires them. | None | The engraving view is a different CAM pipeline | The overlay is drawn from the workspace redraw, which also calls `drawHeadstock` | Yes. Tuner holes, truss rod, pitch, screw holes |
| SVG or DXF download | `exportWorkspaceSVG` is missing. `useExportDxf` posts to `/api/export/headstock-dxf`. | The button named export copies a prompt | Pipeline run, not this DXF | SVG export is one of the four missing functions | Yes |

The designer's geometry and the suite's geometry are different authorities. The suite path space is 200 by 320 units, nut datum at y=298, with `MM = 0.215` used when a DXF payload is built. The designer stores length and width in millimetres and does not build a path. The neck generator and unified canvas elsewhere in the API have their own millimetre outlines. A port that draws `buildHeadstockPath` is a preview in the suite's path space. It is not a replacement for those outlines, and it is not a manufacturing admission.
