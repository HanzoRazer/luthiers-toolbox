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

## Census refresh / runtime

Filled after accepted Phase 2 and Phases 5–9 runs. No labels here.
