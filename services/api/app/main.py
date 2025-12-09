from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.cam_sim_router import router as sim_router
from .routers.feeds_router import router as feeds_router
from .routers.geometry_router import router as geometry_router
from .routers.tooling_router import router as tooling_router
from .routers.adaptive_router import router as adaptive_router
from .routers.machine_router import router as machine_router
from .routers.cam_opt_router import router as cam_opt_router  # M.2
from .routers.material_router import router as material_router  # M.3
from .routers.cam_metrics_router import router as cam_metrics_router  # M.3
from .routers.cam_logs_router import router as cam_logs_router  # M.4
from .routers.cam_learn_router import router as cam_learn_router  # M.4
from .routers.health_router import router as health_router

# RMOS 2.0 — Rosette Manufacturing Orchestration System
try:
    from .rmos import rmos_router
except Exception as e:
    print(f"Warning: Could not load RMOS 2.0 router: {e}")
    rmos_router = None

# Phase B (Wave 17→18): RMOS Context Management
try:
    from .rmos.context_router import router as rmos_context_router
except Exception as e:
    print(f"Warning: Could not load RMOS context router: {e}")
    rmos_context_router = None

# Phase D (Wave 18): Feasibility Fusion
try:
    from .rmos.feasibility_router import router as rmos_feasibility_router
except Exception as e:
    print(f"Warning: Could not load RMOS feasibility router: {e}")
    rmos_feasibility_router = None

# Phase E (Wave 17→18): CAM Preview Integration
try:
    from .cam.cam_preview_router import router as cam_preview_router
except Exception as e:
    print(f"Warning: Could not load CAM preview router: {e}")
    cam_preview_router = None

# Directional Workflow 2.0 — Art Studio integration
try:
    from .workflow.mode_preview_routes import router as workflow_router
except Exception as e:
    print(f"Warning: Could not load Directional Workflow router: {e}")
    workflow_router = None

# RMOS Constraint Search API
try:
    from .rmos.api.constraint_search_routes import router as rmos_constraint_router
except Exception as e:
    print(f"Warning: Could not load RMOS constraint search router: {e}")
    rmos_constraint_router = None

# RMOS Logs API
try:
    from .rmos.api.log_routes import router as rmos_log_router
except Exception as e:
    print(f"Warning: Could not load RMOS log router: {e}")
    rmos_log_router = None

# RMOS AI Logs Viewer API
try:
    from .rmos.api_logs_viewer import router as rmos_ai_logs_router
except Exception as e:
    print(f"Warning: Could not load RMOS AI logs router: {e}")
    rmos_ai_logs_router = None

# RMOS AI Constraint Profiles API
try:
    from .rmos.api_constraint_profiles import router as rmos_constraint_profiles_router
except Exception as e:
    print(f"Warning: Could not load RMOS constraint profiles router: {e}")
    rmos_constraint_profiles_router = None

# RMOS AI Generator Snapshots API
try:
    from .rmos.api_ai_snapshots import router as rmos_ai_snapshots_router
except Exception as e:
    print(f"Warning: Could not load RMOS AI snapshots router: {e}")
    rmos_ai_snapshots_router = None

# B22: Compare Mode Diff API
try:
    from .routers.cam_compare_diff_router import router as cam_compare_diff_router
except Exception as e:
    print(f"Warning: Could not load cam_compare_diff_router: {e}")
    cam_compare_diff_router = None

try:
    from .cnc_production import routers as cnc_production_routers
except Exception as e:  # pragma: no cover - optional CNC Production namespace
    print(f"Warning: Could not load CNC Production routers: {e}")
    cnc_production_routers = None

try:
    from .routers.art.root_art_router import router as art_root_router
except Exception as e:  # pragma: no cover - optional Art namespace
    print(f"Warning: Could not load Art Studio routers: {e}")
    art_root_router = None

# Art Studio — Bracing Calculator API
try:
    from .art_studio.bracing_router import router as art_studio_bracing_router
except Exception as e:
    print(f"Warning: Could not load Art Studio bracing router: {e}")
    art_studio_bracing_router = None

# Art Studio — Rosette Calculator API
try:
    from .art_studio.rosette_router import router as art_studio_rosette_router_new
except Exception as e:
    print(f"Warning: Could not load Art Studio rosette router: {e}")
    art_studio_rosette_router_new = None

# Art Studio — Inlay Calculator API
try:
    from .art_studio.inlay_router import router as art_studio_inlay_router
except Exception as e:
    print(f"Warning: Could not load Art Studio inlay router: {e}")
    art_studio_inlay_router = None

# Art Studio — VCarve Router (Wave 1)
try:
    from .art_studio.vcarve_router import router as art_studio_vcarve_router
except Exception as e:
    print(f"Warning: Could not load Art Studio vcarve router: {e}")
    art_studio_vcarve_router = None

# Art Studio — Relief Router (Wave 3)
try:
    from .art_studio.relief_router import router as art_studio_relief_router
except Exception as e:
    print(f"Warning: Could not load Art Studio relief router: {e}")
    art_studio_relief_router = None

# Wave 7 — Instrument Geometry Router
try:
    from .routers.instrument_router import router as instrument_router
except Exception as e:
    print(f"Warning: Could not load instrument_router: {e}")
    instrument_router = None

# Wave 8 — Calculators Router (Unified chipload/heat/deflection)
try:
    from .routers.calculators_router import router as calculators_router
except Exception as e:
    print(f"Warning: Could not load calculators_router: {e}")
    calculators_router = None

# Wave 11 — AI-CAM Advisor + G-Code Explainer 2.0
try:
    from .routers.ai_cam_router import router as ai_cam_router
except Exception as e:
    print(f"Warning: Could not load ai_cam_router: {e}")
    ai_cam_router = None

# Wave 14 — Instrument Geometry Core (19-model expanded architecture)
try:
    from .routers.instrument_geometry_router import router as instrument_geometry_router
