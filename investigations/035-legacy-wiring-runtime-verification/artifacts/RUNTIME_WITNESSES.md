# RUNTIME WITNESSES

Frozen from accepted `artifacts/census/WITNESS_*.json`.
Production SHA for all specimens: `cab91edacaedc66a0492c35275ce2c255935bf8e`

D-status is **not** assigned in this file.

Spy method used after IW-03 control: `fastapi.routing.APIRoute.handle` class hook keyed by
`(endpoint.__module__, endpoint.__name__)`, plus module-level patches as the IW-02
control. Module patches often stay at 0 (bound-name hazard). FastAPI dispatch spy
is the dereference used for handler identity.

Voided: first IW-03 attempt (HTTP 422) after wrapping `route.endpoint` broke
FastAPI signature inspection. That run is VOIDED. Accepted IW-03 is HTTP 200
with `expected_vectorize_route = 1`.

S4 and S5 were collected in the same batch as S3 before S3 was inspected.
The severe-stop rule is satisfied by S3; S4/S5 remain frozen additional
evidence, not a reason to keep sampling.

---

## SPECIMEN S1_CAM_SIM_FE_PATH

```text
SPECIMEN                 S1_CAM_SIM_FE_PATH
PRODUCTION SHA           cab91edacaedc66a0492c35275ce2c255935bf8e
ENTRYPOINT               POST /api/cam/simulate_gcode
                         (SimLab.vue / SimLabWorker.vue / GeometryOverlay.vue /
                          useGcodeSimulation.ts)
EXPECTED IMPLEMENTATION  app.routers.simulation_consolidated_router.simulate_gcode_json
                         (live mount POST /api/cam/sim/gcode)
ALTERNATES               app.cam.routers.simulation...simulate_gcode (aggregator disabled)
                         app.routers.gcode_consolidated_router.simulate_gcode
                         simulate_gcode_legacy at POST /api/cam/sim/simulate_gcode
SPY LOCATION             APIRoute.handle + module names listed in WITNESS_S1.json
REQUEST OR INVOCATION    POST /api/cam/simulate_gcode  JSON {gcode: G21/G90 tiny program}
HTTP/CLI RESULT          404 {"detail":"Not Found"}
ACTUAL CALLS             expected_sim_json=0
                         alternate_sim_legacy_under_sim_prefix=0
                         alternate_gcode_consolidated_simulate=0
TERMINAL EFFECT          HTTP 404; no spied implementation called
CONSUMER                 SimLab / BridgeLab overlay / GeometryOverlay
TEST-PATH COMPARISON     DIFFERENT — tests hit /api/cam/sim/gcode, not this FE URL
LIMITATIONS              Disabled package handler was not imported (not a production
                         dereference). This request does not prove /api/cam/sim/gcode
                         works; it proves the FE URL does not reach it.
```

---

## SPECIMEN S2_SOUNDHOLE_POST_DUAL_MOUNT

```text
SPECIMEN                 S2_SOUNDHOLE_POST_DUAL_MOUNT
PRODUCTION SHA           cab91edacaedc66a0492c35275ce2c255935bf8e
ENTRYPOINT               POST /api/instrument/soundhole
EXPECTED IMPLEMENTATION  app.routers.instrument_geometry.soundhole_router.calculate_soundhole
                         → soundhole_facade.compute_soundhole_spec
ALTERNATES               app.routers.instrument_router.get_soundhole_spec
                         (also bound to compute_soundhole_spec)
SPY LOCATION             APIRoute.handle on both POST handlers;
                         bound compute_soundhole_spec on each router module;
                         source facade namespace as IW-02 control
REQUEST OR INVOCATION    POST /api/instrument/soundhole
                         {body_style:dreadnought, body_length_mm:500,
                          soundhole_type:spiral}
HTTP/CLI RESULT          200 spiral spec; diameter_mm=49.9; gate GREEN;
                         notes include Williams P:A 0.143
ACTUAL CALLS             expected_geometry_router=0
                         alternate_legacy_instrument_router=1
                         legacy_router_bound_facade=1
                         geometry_router_bound_compute=0
                         shared_facade_source_namespace=0
TERMINAL EFFECT          HTTP 200 spiral payload from instrument_router + bound facade
CONSUMER                 instrument geometry UI / type dropdown via this URL
TEST-PATH COMPARISON     PARTIAL — TestClient on the same app hits the same first-match
                         handler; facade unit tests are a second path
LIMITATIONS              Source-module facade spy is IW-02 (0). Physics came from the
                         bound name on instrument_router, which is the same
                         compute_soundhole_spec object imported from the facade.
                         Dual-mount ownership ≠ obsolete calculator.
```

---

## SPECIMEN S3_POLYGON_OFFSET_NC_DUAL_MOUNT

