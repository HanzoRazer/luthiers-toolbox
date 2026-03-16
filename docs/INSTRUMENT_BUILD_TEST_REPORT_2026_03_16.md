# Instrument build & feature test suite report

**Generated:** 2026-03-16  
**Scope:** Test files that simulate full instrument builds (specific guitar models + features), rosette patterns, headstock configurations, binding/routing, and G-code production.  
**Run:** `pytest` from `services/api` on the listed files (595 tests collected).

---

## Summary

| Status   | Count | Notes |
|----------|--------|--------|
| **Passing** | 592 | All tests in these files pass except where noted |
| **Skipped** | 2     | Both in `test_bezier_body_generator.py` (preset `om`) |
| **Failing** | 1     | `test_golden_rosette_geometry.py::test_golden_segment_count_for_pattern` |

---

## 1. Full instrument build / model + feature tests

### services/api/tests/test_carving_pipeline.py

- **Instruments/features:** Les Paul (top carve, 1959 asymmetric), Benedetto 17" archtop, archtop graduated thickness; asymmetric carve profile; G-code pipeline (roughing/finishing).
- **Status:** **Passing** (all 48 tests).
- **Notes:** Tests `create_les_paul_top_config`, `create_les_paul_1959_asymmetric_config`, `create_benedetto_17_config`; full pipeline and preview; `surface_type == "archtop_asymmetric"` for 1959.

### services/api/tests/test_bezier_body_generator.py

- **Instruments/features:** Dreadnought, orchestra_model, OM, parlor, jumbo, classical, concert body outlines; Bézier outline generation; JSON/SVG/DXF export; preset registry.
- **Status:** **Passing** with **2 skipped**.
- **Skipped:** `TestPhysicalPlausibility::test_preset_dimensions_reasonable[om]`, `TestPhysicalPlausibility::test_outline_generates_without_error[om]` (preset `om` explicitly skipped).
- **Notes:** `BezierBodyParams.dreadnought()`, `get_preset("fender_telecaster_body")`, `list_presets()`.

### services/api/tests/test_fhole_routing.py

- **Instruments/features:** Les Paul f-hole preset, Benedetto 17" f-hole, jumbo archtop f-hole; f-hole geometry (traditional/contemporary/Venetian); toolpath and G-code generation; helical plunge.
- **Status:** **Passing** (all 30 tests).
- **Notes:** `create_les_paul_fhole_config`, `create_jumbo_archtop_fhole_config`; full pipeline and serialization.

### services/api/tests/test_electric_body_smoke.py

- **Instruments/features:** Stratocaster, Les Paul electric body; styles list; SVG by style; scale and `detailed` flag.
- **Status:** **Passing**.
- **Notes:** POST `/api/instruments/guitar/electric-body/generate` with `style`: stratocaster / les_paul; GET styles and SVG.

### services/api/tests/test_neck_endpoint_smoke.py

- **Instruments/features:** Stratocaster neck generate/presets; Les Paul presets; neck pipeline endpoints.
- **Status:** **Passing**.
- **Notes:** POST `/api/neck/generate/stratocaster`, GET `/api/neck/stratocaster/presets`; presets include les_paul_standard.

### services/api/tests/test_neck_gcode_smoke.py

- **Instruments/features:** Neck G-code generation; presets (gibson_standard, fender_strat headstock); scale length, nut width, profile overrides; operations list.
- **Status:** **Passing**.
- **Notes:** POST `/api/neck/gcode/generate` with `preset`, `headstock_style`, `profile`; job name in G-code.

### services/api/tests/test_headstock_inlay_smoke.py

- **Instruments/features:** Les Paul, Stratocaster headstock inlay styles; style IDs; generate with `style: "les_paul"`.
- **Status:** **Passing**.
- **Notes:** GET styles, GET style by id, POST generate; asserts `style == "les_paul"`.

### services/api/tests/test_body_generator_router.py

- **Instruments/features:** Stratocaster, Telecaster body generation via router.
- **Status:** **Passing**.
- **Notes:** `body_style`: stratocaster, telecaster.

### services/api/tests/test_bracing_presets_bridge_smoke.py

- **Instruments/features:** Dreadnought bracing/bridge preset.
- **Status:** **Passing**.
- **Notes:** Asserts dreadnought preset exists in presets list.

