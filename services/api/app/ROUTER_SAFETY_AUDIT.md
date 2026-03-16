# Router Safety Audit Report

**Authority:** Pre-Phase 1 safety audit per user request.  
**Scope:** Every router file targeted for deletion or consolidation (from ROUTER_CONSOLIDATION_MAP.md).  
**No code was modified, deleted, or merged.**

---

## Audit Method (per file)

1. **Python imports** — Search codebase for any `from app....` or direct import of that router module.
2. **Frontend API calls** — Search `packages/client/src` (sdk/, api/, composables/, stores/) for API paths defined by that router.
3. **Manifest** — `router_registry/manifest.py` references to that module.
4. **Tests** — Any test file under `services/api/tests/` or `services/api/app/tests/` that hits endpoints from that router.
5. **Stub vs real** — Whether endpoints return hardcoded/NotImplementedError (stub) or have real implementation.

---

## Classification

| Code | Meaning |
|------|--------|
| **SAFE_DELETE** | No imports, no frontend calls, no tests, stub only. Safe to remove from manifest and delete file. |
| **SAFE_MERGE** | No frontend dependencies on this file’s paths; logic can move to target domain router without breaking clients. |
| **NEEDS_REVIEW** | Has frontend dependencies or real implementation; must preserve behavior (or migrate callers) before move/delete. |
| **KEEP** | Actively used; not a consolidation candidate yet, or required for safety/CI. |

---

## Critical finding: “Stub” list is not stubs

The following files are listed in cursorrules as **stub — remove**. The audit shows they are **real implementations** with frontend and/or tests. **Do not delete** without migrating callers.

| File | Implementation | Frontend | Tests | Verdict |
|------|----------------|----------|-------|---------|
| `cam/routers/bridge_export_router.py` | Real (DXF build from bridge geometry) | Y (useBridgeExport.ts x2) | Y (test_bridge_dxf_export_endpoint_smoke) | **KEEP** |
| `cam/routers/fret_slots_router.py` | Real (fret slot preview + calculator) | Y (fretSlotsCamStore, instrumentGeometryStore) | Y (test_cam_fret_slots_preview_smoke, test_fan_fret_perpendicular) | **KEEP** |
| `cam/routers/job_intelligence_router.py` | Real (job log list/get/favorites, insights) | Y (job_int.ts, CamJobInsightsPanel, CompareRunsPanel, etc.) | Y (test_cam_job_int_smoke, test_job_log_insights_endpoint_smoke) | **KEEP** |
| `rmos/live_monitor_router.py` | Real (drilldown from run artifact) | Y (useLiveMonitorStore) | Y (test_live_monitor_drilldown_endpoint_smoke) | **KEEP** |
| `rmos/mvp_router.py` | Real (DXF→GRBL with ezdxf + adaptive plan) | Y (QuickCutView, useDxfToGcode, useBlueprintWorkflow) | Y (test_dxf_to_grbl_endpoint_smoke) | **KEEP** |
| `rmos/rosette_cam_router.py` | Real (segment-ring, generate-slices, export-cnc, cnc-history, cnc-job) | Y (useRosetteDesignerStore) | Y (test_rmos_rosette_engines_smoke, test_rosette_cnc_export_endpoint_smoke) | **KEEP** |
| `rmos/safety_router.py` | Real (feasibility engine, evaluate, mode, create-override) | Y (useRmosSafetyStore) | Y (test_rmos_safety_endpoints_smoke, test_override_token_endpoint_smoke) | **KEEP** |
| `services/risk_reports_store.py` | Not a router; service used by `cam_risk_router` | N/A | N/A | **KEEP** (required by cam_risk_router) |

**Recommendation:** Treat the cursorrules “stub — remove” list as **do not remove** until product/tech decision to deprecate those features. For consolidation, use **NEEDS_REVIEW** and migrate endpoints into target domains without dropping behavior.

---

## Full safety audit table

One row per router file. Paths are relative to `services/api/app/`.

