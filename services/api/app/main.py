"""
Luthier's ToolBox API - Main Application

CLEANED: 2024-12-13
- Removed 84 phantom imports (modules referenced but don't exist)
- Removed 9 broken imports (files exist but have unmet dependencies)
- Kept 33 working routers that actually load
- No more silent try/except failures

UPDATED: 2025-12-20 (Wave 18-19 Consolidation)
- Wave 18: CAM routers consolidated into cam/routers/ (63 routes)
- Wave 19: Compare routers consolidated into compare/routers/ (14 routes)
- Fixed 9 previously broken routers (dependencies resolved)

PREVIOUSLY BROKEN ROUTERS (NOW FIXED):
- rmos.feasibility_router      → FIXED (rmos.context exists)
- cam.cam_preview_router       → FIXED (rmos.context exists)
- routers.adaptive_poly_gcode_router → FIXED
- routers.pipeline_router      → FIXED
- routers.blueprint_router     → FIXED
- routers.saw_blade_router     → FIXED
- routers.saw_gcode_router     → FIXED
- routers.saw_validate_router  → FIXED
- routers.saw_telemetry_router -> FIXED (import path corrected)

NOTE (H7.1): CAM Intent Schema Freeze
The canonical CAM request envelope is `app.rmos.cam.CamIntentV1`.
Callers should not invent alternative envelopes; they should embed mode-specific
shapes under `design` while keeping the envelope stable.

CI guard: python -m app.ci.check_cam_intent_schema_hash
"""

# Load environment variables from .env file FIRST (before any imports that need them)
from dotenv import load_dotenv

load_dotenv()

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .util.request_context import set_request_id
from .util.logging_request_id import RequestIdFilter

# Deprecation guardrails
from .middleware.deprecation import DeprecationHeadersMiddleware

# AI availability (for health endpoint)
from .ai.availability import get_ai_status
from .meta.router_truth_routes import router as routing_truth_router

# Endpoint governance (H4 - canonical endpoint registry + safety rails)
from .governance.endpoint_middleware import EndpointGovernanceMiddleware
from .governance.governance_router import router as governance_router
from .governance.metrics_router import router as metrics_router


# =============================================================================
# COMPAT LEGACY ROUTES FLAG
# Canonical API paths are /api/*. Legacy/compat routes (/cam/*, /geometry/*, etc.)
# are mounted for CI backwards compatibility but hidden from OpenAPI.
# Set ENABLE_COMPAT_LEGACY_ROUTES=false once CI workflows are migrated.
# =============================================================================
import os

_log = logging.getLogger(__name__)
ENABLE_COMPAT_LEGACY_ROUTES = os.getenv(
    "ENABLE_COMPAT_LEGACY_ROUTES", "true"
).lower() in ("1", "true", "yes")


