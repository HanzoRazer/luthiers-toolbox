# Backend endpoint audit

Design endpoints and manufacturing endpoints are listed apart. The recommended cluster uses none of the manufacturing rows.

Classification is against the tree at `4837c500`.

| Class | Meaning here |
|---|---|
| live | A router module is mounted and the path exists |
| governed | Mounted, and the handler calls a lifecycle or authority guard before it writes a file |
| broken | A reachable client calls a path that has no route |
| obsolete | No current caller and no route. None of the suite paths fell in this class |

## Design

| Method and path | Where it is mounted | Who calls it | Class |
|---|---|---|---|
| `GET /api/instruments/guitar/headstock-inlay/templates` | `app.routers.instruments.guitar.headstock_inlay_router` | `HeadstockDesignerView.vue` via `listHeadstockTemplates` | live |
| `GET /api/instruments/guitar/headstock-inlay/styles` | same router | Declared in the designer comment. The view loads templates, not this list, on mount. | live |
| `POST /api/instruments/guitar/headstock-inlay/generate-prompt` | same router | `generateHeadstockPrompt`. The designer button named export copies that prompt to the clipboard. It does not download a DXF. | live |
| `/api/cam/headstock/inlay` | `app.cam.headstock.router`, prefix in `cam_manifest.py` | Not called by `HeadstockDesignerView.vue`. A second prompt API. | live |

`ArtStudioHeadstock.vue` is not mounted by `/art-studio/headstock`. Its client calls are the CAM pipeline (`runPipeline`) and CAM risk notes. Those are manufacturing surfaces for the comparison view. They are not a shared contract with the designer: one view asks for an inlay prompt, the other runs a pocketing pipeline.

## Manufacturing

| Method and path | Where it is mounted | Who calls it | Class |
|---|---|---|---|
| `POST /api/export/headstock-dxf` | `app.routers.headstock.dxf_export`, prefix `/api/export` in `cam_manifest.py` | Archived `WorkspaceView` through `useExportDxf`. The handler calls `assert_dxf_lifecycle_context` before it builds the document. | live, governed |
| `POST /api/export/headstock-dxf/preview` | same router | `useExportDxf.fetchPreview` | live, governed |
| `POST /api/export/headstock-dxf/cost` | same router | Suite cost estimate. Not called by the routed designer. | live, governed |
| `POST /api/dxf/spline/evaluate` | no mounted route; a direct POST returns 404 | `evaluateSplineServer` in `useDxfImport.ts`, only after `window.DxfParser` exists. The routed shell calls `loadFile`, and that call fails first. | `REACHABLE_VISIBLE_FAILURE` |
| `GET /api/vectorizer/status` | vectorizer router | `useDxfImport.checkVectorizerStatus` | live |

`useExportDxf` is not called from any routed view, so the governed DXF routes are live on the server and idle in the current client. They stay behind that guard. This order does not relax it, and the next order must not call these paths.

## Spline evaluate, corrected

Prior statement from PR #444, withdrawn:

> The spline route is the one unsafe gap already reachable: a user on the inlay workspace can load a DXF, and a SPLINE entity asks for a path the API does not implement.

That sentence treated the path as `broken`: a reachable client call against a missing route. The route is absent, and a direct POST on the running API returns `{"detail":"Not Found"}`. The routed workflow does not make that call.

Current class: **REACHABLE_VISIBLE_FAILURE**. Witness: [SPLINE_EVALUATE_WITNESS.md](SPLINE_EVALUATE_WITNESS.md), measured on `main` at `2e2d635f`.

`/art-studio/inlay-workspace` mounts `InlayWorkspaceShell.vue`. Its Import control calls `useDxfImport().loadFile`. With `window.DxfParser` undefined, `parseDXFText` throws `DxfParser not loaded` before `evaluateSplineServer`. The page shows `Error: DxfParser not loaded`, selects the Custom template, and draws no substitute path. The network log for that upload contains no `spline/evaluate` request.

`evaluateSplineServer` does contain an unreached `catch` that returns `splineFallback`. This witness did not enter that branch, so the workflow is not classified as silent degradation.
