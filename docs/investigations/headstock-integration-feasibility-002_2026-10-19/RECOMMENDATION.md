# Recommendation

Port one cluster. Do not restore the archived application.

**Cluster:** `parametric-outline-preview`

**Destination:** `packages/client/src/views/art-studio/HeadstockDesignerView.vue` at `/art-studio/headstock`

**What it is:** Show the SVG path returned by the recovered `buildHeadstockPath` for a `HeadstockParams` value and a `TipStyle`. The parameter definitions in `PARAM_DEFS` are the control list. The preview stays in the suite's 200 by 320 path space.

**What it is not:** A DXF, a G-code file, a download, a CAM overlay, a tuner-hole schedule, or an admission that the path may be cut. `MM` is not applied. `buildTunerPositions` is not part of this cluster, because the live exporter imports that function for hole coordinates. `ArtStudioHeadstock.vue` is not merged into the designer.

The implementation order is [NEXT_ORDER.md](NEXT_ORDER.md). This branch does not carry it out.

## How the cluster was scored

Each score is 1 to 5. A cluster can be selected only when completeness is at least 4, independence from `useHeadstock` is 5, and it has no manufacturing output (5). The highest total among those that clear the bar is the one named above.

| Cluster | Complete | Fit | Independent | No manufacturing | Testable | Value | Total | Clears |
|---|---|---|---|---|---|---|---|---|
| Parametric outline preview | 5 | 4 | 5 | 5 | 5 | 5 | 29 | yes |
| Novelty scoring | 5 | 3 | 5 | 5 | 5 | 3 | 26 | yes, not selected |
| Preset model paths | 5 | 3 | 5 | 4 | 5 | 3 | 25 | no |
| Import comparison | 4 | 2 | 5 | 1 | 3 | 4 | 19 | no |
| Wood grain | 3 | 2 | 5 | 4 | 3 | 2 | 19 | no |
| Variants | 1 | 2 | 5 | 4 | 2 | 2 | 16 | no |
| CAM overlay | 4 | 1 | 3 | 1 | 2 | 2 | 13 | no |
| Interactive inlay | 1 | 2 | 1 | 2 | 1 | 5 | 12 | no |

Interactive inlay scores last on recoverability even though the interaction would matter to a user. Its implementation is the missing Konva contract, and its pockets are a DXF layer. It is not selected.

Novelty scoring is fully recovered and has no manufacturing output. It needs a `HeadstockParams` value before the number means anything, and the designer has nowhere to hang that number until an outline exists. It stays unscheduled.

Preset paths are complete, and the tuner coordinates stored on `HS_MODELS` make them easy to mistake for a hole list, so they do not get a clear manufacturing score. They stay unscheduled.

Import comparison is already reachable from the inlay workspace and depends on a spline route the API does not implement. It is a manufacturing import, so it is out of this cluster.

## Geometry

The suite path is not the neck generator's outline and not the unified-canvas outline. The next order draws it as a labeled preview. It does not register the path as a manufacturing geometry and it does not call `/api/export/headstock-dxf`.

## Left unscheduled

Novelty scoring, preset galleries, interactive inlay, import comparison, wood grain, variants, SVG download, DXF export, cost, and CAM overlay.