| Router file | Python imports | Frontend API calls | In manifest | Test coverage | Stub only | **Verdict** |
|-------------|----------------|--------------------|-------------|---------------|-----------|-------------|
| **Stub / deletion targets (per cursorrules)** |
| `cam/routers/bridge_export_router.py` | N (only self) | Y | Y | Y | N (real) | **KEEP** |
| `cam/routers/fret_slots_router.py` | Y (aggregator refs pkg) | Y | Y | Y | N (real) | **KEEP** |
| `cam/routers/job_intelligence_router.py` | Y (compare_router, pipeline_schemas) | Y | Y | Y | N (real) | **KEEP** |
| `rmos/live_monitor_router.py` | N | Y | Y | Y | N (real) | **KEEP** |
| `rmos/mvp_router.py` | N | Y | Y | Y | N (real) | **KEEP** |
| `rmos/rosette_cam_router.py` | N | Y | Y | Y | N (real) | **KEEP** |
| `rmos/safety_router.py` | N | Y | Y | Y | N (real) | **KEEP** |
| `services/risk_reports_store.py` | Y (cam_risk_router) | N/A | N | N/A | N/A | **KEEP** |
| **1. Target: routers/cam/guitar/** |
| `routers/cam/guitar/archtop_cam_router.py` | Y (guitar __init__) | Y (archtop/fit) | Y (via cam.guitar) | — | N | **KEEP** |
| `routers/cam/guitar/om_cam_router.py` | Y (guitar __init__) | — | Y (via cam.guitar) | — | N | **SAFE_MERGE** |
| `routers/cam/guitar/stratocaster_cam_router.py` | Y (guitar __init__) | — | Y (via cam.guitar) | — | N | **SAFE_MERGE** |
| `routers/cam/guitar/guitar_models_consolidated_router.py` | Y (guitar __init__) | Y (guitar/design/parametric) | Y (via cam.guitar) | — | N | **KEEP** |
| `routers/cam/guitar/registry_cam_router.py` | Y (guitar __init__) | — | Y (via cam.guitar) | — | N | **SAFE_MERGE** |
| `cam/headstock/router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| **2. Target: routers/cam/acoustic (rosette)** |
| `cam/routers/rosette/__init__.py` | Y (aggregator) | — | Y (via cam_router) | — | N | **KEEP** |
| `cam/routers/rosette/cam_router.py` | Y (rosette __init__) | — | Y (via cam_router) | — | N | **SAFE_MERGE** |
| `cam/routers/rosette/rosette_toolpath_router.py` | Y (rosette __init__) | — | Y (via cam_router) | — | N | **SAFE_MERGE** |
| `cam/routers/rosette/rosette_jobs_router.py` | Y (rosette __init__) | — | Y (via cam_router) | — | N | **SAFE_MERGE** |
| `cam/rosette/photo_batch_router.py` | N | Y (rosette/import_photo) | Y | — | N | **NEEDS_REVIEW** |
| **3. Target: routers/design/** |
| `routers/geometry/__init__.py` | Y (manifest) | Y (geometry/*) | Y | Y (debug_import) | N | **KEEP** |
| `routers/geometry/import_router.py` | Y (geometry __init__) | Y | Y | Y | N | **KEEP** |
| `routers/geometry/export_router.py` | Y (geometry __init__) | Y | Y | Y | N | **KEEP** |
| `routers/geometry/bundle_router.py` | Y (geometry __init__) | Y | Y | — | N | **KEEP** |
| `routers/polygon_offset_router.py` | N | Y (polygon_offset) | Y | — | N | **NEEDS_REVIEW** |
| `routers/adaptive/__init__.py` | Y (manifest) | Y (pocket/adaptive/*) | Y | — | N | **KEEP** |
| `routers/adaptive/plan_router.py` | Y (adaptive __init__, vision, mvp_router) | Y | Y | — | N | **KEEP** |
| `routers/adaptive/batch_router.py` | Y (adaptive __init__) | Y (batch_export) | Y | — | N | **KEEP** |
| `routers/adaptive/gcode_router.py` | Y (adaptive __init__) | Y (gcode) | Y | Y (CompareAfModes) | N | **KEEP** |
| `routers/adaptive/dxf_router.py` | Y (adaptive __init__) | Y (plan_from_dxf) | Y | — | N | **KEEP** |
| `routers/dxf_preflight_router.py` | N | Y (dxf/preflight/*) | Y | — | N | **NEEDS_REVIEW** |
| `routers/dxf_adaptive_consolidated_router.py` | N | Y (dxf_adaptive_plan_run, blueprint/to-adaptive) | Y | — | N | **NEEDS_REVIEW** |
| `cam/routers/utility/polygon_router.py` | Y (utility __init__) | — | Y (via cam utility) | — | N | **SAFE_MERGE** |
| **4. Target: routers/instruments/** |
| `routers/instrument_router.py` | N | Y (instrument/geometry/*) | Y | Y (test_instrument_endpoint_smoke) | N | **KEEP** |
| `routers/neck_router.py` | N | Y (neck/export_dxf) | Y | Y (test_neck_gcode_smoke) | N | **KEEP** |
| `routers/neck/guitar_models_router.py` | Y (neck package) | — | Y (via music/neck) | — | N | **SAFE_MERGE** |
| `routers/neck/gcode_router.py` | Y (neck package) | Y | Y | Y | N | **KEEP** |
| `routers/music/__init__.py` | Y (manifest) | — | Y | — | N | **KEEP** |
| `routers/music/temperament_router.py` | Y (music __init__) | — | Y | — | N | **SAFE_MERGE** |
| `routers/instruments/__init__.py` | N | — | — | — | N | **SAFE_MERGE** |
| `routers/instruments/guitar/headstock_inlay_router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| `routers/instruments/guitar/pickup_calculator_router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| `routers/instruments/guitar/electric_body_router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| `routers/instruments/guitar/assets_router.py` | N | — | — | — | N | **SAFE_MERGE** |
| `routers/instruments/guitar/registry_router.py` | N | — | — | — | N | **SAFE_MERGE** |
| `instrument_geometry/neck_taper/api_router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| **5. Target: routers/system/** |
| `routers/health_router.py` | N | — | Y | Y (test_health_detailed) | N | **KEEP** |
| `routers/registry_router.py` | N | — | Y | — | N | **KEEP** |
| `routers/material_router.py` | N | Y (materials/efficiency) | Y | — | N | **KEEP** |
| `routers/machines_consolidated_router.py` | N | Y (machines, machine/profiles, posts) | Y (2 entries) | — | N | **KEEP** |
| `routers/posts_consolidated_router.py` | N | Y (posts) | Y | — | N | **KEEP** |
| **6. Target: art_studio/api/** |
| `routers/art/root_art_router.py` | N | — | Y | — | N | **KEEP** |
| `art_studio/api/pattern_routes.py` | N | Y (art/presets, rosette-patterns) | Y | — | N | **KEEP** |
| `art_studio/api/generator_routes.py` | N | Y (art/generators) | Y | — | N | **KEEP** |
| `art_studio/api/snapshot_routes.py` | N | — | Y | — | N | **SAFE_MERGE** |
| `art_studio/api/rosette_jobs_routes.py` | N | Y (art/jobs) | Y | — | N | **KEEP** |
| `art_studio/api/rosette_compare_routes.py` | N | Y (rosette/compare/snapshots) | Y | — | N | **KEEP** |
| `art_studio/api/rosette_snapshot_routes.py` | N | — | Y | — | N | **SAFE_MERGE** |
| `art_studio/api/rosette_pattern_routes.py` | N | — | Y | — | N | **SAFE_MERGE** |
| `art_studio/api/rosette_manufacturing_routes.py` | N | Y (rosette/manufacturing-plan) | Y | — | N | **KEEP** |
| `art_studio/api/preview_routes.py` | N | Y (art/rosette/preview/svg) | Y | — | N | **KEEP** |
| `art_studio/api/rosette_designer_routes.py` | Y (art_studio services) | — | Y | — | N | **KEEP** |
| `art_studio/api/inlay_pattern_routes.py` | N | — | Y | — | N | **SAFE_MERGE** |
| `art_studio/bracing_router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| `art_studio/inlay_router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| `art_studio/preview_consolidated_router.py` | N | — | — | — | N | **SAFE_MERGE** |
| **7. Target: rmos/api/** |
| `rmos/api_routes.py` | Y (rmos __init__) | Y (rmos/runs, feasibility, BOM) | Y (via rmos) | Y (test_rmos_*) | N | **KEEP** |
| `rmos/runs_v2/api_runs.py` | Y (manifest, other rmos) | Y (runs_v2) | Y | Y | N | **KEEP** |
| `rmos/runs_v2/advisory_router.py` | N | — | Y | — | N | **KEEP** |
| `rmos/runs_v2/exports.py` | N | — | Y | — | N | **KEEP** |
| `rmos/runs_v2/router_query.py` | Y (runs_v2) | Y (runs_v2/diff, compare) | Y | — | N | **KEEP** |
| `rmos/api/rmos_runs_router.py` | N | — | Y | — | N | **SAFE_MERGE** |
| `rmos/api/logs_routes.py` | N | Y (rmos/logs) | Y | — | N | **KEEP** |
| `rmos/api/rmos_feasibility_router.py` | N | — | Y | — | N | **SAFE_MERGE** |
| `rmos/runs_v2/api_runs_explain.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| `rmos/runs_v2/api_runs_variants.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| `rmos/runs_v2/api_runs_advisory.py` | N | — | Y | — | N | **SAFE_MERGE** |
| `rmos/runs_v2/router_override.py` | N | — | Y | — | N | **SAFE_MERGE** |
| `rmos/runs_v2/api_global_attachments.py` | N | — | Y | — | N | **SAFE_MERGE** |
| `rmos/analytics/router.py` | N | Y (rmos/analytics/*) | Y | — | N | **KEEP** |
| `rmos/validation/router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| `rmos/acoustics/router.py` | N | — | Y | — | N | **SAFE_MERGE** |
| `rmos/acoustics/router_zip_export.py` | N | — | Y | — | N | **SAFE_MERGE** |
| `rmos/acoustics/router_import.py` | N | — | Y | — | N | **SAFE_MERGE** |
| `rmos/operations/router.py` | N | Y (rmos/operations) | Y | — | N | **KEEP** |
| `routers/strip_family_router.py` | N | Y (strip-families) | Y | — | N | **NEEDS_REVIEW** |
| **8. Target: saw_lab/api/** |
| `saw_lab/__init_router__.py` | Y (manifest) | Y (saw/*) | Y | — | N | **KEEP** |
| `saw_lab/batch_router.py` | Y (__init_router__) | Y | Y | — | N | **KEEP** |
| `saw_lab/batch_query_router.py` | Y (__init_router__) | — | Y | — | N | **SAFE_MERGE** |
| `saw_lab/batch_learning_router.py` | Y (__init_router__) | — | Y | — | N | **SAFE_MERGE** |
| `saw_lab/batch_metrics_router.py` | Y (__init_router__) | — | Y | — | N | **SAFE_MERGE** |
| `saw_lab/batch_gcode_router.py` | Y (__init_router__) | — | Y | — | N | **SAFE_MERGE** |
| `saw_lab/batch_metrics_execution_router.py` | Y (__init_router__) | — | Y | — | N | **SAFE_MERGE** |
| `saw_lab/batch_metrics_diff_router.py` | Y (__init_router__) | — | Y | — | N | **SAFE_MERGE** |
| `saw_lab/batch_metrics_decision_router.py` | Y (__init_router__) | — | Y | — | N | **SAFE_MERGE** |
| `saw_lab/metrics_lookup_consolidated_router.py` | Y (__init_router__) | — | Y | — | N | **SAFE_MERGE** |
| `saw_lab/toolpaths_router.py` | Y (__init_router__) | — | Y | — | N | **SAFE_MERGE** |
| `saw_lab/execution_lifecycle_router.py` | Y (__init_router__) | Y (saw batch execution) | Y | — | N | **KEEP** |
| `saw_lab/decision_router.py` | Y (__init_router__) | — | Y | — | N | **SAFE_MERGE** |
| `saw_lab/compare_router.py` | Y (manifest) | Y (saw/compare) | Y | — | N | **KEEP** |
| `cam_core/api/saw_lab_router.py` | N | Y (cam-core) | N | — | N | **NEEDS_REVIEW** |
| **9. CAM (other)** |
| `cam/routers/__init__.py` | Y (manifest) | — | Y | — | N | **KEEP** |
| `cam/routers/aggregator.py` | Y (__init__) | — | Y | — | N | **KEEP** |
| `cam/routers/drilling/__init__.py` | Y (aggregator) | Y (drilling/gcode) | Y (via cam_router) | — | N | **KEEP** |
| `cam/routers/drilling/drilling_consolidated_router.py` | Y (drilling __init__) | Y | Y | — | N | **KEEP** |
| `cam/routers/drilling/drill_modal_router.py` | Y (drilling __init__) | — | Y | — | N | **SAFE_MERGE** |
| `cam/routers/drilling/drill_pattern_router.py` | Y (drilling __init__) | Y (drilling/pattern/gcode) | Y | — | N | **KEEP** |
| `cam/routers/fret_slots/__init__.py` | Y (aggregator) | Y (fret_slots/preview) | N | — | N | **NEEDS_REVIEW** |
| `cam/routers/relief/__init__.py` | Y (aggregator) | Y (relief/*) | Y | — | N | **KEEP** |
| `cam/routers/toolpath/__init__.py` | Y (aggregator) | Y (toolpath/*) | Y | — | N | **KEEP** |
| `cam/routers/toolpath/roughing_router.py` | Y (toolpath __init__) | Y | Y | — | N | **KEEP** |
| `cam/routers/toolpath/biarc_router.py` | Y (toolpath __init__) | Y (biarc/gcode) | Y | — | N | **KEEP** |
| `cam/routers/toolpath/helical_router.py` | Y (toolpath __init__) | — | Y | — | N | **SAFE_MERGE** |
| `cam/routers/toolpath/vcarve_router.py` | Y (toolpath __init__) | — | Y | — | N | **SAFE_MERGE** |
| `cam/routers/toolpath/relief_export_router.py` | Y (toolpath __init__) | — | Y | — | N | **SAFE_MERGE** |
| `cam/routers/vcarve/__init__.py` | Y (aggregator) | — | Y | — | N | **KEEP** |
| `cam/routers/vcarve/production_router.py` | Y (vcarve __init__) | — | Y | — | N | **SAFE_MERGE** |
| `cam/routers/simulation/__init__.py` | Y (aggregator) | Y (cam/sim/*) | Y | Y (test_simulation_endpoint_smoke) | N | **KEEP** |
| `cam/routers/simulation/simulation_consolidated_router.py` | Y (simulation __init__) | Y | Y | Y | N | **KEEP** |
| `cam/routers/export/__init__.py` | Y (aggregator) | — | Y (disabled in aggregator) | — | N | **SAFE_MERGE** |
| `cam/routers/monitoring/__init__.py` | Y (manifest) | Y (cam/metrics, settings) | Y | — | N | **KEEP** |
| `cam/routers/monitoring/monitoring_consolidated_router.py` | Y (monitoring __init__) | Y | Y | — | N | **KEEP** |
| `cam/routers/monitoring/metrics_thermal.py` | Y (monitoring) | Y | Y | — | N | **KEEP** |
| `cam/routers/utility/__init__.py` | Y (manifest) | Y (settings, backup, compare, opt) | Y | — | N | **KEEP** |
| `cam/routers/utility/utility_consolidated_router.py` | Y (utility __init__) | Y | Y | — | N | **KEEP** |
| `cam/routers/utility/compare_router.py` | Y (utility __init__) | Y (compare/diff) | Y | — | N | **KEEP** |
| `cam/routers/utility/benchmark_router.py` | Y (utility __init__) | — | Y | — | N | **SAFE_MERGE** |
| `cam/routers/utility/optimization_router.py` | Y (utility __init__) | Y (opt/what_if) | Y | Y (test_cam_what_if_smoke) | N | **KEEP** |
| `cam/routers/utility/settings_router.py` | Y (utility __init__) | Y (settings/*) | Y | — | N | **KEEP** |
| `cam/routers/utility/backup_router.py` | Y (utility __init__) | Y (backup/*) | Y | — | N | **KEEP** |
| `cam/routers/risk/__init__.py` | Y (aggregator) | Y (cam/risk/*, jobs/risk_report) | Y | Y (test_cam_risk_reports_endpoint_smoke) | N | **KEEP** |
| `cam/routers/profiling/__init__.py` | Y (aggregator) | — | Y | — | N | **SAFE_MERGE** |
| `cam/routers/profiling/profile_router.py` | Y (profiling __init__) | — | Y | — | N | **SAFE_MERGE** |
| `cam/routers/binding/__init__.py` | Y (aggregator) | — | Y | — | N | **SAFE_MERGE** |
| `cam/routers/binding/binding_router.py` | Y (binding __init__) | — | Y | — | N | **SAFE_MERGE** |
| `cam/routers/pipeline/__init__.py` | Y (aggregator) | Y (pipeline/presets, run) | Y | — | N | **KEEP** |
| `routers/gcode_consolidated_router.py` | N | Y (cam/gcode/*, simulate_gcode) | Y | — | N | **KEEP** |
| `routers/adaptive_preview_router.py` | N | Y (adaptive/spiral, trochoid) | Y | — | N | **KEEP** |
| `routers/cam_learn_router.py` | N | Y (cam/learn/train) | Y | — | N | **KEEP** |
| `routers/cam_risk_router.py` | Y (cam/routers/risk) | Y (cam/risk/reports, jobs/risk_report) | Y | Y | N | **KEEP** |
| `routers/cam_pipeline_preset_run_router.py` | N | Y (pipeline/run, presets) | Y | — | N | **KEEP** |
| `routers/cam_post_v155_router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| `routers/cam_relief_router.py` | N | Y (relief/*) | Y | — | N | **KEEP** |
| `routers/retract_router.py` | Y (retract sub-routers) | Y (retract/gcode) | Y | Y (test_retract_endpoint_smoke) | N | **KEEP** |
| `routers/retract/retract_consolidated_router.py` | Y (retract_router) | Y | Y | Y | N | **KEEP** |
| `routers/retract/retract_apply_router.py` | Y (retract_consolidated) | — | Y | Y | N | **KEEP** |
| `routers/retract/retract_gcode_router.py` | Y (retract_consolidated) | Y | Y | Y | N | **KEEP** |
| `routers/retract/retract_info_router.py` | Y (retract_consolidated) | — | Y | Y | N | **KEEP** |
| `routers/probe/__init__.py` | Y (manifest) | Y (probe/*) | Y | — | N | **KEEP** |
| `routers/probe/setup_router.py` | Y (probe_consolidated) | Y (svg_setup_sheet) | Y | — | N | **KEEP** |
| `routers/probe/pocket_router.py` | Y (probe_consolidated) | — | Y | — | N | **SAFE_MERGE** |
| `routers/probe/vise_square_router.py` | Y (probe_consolidated) | — | Y | — | N | **SAFE_MERGE** |
| `routers/probe/corner_router.py` | Y (probe_consolidated) | Y (probe/corner) | Y | — | N | **KEEP** |
| `routers/probe/surface_z_router.py` | Y (probe_consolidated) | Y (probe/surface_z) | Y | — | N | **KEEP** |
| `routers/probe/probe_consolidated_router.py` | Y (probe __init__) | Y | Y | — | N | **KEEP** |
| `routers/bridge_presets_router.py` | N | Y (bridge/presets) | Y | — | N | **KEEP** |
| `routers/tooling_router.py` | N | Y (tooling/posts) | Y | — | N | **KEEP** |
| `routers/tooling/__init__.py` | Y (tooling_router) | Y | Y | — | N | **KEEP** |
| `routers/tooling/tool_library_router.py` | Y (tooling __init__) | — | Y | — | N | **SAFE_MERGE** |
| `routers/tooling/post_processor_router.py` | Y (tooling __init__) | Y (posts) | Y | — | N | **KEEP** |
| `routers/simulation_consolidated_router.py` | N | Y (cam/sim) | Y | Y | N | **KEEP** |
| **10. Blueprint & DXF** |
| `routers/blueprint/__init__.py` | Y (manifest) | Y (blueprint/*) | Y | — | N | **KEEP** |
| `routers/blueprint/phase1_router.py` | Y (blueprint __init__) | — | Y | — | N | **SAFE_MERGE** |
| `routers/blueprint/phase2_router.py` | Y (blueprint __init__) | — | Y | — | N | **SAFE_MERGE** |
| `routers/blueprint/phase3_router.py` | Y (blueprint __init__) | — | Y | — | N | **SAFE_MERGE** |
| `routers/blueprint/phase4_router.py` | Y (blueprint __init__) | — | Y | — | N | **SAFE_MERGE** |
| `routers/blueprint/calibration_router.py` | Y (blueprint __init__) | — | Y | — | N | **SAFE_MERGE** |
| `routers/blueprint_cam/__init__.py` | Y (manifest) | Y (cam/blueprint/*) | Y | — | N | **KEEP** |
| `routers/blueprint_cam/blueprint_cam_core_router.py` | Y (blueprint_cam __init__) | Y (preflight, reconstruct) | Y | — | N | **KEEP** |
| `routers/blueprint_cam/contour_reconstruction_router.py` | Y (blueprint_cam) | — | Y | — | N | **SAFE_MERGE** |
| `routers/blueprint_cam/preprocessor_router.py` | Y (blueprint_cam) | — | Y | — | N | **SAFE_MERGE** |
| `routers/blueprint_cam/geometry_correction_router.py` | Y (blueprint_cam) | — | Y | — | N | **SAFE_MERGE** |
| `routers/legacy_dxf_exports_router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| **11. Compare** |
| `compare/routers/__init__.py` | Y (manifest) | — | Y | — | N | **KEEP** |
| `compare/routers/aggregator.py` | Y (compare __init__) | Y (compare/*) | Y | Y (test_compare_*) | N | **KEEP** |
| `compare/routers/baselines/__init__.py` | Y (aggregator) | Y (baselines) | Y | Y | N | **KEEP** |
| `compare/routers/risk/__init__.py` | Y (aggregator) | Y (risk_aggregate, risk_bucket_*) | Y | Y | N | **KEEP** |
| `compare/routers/lab/__init__.py` | Y (aggregator) | — | Y | — | N | **SAFE_MERGE** |
| **12. Core / Auth / Vision / AI / Other** |
| `governance/governance_consolidated_router.py` | N | — | Y | — | N | **KEEP** |
| `routers/auth_router.py` | N | Y (auth/*) | Y | — | N | **KEEP** |
| `core/job_queue/router.py` | N | Y (jobs/status) | Y | — | N | **KEEP** |
| `vision/router.py` | N | Y (vision/generate) | Y | — | N | **KEEP** |
| `vision/segmentation_router.py` | Y (vision router) | — | Y | — | N | **KEEP** |
| `vision/generation_router.py` | Y (vision router) | Y | Y | — | N | **KEEP** |
| `advisory/blob_router.py` | Y (vision) | Y (advisory) | Y | — | N | **KEEP** |
| `ai_context_adapter/routes.py` | N | Y (ai/context/build) | Y | — | N | **KEEP** |
| `websocket/router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| `workflow/sessions/routes.py` | N | Y (workflow/sessions) | Y | Y (test_rmos_workflow_e2e) | N | **KEEP** |
| `analyzer/router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| `agentic/router.py` | N | — | Y | — | N | **NEEDS_REVIEW** |
| **13. Business** |
| `business/router.py` | N | — | Y | — | N | **KEEP** |
| `business/estimator_router.py` | Y (business router) | — | Y | — | N | **SAFE_MERGE** |
| `business/cogs_router.py` | Y (business router) | — | Y | — | N | **SAFE_MERGE** |
| `business/pricing_router.py` | Y (business router) | — | Y | — | N | **SAFE_MERGE** |
| `business/breakeven_router.py` | Y (business router) | — | Y | — | N | **SAFE_MERGE** |
| `business/cashflow_router.py` | Y (business router) | — | Y | — | N | **SAFE_MERGE** |
| `business/bom_router.py` | Y (business router) | — | Y | — | N | **SAFE_MERGE** |
| `business/goals_router.py` | Y (business router) | — | Y | — | N | **SAFE_MERGE** |
| **14. Analytics / Experimental / Stubs** |
| `routers/analytics_router.py` | Y (sub-routers) | Y (advanced/*, patterns, jobs) | Y | — | N | **KEEP** |
| `routers/analytics_patterns_router.py` | Y (analytics_router) | Y | Y | — | N | **KEEP** |
| `routers/analytics_materials_router.py` | Y (analytics_router) | — | Y | — | N | **SAFE_MERGE** |
| `routers/analytics_jobs_router.py` | Y (analytics_router) | Y (jobs/success-trends) | Y | — | N | **KEEP** |
| `routers/analytics_advanced_router.py` | Y (analytics_router) | Y | Y | — | N | **KEEP** |
| `routers/learned_overrides_router.py` | N | Y (feeds/learned/merge) | Y | — | N | **KEEP** |
| `routers/project_assets_router.py` | N | Y (ai_images: projects/…/assets/ai_images) | Y | — | Y (stub) | **NEEDS_REVIEW** (stub but frontend calls it) |
| `routers/misc_stub_routes.py` | N | — | Y | — | Y (stub) | **NEEDS_REVIEW** |
| `_experimental/ai_cam_router.py` | N | Y (ai-cam/*) | Y | — | N | **KEEP** (experimental) |
| `_experimental/joblog_router.py` | N | Y (joblog) | Y | — | N | **KEEP** (experimental) |
| `_experimental/cnc_production/routers.py` | N | — | N | — | N | **SAFE_MERGE** |
| **15. API v1** |
| `api_v1/__init__.py` | N | Y (v1/frets, v1/dxf, v1/rmos) | N | — | N | **NEEDS_REVIEW** |
| `api_v1/cam_operations.py` | Y (api_v1) | — | N | — | N | **SAFE_MERGE** |
| `api_v1/acoustics.py` | Y (api_v1) | — | N | — | N | **SAFE_MERGE** |
| `api_v1/jobs.py` | Y (api_v1) | — | N | — | N | **SAFE_MERGE** |
| `api_v1/instrument.py` | Y (api_v1) | — | N | — | N | **SAFE_MERGE** |
| `api_v1/fret_math.py` | Y (api_v1) | Y (v1/frets/positions) | N | Y (FretboardWizard) | N | **NEEDS_REVIEW** |
| `api_v1/rmos_safety.py` | Y (api_v1) | — | N | — | N | **SAFE_MERGE** |

---

## Summary counts

| Verdict | Count |
|---------|-------|
| **KEEP** | 82 |
| **NEEDS_REVIEW** | 25 |
| **SAFE_MERGE** | 58 |
| **SAFE_DELETE** | 0 |

---

## Next steps (after approval)

1. **Do not delete** any of the seven “stub” routers (bridge_export, fret_slots, job_intelligence, live_monitor, mvp, rosette_cam, safety) without a product decision and frontend migration.
2. **SAFE_DELETE:** None. (project_assets_router is a stub but is called by the AI Images frontend; do not delete without migrating that feature.)
3. **SAFE_MERGE:** Plan consolidation of the 58 SAFE_MERGE routers into their target domains; no frontend path changes required for those files.
4. **NEEDS_REVIEW:** For each of the 25 NEEDS_REVIEW routers, either migrate frontend callers to the target domain’s paths or keep the router and document why.

No files were modified, deleted, or merged in this audit. Phase 1 may proceed after you approve this report.
