"""
Luthier's ToolBox API - Main Application

CLEANED: 2024-12-13
- Removed 84 phantom imports (modules referenced but don't exist)
- Removed 9 broken imports (files exist but have unmet dependencies)
- Kept 33 working routers that actually load
- No more silent try/except failures

BROKEN ROUTERS (files exist but won't load - fix dependencies to restore):
- rmos.feasibility_router      → needs rmos.context
- cam.cam_preview_router       → needs rmos.context  
- routers.adaptive_poly_gcode_router → needs routers.util
- routers.pipeline_router      → needs httpx
- routers.blueprint_router     → needs analyzer
- routers.saw_blade_router     → needs cam_core
- routers.saw_gcode_router     → needs cam_core
- routers.saw_validate_router  → needs cam_core
- routers.saw_telemetry_router → needs cnc_production
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# =============================================================================
# CORE ROUTERS (11 routers)
# =============================================================================
from .routers.cam_sim_router import router as sim_router
from .routers.feeds_router import router as feeds_router
from .routers.geometry_router import router as geometry_router
from .routers.tooling_router import router as tooling_router
from .routers.adaptive_router import router as adaptive_router
from .routers.machine_router import router as machine_router
from .routers.cam_opt_router import router as cam_opt_router
from .routers.material_router import router as material_router
from .routers.cam_metrics_router import router as cam_metrics_router
from .routers.cam_logs_router import router as cam_logs_router
from .routers.cam_learn_router import router as cam_learn_router

# =============================================================================
# RMOS 2.0 - Rosette Manufacturing Orchestration System (1 router)
# Note: feasibility_router broken - needs rmos.context module
# =============================================================================
from .rmos import rmos_router

# =============================================================================
# CAM SUBSYSTEM (8 routers)
# Note: cam_preview_router broken - needs rmos.context
# Note: adaptive_poly_gcode_router broken - needs routers.util
# =============================================================================
from .routers.cam_vcarve_router import router as cam_vcarve_router
from .routers.cam_post_v155_router import router as cam_post_v155_router
from .routers.cam_smoke_v155_router import router as cam_smoke_v155_router
from .routers.cam_relief_v160_router import router as cam_relief_router
from .routers.cam_svg_v160_router import router as cam_svg_router
from .routers.cam_helical_v161_router import router as cam_helical_router
from .routers.gcode_backplot_router import router as gcode_backplot_router
from .routers.adaptive_preview_router import router as adaptive_preview_router

# =============================================================================
# PIPELINE & PRESETS (2 routers)
# Note: pipeline_router broken - needs httpx
# =============================================================================
from .routers.pipeline_presets_router import router as pipeline_presets_router
from .routers.dxf_plan_router import router as dxf_plan_router

# =============================================================================
# BLUEPRINT IMPORT (1 router)
# Note: blueprint_router broken - needs analyzer module
# =============================================================================
from .routers.blueprint_cam_bridge import router as blueprint_cam_bridge_router

# =============================================================================
# MACHINE & POST CONFIGURATION (3 routers)
# =============================================================================
from .routers.machines_router import router as machines_router
from .routers.machines_tools_router import router as machines_tools_router
from .routers.posts_router import router as posts_router

# =============================================================================
# INSTRUMENT GEOMETRY (1 router)
# =============================================================================
from .routers.instrument_geometry_router import router as instrument_geometry_router

# =============================================================================
# DATA REGISTRY (1 router)
# =============================================================================
from .routers.registry_router import router as registry_router

# =============================================================================
# SAW LAB (1 router)
# Note: saw_blade/gcode/validate/telemetry routers broken - need cam_core
# =============================================================================
from .saw_lab.debug_router import router as saw_debug_router

# =============================================================================
# SPECIALTY MODULES - Guitar-specific calculators (4 routers)
# =============================================================================
from .routers.archtop_router import router as archtop_router
from .routers.stratocaster_router import router as stratocaster_router
from .routers.smart_guitar_router import router as smart_guitar_router
from .routers.om_router import router as om_router

# =============================================================================
# G-CODE GENERATORS (2 routers) - Wave 3
# =============================================================================
from .routers.body_generator_router import router as body_generator_router
from .routers.neck_generator_router import router as neck_generator_router

# =============================================================================
# CAD ENGINE (1 router) - Wave 4
# =============================================================================
from .cad.api import dxf_router as cad_dxf_router

# =============================================================================
# ROSETTE SYSTEM (2 routers) - Wave 5
# =============================================================================
from .routers.rosette_pattern_router import router as rosette_pattern_router
from .art_studio.rosette_router import router as art_studio_rosette_router

# =============================================================================
# SMART GUITAR TEMPERAMENTS (1 router) - Wave 6
# =============================================================================
from .routers.temperament_router import router as temperament_router

# =============================================================================
# WAVE 7: CALCULATOR SUITE + FRET SLOTS CAM + BRIDGE CALCULATOR (3 routers)
# =============================================================================
from .routers.calculators_router import router as calculators_router
from .routers.cam_fret_slots_router import router as cam_fret_slots_router
from .routers.bridge_router import router as bridge_router

# =============================================================================
# WAVE 8: PRESETS + RMOS EXTENSIONS + CAM TOOLS (7 routers)
# =============================================================================
from .routers.unified_presets_router import router as unified_presets_router
from .routers.strip_family_router import router as strip_family_router
from .routers.rmos_patterns_router import router as rmos_patterns_router
from .routers.rmos_saw_ops_router import router as rmos_saw_ops_router
from .routers.sim_metrics_router import router as sim_metrics_router
from .routers.retract_router import router as retract_router
from .routers.rosette_photo_router import router as rosette_photo_router

# =============================================================================
# WAVE 9: AI-CAM + DRILL/ROUGHING + COMPARE + DXF PREFLIGHT + JOBLOG + NECK (8 routers)
# =============================================================================
from .routers.ai_cam_router import router as ai_cam_router
from .routers.cam_drill_pattern_router import router as cam_drill_pattern_router
from .routers.cam_roughing_router import router as cam_roughing_router
from .routers.compare_router import router as compare_router
from .routers.dxf_preflight_router import router as dxf_preflight_router
from .routers.joblog_router import router as joblog_router
from .routers.neck_router import router as neck_router
from .routers.parametric_guitar_router import router as parametric_guitar_router

# =============================================================================
# WAVE 10: INSTRUMENT + COMPARE LAB + DRILLING + RISK + LEARN + BACKUP (8 routers)
# =============================================================================
from .routers.instrument_router import router as instrument_router
from .routers.compare_lab_router import router as compare_lab_router
from .routers.drilling_router import router as drilling_router
from .routers.cam_risk_router import router as cam_risk_router
from .routers.job_risk_router import router as job_risk_router
from .routers.learn_router import router as learn_router
from .routers.learned_overrides_router import router as learned_overrides_router
from .routers.cam_backup_router import router as cam_backup_router

# =============================================================================
# WAVE 11: ANALYTICS + PROBE + LTB CALCULATOR + CAM TOOLS (8 routers)
# =============================================================================
from .routers.analytics_router import router as analytics_router
from .routers.advanced_analytics_router import router as advanced_analytics_router
from .routers.probe_router import router as probe_router
from .routers.ltb_calculator_router import router as ltb_calculator_router
from .routers.dashboard_router import router as dashboard_router
from .routers.cam_settings_router import router as cam_settings_router
from .routers.cam_biarc_router import router as cam_biarc_router
from .routers.job_intelligence_router import router as job_intelligence_router

# =============================================================================
# WAVE 12: CAM EXTENSIONS + COMPARE RISK + FRET EXPORT + POLYGON (8 routers)
# =============================================================================
from .routers.cam_adaptive_benchmark_router import router as cam_adaptive_benchmark_router
from .routers.cam_fret_slots_export_router import router as cam_fret_slots_export_router
from .routers.cam_risk_aggregate_router import router as cam_risk_aggregate_router
from .routers.compare_risk_aggregate_router import router as compare_risk_aggregate_router
from .routers.compare_risk_bucket_detail_router import router as compare_risk_bucket_detail_router
from .routers.polygon_offset_router import router as polygon_offset_router
from .routers.job_insights_router import router as job_insights_router
from .routers.pipeline_preset_router import router as pipeline_preset_router

# =============================================================================
# WAVE 13 (FINAL): ART PRESETS + CAM UTILITIES + COMPARE + MONITOR (10 routers)
# =============================================================================
from .routers.art_presets_router import router as art_presets_router
from .routers.cam_compare_diff_router import router as cam_compare_diff_router
from .routers.cam_dxf_adaptive_router import router as cam_dxf_adaptive_router
from .routers.cam_pipeline_preset_run_router import router as cam_pipeline_preset_run_router
from .routers.cam_polygon_offset_router import router as cam_polygon_offset_router
from .routers.cam_simulate_router import router as cam_simulate_router
from .routers.compare_automation_router import router as compare_automation_router
from .routers.compare_risk_bucket_export_router import router as compare_risk_bucket_export_router
from .routers.health_router import router as health_router_ext
from .routers.live_monitor_drilldown_api import router as live_monitor_router

# =============================================================================
# CNC PRODUCTION (1 router)
# =============================================================================
from .routers.cnc_production.compare_jobs_router import router as cnc_compare_jobs_router

# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="Luthier's ToolBox API",
    description="CAM system for guitar builders - DXF templates, G-code generation, manufacturing orchestration",
    version="2.0.0-clean",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# ROUTER REGISTRATION
# =============================================================================

# Core CAM (11)
app.include_router(sim_router, prefix="/api/sim", tags=["Simulation"])
app.include_router(feeds_router, prefix="/api/feeds", tags=["Feeds & Speeds"])
app.include_router(geometry_router, prefix="/api/geometry", tags=["Geometry"])
app.include_router(tooling_router, prefix="/api/tooling", tags=["Tooling"])
app.include_router(adaptive_router, prefix="/api/adaptive", tags=["Adaptive Pocketing"])
app.include_router(machine_router, prefix="/api/machine", tags=["Machine"])
app.include_router(cam_opt_router, prefix="/api/cam/opt", tags=["CAM Optimization"])
app.include_router(material_router, prefix="/api/material", tags=["Materials"])
app.include_router(cam_metrics_router, prefix="/api/cam/metrics", tags=["CAM Metrics"])
app.include_router(cam_logs_router, prefix="/api/cam/logs", tags=["CAM Logs"])
app.include_router(cam_learn_router, prefix="/api/cam/learn", tags=["CAM Learning"])

# RMOS 2.0 (1)
app.include_router(rmos_router, prefix="/api/rmos", tags=["RMOS"])

# CAM Subsystem (8)
app.include_router(cam_vcarve_router, prefix="/api/cam/vcarve", tags=["V-Carve"])
app.include_router(cam_post_v155_router, prefix="/api/cam/post", tags=["Post Processor"])
app.include_router(cam_smoke_v155_router, prefix="/api/cam/smoke", tags=["Smoke Tests"])
app.include_router(cam_relief_router, prefix="/api/cam/relief", tags=["Relief Carving"])
app.include_router(cam_svg_router, prefix="/api/cam/svg", tags=["SVG Export"])
app.include_router(cam_helical_router, prefix="/api/cam/helical", tags=["Helical Ramping"])
app.include_router(gcode_backplot_router, prefix="/api/cam/backplot", tags=["G-Code Backplot"])
app.include_router(adaptive_preview_router, prefix="/api/cam/adaptive-preview", tags=["Adaptive Preview"])

# Pipeline (2)
app.include_router(pipeline_presets_router, prefix="/api/pipeline/presets", tags=["Pipeline Presets"])
app.include_router(dxf_plan_router, prefix="/api/dxf", tags=["DXF Planning"])

# Blueprint (1)
app.include_router(blueprint_cam_bridge_router, prefix="/api/blueprint/cam", tags=["Blueprint CAM Bridge"])

# Machine & Post Configuration (3)
app.include_router(machines_router, prefix="/api/machines", tags=["Machines"])
app.include_router(machines_tools_router, prefix="/api/machines/tools", tags=["Machine Tools"])
app.include_router(posts_router, prefix="/api/posts", tags=["Post Processors"])

# Instrument Geometry (1)
app.include_router(instrument_geometry_router, prefix="/api/instrument", tags=["Instrument Geometry"])

# Data Registry (1)
app.include_router(registry_router, prefix="/api/registry", tags=["Data Registry"])

# Saw Lab (1)
app.include_router(saw_debug_router, prefix="/api/saw/debug", tags=["Saw Lab", "Debug"])

# Specialty Modules (4)
app.include_router(archtop_router, prefix="/api/guitar/archtop", tags=["Guitar", "Archtop"])
app.include_router(stratocaster_router, prefix="/api/guitar/stratocaster", tags=["Guitar", "Stratocaster"])
app.include_router(smart_guitar_router, prefix="/api/guitar/smart", tags=["Guitar", "Smart Guitar"])
app.include_router(om_router, prefix="/api/guitar/om", tags=["Guitar", "OM"])

# G-Code Generators (2)
app.include_router(body_generator_router, prefix="/api/cam/body", tags=["G-Code Generators", "Body"])
app.include_router(neck_generator_router, prefix="/api/cam/neck", tags=["G-Code Generators", "Neck"])

# CAD Engine (1) - Wave 4
app.include_router(cad_dxf_router, prefix="/api/cad", tags=["CAD", "DXF"])

# Rosette System (2) - Wave 5
app.include_router(rosette_pattern_router, prefix="/api/rosette", tags=["Rosette", "Patterns"])
app.include_router(art_studio_rosette_router, prefix="/api", tags=["Rosette", "Art Studio"])

# Smart Guitar Temperaments (1) - Wave 6
app.include_router(temperament_router, prefix="/api/smart-guitar", tags=["Smart Guitar", "Temperaments"])

# Wave 7: Calculator Suite + Fret Slots CAM + Bridge Calculator (3)
app.include_router(calculators_router, prefix="/api", tags=["Calculators"])
app.include_router(cam_fret_slots_router, prefix="/api/cam/fret_slots", tags=["CAM", "Fret Slots"])
app.include_router(bridge_router, prefix="/api", tags=["CAM", "Bridge Calculator"])

# Wave 8: Presets + RMOS Extensions + CAM Tools (7)
app.include_router(unified_presets_router, prefix="/api", tags=["Presets", "Unified"])
app.include_router(strip_family_router, prefix="/api/rmos", tags=["RMOS", "Strip Families"])
app.include_router(rmos_patterns_router, prefix="/api/rmos", tags=["RMOS", "Patterns"])
app.include_router(rmos_saw_ops_router, prefix="/api/rmos", tags=["RMOS", "Saw Operations"])
app.include_router(sim_metrics_router, prefix="/api", tags=["CAM", "Simulation"])
app.include_router(retract_router, prefix="/api/cam/retract", tags=["CAM", "Retract Patterns"])
app.include_router(rosette_photo_router, prefix="/api", tags=["Rosette", "Photo Import"])

# Wave 9: AI-CAM + Drill/Roughing + Compare + DXF Preflight + JobLog + Neck (8)
app.include_router(ai_cam_router, prefix="/api", tags=["AI-CAM"])
app.include_router(cam_drill_pattern_router, prefix="/api", tags=["CAM", "Drill Patterns"])
app.include_router(cam_roughing_router, prefix="/api", tags=["CAM", "Roughing"])
app.include_router(compare_router, prefix="/api", tags=["Compare", "Baselines"])
app.include_router(dxf_preflight_router, prefix="/api", tags=["DXF", "Preflight"])
app.include_router(joblog_router, prefix="/api", tags=["JobLog", "Telemetry"])
app.include_router(neck_router, prefix="/api", tags=["Neck", "Generator"])
app.include_router(parametric_guitar_router, prefix="/api", tags=["Guitar", "Parametric"])

# Wave 10: Instrument + Compare Lab + Drilling + Risk + Learn + Backup (8)
app.include_router(instrument_router, prefix="/api", tags=["Instrument"])
app.include_router(compare_lab_router, prefix="/api", tags=["Compare", "Lab"])
app.include_router(drilling_router, prefix="/api/cam/drilling", tags=["CAM", "Drilling"])
app.include_router(cam_risk_router, prefix="/api", tags=["CAM", "Risk"])
app.include_router(job_risk_router, prefix="/api", tags=["Jobs", "Risk"])
app.include_router(learn_router, prefix="/api", tags=["Learn", "Telemetry"])
app.include_router(learned_overrides_router, prefix="/api", tags=["Feeds", "Learned"])
app.include_router(cam_backup_router, prefix="/api", tags=["CAM", "Backup"])

# Wave 11: Analytics + Probe + LTB Calculator + CAM Tools (8)
app.include_router(analytics_router, prefix="/api", tags=["Analytics"])
app.include_router(advanced_analytics_router, prefix="/api", tags=["Analytics", "Advanced"])
app.include_router(probe_router, prefix="/api", tags=["Probe", "Touch-off"])
app.include_router(ltb_calculator_router, prefix="/api", tags=["Calculator", "LTB"])
app.include_router(dashboard_router, prefix="/api", tags=["Dashboard"])
app.include_router(cam_settings_router, prefix="/api", tags=["CAM", "Settings"])
app.include_router(cam_biarc_router, prefix="/api", tags=["CAM", "Biarc"])
app.include_router(job_intelligence_router, prefix="/api", tags=["Jobs", "Intelligence"])

# Wave 12: CAM Extensions + Compare Risk + Fret Export + Polygon (8)
app.include_router(cam_adaptive_benchmark_router, prefix="/api", tags=["CAM", "Benchmark"])
app.include_router(cam_fret_slots_export_router, prefix="/api", tags=["CAM", "Fret Export"])
app.include_router(cam_risk_aggregate_router, prefix="/api", tags=["CAM", "Risk"])
app.include_router(compare_risk_aggregate_router, prefix="/api", tags=["Compare", "Risk"])
app.include_router(compare_risk_bucket_detail_router, prefix="/api", tags=["Compare", "Risk"])
app.include_router(polygon_offset_router, prefix="/api", tags=["CAM", "Polygon"])
app.include_router(job_insights_router, prefix="/api", tags=["Jobs", "Insights"])
app.include_router(pipeline_preset_router, prefix="/api", tags=["Pipeline", "Presets"])

# Wave 13 (FINAL): Art Presets + CAM Utilities + Compare + Monitor (10)
app.include_router(art_presets_router, prefix="/api", tags=["Art", "Presets"])
app.include_router(cam_compare_diff_router, prefix="/api", tags=["CAM", "Compare"])
app.include_router(cam_dxf_adaptive_router, prefix="/api", tags=["CAM", "DXF"])
app.include_router(cam_pipeline_preset_run_router, prefix="/api", tags=["CAM", "Pipeline"])
app.include_router(cam_polygon_offset_router, prefix="/api", tags=["CAM", "Polygon"])
app.include_router(cam_simulate_router, prefix="/api", tags=["CAM", "Simulate"])
app.include_router(compare_automation_router, prefix="/api", tags=["Compare", "Automation"])
app.include_router(compare_risk_bucket_export_router, prefix="/api", tags=["Compare", "Export"])
app.include_router(health_router_ext, prefix="/api/system", tags=["Health", "Extended"])
app.include_router(live_monitor_router, prefix="/api", tags=["Monitor", "Live"])

# CNC Production (1)
app.include_router(cnc_compare_jobs_router, prefix="/api/cnc/compare", tags=["CNC Production"])

# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "version": "2.0.0-clean"}


@app.get("/api/health", tags=["Health"])
async def api_health_check():
    """API health check with router summary"""
    return {
        "status": "healthy",
        "version": "2.0.0-clean",
        "routers": {
            "core_cam": 11,
            "rmos": 1,
            "cam_subsystem": 8,
            "pipeline": 2,
            "blueprint": 1,
            "machine_config": 3,
            "instrument_geometry": 1,
            "saw_lab": 1,
            "specialty": 4,
            "gcode_generators": 2,
            "cad_engine": 1,
            "rosette_system": 2,
            "smart_guitar_temperaments": 1,
            "cnc_production": 1,
            "wave7_calculators_frets_bridge": 3,
            "wave8_presets_rmos_cam": 7,
            "wave9_ai_drill_compare_neck": 8,
            "wave10_instrument_risk_learn": 8,
            "wave11_analytics_probe_calc": 8,
            "wave12_cam_risk_polygon": 8,
            "wave13_final_art_monitor": 10,
        },
        "total_working": 91,
        "broken_pending_fix": 9,
        "phantoms_removed": 84,
    }