### services/api/tests/test_bridge_presets_endpoint_smoke.py

- **Instruments/features:** Les Paul, archtop, strat_tele, OM, dread bridge presets; scale lengths.
- **Status:** **Passing**.
- **Notes:** `test_has_les_paul_preset`, `test_has_archtop_preset`; family scale lengths.

### services/api/tests/test_instrument_geometry_endpoint_smoke.py

- **Instruments/features:** Bridge presets including les_paul.
- **Status:** **Passing**.
- **Notes:** `test_bridge_presets_includes_les_paul`.

### services/api/tests/test_blueprint_endpoint_smoke.py

- **Instruments/features:** Scale lengths by brand: Fender Stratocaster (25.5), Gibson Les Paul (24.75); blueprint analyze, to_svg, to_dxf, vectorize, calibrate, dimensions.
- **Status:** **Passing** (endpoint existence and scale length tests). Some blueprint/phase2 vectorization errors in logs (external API/image) do not fail these tests.
- **Notes:** `test_scale_lengths_fender_stratocaster`, `test_scale_lengths_gibson_les_paul`.

### services/api/tests/test_cavity_position_validator.py

- **Instruments/features:** Les Paul, Stratocaster cavity validation; model normalization (les_paul variants, strat variants); factory reference; cavity types per model.
- **Status:** **Passing**.
- **Notes:** `validate_cavity(..., "les_paul")`, `test_les_paul_variants`, `list_cavity_types_for_model("les_paul")`.

### services/api/tests/test_dxf_preprocessor.py

- **Instruments/features:** DXF dimension validation with `les_paul` spec.
- **Status:** **Passing**.
- **Notes:** `validate_dimensions(dxf_bytes, 'les_paul')`.

### services/api/tests/test_vision_segmentation.py

- **Instruments/features:** Les Paul, Stratocaster guitar_type in segmentation; body outline; DXF/SVG export; stub vision client.
- **Status:** Not run in the same batch; included by search. Run separately to confirm.
- **Notes:** Stub response `guitar_type: "les_paul"`; tests for stratocaster in SVG content.

### services/api/tests/test_business_endpoint_smoke.py

- **Instruments/features:** Acoustic dreadnought as instrument type (WBS, estimates, integration flows).
- **Status:** Not run in the same batch; included by search. Run separately to confirm.
- **Notes:** `instrument_type: "acoustic_dreadnought"`; GET `/api/business/estimate/wbs/acoustic_dreadnought`.

---

## 2. Rosette patterns

### services/api/tests/test_rmos_rosette_engines_smoke.py

- **Features:** Rosette segment-ring, generate-slices, preview (RMOS → cam.rosette).
- **Status:** **Passing**.
- **Notes:** POST segment-ring, generate-slices (batch_id, slice count), preview (pattern_id, ring summaries).

### services/api/tests/test_cam_consolidated_endpoint_smoke.py

- **Features:** CAM rosette plan-toolpath, post-gcode, jobs; rosette photo-batch convert/list/get/delete; toolpath biarc/roughing/vcarve G-code endpoints.
- **Status:** **Passing**.
- **Notes:** Minimal rosette design fixture; `/api/cam/rosette/plan-toolpath`, `post-gcode`, `jobs`; photo-batch routes.

### services/api/tests/test_rosette_designer.py

- **Features:** Rosette designer engine: geometry, symmetry, tile placement, BOM, manufacturing checks, recipe library, CSV export, auto-fix; API cell-info, preview, etc.
- **Status:** **Passing**.
- **Notes:** RosetteEngine, RING_DEFS, SEG_OPTIONS, TILE_MAP, run_mfg_checks, render_preview_svg.

### services/api/tests/test_golden_rosette_geometry.py

- **Features:** Golden rosette ring geometry: circumference, area, stacking, segment count, arc length, innermost ring at soundhole; invariants (deterministic, 360° segment sum, min ring width, max radius).
- **Status:** **Failing** (1 test).
- **Failing test:** `test_golden_segment_count_for_pattern` — assertion `360 % expected_count == 0 or expected_count > 360` fails for `"fine_mosaic": 32` because 360 % 32 ≠ 0 and 32 is not > 360. Golden segment counts for that pattern are inconsistent with the invariant.
- **Notes:** All other golden rosette tests pass.