except Exception as e:
    print(f"Warning: Could not load instrument_geometry_router: {e}")
    instrument_geometry_router = None

# Wave 17 — Instrument Geometry: Neck Taper Suite
try:
    from .instrument_geometry.neck_taper.api_router import router as neck_taper_router
except Exception as e:
    print(f"Warning: Could not load neck_taper_router: {e}")
    neck_taper_router = None

# Patch N.12 — Machine Tool Tables
try:
    from .routers.machines_tools_router import router as machines_tools_router
except Exception:
    machines_tools_router = None

# Patch N.14 — Unified CAM Settings (Post Templates + Adaptive Preview)
try:
    from .routers.posts_router import router as posts_router
except Exception:
    posts_router = None

try:
    from .routers.machines_router import router as machines_router
except Exception:
    machines_router = None

try:
    from .routers.adaptive_preview_router import router as adaptive_preview_router
except Exception:
    adaptive_preview_router = None

# Art Studio preview router (v13)
try:
    from .routers.cam_vcarve_router import router as cam_vcarve_router
except Exception as _e:
    cam_vcarve_router = None

# Art Studio v15.5 — Post-processor with CRC + Lead-in/out
try:
    from .routers.cam_post_v155_router import router as cam_post_v155_router
except Exception:
    cam_post_v155_router = None

# Art Studio v15.5 — Smoke test router
try:
    from .routers.cam_smoke_v155_router import router as cam_smoke_v155_router
except Exception:
    cam_smoke_v155_router = None

# Patch N.15 — G-code Backplot + Time Estimator
try:
    from .routers.gcode_backplot_router import router as gcode_backplot_router
except Exception:
    gcode_backplot_router = None

# Patch N.18 — G2/G3 Arc Linkers + Feed Floors
try:
    from .routers.adaptive_poly_gcode_router import router as adaptive_poly_gcode_router
except Exception:
    adaptive_poly_gcode_router = None

# Art Studio v16.0 — SVG Editor + Relief Mapper
try:
    from .routers.cam_svg_v160_router import router as cam_svg_v160_router
except Exception:
    cam_svg_v160_router = None

try:
    from .routers.cam_relief_v160_router import router as cam_relief_v160_router
except Exception:
    cam_relief_v160_router = None

# Art Studio v16.1 — Helical Z-Ramping
try:
    from .routers.cam_helical_v161_router import router as cam_helical_v161_router
except Exception:
    cam_helical_v161_router = None

# RMOS N10.1 — LiveMonitor Drill-Down (Subjobs + CAM Events)
try:
    from .routers.live_monitor_drilldown_api import router as live_monitor_drilldown_router
except Exception as e:
    print(f"Warning: Could not load live_monitor_drilldown_router: {e}")
    live_monitor_drilldown_router = None

# Phase 3 — N17 Polygon Offset (Pyclipper + Arc Linkers)
try:
    from .routers.cam_polygon_offset_router import router as cam_polygon_offset_router
except Exception as e:
    print(f"Warning: Could not load cam_polygon_offset_router: {e}")
    cam_polygon_offset_router = None

# N.17 sandbox polygon-offset router
try:
    from .routers.polygon_offset_router import router as polygon_offset_router
except Exception as e:
    print(f"Warning: Could not load polygon_offset_router: {e}")
    polygon_offset_router = None

# Phase 4 — N16 Adaptive Benchmark Suite
try:
    from .routers.cam_adaptive_benchmark_router import router as cam_adaptive_benchmark_router
except Exception as e:
    print(f"Warning: Could not load cam_adaptive_benchmark_router: {e}")
    cam_adaptive_benchmark_router = None

# Phase 24.0 — Relief Carving (Heightmap → Roughing/Finishing)
try:
    from .routers.cam_relief_router import router as cam_relief_router
except Exception as e:
    print(f"Warning: Could not load cam_relief_router: {e}")
    cam_relief_router = None

# CAM Pipeline Validation & DXF-to-Adaptive Bridge
try:
    from .routers.cam_dxf_adaptive_router import router as cam_dxf_adaptive_router
except Exception as e:
    print(f"Warning: Could not load cam_dxf_adaptive_router: {e}")
    cam_dxf_adaptive_router = None

try:
    from .routers.cam_simulate_router import router as cam_simulate_router
except Exception as e:
    print(f"Warning: Could not load cam_simulate_router: {e}")
    cam_simulate_router = None

# Blueprint Import — Phase 1 & 2 (AI Analysis + SVG/DXF Export)
try:
    from .routers.blueprint_router import router as blueprint_router
except Exception as e:
    print(f"Warning: Could not load blueprint_router: {e}")
    blueprint_router = None

# Blueprint → CAM Bridge (Phase 2 Integration)
try:
    from .routers.blueprint_cam_bridge import router as blueprint_cam_bridge_router
except Exception as e:
    print(f"Warning: Could not load blueprint_cam_bridge: {e}")
    blueprint_cam_bridge_router = None

# Unified CAM Pipeline Router (DXF → Preflight → Adaptive → Post → Sim)
try:
    from .routers.pipeline_router import router as pipeline_router
except Exception as e:
    print(f"Warning: Could not load pipeline_router: {e}")
    pipeline_router = None

# Pipeline Presets (Named machine/post recipes) [LEGACY - Use /api/presets instead]
try:
    from .routers.pipeline_presets_router import router as pipeline_presets_router
    # Deprecated: Use /api/presets with ?kind=cam instead
except Exception as e:
    print(f"Warning: Could not load pipeline_presets_router: {e}")
    pipeline_presets_router = None

# Phase 25.0 — Pipeline Preset Runner (Execute saved presets)
try:
    from .routers.cam_pipeline_preset_run_router import router as cam_pipeline_preset_run_router
except Exception as e:
    print(f"Warning: Could not load cam_pipeline_preset_run_router: {e}")
    cam_pipeline_preset_run_router = None

