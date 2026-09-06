# TEST / RUNTIME COMPARISON

Allowed relation: `SAME` | `DIFFERENT` | `PARTIAL` | `UNKNOWN`

`DIFFERENT` is not synonymous with defect.

Machine extraction: `artifacts/census/TEST_RUNTIME_COMPARISON.json`

---

## S1

```text
TEST ENTRYPOINT            services/api/tests/test_simulation_endpoint_smoke.py
                           POST /api/cam/sim/gcode
TEST IMPLEMENTATION        app.routers.simulation_consolidated_router.simulate_gcode_json
PRODUCTION ENTRYPOINT      POST /api/cam/simulate_gcode (FE SimLab)
PRODUCTION IMPLEMENTATION  none (404)
RELATION                   DIFFERENT
```

---

## S2

```text
TEST ENTRYPOINT            services/api/tests/test_soundhole_spiral_endpoint.py
                           POST /api/instrument/soundhole TestClient(app)
TEST IMPLEMENTATION        first-match handler (instrument_router.get_soundhole_spec)
PRODUCTION ENTRYPOINT      POST /api/instrument/soundhole
PRODUCTION IMPLEMENTATION  instrument_router.get_soundhole_spec
                           + bound soundhole_facade.compute_soundhole_spec
RELATION                   PARTIAL
```

App-level tests share production first-match. Geometry-router-only tests would
be a different path. Facade unit tests are direct-import.

---

## S3

```text
TEST ENTRYPOINT            services/api/tests/test_polygon_offset_endpoint_smoke.py
                           POST /api/cam/polygon_offset.nc
TEST IMPLEMENTATION        first-match (witnessed: utility N17)
PRODUCTION ENTRYPOINT      POST /api/cam/polygon_offset.nc (OffsetLab)
PRODUCTION IMPLEMENTATION  app.cam.routers.utility.polygon_router.polygon_offset
RELATION                   DIFFERENT
```

Different from the governed `polygon_offset_nc` implementation. Same URL as
the FE consumer. App tests of this URL likely first-match N17 as well
(`DIFFERENT` vs governed, not vs the smoke test URL).

---

## S4

```text
TEST ENTRYPOINT            governed translate TestClient
                           POST /api/export/translate/dxf
TEST IMPLEMENTATION        dxf_translate_router.translate_to_dxf
PRODUCTION ENTRYPOINT      POST /exports/polyline_dxf
PRODUCTION IMPLEMENTATION  legacy_dxf_exports_router.export_polyline_dxf
RELATION                   DIFFERENT
```

---

## S5

```text
TEST ENTRYPOINT            services/api/tests/test_cam_fret_slots_preview_smoke.py
                           POST /api/cam/fret_slots/preview
TEST IMPLEMENTATION        preview_fret_slots
PRODUCTION ENTRYPOINT      POST /api/cam/fret_slots/preview
PRODUCTION IMPLEMENTATION  preview_fret_slots (generator source spy 0)
RELATION                   PARTIAL
```
