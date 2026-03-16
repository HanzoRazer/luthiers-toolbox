# Router Consolidation Map

**Authority:** `cbsp21/cursorrules` + `docs/PLATFORM_ARCHITECTURE.md`  
**Purpose:** Categorized list of all router files in `services/api/app/` mapped to their consolidation target domain. No code changes — audit only.  
**Target:** Reduce router count from 159 → &lt;80.

---

## Consolidation target domains (from cursorrules)

| Target | Scope |
|--------|--------|
| **routers/cam/guitar/** | All guitar body/neck CAM operations |
| **routers/cam/acoustic/** | All acoustic body CAM operations |
| **routers/design/** | Design utilities (utilities_router.py absorbs all design utilities) |
| **routers/instruments/** | Instrument geometry endpoints |
| **routers/system/** | Materials, registry, health |
| **art_studio/api/** | All Art Studio routes |
| **rmos/api/** | All RMOS routes |
| **saw_lab/api/** | All Saw Lab routes |

---

## 1. Target: **routers/cam/guitar/** (guitar body/neck CAM)

| Router file | Notes |
|-------------|--------|
| `routers/cam/guitar/archtop_cam_router.py` | Already under cam/guitar |
| `routers/cam/guitar/om_cam_router.py` | Already under cam/guitar |
| `routers/cam/guitar/stratocaster_cam_router.py` | Already under cam/guitar |
| `routers/cam/guitar/guitar_models_consolidated_router.py` | Aggregates archtop/om/stratocaster |
| `routers/cam/guitar/registry_cam_router.py` | Registry CAM for all guitar models |
| `cam/headstock/router.py` | Headstock inlay CAM — **consolidate here** |

---

## 2. Target: **routers/cam/acoustic/** (acoustic body CAM)

| Router file | Notes |
|-------------|--------|
| *(none currently)* | Acoustic-specific CAM could absorb rosette/body from cam/routers if split. |
| `cam/routers/rosette/__init__.py` | Rosette CAM aggregator |
| `cam/routers/rosette/cam_router.py` | Rosette toolpath/CAM |
| `cam/routers/rosette/rosette_toolpath_router.py` | Rosette toolpaths |
| `cam/routers/rosette/rosette_jobs_router.py` | Rosette jobs |
| `cam/rosette/photo_batch_router.py` | Rosette photo batch — **candidate for cam/acoustic** if domain split |

---

## 3. Target: **routers/design/** (design utilities)

| Router file | Notes |
|-------------|--------|
| `routers/geometry/__init__.py` | Geometry package aggregator |
| `routers/geometry/import_router.py` | DXF/SVG/JSON import |
| `routers/geometry/export_router.py` | Export (DXF/SVG/G-code) |
| `routers/geometry/bundle_router.py` | Export bundle (multi-format) |
| `routers/polygon_offset_router.py` | Polygon offset — **design utility** |
| `routers/adaptive/__init__.py` | Adaptive pocketing aggregator |
| `routers/adaptive/plan_router.py` | Adaptive plan |
| `routers/adaptive/batch_router.py` | Adaptive batch export |
| `routers/adaptive/gcode_router.py` | Adaptive G-code |
| `routers/adaptive/dxf_router.py` | DXF → adaptive |
| `routers/dxf_preflight_router.py` | DXF preflight — design/CAM boundary |
| `routers/dxf_adaptive_consolidated_router.py` | DXF → adaptive workflow |
| `cam/routers/utility/polygon_router.py` | Polygon (no prefix) — **design utility** |

---

## 4. Target: **routers/instruments/** (instrument geometry)

| Router file | Notes |
|-------------|--------|
| `routers/instrument_router.py` | Instrument CRUD/design-state |
| `routers/neck_router.py` | Neck generator |
| `routers/neck/guitar_models_router.py` | Neck guitar models |
| `routers/neck/gcode_router.py` | Neck G-code |
| `routers/music/__init__.py` | Music aggregator |
| `routers/music/temperament_router.py` | Temperaments |
| `routers/instruments/__init__.py` | Instruments package |
| `routers/instruments/guitar/headstock_inlay_router.py` | Headstock inlay (geometry context) |
| `routers/instruments/guitar/pickup_calculator_router.py` | Pickup position calculator |
| `routers/instruments/guitar/electric_body_router.py` | Electric body outline generator |
| `routers/instruments/guitar/assets_router.py` | Guitar assets |
| `routers/instruments/guitar/registry_router.py` | Instrument registry (guitar) |
| `instrument_geometry/neck_taper/api_router.py` | Neck taper API |

---

## 5. Target: **routers/system/** (materials, registry, health)

| Router file | Notes |
|-------------|--------|
| `routers/health_router.py` | Health check |
| `routers/registry_router.py` | Data registry |
| `routers/material_router.py` | Material list/get/upsert (M.3 Energy model) |
| `routers/machines_consolidated_router.py` | Machine profiles + tools (also exposes cam_machines_router) |
| `routers/posts_consolidated_router.py` | Post processors — **config/system** |

---

## 6. Target: **art_studio/api/** (all Art Studio routes)

| Router file | Notes |
|-------------|--------|
| `routers/art/root_art_router.py` | Art Studio root |
| `art_studio/api/pattern_routes.py` | Patterns |
| `art_studio/api/generator_routes.py` | Generators |
| `art_studio/api/snapshot_routes.py` | Snapshots |
| `art_studio/api/rosette_jobs_routes.py` | Rosette jobs |
| `art_studio/api/rosette_compare_routes.py` | Rosette compare |
| `art_studio/api/rosette_snapshot_routes.py` | Rosette snapshots v2 |
| `art_studio/api/rosette_pattern_routes.py` | Rosette patterns |
| `art_studio/api/rosette_manufacturing_routes.py` | Rosette manufacturing |
| `art_studio/api/preview_routes.py` | Preview |
| `art_studio/api/rosette_designer_routes.py` | Rosette designer |
| `art_studio/api/inlay_pattern_routes.py` | Inlay patterns |
| `art_studio/bracing_router.py` | Bracing |
| `art_studio/inlay_router.py` | Inlay |
| `art_studio/preview_consolidated_router.py` | Preview consolidated (relief/vcarve sub-routers) |

---

## 7. Target: **rmos/api/** (all RMOS routes)

| Router file | Notes |
|-------------|--------|
| `rmos/api_routes.py` | Feasibility, BOM, toolpaths |
| `rmos/runs_v2/api_runs.py` | Runs CRUD |
| `rmos/runs_v2/advisory_router.py` | Advisory |
| `rmos/runs_v2/exports.py` | Operator pack exports |
| `rmos/runs_v2/router_query.py` | Runs v2 query |
| `rmos/api/rmos_runs_router.py` | Runs index |
| `rmos/api/logs_routes.py` | Logs v2 |
| `rmos/api/rmos_feasibility_router.py` | Feasibility |
| `rmos/runs_v2/api_runs_explain.py` | Run explain |
| `rmos/runs_v2/api_runs_variants.py` | Advisory variants, manufacturing candidates |
| `rmos/runs_v2/api_runs_advisory.py` | Runs advisory |
| `rmos/runs_v2/router_override.py` | Override |
| `rmos/runs_v2/api_global_attachments.py` | Attachments |
| `rmos/rosette_cam_router.py` | **STUB — remove** (per cursorrules) |
| `rmos/safety_router.py` | **STUB — remove** |
| `rmos/live_monitor_router.py` | **STUB — remove** |
| `rmos/mvp_router.py` | **STUB — remove** |
| `rmos/analytics/router.py` | RMOS analytics |
| `rmos/validation/router.py` | RMOS validation (30-run protocol) |
| `rmos/acoustics/router.py` | Acoustics (runs) |
| `rmos/acoustics/router_zip_export.py` | Acoustics zip export |
| `rmos/acoustics/router_import.py` | Acoustics import |
| `rmos/operations/router.py` | RMOS operations |
| `routers/strip_family_router.py` | Strip families — **consolidate into rmos/api** |

---

## 8. Target: **saw_lab/api/** (all Saw Lab routes)

| Router file | Notes |
|-------------|--------|
| `saw_lab/__init_router__.py` | Aggregator (batch, query, learning, metrics, gcode, toolpaths, execution, decision, compare) |
| `saw_lab/batch_router.py` | Batch |
| `saw_lab/batch_query_router.py` | Batch query |
| `saw_lab/batch_learning_router.py` | Learning events/overrides |
| `saw_lab/batch_metrics_router.py` | Batch metrics |
| `saw_lab/batch_gcode_router.py` | Batch G-code |
| `saw_lab/batch_metrics_execution_router.py` | Execution metrics |
| `saw_lab/batch_metrics_diff_router.py` | Metrics diff |
| `saw_lab/batch_metrics_decision_router.py` | Metrics decision |
| `saw_lab/metrics_lookup_consolidated_router.py` | Metrics lookup |
| `saw_lab/toolpaths_router.py` | Toolpaths |
| `saw_lab/execution_lifecycle_router.py` | Execution lifecycle (abort/complete/confirm/status) |
| `saw_lab/decision_router.py` | Decision intelligence |
| `saw_lab/compare_router.py` | Compare |
| `cam_core/api/saw_lab_router.py` | CAM core Saw Lab proxy — **consolidate into saw_lab/api or remove** |

---

## 9. CAM (other) — consolidate under **routers/cam/** where applicable

| Router file | Notes |
|-------------|--------|
| `cam/routers/__init__.py` | Exposes cam_router |
| `cam/routers/aggregator.py` | cam_router aggregator |
| `cam/routers/drilling/__init__.py` | Drilling aggregator |
| `cam/routers/drilling/drilling_consolidated_router.py` | Drilling consolidated |
| `cam/routers/drilling/drill_modal_router.py` | Modal drilling |
| `cam/routers/drilling/drill_pattern_router.py` | Drill patterns |
| `cam/routers/fret_slots/__init__.py` | Fret slots aggregator |
| `cam/routers/fret_slots_router.py` | **STUB — remove** unless wiring LP-GAP-04 |
| `cam/routers/relief/__init__.py` | Relief aggregator |
| `cam/routers/toolpath/__init__.py` | Toolpath aggregator |
| `cam/routers/toolpath/roughing_router.py` | Roughing |
| `cam/routers/toolpath/biarc_router.py` | Biarc |
| `cam/routers/toolpath/helical_router.py` | Helical |
| `cam/routers/toolpath/vcarve_router.py` | V-carve |
| `cam/routers/toolpath/relief_export_router.py` | Relief export |
| `cam/routers/vcarve/__init__.py` | V-carve aggregator |
| `cam/routers/vcarve/production_router.py` | V-carve production |
| `cam/routers/simulation/__init__.py` | Simulation aggregator |
| `cam/routers/simulation/simulation_consolidated_router.py` | Simulation |
| `cam/routers/export/__init__.py` | Export aggregator |
| `cam/routers/monitoring/__init__.py` | Monitoring aggregator |
| `cam/routers/monitoring/monitoring_consolidated_router.py` | Logs + metrics |
| `cam/routers/monitoring/metrics_thermal.py` | Thermal metrics |
| `cam/routers/utility/__init__.py` | Utility aggregator |
| `cam/routers/utility/utility_consolidated_router.py` | Utility consolidated |
| `cam/routers/utility/compare_router.py` | CAM compare |
| `cam/routers/utility/benchmark_router.py` | Benchmark |
| `cam/routers/utility/optimization_router.py` | Optimization |
| `cam/routers/utility/settings_router.py` | Settings |
| `cam/routers/utility/backup_router.py` | Backup |
| `cam/routers/utility/polygon_router.py` | Polygon (see design) |
| `cam/routers/risk/__init__.py` | Risk aggregator (wires cam_risk_router) |
| `cam/routers/profiling/__init__.py` | Profiling aggregator |
| `cam/routers/profiling/profile_router.py` | Profile router |
| `cam/routers/binding/__init__.py` | Binding aggregator |
| `cam/routers/binding/binding_router.py` | Binding |
| `cam/routers/pipeline/__init__.py` | Pipeline aggregator |
| `cam/routers/job_intelligence_router.py` | **STUB — remove** |
| `cam/routers/bridge_export_router.py` | **STUB — remove** |
| `routers/gcode_consolidated_router.py` | G-code consolidated |
| `routers/adaptive_preview_router.py` | Adaptive preview |
| `routers/cam_learn_router.py` | CAM learning |
| `routers/cam_risk_router.py` | CAM risk (wired to risk_reports_store) — **safety-critical; keep, consolidate under cam** |
| `routers/cam_pipeline_preset_run_router.py` | Pipeline preset run |
| `routers/cam_post_v155_router.py` | Post V155 (CRC, lead-in/out) |
| `routers/cam_relief_router.py` | Relief CAM (heightmap, roughing, finishing) |
| `routers/retract_router.py` | Retract router (legacy entry point) |
| `routers/retract/retract_consolidated_router.py` | Retract consolidated |
| `routers/retract/retract_apply_router.py` | Retract apply |
| `routers/retract/retract_gcode_router.py` | Retract G-code |
| `routers/retract/retract_info_router.py` | Retract info |
| `routers/probe/__init__.py` | Probe aggregator |
| `routers/probe/setup_router.py` | Probe setup |
| `routers/probe/pocket_router.py` | Pocket |
| `routers/probe/vise_square_router.py` | Vise square |
| `routers/probe/corner_router.py` | Corner |
| `routers/probe/surface_z_router.py` | Surface Z |
| `routers/probe/probe_consolidated_router.py` | Probe consolidated |
| `routers/bridge_presets_router.py` | Bridge presets |
| `routers/tooling_router.py` | Top-level tooling (delegates to tooling/) |
| `routers/tooling/__init__.py` | Tooling aggregator |
| `routers/tooling/tool_library_router.py` | Tool library |
| `routers/tooling/post_processor_router.py` | Post processor |
| `routers/simulation_consolidated_router.py` | Simulation (legacy mount at /api/cam/sim) |

---

## 10. Blueprint & DXF — **routers/blueprint/** / **routers/design/** boundary

| Router file | Notes |
|-------------|--------|
| `routers/blueprint/__init__.py` | Blueprint aggregator |
| `routers/blueprint/phase1_router.py` | Phase 1 |
| `routers/blueprint/phase2_router.py` | Phase 2 |
| `routers/blueprint/phase3_router.py` | Phase 3 |
| `routers/blueprint/phase4_router.py` | Phase 4 |
| `routers/blueprint/calibration_router.py` | Calibration |
| `routers/blueprint_cam/__init__.py` | Blueprint CAM aggregator |
| `routers/blueprint_cam/blueprint_cam_core_router.py` | Core (contour, preflight, pipeline_adapter, adaptive, router) |
| `routers/blueprint_cam/contour_reconstruction_router.py` | Contour reconstruction |
| `routers/blueprint_cam/preprocessor_router.py` | Preprocessor |
| `routers/blueprint_cam/geometry_correction_router.py` | Geometry correction |
| `routers/legacy_dxf_exports_router.py` | Legacy DXF exports |

---

## 11. Compare — **compare/routers/** (consolidated; keep as-is or map to design)

| Router file | Notes |
|-------------|--------|
| `compare/routers/__init__.py` | Exposes compare_router |
| `compare/routers/aggregator.py` | compare_router |
| `compare/routers/baselines/__init__.py` | Baselines |
| `compare/routers/risk/__init__.py` | Risk (aggregate, bucket detail, export) |
| `compare/routers/lab/__init__.py` | Compare Lab |

---

## 12. Core / Auth / Jobs / Governance / Vision / AI / Other (no single domain target)

| Router file | Notes |
|-------------|--------|
| `governance/governance_consolidated_router.py` | Meta/governance (/api/_meta) |
| `routers/auth_router.py` | Auth |
| `core/job_queue/router.py` | Job queue (/api/jobs) |
| `routers/health_router.py` | Health (also under system) |
| `vision/router.py` | Vision aggregator |
| `vision/segmentation_router.py` | Segmentation |
| `vision/generation_router.py` | Generation |
| `advisory/blob_router.py` | Advisory blobs |
| `ai_context_adapter/routes.py` | AI context |
| `websocket/router.py` | WebSocket |
| `workflow/sessions/routes.py` | Workflow sessions |
| `analyzer/router.py` | Analyzer (acoustic) |
| `agentic/router.py` | Agentic |

---

## 13. Business (keep as separate domain or fold into system)

| Router file | Notes |
|-------------|--------|
| `business/router.py` | Business aggregator |
| `business/estimator_router.py` | Estimator |
| `business/cogs_router.py` | COGS |
| `business/pricing_router.py` | Pricing |
| `business/breakeven_router.py` | Breakeven |
| `business/cashflow_router.py` | Cash flow |
| `business/bom_router.py` | BOM |
| `business/goals_router.py` | Goals |

---

## 14. Analytics / Experimental / Stubs / Projects

| Router file | Notes |
|-------------|--------|
| `routers/analytics_router.py` | Analytics aggregator |
| `routers/analytics_patterns_router.py` | Patterns |
| `routers/analytics_materials_router.py` | Materials |
| `routers/analytics_jobs_router.py` | Jobs |
| `routers/analytics_advanced_router.py` | Advanced |
| `routers/learned_overrides_router.py` | Learned overrides (feeds) |
| `routers/project_assets_router.py` | Project assets (stub) |
| `routers/misc_stub_routes.py` | Misc stubs |
| `_experimental/ai_cam_router.py` | **ARCHIVED** — experimental |
| `_experimental/joblog_router.py` | **ARCHIVED** — experimental |
| `_experimental/cnc_production/routers.py` | Experimental CNC |

---

## 15. API v1 / Legacy (if still mounted)

| Router file | Notes |
|-------------|--------|
| `api_v1/__init__.py` | API v1 aggregator |
| `api_v1/cam_operations.py` | CAM operations |
| `api_v1/acoustics.py` | Acoustics |
| `api_v1/jobs.py` | Jobs |
| `api_v1/instrument.py` | Instrument design |
| `api_v1/fret_math.py` | Fret math |
| `api_v1/rmos_safety.py` | RMOS safety |

---

## Stub routers to remove (per cursorrules)

Do not extend; remove from manifest when cleaning up:

| File | Note |
|------|------|
| `cam/routers/bridge_export_router.py` | Stub |
| `cam/routers/fret_slots_router.py` | Remove unless wiring LP-GAP-04 |
| `cam/routers/job_intelligence_router.py` | Stub |
| `rmos/live_monitor_router.py` | Stub |
| `rmos/mvp_router.py` | Stub |
| `rmos/rosette_cam_router.py` | Stub |
| `rmos/safety_router.py` | Stub |
| `services/risk_reports_store.py` | Not a router; compatibility layer for cam_risk_router — remove references if stub routes removed |

*(cursorrules also list: bridge_export_router, fret_slots_router, job_intelligence_router, live_monitor_router, mvp_router, rosette_cam_router, safety_router, risk_reports_store.)*

---

## Summary counts (approximate)

| Target domain | Router file count (incl. sub-routers) |
|---------------|----------------------------------------|
| routers/cam/guitar | 6 |
| routers/cam/acoustic | 0 (candidates: 5 rosette) |
| routers/design | 14 |
| routers/instruments | 13 |
| routers/system | 5 |
| art_studio/api | 15 |
| rmos/api | 24 |
| saw_lab/api | 15 |
| CAM (other) | 55+ |
| Blueprint/DXF | 12 |
| Compare | 5 |
| Core/Auth/Jobs/Governance/Vision/AI | 12 |
| Business | 7 |
| Analytics/Experimental/Stubs/Projects | 10 |
| API v1 | 6 |

**Total router files (defining APIRouter or routes):** ~160 (aligns with “159” in cursorrules). Consolidation into the eight target domains (and removing stubs) should move the count toward &lt;80.