# Pipeline Lab — CAM Settings Hub (Machines/Posts/Presets summary)
try:
    from .routers.cam_settings_router import router as cam_settings_router
except Exception as e:
    print(f"Warning: Could not load cam_settings_router: {e}")
    cam_settings_router = None

# CAM Backup — Daily auto-backup + manual snapshot/download
try:
    from .routers.cam_backup_router import router as cam_backup_router
except Exception as e:
    print(f"Warning: Could not load cam_backup_router: {e}")
    cam_backup_router = None

# Bundle B41 — UnifiedPresets Backend Skeleton
try:
    from .api.routes.presets_router import router as presets_router
except Exception as e:
    print(f"Warning: Could not load presets_router: {e}")
    presets_router = None

# Simulation Metrics — Realistic time/energy estimation
try:
    from .routers.sim_metrics_router import router as sim_metrics_router
except Exception as e:
    print(f"Warning: Could not load sim_metrics_router: {e}")
    sim_metrics_router = None

# Job Intelligence — AI-assisted job analysis
try:
    from .routers.job_insights_router import router as job_insights_router
except Exception as e:
    print(f"Warning: Could not load job_insights_router: {e}")
    job_insights_router = None

# Job Intelligence — Pipeline run history log with favorites
try:
    from .routers.job_intelligence_router import router as job_intelligence_router
except Exception as e:
    print(f"Warning: Could not load job_intelligence_router: {e}")
    job_intelligence_router = None

# Unified Preset System — Consolidated CAM/Export/Neck presets with kind-based filtering
try:
    from .routers.unified_presets_router import router as unified_presets_router
except Exception as e:
    print(f"Warning: Could not load unified_presets_router: {e}")
    unified_presets_router = None

# CNC Production — Preset CRUD + lineage metadata (B20) [LEGACY - Use /api/presets instead]
try:
    from .routers.cnc_production.presets_router import router as cnc_presets_router
    # Deprecated: Use /api/presets with ?kind=cam instead
except Exception as e:
    print(f"Warning: Could not load cnc_presets_router: {e}")
    cnc_presets_router = None

# CNC Production — Job Comparison (B21)
try:
    from .routers.cnc_production.compare_jobs_router import router as cnc_compare_jobs_router
except Exception as e:
    print(f"Warning: Could not load cnc_compare_jobs_router: {e}")
    cnc_compare_jobs_router = None

# CP-S57 — Saw G-Code Generator
try:
    from .routers.saw_gcode_router import router as saw_gcode_router
except Exception as e:
    print(f"Warning: Could not load saw_gcode_router: {e}")
    saw_gcode_router = None

# CP-S50 — Saw Blade Registry (CRUD + PDF Import Integration)
try:
    from .routers.saw_blade_router import router as saw_blade_router
except Exception as e:
    print(f"Warning: Could not load saw_blade_router: {e}")
    saw_blade_router = None

# N8.6 — RMOS SQLite Stores (Patterns, JobLogs, Strip Families)
try:
    from .api.routes.rmos_stores_api import router as rmos_stores_router
except Exception as e:
    print(f"Warning: Could not load rmos_stores_router: {e}")
    rmos_stores_router = None

# N9.0 — RMOS Analytics Engine (Pattern/Material/Job Analytics)
try:
    from .routers.analytics_router import router as analytics_router
except Exception as e:
    print(f"Warning: Could not load analytics_router: {e}")
    analytics_router = None

# N9.1 — RMOS Advanced Analytics (Correlation/Anomaly/Prediction)
try:
    from .routers.advanced_analytics_router import router as advanced_analytics_router
except Exception as e:
    print(f"Warning: Could not load advanced_analytics_router: {e}")
    advanced_analytics_router = None

# N10.0 — RMOS Real-time Monitoring (WebSocket)
try:
    from .routers.websocket_router import router as websocket_router
except Exception as e:
    print(f"Warning: Could not load websocket_router: {e}")
    websocket_router = None

# MM-0 — RMOS Mixed-Material Strip Families
try:
    from .routers.strip_family_router import router as strip_family_router
except Exception as e:
    print(f"Warning: Could not load strip_family_router: {e}")
    strip_family_router = None

# MM-3 — RMOS PDF Design Sheets
try:
    from .api.routes.rosette_design_sheet_api import router as rosette_design_sheet_router
except Exception as e:
    print(f"Warning: Could not load rosette_design_sheet_router: {e}")
    rosette_design_sheet_router = None

# MM-4 — RMOS Material-Aware Analytics
try:
    from .api.routes.rmos_analytics_api import router as rmos_analytics_router
except Exception as e:
    print(f"Warning: Could not load rmos_analytics_router: {e}")
    rmos_analytics_router = None

# MM-5 — RMOS Ultra-Fragility Promotion Policy
try:
    from .api.routes.rmos_presets_api import router as rmos_presets_router
except Exception as e:
    print(f"Warning: Could not load rmos_presets_router: {e}")
    rmos_presets_router = None

# N10.2 — RMOS Apprenticeship Mode + Safety Overrides
try:
    from .api.routes.rmos_safety_api import router as rmos_safety_router
except Exception as e:
    print(f"Warning: Could not load rmos_safety_router: {e}")
    rmos_safety_router = None

# N10.2.1 — RMOS Pipeline Run (with safety evaluation)
try:
    from .api.routes.rmos_pipeline_run_api import router as rmos_pipeline_run_router
except Exception as e:
    print(f"Warning: Could not load rmos_pipeline_run_router: {e}")
    rmos_pipeline_run_router = None

# N11.1 — RMOS Rosette Pattern API (Scaffolding for RMOS Studio rosette patterns)
try:
    from .api.routes.rmos_pattern_api import router as rmos_pattern_router
except Exception as e:
    print(f"Warning: Could not load rmos_pattern_router: {e}")
    rmos_pattern_router = None

