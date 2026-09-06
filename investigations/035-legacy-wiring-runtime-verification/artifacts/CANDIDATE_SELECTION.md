# CANDIDATE SELECTION — Investigation 035

**Frozen before runtime work.** Manual evidence table. No automated risk verdict.

Current production SHA: `cab91edacaedc66a0492c35275ce2c255935bf8e`

Selection rule: five candidates, diverse subsystems and failure shapes.
Prefer cases where static evidence could support “the technology does not work”
when the real condition may be “production does not execute the intended
implementation.”

Vectorizer current Toolbox path is a **control**, not selected.

---

## Considered

### C-01 — CAM G-code simulation FE URL vs live mount

```text
CAPABILITY                 G-code motion simulation (SimLab / BridgeLab overlay)
ENTRYPOINT                 POST /api/cam/simulate_gcode
EXPECTED IMPLEMENTATION    app.routers.simulation_consolidated_router.simulate_gcode_json
                           live path POST /api/cam/sim/gcode
ALTERNATE IMPLEMENTATION(S)
                           app.cam.routers.simulation.simulation_consolidated_router.simulate_gcode
                           (aggregator sets simulation_router = None; package disabled)
                           app.routers.gcode_consolidated_router.simulate_gcode
                           POST /api/cam/gcode/simulate
                           simulate_gcode_legacy at POST /api/cam/sim/simulate_gcode
CURRENT STATIC EVIDENCE    FE literals in SimLab.vue, SimLabWorker.vue,
                           GeometryOverlay.vue, useGcodeSimulation.ts
                           live_routes.json has /api/cam/sim/gcode, not /api/cam/simulate_gcode
                           aggregator comment “DISABLED - zero frontend usage” contradicts FE
TEST LEVEL                 App TestClient on /api/cam/sim/* (test_simulation_endpoint_smoke.py)
                           — not the FE path
USER/MANUFACTURING CONSEQUENCE
                           Simulation UI can appear broken; operator may skip sim
WHY HIGH-RISK              Backend capability exists; FE may never reach it
SELECTED / NOT SELECTED    SELECTED as S1
```

### C-02 — Soundhole POST dual mount

```text
CAPABILITY                 Soundhole sizing / type system (round, oval, spiral, fhole)
ENTRYPOINT                 POST /api/instrument/soundhole
EXPECTED IMPLEMENTATION    app.routers.instrument_geometry.soundhole_router.calculate_soundhole
                           → soundhole_facade.compute_soundhole_spec
ALTERNATE IMPLEMENTATION(S)
                           app.routers.instrument_router.get_soundhole_spec
                           (also → soundhole_facade.compute_soundhole_spec)
                           app.routers.instrument.soundhole_router (thin calc-only)
CURRENT STATIC EVIDENCE    live_routes.json lists both instrument_router and
                           instrument_geometry.soundhole_router on the same path
                           docs/INSTRUMENT_ROUTER_OVERLAP.md: parallel impls; “legacy wins”
                           Both current handlers import the facade/calc, so static dual-mount
                           may or may not be execution-path divergence at the calc layer
TEST LEVEL                 App TestClient test_soundhole_spiral_endpoint.py
USER/MANUFACTURING CONSEQUENCE
                           Wrong schema/handler could yield wrong hole spec; spiral type
                           blamed as “not working”
WHY HIGH-RISK              Documented live duplicate; first-match ownership unclear until witnessed
SELECTED / NOT SELECTED    SELECTED as S2
```

### C-03 — Polygon offset `.nc` dual mount

```text
CAPABILITY                 Polygon offset G-code
ENTRYPOINT                 POST /api/cam/polygon_offset.nc
EXPECTED IMPLEMENTATION    app.routers.polygon_offset_router.polygon_offset_nc
                           (stepover as 0–1 fraction; governed NC)
ALTERNATE IMPLEMENTATION(S)
                           app.cam.routers.utility.polygon_router.polygon_offset
                           → polygon_offset_n17.toolpath_offsets (stepover as mm)
CURRENT STATIC EVIDENCE    live_routes.json duplicates POST /api/cam/polygon_offset.nc
                           utility handler listed first
                           OffsetLabView.vue default stepover = 0.4 and posts this URL
                           preview URL /polygon_offset.preview is governed-only in live_routes
                           OVERLAP.md treats both as intentional parallel implementations
TEST LEVEL                 App TestClient test_polygon_offset_endpoint_smoke.py
                           (ambiguous which handler the test actually hits)
USER/MANUFACTURING CONSEQUENCE
                           Preview (fraction) vs NC (mm) could disagree; wrong stepover
                           in emitted G-code
WHY HIGH-RISK              Manufacturing G-code; FE schema matches governed, URL collides
                           with utility
SELECTED / NOT SELECTED    SELECTED as S3
```

