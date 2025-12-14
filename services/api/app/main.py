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

# Saw Lab (1)
app.include_router(saw_debug_router, prefix="/api/saw/debug", tags=["Saw Lab", "Debug"])

# Specialty Modules (4)
app.include_router(archtop_router, prefix="/api/guitar/archtop", tags=["Guitar", "Archtop"])
app.include_router(stratocaster_router, prefix="/api/guitar/stratocaster", tags=["Guitar", "Stratocaster"])
app.include_router(smart_guitar_router, prefix="/api/guitar/smart", tags=["Guitar", "Smart Guitar"])
app.include_router(om_router, prefix="/api/guitar/om", tags=["Guitar", "OM"])

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
            "cnc_production": 1,
        },
        "total_working": 33,
        "broken_pending_fix": 9,
        "phantoms_removed": 84,
    }