# N11.2 — RMOS Rosette Geometry API (Stub geometry engine endpoints)
try:
    from .api.routes.rmos_rosette_api import router as rmos_rosette_router
except Exception as e:
    print(f"Warning: Could not load rmos_rosette_router: {e}")
    rmos_rosette_router = None

# CP-S51 — Saw Blade Validator (Safety checks before G-code generation)
try:
    from .routers.saw_validate_router import router as saw_validate_router
except Exception as e:
    print(f"Warning: Could not load saw_validate_router: {e}")
    saw_validate_router = None

# CP-S59 — Saw JobLog & Telemetry
try:
    from .routers.joblog_router import router as joblog_router
except Exception as e:
    print(f"Warning: Could not load joblog_router: {e}")
    joblog_router = None

# CP-S59B — Saw Telemetry Router (live telemetry + auto-learning)
try:
    from .routers.saw_telemetry_router import router as saw_telemetry_router
except Exception as e:
    print(f"Warning: Could not load saw_telemetry_router: {e}")
    saw_telemetry_router = None

# CP-S52 — Learned Overrides (4-tuple lane learning)
try:
    from .routers.learned_overrides_router import router as learned_overrides_router
except Exception as e:
    print(f"Warning: Could not load learned_overrides_router: {e}")
    learned_overrides_router = None

# CP-S60 — Live Learn Ingestor
try:
    from .routers.learn_router import router as learn_router
except Exception as e:
    print(f"Warning: Could not load learn_router: {e}")
    learn_router = None

# CP-S61/62 — Dashboard + Risk Actions
try:
    from .routers.dashboard_router import router as dashboard_router
except Exception as e:
    print(f"Warning: Could not load dashboard_router: {e}")
    dashboard_router = None

# Pipeline Lab — Single-Preset Import/Export
try:
    from .routers.pipeline_preset_router import router as pipeline_preset_router
except Exception as e:
    print(f"Warning: Could not load pipeline_preset_router: {e}")
    pipeline_preset_router = None

# Phase 18.0 — Job Risk Store + Timeline Lab
try:
    from .routers.job_risk_router import router as job_risk_router
except Exception as e:
    print(f"Warning: Could not load job_risk_router: {e}")
    job_risk_router = None

# DXF → Adaptive Plan (Direct DXF-to-loops conversion)
try:
    from .routers.dxf_plan_router import router as dxf_plan_router
except Exception as e:
    print(f"Warning: Could not load dxf_plan_router: {e}")
    dxf_plan_router = None

# Specialty Module Routers (Archtop, Stratocaster, Smart Guitar, Bridge, Neck)
try:
    from .routers.archtop_router import router as archtop_router
except Exception as e:
    print(f"Warning: Could not load archtop_router: {e}")
    archtop_router = None

try:
    from .routers.bridge_router import router as bridge_router
except Exception as e:
    print(f"Warning: Could not load bridge_router: {e}")
    bridge_router = None

try:
    from .routers.neck_router import router as neck_router
except Exception as e:
    print(f"Warning: Could not load neck_router: {e}")
    neck_router = None

try:
    from .routers.dxf_preflight_router import router as dxf_preflight_router
except Exception as e:
    print(f"Warning: Could not load dxf_preflight_router: {e}")
    dxf_preflight_router = None

try:
    from .routers.stratocaster_router import router as stratocaster_router
except Exception as e:
    print(f"Warning: Could not load stratocaster_router: {e}")
    stratocaster_router = None

try:
    from .routers.smart_guitar_router import router as smart_guitar_router
except Exception as e:
    print(f"Warning: Could not load smart_guitar_router: {e}")
    smart_guitar_router = None

try:
    from .routers.om_router import router as om_router
except Exception as e:
    print(f"Warning: Could not load om_router: {e}")
    om_router = None

# Parametric Guitar Design — Dimension-driven body outline generation
try:
    from .routers.parametric_guitar_router import router as parametric_guitar_router
except Exception as e:
    print(f"Warning: Could not load parametric_guitar_router: {e}")

# Rosette MVP — Art Studio Rosette patterns (SQLite + FastAPI)
try:
    from .routers.art_studio_rosette_router import router as art_studio_rosette_router
    from .art_studio_rosette_store import init_db
    init_db()  # Initialize Rosette database and seed presets
except Exception as e:
    print(f"Warning: Could not load art_studio_rosette_router: {e}")
    art_studio_rosette_router = None
    parametric_guitar_router = None

# Phase 27.0 + 27.1 + 27.2 — Rosette Compare Mode MVP (Baseline Diff + History)
try:
    from .routers.compare_router import router as compare_router
except Exception as e:
    print(f"Warning: Could not load compare_router: {e}")
    compare_router = None

# Art Studio Bundle B22 — Compare Lab (SVG dual display)
try:
    from .routers.compare_lab_router import router as compare_lab_router
except Exception as e:
    print(f"Warning: Could not load compare_lab_router: {e}")
    compare_lab_router = None

try:
    from .routers.compare_lab_router import router as compare_lab_router
except Exception as e:
    print(f"Warning: Could not load compare_lab_router: {e}")
    compare_lab_router = None

# Compare Automation — B22 Arc-Enhanced Compare Engine
try:
    from .routers.compare_automation_router import router as compare_automation_router
except Exception as e:
    print(f"Warning: Could not load compare_automation_router: {e}")
    compare_automation_router = None

# Art Studio Bundle 5 — Rosette CAM Integration (Pipeline + Risk Timeline)
try:
    from .routers.cam_pipeline_router import router as cam_pipeline_router
except Exception as e:
    print(f"Warning: Could not load cam_pipeline_router: {e}")
    cam_pipeline_router = None

try:
    from .routers.cam_risk_router import router as cam_risk_router
except Exception as e:
    print(f"Warning: Could not load cam_risk_router: {e}")
    cam_risk_router = None