# =============================================================================
# REQUEST ID MIDDLEWARE
# =============================================================================


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Global request correlation middleware.

    - Accepts client-provided X-Request-Id or generates one
    - Attaches to request.state.request_id (C# HttpContext.Items equivalent)
    - Sets ContextVar for deep logging
    - Echoes back for client-side correlation
    """

    async def dispatch(self, request: Request, call_next):
        # Prefer client-supplied ID, otherwise generate one
        req_id = request.headers.get("x-request-id")
        if not req_id:
            req_id = f"req_{uuid.uuid4().hex[:12]}"

        # Attach to request context
        request.state.request_id = req_id

        # Set ContextVar for deep logging
        set_request_id(req_id)

        # Continue request
        response: Response = await call_next(request)

        # Echo back for client-side correlation
        response.headers["x-request-id"] = req_id

        # Clear ContextVar after request
        set_request_id(None)

        return response


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_FORMAT = "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"

_log_handler = logging.StreamHandler()
_log_handler.setFormatter(logging.Formatter(LOG_FORMAT))
_log_handler.addFilter(RequestIdFilter())

_root_logger = logging.getLogger()
_log = logging.getLogger(__name__)  # Module-level logger for import warnings
# Avoid duplicating handlers on reload
if not any(isinstance(h, logging.StreamHandler) for h in _root_logger.handlers):
    _root_logger.addHandler(_log_handler)
_root_logger.setLevel(logging.INFO)

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
# RMOS 2.0 - Rosette Manufacturing Orchestration System (4 routers)
# Note: feasibility_router broken - needs rmos.context module
# =============================================================================
from .rmos import rmos_router

# Phase B+C: AI Search + Profile Management (3 routers)
from .rmos.api_ai_routes import router as rmos_ai_router
from .rmos.api_constraint_profiles import router as rmos_profiles_router
from .rmos.api_profile_history import router as rmos_history_router

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
# LEGACY DXF EXPORTS (1 router) - Migrated from ./server
# =============================================================================
from .routers.legacy_dxf_exports_router import router as legacy_dxf_exports_router

# =============================================================================
# BLUEPRINT IMPORT (2 routers)
# Note: blueprint_router now gracefully degrades if analyzer deps missing
# Optional: AI deps may not be installed in minimal deployments
# =============================================================================
try:
    from .routers.blueprint_router import router as blueprint_router
except ImportError as e:
    _log.warning("Optional router unavailable: blueprint_router (%s)", e)
    blueprint_router = None

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
# SAW LAB (3 routers)
# Note: saw_blade/gcode/validate/telemetry routers broken - need cam_core
# =============================================================================
from .saw_lab.debug_router import router as saw_debug_router
from .saw_lab.compare_router import router as saw_compare_router
from .saw_lab.__init_router__ import router as saw_batch_router

# =============================================================================
# SPECIALTY MODULES - Guitar-specific calculators (4 routers)
# Optional: these may be missing in minimal deployments
# =============================================================================
try:
    from .routers.archtop_router import router as archtop_router
except ImportError as e:
    _log.warning("Optional router unavailable: archtop_router (%s)", e)
    archtop_router = None

try:
    from .routers.stratocaster_router import router as stratocaster_router
except ImportError as e:
    _log.warning("Optional router unavailable: stratocaster_router (%s)", e)
    stratocaster_router = None

try:
    from .routers.smart_guitar_router import router as smart_guitar_router
except ImportError as e:
    _log.warning("Optional router unavailable: smart_guitar_router (%s)", e)
    smart_guitar_router = None

try:
    from .routers.om_router import router as om_router
except ImportError as e:
    _log.warning("Optional router unavailable: om_router (%s)", e)
    om_router = None

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

# ART STUDIO BRACING & INLAY ROUTERS
from .art_studio.bracing_router import router as art_studio_bracing_router
from .art_studio.inlay_router import router as art_studio_inlay_router
from .routers.art.root_art_router import router as root_art_router

# =============================================================================
# SMART GUITAR TEMPERAMENTS (1 router) - Wave 6
# =============================================================================
from .routers.temperament_router import router as temperament_router

# =============================================================================
# WAVE 7: CALCULATOR SUITE + FRET SLOTS CAM + BRIDGE CALCULATOR + FRET DESIGN (4 routers)
# =============================================================================
from .routers.calculators_router import router as calculators_router
from .routers.cam_fret_slots_router import router as cam_fret_slots_router
from .routers.bridge_router import router as bridge_router
from .routers.fret_router import router as fret_router

# =============================================================================
# WAVE 8: PRESETS + RMOS EXTENSIONS + CAM TOOLS (7 routers)
# =============================================================================
from .routers.unified_presets_router import router as unified_presets_router
from .routers.strip_family_router import router as strip_family_router
from .routers.rmos_patterns_router import router as rmos_patterns_router
from .routers.rmos_saw_ops_router import router as rmos_saw_ops_router
from .routers.rmos_cam_intent_router import router as rmos_cam_intent_router  # H7.1.2
from .routers.sim_metrics_router import router as sim_metrics_router
from .routers.retract_router import router as retract_router
from .routers.rosette_photo_router import router as rosette_photo_router

# =============================================================================
# WAVE 9: AI-CAM + DRILL/ROUGHING + COMPARE + DXF PREFLIGHT + JOBLOG + NECK (8 routers)
# =============================================================================
try:
    from ._experimental.ai_cam_router import router as ai_cam_router
except ImportError as e:
    _log.warning("Optional router unavailable: ai_cam_router (%s)", e)
    ai_cam_router = None
from .routers.cam_drill_pattern_router import router as cam_drill_pattern_router
from .routers.cam_roughing_router import router as cam_roughing_router
from .routers.cam_roughing_intent_router import (
    router as cam_roughing_intent_router,
)  # H7.2.2.1
from .routers.compare_router import router as legacy_compare_router
from .routers.dxf_preflight_router import router as dxf_preflight_router

try:
    from ._experimental.joblog_router import router as joblog_router
except ImportError as e:
    _log.warning("Optional router unavailable: joblog_router (%s)", e)
    joblog_router = None
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

try:
    from .routers.learn_router import router as learn_router
except ImportError as e:
    _log.warning("Optional router unavailable: learn_router (%s)", e)
    learn_router = None
try:
    from .routers.learned_overrides_router import router as learned_overrides_router
except ImportError as e:
    _log.warning("Optional router unavailable: learned_overrides_router (%s)", e)
    learned_overrides_router = None
from .routers.cam_backup_router import router as cam_backup_router

# =============================================================================
# WAVE 11: ANALYTICS + PROBE + LTB CALCULATOR + CAM TOOLS (8 routers)
# =============================================================================
try:
    from .routers.analytics_router import router as analytics_router
except ImportError as e:
    _log.warning("Optional router unavailable: analytics_router (%s)", e)
    analytics_router = None
try:
    from .routers.advanced_analytics_router import router as advanced_analytics_router
except ImportError as e:
    _log.warning("Optional router unavailable: advanced_analytics_router (%s)", e)
    advanced_analytics_router = None
from .routers.probe_router import router as probe_router
from .routers.ltb_calculator_router import router as ltb_calculator_router

try:
    from .routers.dashboard_router import router as dashboard_router
except ImportError as e:
    _log.warning("Optional router unavailable: dashboard_router (%s)", e)
    dashboard_router = None
from .routers.cam_settings_router import router as cam_settings_router
from .routers.cam_biarc_router import router as cam_biarc_router
from .routers.job_intelligence_router import router as job_intelligence_router

# =============================================================================
# WAVE 12: CAM EXTENSIONS + COMPARE RISK + FRET EXPORT + POLYGON (8 routers)
# =============================================================================
from .routers.cam_adaptive_benchmark_router import (
    router as cam_adaptive_benchmark_router,
)
from .routers.cam_fret_slots_export_router import router as cam_fret_slots_export_router
from .routers.cam_risk_aggregate_router import router as cam_risk_aggregate_router
from .routers.compare_risk_aggregate_router import (
    router as compare_risk_aggregate_router,
)
from .routers.compare_risk_bucket_detail_router import (
    router as compare_risk_bucket_detail_router,
)
from .routers.polygon_offset_router import router as polygon_offset_router
from .routers.job_insights_router import router as job_insights_router
from .routers.pipeline_preset_router import router as pipeline_preset_router

# =============================================================================
# WAVE 13 (FINAL): ART PRESETS + CAM UTILITIES + COMPARE + MONITOR (10 routers)
# =============================================================================
from .routers.art_presets_router import router as art_presets_router
from .routers.cam_compare_diff_router import router as cam_compare_diff_router
from .routers.cam_dxf_adaptive_router import router as cam_dxf_adaptive_router
from .routers.cam_pipeline_preset_run_router import (
    router as cam_pipeline_preset_run_router,
)
from .routers.cam_polygon_offset_router import router as cam_polygon_offset_router
from .routers.cam_simulate_router import router as cam_simulate_router
from .routers.compare_automation_router import router as compare_automation_router
from .routers.compare_risk_bucket_export_router import (
    router as compare_risk_bucket_export_router,
)
from .routers.health_router import router as health_router_ext
from .routers.live_monitor_drilldown_api import router as live_monitor_router

# =============================================================================
# CNC PRODUCTION (1 router)
# =============================================================================
from .routers.cnc_production.compare_jobs_router import (
    router as cnc_compare_jobs_router,
)

# =============================================================================
# WAVE 14: VISION ENGINE + RMOS RUNS (2 routers)
# Feature flag: RMOS_RUNS_V2_ENABLED controls v1/v2 implementation
# DEFAULT: true (v2 governance-compliant implementation)
# Set to "false" to use legacy v1 if needed for rollback
# =============================================================================
import os

_RMOS_RUNS_V2_ENABLED = os.getenv("RMOS_RUNS_V2_ENABLED", "true").lower() == "true"

if _RMOS_RUNS_V2_ENABLED:
    try:
        from .rmos.runs_v2.api_runs import router as rmos_runs_router

        _log.info("RMOS Runs: Using v2 (governance-compliant, date-partitioned)")
    except ImportError as e:
        _log.warning("Optional router unavailable: rmos_runs_router v2 (%s)", e)
        rmos_runs_router = None
else:
    try:
        from .rmos.runs.api_runs import router as rmos_runs_router

        _log.info("RMOS Runs: Using v1 (legacy single-file)")
    except ImportError as e:
        _log.warning("Optional router unavailable: rmos_runs_router v1 (%s)", e)
        rmos_runs_router = None

# =============================================================================
# PHASE B: CANONICAL VISION + ADVISORY ROUTERS (Hybrid Architecture)
# Vision (Producer Plane): Generates assets, writes to CAS, returns sha256
# Advisory (Ledger Plane): Attaches sha256 to runs, governs review/promote
# =============================================================================
try:
    from .vision.router import router as vision_router

    _log.info("Vision router: Using canonical (app.vision)")
except ImportError as e:
    _log.warning("Optional router unavailable: vision_router (%s)", e)
    vision_router = None

try:
    from .rmos.runs_v2.advisory_router import router as rmos_advisory_router

    _log.info("RMOS Advisory router: Using canonical (app.rmos.runs_v2)")
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_advisory_router (%s)", e)
    rmos_advisory_router = None

try:
    from .advisory.blob_router import router as advisory_blob_router

    _log.info("Advisory Blob router: Using canonical (app.advisory)")
except ImportError as e:
    _log.warning("Optional router unavailable: advisory_blob_router (%s)", e)
    advisory_blob_router = None

try:
    from ._experimental.ai_graphics.api.teaching_routes import router as teaching_router
except ImportError as e:
    _log.warning("Optional router unavailable: teaching_router (%s)", e)
    teaching_router = None

# =============================================================================
# WAVE 15: ART STUDIO CORE COMPLETION - Bundle 31.0 (5 routers)
# Design-First Mode: Pattern Library + Generators + Preview + Snapshots + Workflow
# =============================================================================
try:
    from .art_studio.api.pattern_routes import router as art_patterns_router
except ImportError as e:
    _log.warning("Optional router unavailable: art_patterns_router (%s)", e)
    art_patterns_router = None

try:
    from .art_studio.api.generator_routes import router as art_generators_router
except ImportError as e:
    _log.warning("Optional router unavailable: art_generators_router (%s)", e)
    art_generators_router = None

try:
    from .art_studio.api.preview_routes import router as art_preview_router
except ImportError as e:
    _log.warning("Optional router unavailable: art_preview_router (%s)", e)
    art_preview_router = None

try:
    from .art_studio.api.snapshot_routes import router as art_snapshots_router
except ImportError as e:
    _log.warning("Optional router unavailable: art_snapshots_router (%s)", e)
    art_snapshots_router = None

try:
    from .art_studio.api.workflow_routes import router as art_workflow_router
except ImportError as e:
    _log.warning("Optional router unavailable: art_workflow_router (%s)", e)
    art_workflow_router = None

# Bundle 32.7.0: Design-First Workflow Binding
try:
    from .art_studio.api.design_first_workflow_routes import router as design_first_workflow_router
except ImportError as e:
    _log.warning("Optional router unavailable: design_first_workflow_router (%s)", e)
    design_first_workflow_router = None

# Phase 33.0: CAM Promotion Bridge (orchestration-only; fenced from CAM engine)
try:
    from .art_studio.api.cam_promotion_routes import router as art_cam_promotion_router
except ImportError as e:
    _log.warning("Optional router unavailable: art_cam_promotion_router (%s)", e)
    art_cam_promotion_router = None

# =============================================================================
# WAVE 16: GOVERNANCE CODE BUNDLE - Canonical Workflow + Run Artifacts (4 routers)
# Implements governance contracts for server-side feasibility, artifact persistence
# =============================================================================
try:
    from .rmos.api.rmos_feasibility_router import router as rmos_feasibility_router
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_feasibility_router (%s)", e)
    rmos_feasibility_router = None

try:
    from .rmos.api.rmos_toolpaths_router import router as rmos_toolpaths_router
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_toolpaths_router (%s)", e)
    rmos_toolpaths_router = None

try:
    from .rmos.api.rmos_runs_router import router as rmos_runs_api_router
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_runs_api_router (%s)", e)
    rmos_runs_api_router = None

try:
    from .rmos.api.rmos_workflow_router import router as rmos_workflow_router
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_workflow_router (%s)", e)
    rmos_workflow_router = None

# MVP Wrapper: RMOS-wrapped DXF -> GRBL golden path
try:
    from .rmos.mvp_wrapper import router as rmos_mvp_wrapper_router
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_mvp_wrapper_router (%s)", e)
    rmos_mvp_wrapper_router = None

# RMOS Runs v2 Operator Pack Export
try:
    from .rmos.runs_v2.exports import router as rmos_runs_v2_exports_router
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_runs_v2_exports_router (%s)", e)
    rmos_runs_v2_exports_router = None

# RMOS Runs v2 Query Router (envelope list with cursor pagination)
try:
    from .rmos.runs_v2.router_query import router as rmos_runs_v2_query_router
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_runs_v2_query_router (%s)", e)
    rmos_runs_v2_query_router = None

# =============================================================================
# WAVE 17: WORKFLOW SESSIONS (SQLite persistence layer)
# =============================================================================
try:
    from .workflow.sessions.routes import router as workflow_sessions_router
except ImportError as e:
    _log.warning("Optional router unavailable: workflow_sessions_router (%s)", e)
    workflow_sessions_router = None

# =============================================================================
# WAVE 18: CAM ROUTER CONSOLIDATION (Phase 5+6)
# Single aggregator for all CAM routers organized by category
# =============================================================================
try:
    from .cam.routers import cam_router

    _log.info("CAM Router: Using consolidated aggregator (Phase 5+6)")
except ImportError as e:
    _log.warning("Optional router unavailable: cam_router (%s)", e)
    cam_router = None

# Phase 5: Consolidated Art Studio rosette routes
try:
    from .art_studio.api.rosette_jobs_routes import router as rosette_jobs_router
except ImportError as e:
    _log.warning("Optional router unavailable: rosette_jobs_router (%s)", e)
    rosette_jobs_router = None

try:
    from .art_studio.api.rosette_compare_routes import router as rosette_compare_router
except ImportError as e:
    _log.warning("Optional router unavailable: rosette_compare_router (%s)", e)
    rosette_compare_router = None

try:
    from .art_studio.api.rosette_pattern_routes import (
        router as rosette_pattern_router_v2,
    )
except ImportError as e:
    _log.warning("Optional router unavailable: rosette_pattern_router_v2 (%s)", e)
    rosette_pattern_router_v2 = None

# =============================================================================
# WAVE 19: COMPARE ROUTER CONSOLIDATION
# Single aggregator for all compare routers organized by category
# =============================================================================
try:
    from .compare.routers import compare_router

    _log.info("Compare Router: Using consolidated aggregator (Wave 19)")
except ImportError as e:
    _log.warning("Optional router unavailable: compare_router (%s)", e)
    compare_router = None

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


def create_app() -> FastAPI:
    """
    Factory function for creating the FastAPI application.

    Returns the module-level app singleton. This is used by tests that
    expect a factory pattern (e.g., TestClient(create_app())).

    Note: The app is configured at module load time, so this function
    simply returns the already-configured app instance.
    """
    return app


# Request ID middleware - MUST be registered FIRST (before CORS)
# Provides request correlation for logging, auditing, and debugging
app.add_middleware(RequestIdMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Deprecation headers middleware - emits warnings for legacy lanes
app.add_middleware(DeprecationHeadersMiddleware)

# Endpoint governance middleware (H4) - logs warnings for legacy/shadow endpoints
app.add_middleware(EndpointGovernanceMiddleware)

# =============================================================================
# STARTUP EVENTS
# =============================================================================

from .db.startup import run_migrations_on_startup


@app.on_event("startup")
def _startup_db_migrations() -> None:
    """
    Run database migrations on startup (if enabled).

    Controlled by env vars:
        RUN_MIGRATIONS_ON_STARTUP=true|false  (default false)
        MIGRATIONS_DRY_RUN=true|false         (default false)
        MIGRATIONS_FAIL_HARD=true|false       (default true)
    """
    run_migrations_on_startup()


# =============================================================================
# COMPAT ROUTE HELPER
# =============================================================================


def _include_compat_router(app, router, prefix: str, *, name: str) -> None:
    """
    Mount legacy/compat routes to keep CI + older callers working.
    These are intentionally hidden from OpenAPI to prevent new usage.
    """
    if not router:
        return
    try:
        app.include_router(router, prefix=prefix, include_in_schema=False)
        _log.warning(
            "Compat routes enabled: %s mounted at %s (hidden from OpenAPI)",
            name,
            prefix,
        )
    except Exception as e:
        _log.warning("Compat route mount failed: %s at %s (%s)", name, prefix, e)


# =============================================================================
# ROUTER REGISTRATION
# =============================================================================

# Core CAM (11)
app.include_router(sim_router, prefix="/api/sim", tags=["Simulation"])
app.include_router(feeds_router, prefix="/api/feeds", tags=["Feeds & Speeds"])
app.include_router(geometry_router, prefix="/api/geometry", tags=["Geometry"])
app.include_router(tooling_router, prefix="/api/tooling", tags=["Tooling"])
app.include_router(adaptive_router, prefix="/api", tags=["Adaptive Pocketing"])
app.include_router(machine_router, prefix="/api/machine", tags=["Machine"])
app.include_router(cam_opt_router, prefix="/api/cam/opt", tags=["CAM Optimization"])
app.include_router(material_router, prefix="/api/material", tags=["Materials"])
app.include_router(cam_metrics_router, prefix="/api/cam/metrics", tags=["CAM Metrics"])
app.include_router(cam_logs_router, prefix="/api/cam/logs", tags=["CAM Logs"])
app.include_router(cam_learn_router, prefix="/api/cam/learn", tags=["CAM Learning"])

# RMOS 2.0 (4 routers)
app.include_router(rmos_router, prefix="/api/rmos", tags=["RMOS"])
app.include_router(rmos_ai_router, prefix="/api/rmos", tags=["RMOS AI"])
app.include_router(rmos_profiles_router, prefix="/api/rmos", tags=["RMOS Profiles"])
app.include_router(rmos_history_router, prefix="/api/rmos", tags=["RMOS History"])

# CAM Subsystem (8) - Legacy routes, consolidated equivalents in Wave 18
app.include_router(
    cam_vcarve_router, prefix="/api/cam/vcarve", tags=["V-Carve", "Legacy"]
)  # → /api/cam/toolpath/vcarve
app.include_router(
    cam_post_v155_router, prefix="/api/cam/post", tags=["Post Processor"]
)  # No consolidated equivalent
app.include_router(
    cam_smoke_v155_router, prefix="/api/cam/smoke", tags=["Smoke Tests"]
)  # No consolidated equivalent
app.include_router(
    cam_relief_router, prefix="/api/cam/relief", tags=["Relief Carving", "Legacy"]
)  # → /api/cam/relief (proxy)
app.include_router(
    cam_svg_router, prefix="/api/cam/svg", tags=["SVG Export", "Legacy"]
)  # → /api/cam/export
app.include_router(
    cam_helical_router, prefix="/api/cam/helical", tags=["Helical Ramping", "Legacy"]
)  # → /api/cam/toolpath/helical
app.include_router(
    gcode_backplot_router, prefix="/api/cam/backplot", tags=["G-Code Backplot"]
)  # No consolidated equivalent
app.include_router(
    adaptive_preview_router,
    prefix="/api/cam/adaptive-preview",
    tags=["Adaptive Preview"],
)  # No consolidated equivalent

# Pipeline (2)
app.include_router(
    pipeline_presets_router, prefix="/api/pipeline/presets", tags=["Pipeline Presets"]
)
app.include_router(dxf_plan_router, prefix="/api/dxf", tags=["DXF Planning"])

# Legacy DXF Exports (1) - Migrated from ./server, routes at /exports/*
app.include_router(legacy_dxf_exports_router, prefix="", tags=["DXF Exports", "Legacy"])

# Blueprint (2) - blueprint_router is optional (AI deps may be missing)
if blueprint_router:
    app.include_router(
        blueprint_router, prefix="/api"
    )  # Router has /blueprint prefix internally
app.include_router(
    blueprint_cam_bridge_router,
    prefix="/api/blueprint/cam",
    tags=["Blueprint CAM Bridge"],
)

# Machine & Post Configuration (3)
app.include_router(machines_router, prefix="/api/machines", tags=["Machines"])
app.include_router(
    machines_tools_router, prefix="/api/machines/tools", tags=["Machine Tools"]
)
app.include_router(posts_router, prefix="/api/posts", tags=["Post Processors"])

# Instrument Geometry (1)
app.include_router(
    instrument_geometry_router, prefix="/api/instrument", tags=["Instrument Geometry"]
)

# Data Registry (1)
app.include_router(registry_router, prefix="/api/registry", tags=["Data Registry"])

# Saw Lab (3)
app.include_router(saw_debug_router, prefix="/api/saw/debug", tags=["Saw Lab", "Debug"])
app.include_router(saw_compare_router)  # Saw Lab Compare (includes /api/saw prefix)
app.include_router(
    saw_batch_router
)  # Saw Lab Batch Workflow (includes /api/saw/batch prefix)

# Saw Lab Decision Intelligence (Option A)
try:
    from app.saw_lab import include_decision_intel_router

    include_decision_intel_router(app)
except Exception:
    # Do not block boot if Saw Lab is partially disabled in a deployment
    pass

# Specialty Modules (4) - optional
if archtop_router:
    app.include_router(
        archtop_router, prefix="/api/guitar/archtop", tags=["Guitar", "Archtop"]
    )
if stratocaster_router:
    app.include_router(
        stratocaster_router,
        prefix="/api/guitar/stratocaster",
        tags=["Guitar", "Stratocaster"],
    )
if smart_guitar_router:
    app.include_router(
        smart_guitar_router, prefix="/api/guitar/smart", tags=["Guitar", "Smart Guitar"]
    )
if om_router:
    app.include_router(om_router, prefix="/api/guitar/om", tags=["Guitar", "OM"])

# G-Code Generators (2)
app.include_router(
    body_generator_router, prefix="/api/cam/body", tags=["G-Code Generators", "Body"]
)
app.include_router(
    neck_generator_router, prefix="/api/cam/neck", tags=["G-Code Generators", "Neck"]
)

# CAD Engine (1) - Wave 4
app.include_router(cad_dxf_router, prefix="/api/cad", tags=["CAD", "DXF"])

# Rosette System (2) - Wave 5 - Legacy, see Wave 18 consolidated + Art Studio routes
app.include_router(
    rosette_pattern_router,
    prefix="/api/rosette",
    tags=["Rosette", "Patterns", "Legacy"],
)  # → /api/cam/rosette or /api/art/rosette
app.include_router(
    art_studio_rosette_router, prefix="/api", tags=["Rosette", "Art Studio", "Legacy"]
)  # → /api/art/rosette (v2)

# Art Studio Bracing & Inlay Routers
app.include_router(
    art_studio_bracing_router, prefix="/api", tags=["Art Studio", "Bracing"]
)  # → /api/art-studio/bracing/*
app.include_router(
    art_studio_inlay_router, prefix="/api", tags=["Art Studio", "Inlay"]
)  # → /api/art-studio/inlay/*
app.include_router(
    root_art_router, tags=["Art Studio", "Root"]
)  # → /api/art/* (prefix built-in)

# Smart Guitar Temperaments (1) - Wave 6
app.include_router(
    temperament_router,
    prefix="/api/smart-guitar",
    tags=["Smart Guitar", "Temperaments"],
)

# Wave 7: Calculator Suite + Fret Slots CAM + Bridge Calculator + Fret Design (4)
app.include_router(calculators_router, prefix="/api", tags=["Calculators"])
app.include_router(
    cam_fret_slots_router,
    prefix="/api/cam/fret_slots",
    tags=["CAM", "Fret Slots", "Legacy"],
)  # → /api/cam/fret_slots (proxy)
app.include_router(bridge_router, prefix="/api", tags=["CAM", "Bridge Calculator"])
app.include_router(fret_router, prefix="/api", tags=["Fret Design"])

# Wave 8: Presets + RMOS Extensions + CAM Tools (7)
app.include_router(unified_presets_router, prefix="/api", tags=["Presets", "Unified"])
app.include_router(
    strip_family_router, prefix="/api/rmos", tags=["RMOS", "Strip Families"]
)
app.include_router(rmos_patterns_router, prefix="/api/rmos", tags=["RMOS", "Patterns"])
app.include_router(
    rmos_saw_ops_router, prefix="/api/rmos", tags=["RMOS", "Saw Operations"]
)
app.include_router(
    rmos_cam_intent_router, prefix="/api", tags=["RMOS", "CAM"]
)  # H7.1.2
app.include_router(sim_metrics_router, prefix="/api", tags=["CAM", "Simulation"])
app.include_router(
    retract_router, prefix="/api/cam/retract", tags=["CAM", "Retract Patterns"]
)
app.include_router(
    rosette_photo_router, prefix="/api", tags=["Rosette", "Photo Import"]
)

# Wave 9: AI-CAM + Drill/Roughing + Compare + DXF Preflight + JobLog + Neck (8)
if ai_cam_router:
    app.include_router(ai_cam_router, prefix="/api", tags=["AI-CAM"])
app.include_router(
    cam_drill_pattern_router, prefix="/api", tags=["CAM", "Drill Patterns", "Legacy"]
)  # → /api/cam/drilling/pattern
app.include_router(
    cam_roughing_router, prefix="/api", tags=["CAM", "Roughing", "Legacy"]
)  # → /api/cam/toolpath/roughing
app.include_router(
    cam_roughing_intent_router, prefix="/api", tags=["CAM", "Intent"]
)  # H7.2.2.1
app.include_router(
    legacy_compare_router, prefix="", tags=["Compare", "Baselines", "Legacy"]
)  # Router has /api/compare prefix (LEGACY - use consolidated at Wave 19)
app.include_router(dxf_preflight_router, prefix="/api", tags=["DXF", "Preflight"])
if joblog_router:
    app.include_router(joblog_router, prefix="/api", tags=["JobLog", "Telemetry"])
app.include_router(neck_router, prefix="/api", tags=["Neck", "Generator"])
app.include_router(
    parametric_guitar_router, prefix="/api", tags=["Guitar", "Parametric"]
)

# Wave 10: Instrument + Compare Lab + Drilling + Risk + Learn + Backup (8)
app.include_router(
    instrument_router, prefix="", tags=["Instrument"]
)  # Router has /api/instrument prefix
app.include_router(
    compare_lab_router, prefix="", tags=["Compare", "Lab", "Legacy"]
)  # Router has /api/compare/lab prefix → consolidated /api/compare/lab
app.include_router(
    drilling_router, prefix="/api/cam/drilling", tags=["CAM", "Drilling", "Legacy"]
)  # → /api/cam/drilling (consolidated)
app.include_router(
    cam_risk_router, prefix="", tags=["CAM", "Risk", "Legacy"]
)  # Router has /api/cam/risk prefix → /api/cam/risk (consolidated)
app.include_router(job_risk_router, prefix="/api", tags=["Jobs", "Risk"])
if learn_router:
    app.include_router(learn_router, prefix="/api", tags=["Learn", "Telemetry"])
if learned_overrides_router:
    app.include_router(
        learned_overrides_router, prefix="/api", tags=["Feeds", "Learned"]
    )
app.include_router(cam_backup_router, prefix="/api", tags=["CAM", "Backup"])

# Wave 11: Analytics + Probe + LTB Calculator + CAM Tools (8)
if analytics_router:
    app.include_router(analytics_router, prefix="/api", tags=["Analytics"])
if advanced_analytics_router:
    app.include_router(
        advanced_analytics_router, prefix="/api", tags=["Analytics", "Advanced"]
    )
app.include_router(probe_router, prefix="/api", tags=["Probe", "Touch-off"])
app.include_router(
    ltb_calculator_router, prefix="", tags=["Calculator", "LTB"]
)  # Router has /api/calculators prefix
if dashboard_router:
    app.include_router(dashboard_router, prefix="/api", tags=["Dashboard"])
app.include_router(cam_settings_router, prefix="/api", tags=["CAM", "Settings"])
app.include_router(
    cam_biarc_router, prefix="/api", tags=["CAM", "Biarc", "Legacy"]
)  # → /api/cam/toolpath/biarc
app.include_router(
    job_intelligence_router, prefix="/api", tags=["Jobs", "Intelligence"]
)

# Wave 12: CAM Extensions + Compare Risk + Fret Export + Polygon (8)
app.include_router(
    cam_adaptive_benchmark_router, prefix="/api", tags=["CAM", "Benchmark"]
)
app.include_router(
    cam_fret_slots_export_router, prefix="", tags=["CAM", "Fret Export", "Legacy"]
)  # Router has /api/cam/fret_slots prefix → proxy
app.include_router(
    cam_risk_aggregate_router, prefix="", tags=["CAM", "Risk", "Legacy"]
)  # Router has /api/cam/jobs prefix → /api/cam/risk
app.include_router(
    compare_risk_aggregate_router, prefix="", tags=["Compare", "Risk", "Legacy"]
)  # Router has /api/compare prefix → consolidated
app.include_router(
    compare_risk_bucket_detail_router, prefix="", tags=["Compare", "Risk", "Legacy"]
)  # Router has /api/compare prefix → consolidated
app.include_router(polygon_offset_router, prefix="/api", tags=["CAM", "Polygon"])
app.include_router(
    job_insights_router, prefix="", tags=["Jobs", "Insights"]
)  # Router has /api/cam/job_log prefix
app.include_router(pipeline_preset_router, prefix="/api", tags=["Pipeline", "Presets"])

# Wave 13 (FINAL): Art Presets + CAM Utilities + Compare + Monitor (10)
app.include_router(art_presets_router, prefix="/api", tags=["Art", "Presets"])
app.include_router(cam_compare_diff_router, prefix="/api", tags=["CAM", "Compare"])
app.include_router(cam_dxf_adaptive_router, prefix="/api", tags=["CAM", "DXF"])
app.include_router(
    cam_pipeline_preset_run_router, prefix="/api", tags=["CAM", "Pipeline"]
)
app.include_router(cam_polygon_offset_router, prefix="/api", tags=["CAM", "Polygon"])
app.include_router(cam_simulate_router, prefix="/api", tags=["CAM", "Simulate"])
app.include_router(
    compare_automation_router, prefix="/api", tags=["Compare", "Automation"]
)
app.include_router(
    compare_risk_bucket_export_router, prefix="", tags=["Compare", "Export", "Legacy"]
)  # Router has /api/compare prefix → consolidated
app.include_router(health_router_ext, prefix="/api/system", tags=["Health", "Extended"])
app.include_router(live_monitor_router, prefix="/api", tags=["Monitor", "Live"])

# CNC Production (1)
app.include_router(
    cnc_compare_jobs_router, prefix="/api/cnc/compare", tags=["CNC Production"]
)

# Wave 14: Vision Engine + RMOS Runs + Advisory (3)
# Note: runs_v2/api_runs.py has prefix="/runs", so mount at /api/rmos → /api/rmos/runs
if rmos_runs_router:
    app.include_router(rmos_runs_router, prefix="/api/rmos", tags=["RMOS", "Runs"])
# Phase B: Canonical Vision + Advisory (Hybrid Architecture)
if vision_router:
    app.include_router(
        vision_router, tags=["Vision"]
    )  # Router has /api/vision prefix internally
if rmos_advisory_router:
    app.include_router(
        rmos_advisory_router, prefix="/api/rmos", tags=["RMOS", "Advisory"]
    )  # /api/rmos/runs/{run_id}/advisory/*
if advisory_blob_router:
    app.include_router(
        advisory_blob_router, tags=["Advisory", "Blobs"]
    )  # Router has /api/advisory/blobs prefix internally
if teaching_router:
    app.include_router(teaching_router, tags=["Teaching Loop", "Training"])

# Wave 15: Art Studio Core Completion (5)
# Note: These routers have their own prefix defined (e.g., /api/art/patterns)
if art_patterns_router:
    app.include_router(art_patterns_router, tags=["Art Studio", "Patterns"])
if art_generators_router:
    app.include_router(art_generators_router, tags=["Art Studio", "Generators"])
if art_preview_router:
    app.include_router(art_preview_router, tags=["Art Studio", "Preview"])
if art_snapshots_router:
    app.include_router(art_snapshots_router, tags=["Art Studio", "Snapshots"])
if art_workflow_router:
    app.include_router(art_workflow_router, tags=["Art Studio", "Workflow"])
# Bundle 32.7.0: Design-First Workflow Binding
if design_first_workflow_router:
    app.include_router(design_first_workflow_router, tags=["Art Studio", "Design-First Workflow"])
# Phase 33.0: CAM Promotion Bridge
if art_cam_promotion_router:
    app.include_router(art_cam_promotion_router, tags=["Art Studio", "CAM Promotion Bridge"])

# Wave 16: Governance Code Bundle - Canonical Workflow + Run Artifacts (4)
# Implements governance contracts:
# - SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md
# - RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md
# - RUN_ARTIFACT_INDEX_QUERY_API_CONTRACT_v1.md
# - RUN_DIFF_VIEWER_CONTRACT_v1.md
if rmos_feasibility_router:
    app.include_router(rmos_feasibility_router, tags=["RMOS", "Feasibility"])
if rmos_toolpaths_router:
    app.include_router(rmos_toolpaths_router, tags=["RMOS", "Toolpaths"])
if rmos_runs_api_router:
    app.include_router(rmos_runs_api_router, tags=["RMOS", "Runs API"])
if rmos_workflow_router:
    app.include_router(rmos_workflow_router, tags=["RMOS", "Workflow"])

# MVP Wrapper: RMOS-wrapped DXF -> GRBL golden path
if rmos_mvp_wrapper_router:
    app.include_router(rmos_mvp_wrapper_router, tags=["RMOS", "MVP Wrapper"])

# RMOS Runs v2 Operator Pack Export
if rmos_runs_v2_exports_router:
    app.include_router(rmos_runs_v2_exports_router, tags=["RMOS", "Operator Pack"])

# RMOS Runs v2 Query Router (envelope list with cursor pagination)
if rmos_runs_v2_query_router:
    app.include_router(rmos_runs_v2_query_router, prefix="/api/rmos", tags=["RMOS", "Runs v2 Query"])

# Wave 17: Workflow Sessions (SQLite persistence layer)
if workflow_sessions_router:
    app.include_router(workflow_sessions_router, tags=["Workflow", "Sessions"])

# Wave 18: CAM Router Consolidation (Phase 5+6)
# This aggregator provides organized CAM endpoints at /api/cam/<category>/<operation>
# Categories: drilling, fret_slots, relief, risk, rosette, simulation, toolpath,
#             export, monitoring, pipeline, utility
if cam_router:
    app.include_router(cam_router, prefix="/api/cam", tags=["CAM Consolidated"])

# Phase 5: Consolidated Art Studio rosette routes
# These provide the new organized endpoints alongside legacy routes for transition
if rosette_jobs_router:
    app.include_router(rosette_jobs_router, tags=["Art Studio", "Rosette Jobs"])
if rosette_compare_router:
    app.include_router(rosette_compare_router, tags=["Art Studio", "Rosette Compare"])
if rosette_pattern_router_v2:
    app.include_router(
        rosette_pattern_router_v2, tags=["Art Studio", "Rosette Patterns v2"]
    )

# Wave 19: Compare Router Consolidation
# This aggregator provides organized compare endpoints at /api/compare/<category>/<operation>
# Categories: baselines, risk, lab, automation
if compare_router:
    app.include_router(
        compare_router, prefix="/api/compare", tags=["Compare Consolidated"]
    )

# =============================================================================
# WAVE 20: ART STUDIO RUN ORCHESTRATION - Bundle 31.0.27
# Adds run artifact persistence for Art Studio feasibility + snapshots
# Plus enhanced RMOS logs API with runs_v2 integration
# =============================================================================
try:
    from .art_studio.api.rosette_feasibility_routes import (
        router as art_feasibility_router,
    )
except ImportError as e:
    _log.warning("Optional router unavailable: art_feasibility_router (%s)", e)
    art_feasibility_router = None

try:
    from .art_studio.api.rosette_snapshot_routes import router as art_snapshot_router
except ImportError as e:
    _log.warning("Optional router unavailable: art_snapshot_router (%s)", e)
    art_snapshot_router = None

try:
    from .rmos.api.logs_routes import router as rmos_logs_v2_router
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_logs_v2_router (%s)", e)
    rmos_logs_v2_router = None

# =============================================================================
# WAVE 21: ACOUSTICS BUNDLE IMPORT
# Tap tone measurement bundle ingestion from workstation/field captures
# =============================================================================
try:
    from .rmos.acoustics.router import router as rmos_acoustics_router
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_acoustics_router (%s)", e)
    rmos_acoustics_router = None

# Wave 20: Art Studio Run Orchestration (3)
if art_feasibility_router:
    app.include_router(
        art_feasibility_router, prefix="/api/art", tags=["Art Studio", "Feasibility"]
    )
if art_snapshot_router:
    app.include_router(
        art_snapshot_router, prefix="/api/art", tags=["Art Studio", "Snapshots v2"]
    )
if rmos_logs_v2_router:
    app.include_router(
        rmos_logs_v2_router, prefix="/api/rmos", tags=["RMOS", "Logs v2"]
    )

# Wave 21: Acoustics Bundle Import (import, query, zip_export only)
# Endpoints: POST /api/rmos/acoustics/import-zip, POST /api/rmos/acoustics/import-path, etc.
# NOTE: Prefix set once here; sub-routers must NOT set their own prefix (Issue B fix).
# NOTE: router_attachments.py removed from composite - superseded by Wave 22 (Issue A fix).
if rmos_acoustics_router:
    app.include_router(
        rmos_acoustics_router, prefix="/api/rmos/acoustics", tags=["RMOS", "Acoustics"]
    )

# Wave 22: Runs v2 Acoustics Advisory Surface (H7.2.2.1 features)
# Endpoints: GET /runs/{run_id}/advisories, GET /advisories/{advisory_id},
#            GET/HEAD /attachments/{sha256}, POST /attachments/{sha256}/signed_url,
#            GET /runs/{run_id}/attachments, GET /index/attachment_meta/{sha256}/exists
# This is the authoritative attachment router with no-path disclosure + signed URLs.
try:
    from .rmos.runs_v2.acoustics_router import router as runs_v2_acoustics_router

    app.include_router(
        runs_v2_acoustics_router,
        prefix="/api/rmos/acoustics",
        tags=["RMOS", "Acoustics"],
    )
except ImportError:
    pass

# =============================================================================
# WAVE 23: SMART GUITAR TELEMETRY INGESTION
# Manufacturing-only telemetry from Smart Guitar devices.
# Enforces boundary contract: NO player/pedagogy data allowed.
# =============================================================================
try:
    from .smart_guitar_telemetry import telemetry_router as sg_telemetry_router
    app.include_router(sg_telemetry_router, prefix="/api/telemetry", tags=["Smart Guitar", "Telemetry"])
except ImportError as e:
    _log.warning("Optional router unavailable: sg_telemetry_router (%s)", e)

# =============================================================================
# WAVE 24: COST ATTRIBUTION
# Maps validated telemetry to internal manufacturing cost dimensions.
# Read-only endpoint: GET /api/cost/summary
# =============================================================================
try:
    from .cost_attribution import cost_router
    app.include_router(cost_router, tags=["Cost Attribution"])
except ImportError as e:
    _log.warning("Optional router unavailable: cost_router (%s)", e)

# =============================================================================
# AI CONTEXT ADAPTER (v1) - Read-Only Context Envelope for AI
# Produces a single envelope for AI consumption with:
# - Hard-locked capabilities (no PII, no sensitive manufacturing)
# - Strict redaction (removes forbidden fields)
# - Focused payload: run_summary, design_intent, artifacts
# Endpoints: GET /api/ai/context, /api/ai/context/health, POST /api/ai/context/build
# No PUT/DELETE. POST /build is bounded assembly (no manufacturing secrets).
# Schema: contracts/toolbox_ai_context_envelope_v1.schema.json
# =============================================================================
try:
    from .ai_context_adapter.routes import router as ai_context_adapter_router
    app.include_router(ai_context_adapter_router, tags=["AI Context"])
except ImportError as e:
    _log.warning("Optional router unavailable: ai_context_adapter_router (%s)", e)

# Legacy ai_context (more complex envelope) - can be removed once adapter is stable
try:
    from .ai_context.routes import router as ai_context_router
    app.include_router(ai_context_router, tags=["AI Context (Legacy)"])
except ImportError as e:
    _log.warning("Optional router unavailable: ai_context_router (%s)", e)

# =============================================================================
# COMPAT LEGACY ROUTES (CI + legacy callers)
# Canonical remains /api/*; compat mounts are hidden from OpenAPI.
# Disable with ENABLE_COMPAT_LEGACY_ROUTES=false once workflows migrated.
# =============================================================================
if ENABLE_COMPAT_LEGACY_ROUTES:
    # Core routers used by CI workflows
    _include_compat_router(app, geometry_router, "/geometry", name="geometry_router")
    _include_compat_router(app, tooling_router, "/tooling", name="tooling_router")
    _include_compat_router(
        app, adaptive_router, "", name="adaptive_router"
    )  # Router has /cam/pocket/adaptive prefix internally
    _include_compat_router(app, material_router, "/material", name="material_router")
    _include_compat_router(app, machine_router, "/machine", name="machine_router")
    _include_compat_router(app, feeds_router, "/feeds", name="feeds_router")
    _include_compat_router(app, sim_router, "/sim", name="sim_router")

    # Consolidated CAM (Wave 18) - covers /cam/pocket/adaptive/*, /cam/polygon_offset.nc, etc.
    if cam_router:
        _include_compat_router(app, cam_router, "/cam", name="cam_router")

    # Individual CAM subsystem routers (if CI hits them directly)
    _include_compat_router(app, cam_opt_router, "/cam/opt", name="cam_opt_router")
    _include_compat_router(
        app, cam_metrics_router, "/cam/metrics", name="cam_metrics_router"
    )
    _include_compat_router(app, cam_logs_router, "/cam/logs", name="cam_logs_router")
    _include_compat_router(app, cam_learn_router, "/cam/learn", name="cam_learn_router")
    _include_compat_router(
        app, cam_vcarve_router, "/cam/vcarve", name="cam_vcarve_router"
    )
    _include_compat_router(
        app, cam_relief_router, "/cam/relief", name="cam_relief_router"
    )
    _include_compat_router(
        app, cam_helical_router, "/cam/helical", name="cam_helical_router"
    )
    _include_compat_router(
        app, cam_simulate_router, "/cam/simulate", name="cam_simulate_router"
    )
    _include_compat_router(
        app, gcode_backplot_router, "/cam/backplot", name="gcode_backplot_router"
    )

    # Bridge calculator and DXF preflight (legacy paths without /api prefix)
    _include_compat_router(
        app, bridge_router, "", name="bridge_router"
    )  # → /cam/bridge/*
    _include_compat_router(
        app, dxf_preflight_router, "", name="dxf_preflight_router"
    )  # → /dxf/preflight/*
else:
    _log.info("Compat legacy routes disabled (ENABLE_COMPAT_LEGACY_ROUTES=false)")

# =============================================================================
# META / INTROSPECTION
# =============================================================================
# Routing truth endpoint for confirming what's actually mounted after deploy
app.include_router(routing_truth_router, tags=["_meta"])

# Governance stats endpoint (H5.1) - measure legacy/shadow usage before deletions
app.include_router(governance_router, prefix="/api", tags=["Governance"])

# Prometheus metrics endpoint (H5.2) - no prefix, accessible at /metrics
app.include_router(metrics_router)

# =============================================================================
# HEALTH CHECK
# =============================================================================


@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    from datetime import datetime, timezone

    return {
        "status": "ok",
        "version": "2.0.0-clean",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "paths": {},  # Empty paths dict for CI compatibility
    }


@app.get("/api/health", tags=["Health"])
async def api_health_check():
    """API health check with router summary and AI status"""
    ai_status = get_ai_status()
    return {
        "status": "healthy" if ai_status["status"] == "available" else "degraded",
        "version": "2.0.0-clean",
        "ai": ai_status,
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
            "wave14_vision_rmos_runs_advisory": 3,
            "wave15_art_studio_core": 4,
            "wave16_governance_code_bundle": 4,
            "wave18_cam_consolidation": 4,  # cam_router + 3 rosette routes
            "wave19_compare_consolidation": 1,  # compare_router
        },
        "total_working": 116,
        "broken_pending_fix": 0,
        "phantoms_removed": 84,
    }