### C-04 — DXF CurveMath legacy export vs governed translator

```text
CAPABILITY                 DXF export for CAD/CAM
ENTRYPOINT                 POST /exports/polyline_dxf
EXPECTED IMPLEMENTATION    app.routers.export.dxf_translate_router.translate_to_dxf
                           + dxf_compat dual-format (R12/R2000)
ALTERNATE IMPLEMENTATION(S)
                           app.routers.legacy_dxf_exports_router.export_polyline_dxf
                           try_build_with_ezdxf then ASCII R12 fallback
CURRENT STATIC EVIDENCE    curvemath_dxf.ts POSTs /exports/polyline_dxf
                           CLAUDE.md dual-format via dxf_compat for generators
                           legacy router docstring: migrated from ./server/...
TEST LEVEL                 App TestClient for translate; legacy path lighter
USER/MANUFACTURING CONSEQUENCE
                           Wrong DXF dialect / missing LWPOLYLINE / CAM reject
WHY HIGH-RISK              Customer-facing export; FE may never hit governed translator
SELECTED / NOT SELECTED    SELECTED as S4
```

### C-05 — Fret slots CAM preview vs ecosphere DXF

```text
CAPABILITY                 Fret slotting for CNC
ENTRYPOINT                 POST /api/cam/fret_slots/preview
EXPECTED IMPLEMENTATION    app.cam.routers.fret_slots_router.preview_fret_slots
                           → generate_fret_slot_toolpaths
ALTERNATE IMPLEMENTATION(S)
                           generate_fan_fret_cam (mode=fan_fret)
                           POST /api/v1/fretboard/dxf (ecosphere; FretSlottingView comments)
CURRENT STATIC EVIDENCE    fretSlotsCamStore.ts and instrumentGeometryStore.ts call preview
                           FretSlottingView.vue: former generate endpoints “never built”;
                           preview-only vs DXF dual stack
TEST LEVEL                 App TestClient test_cam_fret_slots_preview_smoke.py
USER/MANUFACTURING CONSEQUENCE
                           Operator expecting G-code may receive preview-only;
                           or DXF from a different stack than CAM preview
WHY HIGH-RISK              Manufacturing expectation vs preview surface; two product paths
SELECTED / NOT SELECTED    SELECTED as S5
```

### C-06 — ApertureWorkspace vs SpiralSoundholeDesigner

```text
CAPABILITY                 Spiral / aperture design UX
ENTRYPOINT                 UI /art-studio/aperture vs /calculators/acoustics/spiral-soundhole
EXPECTED IMPLEMENTATION    SpiralSoundholeDesigner.vue (canonical per FEATURE_PARITY)
ALTERNATE IMPLEMENTATION(S)
                           ApertureWorkspace.vue State 3 shell
CURRENT STATIC EVIDENCE    FEATURE_PARITY_MIGRATION_POLICY.md; toolRegistry canonical:false
TEST LEVEL                 Spiral geometry TestClient; shell mostly none
USER/MANUFACTURING CONSEQUENCE
                           Users in “new” workspace hit incomplete/shadowed APIs
WHY HIGH-RISK              Policy-flagged false consolidation
SELECTED / NOT SELECTED    NOT SELECTED — same soundhole subsystem as S2; avoid two
                           variants of one family. Runtime of S2 covers the shared API.
```

### C-07 — CAM drilling shim vs package aggregate

```text
CAPABILITY                 Peck / modal / pattern drilling G-code
ENTRYPOINT                 POST /api/cam/drilling/gcode (and siblings)
EXPECTED IMPLEMENTATION    app.cam.routers.drilling package inline aggregate
ALTERNATE IMPLEMENTATION(S)
                           deprecated drilling_consolidated_router.py facade
CURRENT STATIC EVIDENCE    WP-002-C3; shim retained import-compatible
TEST LEVEL                 App TestClient + retirement invariant tests
USER/MANUFACTURING CONSEQUENCE
                           Wrong aggregate if a caller imported the shim as the mount
WHY HIGH-RISK              Manufacturing G-code dual module story
SELECTED / NOT SELECTED    NOT SELECTED — third CAM G-code family after S1/S3;
                           static evidence already has retirement tests.
```