# B22.12: Diff Report Export (P0.1)
try:
    from .api.routes.b22_diff_export_routes import router as b22_diff_export_router
except Exception as e:
    print(f"Warning: Could not load b22_diff_export_router: {e}")
    b22_diff_export_router = None

# AI Graphics — AI-powered rosette parameter suggestions (sandbox mode)
try:
    from .ai_graphics.api.ai_routes import router as ai_graphics_router
    from .ai_graphics.api.session_routes import router as ai_session_router
except Exception as e:
    print(f"Warning: Could not load AI Graphics routers: {e}")
    ai_graphics_router = None
    ai_session_router = None

# RMOS Presets — Material and tool presets for RMOS context
try:
    from .rmos.api_presets import router as rmos_presets_api_router
except Exception as e:
    print(f"Warning: Could not load RMOS presets router: {e}")
    rmos_presets_api_router = None

# RMOS Profile History — Profile versioning and rollback
try:
    from .rmos.api_profile_history import router as rmos_profile_history_router
except Exception as e:
    print(f"Warning: Could not load RMOS profile history router: {e}")
    rmos_profile_history_router = None

# Saw Lab Physics Debug — Calculator debugging panel
try:
    from .saw_lab.debug_router import router as saw_physics_debug_router
except Exception as e:
    print(f"Warning: Could not load saw physics debug router: {e}")
    saw_physics_debug_router = None

import os

app = FastAPI(title="ToolBox API", version="0.2.0")

# CORS configuration
origins = (os.getenv("CORS_ORIGINS") or "").split(",") if os.getenv("CORS_ORIGINS") else []
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if cnc_production_routers is not None:
    app.include_router(cnc_production_routers.router)

if art_root_router is not None:
    app.include_router(art_root_router)

# Art Studio Bracing Calculator
if art_studio_bracing_router is not None:
    app.include_router(art_studio_bracing_router, prefix="/api", tags=["Art Studio"])

# Art Studio Rosette Calculator (new façade-based)
if art_studio_rosette_router_new is not None:
    app.include_router(art_studio_rosette_router_new, prefix="/api", tags=["Art Studio"])

# Art Studio Inlay Calculator
if art_studio_inlay_router is not None:
    app.include_router(art_studio_inlay_router, prefix="/api", tags=["Art Studio"])

# Art Studio VCarve (Wave 1)
if art_studio_vcarve_router is not None:
    app.include_router(art_studio_vcarve_router, prefix="/api/art-studio/vcarve", tags=["Art Studio"])

# Art Studio Relief (Wave 3)
if art_studio_relief_router is not None:
    app.include_router(art_studio_relief_router, prefix="/api/art-studio/relief", tags=["Art Studio"])

# Wave 7 — Instrument Geometry (Frets, Fretboard, Bridge, Radius)
if instrument_router is not None:
    app.include_router(instrument_router, tags=["Instrument Geometry"])

# Wave 14 — Instrument Geometry Core (19-model registry, expanded architecture)
if instrument_geometry_router is not None:
    app.include_router(instrument_geometry_router, prefix="/api/instrument_geometry", tags=["Instrument Geometry"])

# Wave 17 — Instrument Geometry: Neck Taper Suite
if neck_taper_router is not None:
    app.include_router(neck_taper_router, prefix="/api/instrument/neck_taper", tags=["Instrument Geometry"])

# Wave 8 — Calculator Service (Chipload, Heat, Deflection, Rim Speed)
if calculators_router is not None:
    app.include_router(calculators_router, tags=["Calculators"])

# Wave 11 — AI-CAM Advisor + G-Code Explainer 2.0
if ai_cam_router is not None:
    app.include_router(ai_cam_router, prefix="/api", tags=["AI-CAM"])

app.include_router(sim_router)
app.include_router(feeds_router)
app.include_router(geometry_router)
app.include_router(tooling_router)
app.include_router(adaptive_router)
if cam_compare_diff_router:
    app.include_router(cam_compare_diff_router, prefix="/api", tags=["Compare", "CAM"])
app.include_router(machine_router)
app.include_router(cam_opt_router)  # M.2
app.include_router(material_router)  # M.3
app.include_router(cam_metrics_router)  # M.3
app.include_router(cam_logs_router)  # M.4
app.include_router(cam_learn_router)  # M.4

# RMOS 2.0: Feasibility, BOM, Toolpath endpoints
if rmos_router:
    app.include_router(rmos_router, prefix="/api/rmos", tags=["RMOS"])

# Phase B (Wave 17→18): RMOS Context Management
if rmos_context_router:
    app.include_router(rmos_context_router, prefix="/api/rmos", tags=["RMOS", "Context"])

# Phase D (Wave 18): Feasibility Fusion
if rmos_feasibility_router:
    app.include_router(rmos_feasibility_router, prefix="/api/rmos/feasibility", tags=["RMOS", "Feasibility"])

# Phase E (Wave 17→18): CAM Preview Integration
if cam_preview_router:
    app.include_router(cam_preview_router, prefix="/api/cam", tags=["CAM", "Preview", "Wave17-18"])

# Directional Workflow 2.0: Mode preview and constraints
if workflow_router:
    app.include_router(workflow_router, prefix="/api/rmos/workflow", tags=["Workflow", "RMOS"])

# RMOS Constraint Search: Generate feasible designs from constraints
if rmos_constraint_router:
    app.include_router(rmos_constraint_router, prefix="/api/rmos/constraint", tags=["RMOS", "Constraint Search"])

# RMOS Logs: Event logging and export
if rmos_log_router:
    app.include_router(rmos_log_router, prefix="/api/rmos/logs", tags=["RMOS", "Logs"])

# RMOS AI Logs Viewer: Query AI constraint search logs
if rmos_ai_logs_router:
    app.include_router(rmos_ai_logs_router, prefix="/api", tags=["RMOS", "AI Logs"])

