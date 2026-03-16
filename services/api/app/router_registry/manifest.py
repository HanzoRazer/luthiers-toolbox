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
        module="app.governance.governance_consolidated_router",
        prefix="",  # router has /api/_meta prefix
        tags=["Meta", "Governance"],
        required=True,  # CI routing truth validation
        category="core",
    ),
    # Auth Router (Phase 3 SaaS)
    RouterSpec(
        module="app.routers.auth_router",
        prefix="",  # router has /api/auth prefix
        tags=["Auth"],
        required=True,
        category="core",
    ),
    # Job Queue (Phase 3.3 Async)
    RouterSpec(
        module="app.core.job_queue.router",
        prefix="",  # router has /api/jobs prefix
        tags=["Jobs", "Async"],
        required=False,
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
        module="app.routers.material_router",
        prefix="/api",
        tags=["Material", "Energy Model"],
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
    # Decomposed from stub_routes.py
    RouterSpec(
        module="app.rmos.rosette_cam_router",
        prefix="/api/rmos",
        tags=["RMOS", "Rosette", "CAM"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.safety_router",
        prefix="/api/rmos",
        tags=["RMOS", "Safety"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.live_monitor_router",
        prefix="/api/rmos",
        tags=["RMOS", "Live Monitor"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.mvp_router",
        prefix="/api/rmos",
        tags=["RMOS", "MVP"],
        category="rmos",
    ),
    RouterSpec(
        module="app.rmos.analytics.router",
        prefix="/api/rmos",
        tags=["RMOS", "Analytics"],
        category="rmos",
    ),
    # -------------------------------------------------------------------------
    # CAM SUBSYSTEM
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.gcode_consolidated_router",
        prefix="/api",
        tags=["G-code", "CAM"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.adaptive_preview_router",
        prefix="/api",
        tags=["Adaptive", "Preview"],
        category="cam",
    ),
    RouterSpec(
        module="app.routers.dxf_adaptive_consolidated_router",
        router_attr="router",
        prefix="/api",
        tags=["cam", "dxf", "adaptive"],
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
        module="app.routers.machines_consolidated_router",
        prefix="/api/machines",
        tags=["Machines"],
        category="config",
    ),
    RouterSpec(
        module="app.routers.machines_consolidated_router",
        router_attr="cam_machines_router",
        prefix="/api",
        tags=["CAM", "Machines"],
        category="cam",
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
    RouterSpec(
        module="app.art_studio.api.rosette_pattern_routes",
        prefix="",
        tags=["Art Studio", "Rosette Patterns"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.rosette_manufacturing_routes",
        prefix="",
        tags=["Art Studio", "Rosette Manufacturing"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.preview_routes",
        prefix="/api",
        tags=["Art Studio", "Preview"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.bracing_router",
        prefix="/api",
        tags=["Art Studio", "Bracing"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.inlay_router",
        prefix="/api",
        tags=["Art Studio", "Inlay"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.inlay_pattern_routes",
        prefix="",
        tags=["Art Studio", "Inlay Patterns"],
        category="art_studio",
    ),
    RouterSpec(
        module="app.art_studio.api.rosette_designer_routes",
        prefix="/api/art/rosette-designer",
        tags=["Art Studio", "Rosette Designer"],
        category="art_studio",
    ),
    # -------------------------------------------------------------------------
    # HEADSTOCK INLAY ROUTER (INLAY-01)
    # Moved from art_studio to instruments/guitar (host geometry context)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.instruments.guitar.headstock_inlay_router",
        prefix="/api",
        tags=["Instruments", "Headstock Inlay"],
        category="instruments",
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
    RouterSpec(
        module="app.routers.music",
        prefix="/api/music",
        tags=["Music", "Temperaments"],
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
    # # -------------------------------------------------------------------------
    # # CAM DRILLING (Modal G81/G83 cycles)
    # # -------------------------------------------------------------------------
    # RouterSpec(
    #     module="app.cam.routers.drilling",
    #     prefix="/api/cam/drilling",
    #     tags=["CAM", "Drilling"],
    #     category="cam",
    # ),
    # -------------------------------------------------------------------------
    # CAM DOMAIN ROUTERS (decomposed from stub_routes.py)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.cam.routers.job_intelligence_router",
        prefix="/api/cam",
        tags=["CAM", "Job Intelligence"],
        category="cam",
    ),
    RouterSpec(
        module="app.cam.routers.bridge_export_router",
        prefix="/api/cam",
        tags=["CAM", "Bridge"],
        category="cam",
    ),
    RouterSpec(
        module="app.cam.routers.fret_slots_router",
        prefix="/api/cam",
        tags=["CAM", "Fret Slots"],
        category="cam",
    ),
    # -------------------------------------------------------------------------
    # ROSETTE PHOTO BATCH (Wave 27 - Feature Recovery)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.cam.rosette.photo_batch_router",
        prefix="",  # Router has its own /api/cam/rosette/photo-batch prefix
        tags=["CAM", "Rosette", "Batch"],
        category="cam",
    ),
    # -------------------------------------------------------------------------
    # DEAD CODE RECOVERY (Wave 27.1 - Restored Routers)
    # -------------------------------------------------------------------------
    # Guitar CAM router - archtop, OM, stratocaster, registry (Wave 27.2)
    RouterSpec(
        module="app.routers.cam.guitar",
        prefix="/api/cam/guitar",
        tags=["CAM", "Guitar"],
        category="cam",
    ),
    # Post-processor V155 - CRC, lead-in/out, corner smoothing (Wave 27.2)
    RouterSpec(
        module="app.routers.cam_post_v155_router",
        prefix="/api/cam/post",
        tags=["CAM", "Post", "GCode"],
        category="cam",
    ),
    # DXF -> Adaptive Pocket workflow (P1-HIGH)

    # Relief CAM router - heightmap, roughing, finishing, simulation (P1-HIGH)
    RouterSpec(
        module="app.routers.cam_relief_router",
        prefix="/api",  # Router has /cam/relief prefix
        tags=["CAM", "Relief"],
        category="cam",
    ),
    # CNC Production presets CRUD (P2-MEDIUM)
    RouterSpec(
        module="app.routers.cnc_production.presets_router",
        prefix="/api",  # Router has /cnc/presets prefix
        tags=["CNC", "Presets"],
        category="cnc",
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

    # -------------------------------------------------------------------------
    # BUSINESS STARTUP SUITE
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.business.router",
        prefix="",  # router already has /api/business prefix
        tags=["Business"],
        category="business",
    ),

    # -------------------------------------------------------------------------
    # ANALYZER (Acoustic Interpretation)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.analyzer.router",
        prefix="",  # router already has /api/analyzer prefix
        tags=["Analyzer"],
        category="analyzer",
    ),

    # -------------------------------------------------------------------------
    # RMOS VALIDATION (Wave 25 - 30-run protocol)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.rmos.validation.router",
        prefix="",  # router has /api/rmos/validation prefix
        tags=["RMOS", "Validation"],
        category="rmos",
    ),
    # -------------------------------------------------------------------------
    # INSTRUMENT GEOMETRY (Neck Taper)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.instrument_geometry.neck_taper.api_router",
        prefix="",  # router has /instrument/neck_taper prefix
        tags=["Instrument", "Neck Taper"],
        category="instrument",
    ),
    # -------------------------------------------------------------------------
    # WORKFLOW SESSIONS (CRUD)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.workflow.sessions.routes",
        prefix="",  # router has /api/workflow/sessions prefix
        tags=["Workflow", "Sessions"],
        category="workflow",
    ),
    # -------------------------------------------------------------------------
    # HEADSTOCK INLAY (AI prompt generation)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.cam.headstock.router",
        prefix="",  # router has /api/cam/headstock/inlay prefix
        tags=["CAM", "Headstock", "Inlay"],
        category="cam",
    ),
    # -------------------------------------------------------------------------
    # PICKUP POSITION CALCULATOR (GAP-04)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.instruments.guitar.pickup_calculator_router",
        prefix="/api",
        tags=["Instruments", "Guitar", "Calculators"],
        category="instrument_geometry",
    ),
    # -------------------------------------------------------------------------
    # ELECTRIC BODY OUTLINE GENERATOR (GAP-07)
    # -------------------------------------------------------------------------
    RouterSpec(
        module="app.routers.instruments.guitar.electric_body_router",
        prefix="/api",
        tags=["Instruments", "Guitar", "Generators"],
        category="instrument_geometry",
    ),

]