### C-08 — Feeds/speeds advisory vs governed expectation

```text
CAPABILITY                 Feeds & speeds recommendation
ENTRYPOINT                 POST /api/cam/opt/feeds-speeds
EXPECTED IMPLEMENTATION    optimization_router.calculate_feeds_speeds → cam_core.feeds_speeds
ALTERNATE IMPLEMENTATION(S)
                           RMOS advisory surfaces; authority registry surface_kind=advisory
CURRENT STATIC EVIDENCE    manufacturing_authority_registry tests
TEST LEVEL                 App TestClient smoke
USER/MANUFACTURING CONSEQUENCE
                           Advisory numbers treated as machine-ready
WHY HIGH-RISK              Authority misread, not clearly a wiring miss
SELECTED / NOT SELECTED    NOT SELECTED — closer to authority-label confusion than
                           execution-path divergence.
```

### C-09 — RMOS runs v1/v2 flag

```text
CAPABILITY                 Run persistence
ENTRYPOINT                 /api/rmos/runs* ; RMOS_RUNS_V2_ENABLED
EXPECTED IMPLEMENTATION    app.rmos.runs_v2 (default true)
ALTERNATE IMPLEMENTATION(S)
                           app.rmos.runs v1
CURRENT STATIC EVIDENCE    rmos/__init__.py flag branch; FE mixes paths
TEST LEVEL                 App TestClient for runs_v2
WHY HIGH-RISK              Env flag swap
SELECTED / NOT SELECTED    NOT SELECTED — excluded workstream (do not change RMOS);
                           flag-default true is expected, not a false-integration sample.
```

### C-10 — Photo vs blueprint vectorizer cluster

```text
CAPABILITY                 Image → vector / DXF
ENTRYPOINT                 POST /api/vectorizer/extract vs POST /api/blueprint/vectorize
EXPECTED IMPLEMENTATION    Blueprint: BlueprintOrchestrator + Phase3Vectorizer
ALTERNATE IMPLEMENTATION(S)
                           PhotoOrchestrator; phase2/phase3 extra routes
CURRENT STATIC EVIDENCE    VECTORIZER_DUPLICATION_MATRIX.md
WHY HIGH-RISK              Adjacent to seed failure; easy mis-attribution
SELECTED / NOT SELECTED    NOT SELECTED — do not re-investigate Vectorizer except as control
```

### C-11 — Nut-compensation dual mount

```text
CAPABILITY                 Nut compensation
ENTRYPOINT                 POST /api/instrument/nut-compensation
EXPECTED IMPLEMENTATION    split geometry nut router
ALTERNATE IMPLEMENTATION(S)
                           instrument_router legacy contract
CURRENT STATIC EVIDENCE    same collision set as soundhole
SELECTED / NOT SELECTED    NOT SELECTED — same router family as S2
```

### C-12 — IBG body solver export-blocked / session fallback

```text
CAPABILITY                 Body outline solve → DXF
ENTRYPOINT                 POST /api/body/solve-from-dxf
EXPECTED IMPLEMENTATION    body_solver_router → InstrumentBodyGenerator
ALTERNATE IMPLEMENTATION(S)
                           export hard-block; IBG_SESSION_STORE_ALLOW_FALLBACK
WHY HIGH-RISK              Looks like product failure; may be intended fail-closed
SELECTED / NOT SELECTED    NOT SELECTED — fail-closed may be correct; IW-04 covers
                           that classification discipline instead.
```

---

## Frozen five

| ID | Specimen | Subsystem | Failure shape |
| -- | -------- | --------- | ------------- |
| S1 | CAM SimLab FE URL | cam / frontend | FE path ≠ live mount |
| S2 | Soundhole POST dual mount | soundhole | ambiguous router ownership |
| S3 | Polygon offset NC collision | cam manufacturing G-code | colliding handlers + schema mismatch |
| S4 | CurveMath DXF legacy export | export | FE consumes legacy beside governed |
| S5 | Fret slots CAM preview | fretwork / cam | preview vs sibling DXF stack |

Diversity check: cam-sim, instrument-soundhole, cam-offset (different family than sim), export, fretwork. Not five variants of one router family.

Control (not in the five): IW-03 current Toolbox Vectorizer `POST /api/blueprint/vectorize`.