# RMOS Constraint Profiles: View and resolve AI constraint profiles
if rmos_constraint_profiles_router:
    app.include_router(rmos_constraint_profiles_router, prefix="/api", tags=["RMOS", "AI Profiles"])

# RMOS AI Snapshots: Generator behavior inspection
if rmos_ai_snapshots_router:
    app.include_router(rmos_ai_snapshots_router, prefix="/api", tags=["RMOS", "AI Snapshots"])

# AI Graphics: AI-powered rosette parameter suggestions
if ai_graphics_router:
    app.include_router(ai_graphics_router, tags=["AI Graphics"])
if ai_session_router:
    app.include_router(ai_session_router, tags=["AI Graphics", "Session"])

# RMOS Presets: Material and tool presets
if rmos_presets_api_router:
    app.include_router(rmos_presets_api_router, tags=["RMOS", "Presets"])

# RMOS Profile History: Versioning and rollback
if rmos_profile_history_router:
    app.include_router(rmos_profile_history_router, tags=["RMOS", "History"])

# Saw Lab Physics Debug: Calculator debugging panel
if saw_physics_debug_router:
    app.include_router(saw_physics_debug_router, tags=["Saw Lab", "Debug"])

# RMOS N10.1: LiveMonitor Drill-Down
if live_monitor_drilldown_router:
    app.include_router(live_monitor_drilldown_router)

# Patch N.12: Machine Tool Tables
if machines_tools_router:
    app.include_router(machines_tools_router)

# Patch N.14: Unified CAM Settings
if posts_router:
    app.include_router(posts_router)
if machines_router:
    app.include_router(machines_router)
if adaptive_preview_router:
    app.include_router(adaptive_preview_router)

# v13: Art Studio preview infill endpoint
if cam_vcarve_router:
    app.include_router(cam_vcarve_router)

# v15.5: Art Studio post-processor (CRC + Lead-in/out + Corner smoothing)
if cam_post_v155_router:
    app.include_router(cam_post_v155_router)

# v15.5: Art Studio smoke test (validates all presets)
if cam_smoke_v155_router:
    app.include_router(cam_smoke_v155_router)

# Bundle B41: UnifiedPresets Backend
if presets_router:
    app.include_router(presets_router)

# Patch N.15: G-code backplot and time estimation
if gcode_backplot_router:
    app.include_router(gcode_backplot_router)

# Patch N.18: Adaptive poly offset-spiral with G2/G3 arcs + feed floors
if adaptive_poly_gcode_router:
    app.include_router(adaptive_poly_gcode_router)

# Art Studio v16.0: SVG Editor and Relief Mapper
if cam_svg_v160_router:
    app.include_router(cam_svg_v160_router)
if cam_relief_v160_router:
    app.include_router(cam_relief_v160_router)

# Art Studio v16.1: Helical Z-Ramping
    if cam_helical_v161_router:
        app.include_router(cam_helical_v161_router)

# Rosette MVP Router
if art_studio_rosette_router:
    app.include_router(art_studio_rosette_router, prefix="/api/art/rosette", tags=["Art Studio"])

# Phase 30.5: Art Preset Aggregate (Tuning Tree → Compare Mode)
try:
    from .routers.art_presets_router import router as art_presets_router
    app.include_router(art_presets_router, prefix="/api/art", tags=["Art Studio", "Presets"])
except Exception as e:
    print(f"Warning: Art presets router not available: {e}")
    art_presets_router = None

# Phase 27.0 + 27.1 + 27.2: Rosette Compare Mode (Baseline Diff + Overlay Colors + History)
if compare_router:
    app.include_router(compare_router, tags=["Art Studio", "Compare"])
if compare_lab_router:
    app.include_router(compare_lab_router)

if compare_lab_router:
    app.include_router(compare_lab_router)

# B22: Compare Automation (Arc-Enhanced Compare Engine)
if compare_automation_router:
    app.include_router(compare_automation_router, tags=["Compare", "Automation"])

# B22.12: Diff Report Export (P0.1)
if b22_diff_export_router:
    app.include_router(b22_diff_export_router, prefix="/export", tags=["Export", "Compare"])

# Art Studio Bundle 5: CAM Pipeline and Risk Timeline
if cam_pipeline_router:
    app.include_router(cam_pipeline_router)

if cam_risk_router:
    app.include_router(cam_risk_router)

# Phase 28.3: Server-Side Risk Aggregates (Cross-Lab Dashboard Backend)
try:
    from .routers.compare_risk_aggregate_router import router as compare_risk_aggregate_router
    app.include_router(compare_risk_aggregate_router, tags=["Compare", "Risk"])
except Exception as e:
    print(f"Warning: Compare risk aggregate router not available: {e}")
    compare_risk_aggregate_router = None

# Phase 28.4: Risk Bucket Detail Endpoint
try:
    from .routers.compare_risk_bucket_detail_router import router as compare_risk_bucket_detail_router
    app.include_router(compare_risk_bucket_detail_router, tags=["Compare", "Risk"])
except Exception as e:
    print(f"Warning: Compare risk bucket detail router not available: {e}")
    compare_risk_bucket_detail_router = None

# Phase 28.5: Risk Bucket Export (CSV + JSON)
try:
    from .routers.compare_risk_bucket_export_router import router as compare_risk_bucket_export_router
    app.include_router(compare_risk_bucket_export_router, tags=["Compare", "Risk"])
except Exception as e:
    print(f"Warning: Compare risk bucket export router not available: {e}")
    compare_risk_bucket_export_router = None

# Phase 3: N17 Polygon Offset (Pyclipper + Arc Linkers)
if cam_polygon_offset_router:
    app.include_router(cam_polygon_offset_router, prefix="/cam", tags=["CAM"])

# N.17 sandbox polygon-offset router
if polygon_offset_router:
    app.include_router(polygon_offset_router)

