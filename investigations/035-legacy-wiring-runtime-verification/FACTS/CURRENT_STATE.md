# FACTS — CURRENT STATE

Raw pre-adjudication observations. **No defect labels.**

Production SHA: `cab91edacaedc66a0492c35275ce2c255935bf8e`

## Router loading

- `services/api/app/main.py` calls `load_all_routers()` from `app.router_registry`.
- Manifests compose most HTTP surface.
- Nested `include_router` still occurs (CAM aggregator, instrument geometry package, blueprint package).

## dump_and_assert_routes.py (as found)

- Path: `services/api/scripts/dump_and_assert_routes.py`
- Collects live `app.routes` after import.
- Writes `services/api/metrics/live_routes.json` when `main()` runs.
- Endpoint field stored is `__module__`, not function name.
- File header still says `UNRUN as of 2026-05-30`.
- MVP uniqueness gate is a small exact path set plus prefix groups.
- This investigation does not modify the script.

## Committed live_routes.json (pre-refresh snapshot, current SHA)

Observed in `services/api/metrics/live_routes.json` before Lab census refresh:

- `POST /api/cam/sim/gcode` → `app.routers.simulation_consolidated_router` / `simulate_gcode_json`
- No `POST /api/cam/simulate_gcode` entry in that file
- `POST /api/cam/sim/simulate_gcode` → `simulate_gcode_legacy`
- `POST /api/cam/gcode/simulate` → `app.routers.gcode_consolidated_router` / `simulate_gcode`
- `POST /api/cam/polygon_offset.nc` appears twice:
  - `app.cam.routers.utility.polygon_router` / `polygon_offset`
  - `app.routers.polygon_offset_router` / `polygon_offset_nc`
- `POST /api/instrument/soundhole` appears twice:
  - `app.routers.instrument_router` / `get_soundhole_spec` (earlier in dump)
  - `app.routers.instrument_geometry.soundhole_router` / `calculate_soundhole`

## Frontend literals (pre-refresh)

- SimLab.vue, SimLabWorker.vue, GeometryOverlay.vue, useGcodeSimulation.ts call
  `POST /api/cam/simulate_gcode` with JSON `{ gcode }`.
- OffsetLabView.vue `stepover` ref default `0.4`; posts `/api/cam/polygon_offset.preview`
  and `/api/cam/polygon_offset.nc` with `{ polygon, tool_dia, stepover, link_mode, units }`.
- curvemath_dxf.ts posts `${API_BASE}/exports/polyline_dxf`.
- fretSlotsCamStore.ts and instrumentGeometryStore.ts post `/api/cam/fret_slots/preview`.

## Handler bodies (static)

- `instrument_router.get_soundhole_spec` imports `compute_soundhole_spec` from
  `soundhole_facade`.
- `instrument_geometry.soundhole_router.calculate_soundhole` imports
  `compute_soundhole_spec` from `soundhole_calc`, which re-exports the facade.
- Utility `polygon_router.polygon_offset` calls `toolpath_offsets` with
  `req.stepover` as the N17 stepover argument; default on the model is `2.0`.
- Governed `polygon_offset_nc` uses `OffsetReq.stepover` with `gt=0, le=1.0`
  (fraction of tool diameter) and `generate_polygon_offset_nc_program`.
- CAM aggregator: `simulation_router = None` (disabled include).
- Live simulation router prefix from cam_manifest: `/api/cam/sim`.
- Legacy DXF `export_polyline_dxf` tries `try_build_with_ezdxf` then
  `build_ascii_r12`.
- Governed DXF translator is `POST /api/export/translate/dxf` with Export Object JSON.
- Fret slots preview calls `generate_fret_slot_toolpaths` in standard mode.

## Vectorizer control (static)

- Blueprint package includes `vectorize_router`.
- `vectorize_blueprint` reads upload then `_orchestrator.process_file(...)`.

## Census refresh (Phase 2, 2026-09-06T04:19:01Z)

- Lab workaround live-route walk: 1157 rows (`CURRENT_LIVE_ROUTES.json`).
- `dump_and_assert_routes.collect_routes()`: 10 rows
  (`CURRENT_LIVE_ROUTES_DUMP_AS_IS.json`).
- Collision rows under Lab walk: 15 (`CURRENT_COLLISIONS.json`).
- Name-hint modules: 23.
- Frontend API literals: 276; unmatched vs live table: 137.
- Test files: 455; TestClient: 185; direct router import: 23.
- Uniqueness gate exit 1; missing MVP exact paths recorded in summary JSON.
- Production `services/api/metrics/` was not written.
- PR #17 census artifacts not present; historical numeric counts not restated.

## Runtime witness observations (Phases 4–9)

Spy method for handler identity: `fastapi.routing.APIRoute.handle` keyed by
`(endpoint.__module__, endpoint.__name__)`. Module-level patches recorded as
separate counters; several stayed at 0.

IW-03 control (`POST /api/blueprint/vectorize`): HTTP 200;
`expected_vectorize_route=1`; extraction error on tiny PNG.

S1 `POST /api/cam/simulate_gcode`: HTTP 404 `Not Found`. All listed sim
handler counters 0.

S2 `POST /api/instrument/soundhole` spiral: HTTP 200; `diameter_mm` 49.9;
`gate` GREEN; Williams P:A note 0.143. Counters:
`alternate_legacy_instrument_router=1`, `legacy_router_bound_facade=1`,
`expected_geometry_router=0`, `shared_facade_source_namespace=0`.

S3 `POST /api/cam/polygon_offset.nc` with `stepover=0.4`, `tool_dia=6.0`:
HTTP 200 `text/plain`. Counter `alternate_utility_n17=1`,
`expected_governed_nc=0`. Response text begins with
`(N17 Polygon Offset — arcs + feed floors)`. Pass coordinates include
99.600, 99.200, 98.800, 98.400.

S4 `POST /exports/polyline_dxf`: HTTP 500. Counter
`actual_legacy_handler=1`, `expected_governed_translate=0`, helper
source-module counters 0. Process log included ezdxf R12 dictionary
creation.

S5 `POST /api/cam/fret_slots/preview`: HTTP 200 JSON
`operation=fret_slot_preview`, `status=preview`, `gate=yellow`. Counter
`expected_preview_handler=1`, generator source-module counters 0.

S4 and S5 collected in the same command batch as S3.

Instrument unit tests IW-01, IW-02, IW-04, IW-05: 5 passed at collection time.
After the 2026-09-06 review added IW-06, IW-06b, IW-07 and IW-08: 9 passed.
IW-07 and IW-08 fail against the pre-review harness — that is what makes them
regression witnesses rather than restatements. First IW-03
attempt wrapping `route.endpoint` returned HTTP 422 and was not kept as
accepted IW-03 evidence.

## Test/runtime extraction (Phase 10)

`TEST_RUNTIME_COMPARISON.json` relations: S1 DIFFERENT, S2 PARTIAL,
S3 DIFFERENT, S4 DIFFERENT, S5 PARTIAL.