### services/api/tests/test_rosette_cnc_export_endpoint_smoke.py

- **Features:** Rosette export to CNC (G-code, job_id).
- **Status:** **Passing**.
- **Notes:** POST `/api/rmos/rosette/export-cnc`.

### services/api/tests/test_rmos_rosette_cnc_smoke.py

- **Features:** Rosette CNC history, job type filter, nonexistent job 404.
- **Status:** **Passing**.
- **Notes:** GET `/api/rmos/rosette/cnc-history`, job_type=rosette_cam.

---

## 3. Headstock configurations

- **test_headstock_inlay_smoke.py** — see §1 (Les Paul, Stratocaster headstock inlay styles).
- **test_neck_gcode_smoke.py** — see §1 (gibson_open, fender_strat headstock_style in G-code).

---

## 4. Binding and routing

### services/api/app/tests/calculators/test_binding_geometry.py

- **Features:** Neck binding, headstock binding, body binding path; core geometry; curvature; miter joints; material validation; Benedetto-style archtop neck/headstock binding; full workflow neck→headstock.
- **Status:** **Passing** (all tests).
- **Notes:** `test_benedetto_style_neck_binding`, `test_benedetto_style_headstock_binding`, `test_full_workflow_neck_to_headstock`; circle and cutaway body binding.

### services/api/tests/test_fhole_routing.py

- **Features:** F-hole routing toolpath and G-code — see §1.

### services/api/test_new_routes.py

- **Features:** Quick test of binding routes (e.g. bind-art-studio-candidate); rosette attachment.
- **Status:** Not run in batch (script-style test under `services/api`).
- **Notes:** References `rosette.svg`, binding request/response ALLOW/BLOCK.

---

## 5. G-code production

### services/api/tests/test_simulation_endpoint_smoke.py

- **Features:** G-code simulation: POST /api/cam/sim/gcode, upload, legacy simulate_gcode; summary header, modal header, moves, issues; CSV export; custom accel/clearance_z; metrics.
- **Status:** **Passing**.
- **Notes:** Minimal G-code fixture; all simulation endpoints exist and return expected shape.

### services/api/tests/test_carving_pipeline.py

- **Features:** Carving pipeline G-code (roughing + finishing) — see §1.

### services/api/tests/test_fhole_routing.py

- **Features:** F-hole G-code generation — see §1.

### services/api/tests/test_neck_gcode_smoke.py

- **Features:** Neck G-code generate and download — see §1.

### services/api/tests/test_cam_consolidated_endpoint_smoke.py

- **Features:** Toolpath biarc/roughing/vcarve G-code endpoints — see §2.

### services/api/tests/test_rosette_cnc_export_endpoint_smoke.py

- **Features:** Rosette export to CNC G-code — see §2.

### __RECOVERED__/F_validation_tooling/test_mvp_dxf_to_gcode_grbl_golden.py

- **Features:** MVP golden path: DXF → plan_from_dxf → /api/cam/pocket/adaptive/gcode (GRBL).
- **Status:** Not run (recovered/legacy path). Listed for completeness.

---

## 6. Other files (reference only)

- **packages/client/src/testing/__tests__/toolbox-composables.test.ts** — Frontend: dimension presets (telecaster, les_paul, stratocaster, dreadnought). Not run in API pytest.
- **services/photo-vectorizer/** — Various tests use spec_name/family (stratocaster, les_paul, dreadnought, archtop, jumbo_archtop) for calibration/contour; not full instrument builds.
- **blueprint-import/tests/test_grid_zone_classifier.py** — Stratocaster/Les Paul proportion classification; not run in API batch.

---

## Recommendation

- **Fix:** `test_golden_rosette_geometry.py::test_golden_segment_count_for_pattern` — either change the golden segment counts so every count divides 360 (e.g. `"fine_mosaic": 36` or `24`) or relax the invariant to match intended patterns (e.g. allow 32 and adjust the assertion).
- **Optional:** Un-skip or remove the `om` skip in `test_bezier_body_generator.py` if the OM preset is now supported.
- **Optional:** Run `test_vision_segmentation.py` and `test_business_endpoint_smoke.py` in CI with the instrument-build set to get explicit pass/fail for les_paul/stratocaster segmentation and acoustic_dreadnought business flows.