# Phase 4: N16 Adaptive Benchmark Suite
if cam_adaptive_benchmark_router:
    app.include_router(cam_adaptive_benchmark_router, prefix="/cam/adaptive2", tags=["CAM", "Benchmarks"])

# Phase 5: N10 CAM Essentials (Roughing, Drilling, Patterns, Bi-Arc)
try:
    from .routers.cam_roughing_router import router as cam_roughing_router
except Exception as e:
    print(f"Warning: Could not load cam_roughing_router: {e}")
    cam_roughing_router = None

try:
    from .routers.cam_drill_router import router as cam_drill_router
except Exception as e:
    print(f"Warning: Could not load cam_drill_router: {e}")
    cam_drill_router = None

try:
    from .routers.cam_drill_pattern_router import router as cam_drill_pattern_router
except Exception as e:
    print(f"Warning: Could not load cam_drill_pattern_router: {e}")
    cam_drill_pattern_router = None

try:
    from .routers.cam_biarc_router import router as cam_biarc_router
except Exception as e:
    print(f"Warning: Could not load cam_biarc_router: {e}")
    cam_biarc_router = None

if cam_roughing_router:
    app.include_router(cam_roughing_router, tags=["CAM", "N10"])
if cam_drill_router:
    app.include_router(cam_drill_router, tags=["CAM", "N10"])
if cam_drill_pattern_router:
    app.include_router(cam_drill_pattern_router, tags=["CAM", "N10"])
if cam_biarc_router:
    app.include_router(cam_biarc_router, tags=["CAM", "N10"])

# Phase 5 Part 2: N.0 Smart Post Configurator (CRUD for post-processors)
try:
    from .routers.post_router import router as post_router
except Exception as e:
    print(f"Warning: Could not load post_router: {e}")
    post_router = None

if post_router:
    app.include_router(post_router, tags=["Posts", "N0"])

# Phase 5 Part 3: N.06 Modal Cycles (G81-G89 drilling operations)
try:
    from .routers.drilling_router import router as drilling_router
except Exception as e:
    print(f"Warning: Could not load drilling_router: {e}")
    drilling_router = None

if drilling_router:
    app.include_router(drilling_router, prefix="/api/cam", tags=["CAM", "Drilling", "N06"])

# Phase 5 Part 3: N.09 Probe Patterns (Work offset establishment + SVG setup sheets)
try:
    from .routers.probe_router import router as probe_router
except Exception as e:
    print(f"Warning: Could not load probe_router: {e}")
    probe_router = None

if probe_router:
    app.include_router(probe_router, prefix="/api/cam/probe", tags=["CAM", "Probing", "N09"])

# Phase 5 Part 3: N.08 Retract Patterns (Smart retract strategies for cycle time optimization)
try:
    from .routers.retract_router import router as retract_router
except Exception as e:
    print(f"Warning: Could not load retract_router: {e}")
    retract_router = None

if retract_router:
    app.include_router(retract_router, prefix="/api/cam/retract", tags=["CAM", "Retract", "N08"])

# Phase 24.0: Relief Carving (Heightmap → Roughing/Finishing)
if cam_relief_router:
    app.include_router(cam_relief_router)

# Phase 26.0: Risk Aggregate Router (Risk timeline analytics)
try:
    from .routers.cam_risk_aggregate_router import router as cam_risk_aggregate_router
except Exception as e:
    print(f"Warning: Could not load cam_risk_aggregate_router: {e}")
    cam_risk_aggregate_router = None

if cam_risk_aggregate_router:
    app.include_router(cam_risk_aggregate_router)

# CAM Pipeline Validation & DXF-to-Adaptive Bridge
if cam_dxf_adaptive_router:
    app.include_router(cam_dxf_adaptive_router)

if cam_simulate_router:
    app.include_router(cam_simulate_router)

# Blueprint Import: Phase 1 & 2 (AI analysis + SVG/DXF export)
if blueprint_router:
    app.include_router(blueprint_router)

# Blueprint → CAM Bridge: Phase 2 Integration (DXF → Adaptive pocket)
if blueprint_cam_bridge_router:
    app.include_router(blueprint_cam_bridge_router)

# Unified CAM Pipeline: Full workflow (DXF → Preflight → Adaptive → Post → Sim)
if pipeline_router:
    app.include_router(pipeline_router)

# Pipeline Presets: Named machine/post recipes for quick setup [LEGACY - Deprecated]
if pipeline_presets_router:
    app.include_router(pipeline_presets_router)

# Phase 25.0: Pipeline Preset Runner (Execute saved presets)
if cam_pipeline_preset_run_router:
    app.include_router(cam_pipeline_preset_run_router)

# Pipeline Lab: CAM Settings Hub summary endpoint
if cam_settings_router:
    app.include_router(cam_settings_router)

# CAM Backup: Daily auto-backup + manual endpoints
if cam_backup_router:
    app.include_router(cam_backup_router)

# Simulation Metrics: Realistic time/energy estimation
if sim_metrics_router:
    app.include_router(sim_metrics_router)

# Job Intelligence: AI-assisted job analysis
if job_insights_router:
    app.include_router(job_insights_router)

# Job Intelligence: Pipeline run history log with favorites
if job_intelligence_router:
    app.include_router(job_intelligence_router, prefix="/api/cam/job-int", tags=["CAM", "Job Intelligence"])

# Unified Preset System: Single endpoint for CAM/Export/Neck/Combo presets
if unified_presets_router:
    app.include_router(unified_presets_router, prefix="/api", tags=["Presets", "Unified"])

# CNC Production: Preset Manager API [LEGACY - Deprecated]
if cnc_presets_router:
    app.include_router(cnc_presets_router, prefix="/api")

# CNC Production: Job Comparison API (B21)
if cnc_compare_jobs_router:
    app.include_router(cnc_compare_jobs_router, prefix="/api")