```text
SPECIMEN                 S3_POLYGON_OFFSET_NC_DUAL_MOUNT
PRODUCTION SHA           cab91edacaedc66a0492c35275ce2c255935bf8e
ENTRYPOINT               POST /api/cam/polygon_offset.nc
                         (OffsetLabView.vue default stepover=0.4)
EXPECTED IMPLEMENTATION  app.routers.polygon_offset_router.polygon_offset_nc
                         (stepover 0–1 fraction of tool_dia)
ALTERNATES               app.cam.routers.utility.polygon_router.polygon_offset
                         (N17 toolpath_offsets; stepover mm)
SPY LOCATION             APIRoute.handle on both colliding POST handlers
REQUEST OR INVOCATION    POST /api/cam/polygon_offset.nc
                         polygon=100mm square, tool_dia=6.0, stepover=0.4,
                         link_mode=arc, units=mm
HTTP/CLI RESULT          200 text/plain G-code starting
                         "(N17 Polygon Offset — arcs + feed floors)"
ACTUAL CALLS             expected_governed_nc=0
                         alternate_utility_n17=1
TERMINAL EFFECT          N17 G-code; pass insets 99.600, 99.200, 98.800, 98.400
                         (0.4 mm steps), not 0.4×6.0=2.4 mm governed step
CONSUMER                 OffsetLabView.getGcode(); also n17_n18.ts
TEST-PATH COMPARISON     DIFFERENT vs governed polygon_offset_nc;
                         SAME URL as FE and as test_polygon_offset_endpoint_smoke
                         (that test also first-matches N17 unless proven otherwise)
LIMITATIONS              Preview URL /polygon_offset.preview was not invoked here.
                         OVERLAP.md records both mounts as intentional parallel
                         implementations; FE schema nonetheless matches governed.
```

**Severe-stop freeze fields**

```text
RUNTIME CONFIRMED        OffsetLab NC URL executed N17 utility handler, not governed
MATERIAL CAPABILITY      manufacturing G-code (customer/CAM facing)
MATERIAL CONSEQUENCE     stepover interpreted as 0.4 mm instead of 0.4×tool_dia
                         — denser toolpath than the FE control implies
```

---

## SPECIMEN S4_DXF_CURVEMATH_LEGACY_EXPORT

```text
SPECIMEN                 S4_DXF_CURVEMATH_LEGACY_EXPORT
PRODUCTION SHA           cab91edacaedc66a0492c35275ce2c255935bf8e
ENTRYPOINT               POST /exports/polyline_dxf  (curvemath_dxf.ts)
EXPECTED IMPLEMENTATION  app.routers.export.dxf_translate_router.translate_to_dxf
ALTERNATES               app.routers.legacy_dxf_exports_router.export_polyline_dxf
                         try_build_with_ezdxf / build_ascii_r12
SPY LOCATION             APIRoute.handle on both handlers; module spies on helpers
REQUEST OR INVOCATION    POST /exports/polyline_dxf
                         {polyline:{points:[[0,0],[100,0],[100,50],[0,50]]}}
HTTP/CLI RESULT          500 Internal Server Error
                         server log: ezdxf creating dictionaries; R12 $INSUNITS warning
ACTUAL CALLS             actual_legacy_handler=1
                         legacy_ezdxf_helper=0
                         legacy_ascii_r12_fallback=0
                         expected_governed_translate=0
TERMINAL EFFECT          HTTP 500 after legacy handler dispatch; ezdxf activity in logs
CONSUMER                 packages/client/src/utils/curvemath_dxf.ts
TEST-PATH COMPARISON     DIFFERENT — governed translate tests use another URL
LIMITATIONS              Helper spies were source-module (IW-02). ezdxf logs show
                         R12 export work inside the legacy path. 500 cause not
                         fully isolated (history_store / response assembly possible).
                         Collected after S3 severe condition already existed.
```

---

## SPECIMEN S5_FRET_SLOTS_CAM_PREVIEW

```text
SPECIMEN                 S5_FRET_SLOTS_CAM_PREVIEW
PRODUCTION SHA           cab91edacaedc66a0492c35275ce2c255935bf8e
ENTRYPOINT               POST /api/cam/fret_slots/preview
EXPECTED IMPLEMENTATION  app.cam.routers.fret_slots_router.preview_fret_slots
                         → generate_fret_slot_toolpaths
ALTERNATES               generate_fan_fret_cam; POST /api/v1/fretboard/dxf (not this URL)
SPY LOCATION             APIRoute.handle on preview_fret_slots;
                         source-module spies on generators
REQUEST OR INVOCATION    POST /api/cam/fret_slots/preview
                         {model_id:dreadnought, fret_count:20, mode:standard}
HTTP/CLI RESULT          200 JSON operation=fret_slot_preview status=preview gate=yellow
ACTUAL CALLS             expected_preview_handler=1
                         expected_standard_generator=0
                         alternate_fan_generator=0
TERMINAL EFFECT          HTTP 200 governed preview envelope
CONSUMER                 fretSlotsCamStore.ts / instrumentGeometryStore.ts
TEST-PATH COMPARISON     PARTIAL — same URL as smoke tests; generator source spy 0
LIMITATIONS              generate_fret_slot_toolpaths is imported into the router
                         module (IW-02). Yellow gate may be MODEL_NOT_FOUND default
                         path; that fallback is not automatically D3.
                         Ecosphere DXF was not posted.
                         Collected after S3 severe condition already existed.
```

---

## IW-03 CONTROL (not a selected specimen)

```text
SPECIMEN                 IW03_VECTORIZER_CONTROL
ENTRYPOINT               POST /api/blueprint/vectorize
EXPECTED IMPLEMENTATION  vectorize_blueprint
HTTP/CLI RESULT          200 processed=true, extraction error on tiny PNG
ACTUAL CALLS             expected_vectorize_route=1
TERMINAL EFFECT          production route reached intended handler
```

Control passed. S1–S5 spies using the same APIRoute.handle hook are trusted for
handler identity.
