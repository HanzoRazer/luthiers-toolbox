# Spline evaluate witness

Order: HEADSTOCK-ENDPOINT-EVIDENCE-CORRECTION-002A.

Tree: `main` at `2e2d635f33e44c41256f8dc7d2db6abe08ef0bf0` (merge of PR #444). No production file was edited for this witness.

Classification: **REACHABLE_VISIBLE_FAILURE**.

## What was exercised

Page: `http://127.0.0.1:5173/art-studio/inlay-workspace`.

The router name `ArtStudioInlayWorkspace` loads `InlayWorkspaceShell.vue`. The visible control is the button labeled Import DXF/SVG on the Headstock Design stage. That button opens the shell file input, and the change handler calls `useDxfImport().loadFile`.

File offered: a DXF whose only entity is one `SPLINE` (`$INSUNITS` 4). `window.DxfParser` was `undefined`. `packages/client/index.html` does not load a parser script, and the client package does not assign `window.DxfParser`.

Browser: headless Chrome 154, DevTools protocol, file input set to that DXF.

## What happened

| Observation | Result |
|---|---|
| Page reached | Inlay Workspace, Headstock Design stage |
| Request to `/api/dxf/spline/evaluate` | None. The upload added no network request with `spline` in the URL |
| Visible text | `Error: DxfParser not loaded` |
| Template label after the upload | Custom. `loadFile` catches the parser error and resolves, so the shell still assigns Custom |
| Filename line | Absent. The template reads `dxfImport.importedFile`, and the composable does not return that property |
| Preview | `Headstock: Custom`, `Wood: Mahogany`, `Full grain preview coming soon` |
| SVG paths drawn | 0 |
| Processing continued into a path | No |

Console messages during the same load were Vite connect, an auth warning that Supabase is not configured, a Suspense notice, a 404 for `/api/art-studio/inlay/fret-positions`, and an `InlaySummaryPanel` render error. Those come from the other stages, which stay mounted under `v-show`. They are not the spline request.

## Route absence, separate from the page

Importing `app.main:app` and walking the mounted route graph produced 1157 paths. None is `/api/dxf/spline/evaluate`.

`POST http://127.0.0.1:8010/api/dxf/spline/evaluate` with a JSON body returned `404` and `{"detail":"Not Found"}`. That probe is not a request the page made.

## Not witnessed

`evaluateSplineServer` catches a failed response and returns `splineFallback`, a quadratic path through the control points. The upload never reached that function, because `parseDXFText` throws when `window.DxfParser` is missing. Silent degradation is code that this run did not enter.