# CP-S57: Saw G-Code Generator (slice/batch/contour operations)
if saw_gcode_router:
    app.include_router(saw_gcode_router, prefix="/api", tags=["Saw Lab", "G-Code"])

# CP-S50: Saw Blade Registry (blade specs CRUD + PDF import integration)
if saw_blade_router:
    app.include_router(saw_blade_router, prefix="/api", tags=["Saw Lab", "Blade Registry"])

# N8.6: RMOS SQLite Stores (patterns, joblogs, strip families CRUD)
if rmos_stores_router:
    app.include_router(rmos_stores_router, prefix="/api", tags=["RMOS", "Stores"])

# N9.0: RMOS Analytics Engine (pattern complexity, material efficiency, job performance)
if analytics_router:
    app.include_router(analytics_router, prefix="/api/analytics", tags=["RMOS", "Analytics"])

# N9.1: RMOS Advanced Analytics (correlation, anomaly detection, prediction)
if advanced_analytics_router:
    app.include_router(advanced_analytics_router, prefix="/api/analytics", tags=["RMOS", "Analytics", "Advanced"])

# N10.0: RMOS Real-time Monitoring (WebSocket for live updates)
if websocket_router:
    app.include_router(websocket_router, prefix="/ws", tags=["RMOS", "WebSocket"])

# MM-0: RMOS Mixed-Material Strip Families (template library + CRUD)
if strip_family_router:
    app.include_router(strip_family_router, prefix="/api/rmos", tags=["RMOS", "Strip Families"])

# MM-3: RMOS PDF Design Sheets (generate shop-ready PDFs)
if rosette_design_sheet_router:
    app.include_router(rosette_design_sheet_router, prefix="/api", tags=["RMOS", "Design Sheets"])

# MM-4: RMOS Material-Aware Analytics (lane risk + fragility + material distribution)
if rmos_analytics_router:
    app.include_router(rmos_analytics_router, prefix="/api/rmos/analytics", tags=["RMOS", "Analytics", "Materials"])

# MM-5: RMOS Ultra-Fragility Promotion Policy (block unsafe lane promotions)
if rmos_presets_router:
    app.include_router(rmos_presets_router, prefix="/api/rmos/presets", tags=["RMOS", "Presets", "Promotion"])

# N10.2: RMOS Apprenticeship Mode + Safety Overrides (safety policy layer)
if rmos_safety_router:
    app.include_router(rmos_safety_router, prefix="/api", tags=["RMOS", "Safety", "Apprentice"])

# N10.2.1: RMOS Pipeline Run (job execution with safety evaluation)
if rmos_pipeline_run_router:
    app.include_router(rmos_pipeline_run_router, prefix="/api/rmos/pipeline", tags=["RMOS", "Pipeline", "Safety"])

# N11.1: RMOS Rosette Pattern API (scaffolding for RMOS Studio rosette patterns)
if rmos_pattern_router:
    app.include_router(rmos_pattern_router, tags=["RMOS", "Patterns", "Rosette"])

# N11.2: RMOS Rosette Geometry API (stub geometry engine endpoints)
if rmos_rosette_router:
    app.include_router(rmos_rosette_router, tags=["RMOS", "Rosette", "Geometry"])

# CP-S51: Saw Blade Validator (safety checks: radius, DOC, RPM, feeds)
if saw_validate_router:
    app.include_router(saw_validate_router, prefix="/api", tags=["Saw Lab", "Validation"])

# CP-S52: Learned Overrides (4-tuple lane learning: tool+material+mode+machine)
if learned_overrides_router:
    app.include_router(learned_overrides_router, prefix="/api", tags=["Feeds & Speeds", "Learning"])

# CP-S59: Saw JobLog & Telemetry (job tracking + real-time metrics)
if joblog_router:
    app.include_router(joblog_router, prefix="/api", tags=["Saw Lab", "JobLog", "Telemetry"])

# CP-S59B: Saw Telemetry Router (live ingestion + risk scoring + auto-learning)
if saw_telemetry_router:
    app.include_router(saw_telemetry_router, prefix="/api", tags=["Saw Lab", "Telemetry", "Learning"])

# CP-S60: Live Learn Ingestor (telemetry-based feed/speed optimization)
if learn_router:
    app.include_router(learn_router, prefix="/api", tags=["Saw Lab", "Learning"])

# CP-S61/62: Dashboard + Risk Actions (run summaries + risk classification)
if dashboard_router:
    app.include_router(dashboard_router, prefix="/api", tags=["Saw Lab", "Dashboard"])

# Pipeline Lab: Single-Preset Import/Export
if pipeline_preset_router:
    app.include_router(pipeline_preset_router)

# Phase 18.0: Job Risk Store + Timeline Lab
if job_risk_router:
    app.include_router(job_risk_router)

# DXF → Adaptive Plan: Direct DXF-to-loops conversion endpoint
if dxf_plan_router:
    app.include_router(dxf_plan_router)

# Specialty Modules: Archtop, Stratocaster, Smart Guitar, OM, Bridge Calculator, Neck Generator
if archtop_router:
    app.include_router(archtop_router)

if bridge_router:
    app.include_router(bridge_router)

if neck_router:
    app.include_router(neck_router, prefix="/api", tags=["Design Tools", "Neck"])

if dxf_preflight_router:
    app.include_router(dxf_preflight_router)

if stratocaster_router:
    app.include_router(stratocaster_router)

if smart_guitar_router:
    app.include_router(smart_guitar_router)

if om_router:
    app.include_router(om_router)

# Parametric Guitar Design: Dimension → Body Outline → DXF
if parametric_guitar_router:
    app.include_router(parametric_guitar_router)

app.include_router(health_router)

# Install daily backup service (14-day retention)
try:
    from .services.cam_backup_service import install_daily_backup
    install_daily_backup(app)
except Exception as e:
    print(f"Warning: Could not install daily backup service: {e}")


