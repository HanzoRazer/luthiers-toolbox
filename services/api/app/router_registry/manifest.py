"""Router manifest â€” declarative list of all routers to load."""

from typing import List

from .models import RouterSpec

# =============================================================================
# ROUTER MANIFEST
# =============================================================================
# Organized by wave/category for maintainability

ROUTER_MANIFEST: List[RouterSpec] = [
    # -------------------------------------------------------------------------
    # CORE (Always required)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.health_router",
        prefix="/api",
        tags=["Health"],
        required=True,
        category="core",
    ),
    RouterSpec(
        module="app.governance.metrics_router",
        prefix="",  # /metrics at root
        tags=["Metrics"],
        required=True,
        category="core",
    ),
    # -------------------------------------------------------------------------
    # CAM CORE (11 routers)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.simulation_consolidated_router",
        prefix="/api/cam/sim",
        tags=["CAM Simulation"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.geometry",
        prefix="/api/geometry",
        tags=["Geometry"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.tooling_router",
        prefix="/api/tooling",
        tags=["Tooling"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.adaptive",
        prefix="/api",
        tags=["Adaptive Pocketing"],
        category="cam_core",
    ),
    # CAM Monitoring (consolidated from cam_metrics_router + cam_logs_router)
    RouterSpec(
        module="app.cam.routers.monitoring",
        prefix="/api/cam",
        tags=["CAM Monitoring"],
        category="cam_core",
    ),
    # CAM Utility (consolidated from cam_opt_router + cam_settings, cam_backup, cam_benchmark)
    RouterSpec(
        module="app.cam.routers.utility",
        prefix="/api/cam",
        tags=["CAM Utility"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.cam_learn_router",
        prefix="/api/cam/learn",
        tags=["CAM Learning"],
        category="cam_core",
    ),
    # -------------------------------------------------------------------------
    # RMOS 2.0
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.rmos",
        router_attr="rmos_router",
        prefix="/api/rmos",
        tags=["RMOS"],
        required=True,
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.runs_v2.api_runs",
        prefix="/api/rmos",
        tags=["RMOS", "Runs"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.runs_v2.advisory_router",
        prefix="/api/rmos",
        tags=["RMOS", "Advisory"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.runs_v2.exports",
        prefix="",
        tags=["RMOS", "Operator Pack"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.runs_v2.router_query",
        prefix="/api/rmos",
        tags=["RMOS", "Runs v2 Query"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.api.rmos_runs_router",
        prefix="",
        tags=["RMOS", "Runs API"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.api.logs_routes",
        prefix="/api/rmos",
        tags=["RMOS", "Logs v2"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.stub_routes",
        prefix="/api/rmos",
        tags=["RMOS", "Stubs"],
        category="rmos",
    ),
    # -------------------------------------------------------------------------
    # CAM SUBSYSTEM
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.gcode_backplot_router",
        prefix="/api",
        tags=["G-code", "Backplot"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.adaptive_preview_router",
        prefix="/api",
        tags=["Adaptive", "Preview"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.dxf_plan_router",
        prefix="/api",
        tags=["DXF", "Plan"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.dxf_preflight_router",
        prefix="/api",
        tags=["DXF", "Preflight"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.polygon_offset_router",
        prefix="/api",
        tags=["Geometry", "Polygon"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.cam_polygon_offset_router",
        prefix="/api",
        tags=["CAM", "Polygon"],
        category="cam",
    ),
    # -------------------------------------------------------------------------
    # BLUEPRINT & DXF
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.blueprint",
        prefix="/api",
        tags=["Blueprint"],
        category="blueprint",
    ),
    RouterSpec(
        module="app.routers.blueprint_cam",
        prefix="/api",
        tags=["Blueprint CAM Bridge"],
        category="blueprint",
    ),
    RouterSpec(
        module="app.routers.legacy_dxf_exports_router",
        prefix="",
        tags=["DXF", "Exports"],
        category="blueprint",
    ),
    # -------------------------------------------------------------------------
    # MACHINE & POST CONFIGURATION
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.bridge_presets_router",
        prefix="/api",
        tags=["CAM Bridge"],
        category="config",
    ),
    RouterSpec(
        module="app.routers.machines_router",
        prefix="/api",
        tags=["CAM Machines"],
        category="config",
    ),
    RouterSpec(
        module="app.routers.machines_consolidated_router",
        prefix="/api/machines",
        tags=["Machines"],
        category="config",
    ),
    RouterSpec(
        module="app.routers.posts_consolidated_router",
        prefix="/api/posts",
        tags=["Post Processors"],
        category="config",
    ),
    RouterSpec(
        module="app.routers.registry_router",
        prefix="/api/registry",
        tags=["Data Registry"],
        category="config",
    ),
    # -------------------------------------------------------------------------
    # SAW LAB
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.saw_lab.compare_router",
        prefix="",
        tags=["Saw Lab", "Compare"],
        category="saw_lab",
    ),
    RouterSpec(
        module="app.saw_lab.__init_router__",
        prefix="",
        tags=["Saw Lab", "Batch"],
        required=True,  # Safety-critical
        category="saw_lab",
    ),
    # -------------------------------------------------------------------------
    # ART STUDIO
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.art.root_art_router",
        prefix="",
        tags=["Art Studio", "Root"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.routers.art_presets_router",
        prefix="/api",
        tags=["Art", "Presets"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.pattern_routes",
        prefix="",
        tags=["Art Studio", "Patterns"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.generator_routes",
        prefix="",
        tags=["Art Studio", "Generators"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.snapshot_routes",
        prefix="",
        tags=["Art Studio", "Snapshots"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.rosette_jobs_routes",
        prefix="",
        tags=["Art Studio", "Rosette Jobs"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.rosette_compare_routes",
        prefix="",
        tags=["Art Studio", "Rosette Compare"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.rosette_snapshot_routes",
        prefix="/api/art",
        tags=["Art Studio", "Snapshots v2"],
        category="art_studio",
    ),
    # -------------------------------------------------------------------------
    # VISION
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.vision.router",
        prefix="",
        tags=["Vision"],
        category="vision",
    ),
    RouterSpec(
        module="app.advisory.blob_router",
        prefix="",
        tags=["Advisory", "Blobs"],
        category="vision",
    ),
    # -------------------------------------------------------------------------
    # INSTRUMENT & FRETS
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.instrument_router",
        prefix="",
        tags=["Instrument"],
        category="instrument",
    ),
    RouterSpec(
        module="app.routers.neck_router",
        prefix="/api",
        tags=["Neck", "Generator"],
        category="instrument",
    ),
    # -------------------------------------------------------------------------
    # OPTIONAL/EXPERIMENTAL
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app._experimental.ai_cam_router",
        prefix="/api",
        tags=["AI-CAM"],
        category="experimental",
    ),
    RouterSpec(
        module="app._experimental.joblog_router",
        prefix="/api",
        tags=["JobLog", "Telemetry"],
        category="experimental",
    ),
    RouterSpec(
        module="app.routers.learned_overrides_router",
        prefix="/api",
        tags=["Feeds", "Learned"],
        category="experimental",
    ),
    RouterSpec(
        module="app.routers.analytics_router",
        prefix="/api",
        tags=["Analytics"],
        category="analytics",
    ),
    RouterSpec(
        module="app.routers.advanced_analytics_router",
        prefix="/api",
        tags=["Analytics", "Advanced"],
        category="analytics",
    ),
    # -------------------------------------------------------------------------
    # MISC ROUTERS
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.strip_family_router",
        prefix="/api/rmos",
        tags=["RMOS", "Strip Families"],
        category="misc",
    ),
    RouterSpec(
        module="app.routers.retract_router",
        prefix="/api/cam/retract",
        tags=["CAM", "Retract Patterns"],
        category="misc",
    ),
    RouterSpec(
        module="app.routers.cam_pipeline_preset_run_router",
        prefix="/api",
        tags=["CAM", "Pipeline"],
        category="misc",
    ),
    RouterSpec(
        module="app.routers.cam_risk_router",
        prefix="/api",
        tags=["CAM", "Risk"],
        category="cam",
    ),
    # -------------------------------------------------------------------------
    # ACOUSTICS LIBRARY (Wave 22)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.rmos.runs_v2.acoustics_router",
        prefix="/api/rmos/acoustics",
        tags=["RMOS", "Acoustics"],
        category="rmos",
    ),
    RouterSpec(
        module="app.routers.probe",
        prefix="/api",
        tags=["Probe", "CAM"],
        category="cam",
    ),
    # -------------------------------------------------------------------------
    # CAM STUBS (for missing frontend endpoints)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.cam.routers.stub_routes",
        prefix="/api/cam",
        tags=["CAM", "Stubs"],
        category="cam",
    ),
    # -------------------------------------------------------------------------
    # CONSOLIDATED AGGREGATORS (Wave 18+19)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.cam.routers",
        router_attr="cam_router",
        prefix="/api/cam",
        tags=["CAM Consolidated"],
        category="consolidated",
    ),
    RouterSpec(
        module="app.compare.routers",
        router_attr="compare_router",
        prefix="/api/compare",
        tags=["Compare Consolidated"],
        category="consolidated",
    ),
    # -------------------------------------------------------------------------
    # AI CONTEXT
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.ai_context_adapter.routes",
        prefix="",
        tags=["AI Context"],
        category="ai",
    ),
    # -------------------------------------------------------------------------
    # PROJECT ASSETS (stub for AI Images feature)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.project_assets_router",
        prefix="/api",
        tags=["Projects"],
        category="projects",
    ),
    # -------------------------------------------------------------------------
    # MISC STUBS (for remaining missing endpoints)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.misc_stub_routes",
        prefix="/api",
        tags=["Stubs"],
        category="stubs",
    ),

]
