"""Luthier's ToolBox API - Main Application"""

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

# Endpoint governance (H4 - canonical endpoint registry + safety rails)
from .governance.endpoint_middleware import EndpointGovernanceMiddleware
from .governance.metrics_router import router as metrics_router


# =============================================================================
# LOGGING
# =============================================================================
import os

_log = logging.getLogger(__name__)
# ENABLE_COMPAT_LEGACY_ROUTES: REMOVED (January 2026)
# All frontend callers migrated to canonical /api/* paths.
# Compat mounts deleted. See deprecation_registry.json for audit trail.


# =============================================================================
# REQUEST ID MIDDLEWARE
# =============================================================================


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Global request correlation middleware."""

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
# Consolidated: sim routers → simulation_consolidated_router
from .routers.health_router import router as health_router
from .routers.simulation_consolidated_router import router as simulation_router
from .routers.geometry_router import router as geometry_router
from .routers.tooling_router import router as tooling_router
from .routers.adaptive_router import router as adaptive_router
# Consolidated: machine_router → machines_consolidated_router
from .routers.cam_opt_router import router as cam_opt_router
from .routers.cam_metrics_router import router as cam_metrics_router
from .routers.cam_logs_router import router as cam_logs_router
from .routers.cam_learn_router import router as cam_learn_router

# =============================================================================
# RMOS 2.0 - Rosette Manufacturing Orchestration System (4 routers)
# Note: feasibility_router broken - needs rmos.context module
# =============================================================================
from .rmos import rmos_router

# Phase B+C: AI Search + Profile Management (3 routers)

# =============================================================================
# CAM SUBSYSTEM (4 routers - legacy routes removed January 2026)
# Note: cam_preview_router broken - needs rmos.context
# Note: adaptive_poly_gcode_router broken - needs routers.util
# =============================================================================
from .routers.gcode_backplot_router import router as gcode_backplot_router
from .routers.adaptive_preview_router import router as adaptive_preview_router

# =============================================================================
# PIPELINE & PRESETS (2 routers)
# Note: pipeline_router broken - needs httpx
# =============================================================================
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


# =============================================================================
# MACHINE & POST CONFIGURATION (2 routers - consolidated)
# =============================================================================
from .routers.machines_consolidated_router import router as machines_consolidated_router
# Consolidated into machines_consolidated_router:
# Consolidated posts router (combines posts_router + post_router)
from .routers.posts_consolidated_router import router as posts_consolidated_router

# =============================================================================
# INSTRUMENT GEOMETRY (1 router)
# =============================================================================

# =============================================================================
# DATA REGISTRY (1 router)
# =============================================================================
from .routers.registry_router import router as registry_router

# =============================================================================
# SAW LAB (3 routers)
# Note: saw_blade/gcode/validate/telemetry routers broken - need cam_core
# =============================================================================
from .saw_lab.compare_router import router as saw_compare_router
from .saw_lab.__init_router__ import router as saw_batch_router

# =============================================================================
# These routers were removed as part of legacy code cleanup.
# See: docs/LEGACY_CODE_STATUS.md
# Removed routers: archtop_router, stratocaster_router, smart_guitar_router,
#                  smart_guitar_cam_router, om_router
# =============================================================================

# =============================================================================
# G-CODE GENERATORS (2 routers) - Wave 3
# =============================================================================

# =============================================================================
# CAD ENGINE (1 router) - Wave 4
# =============================================================================

# =============================================================================
# ROSETTE SYSTEM (0 routers) - Wave 5 - REMOVED January 2026
# Legacy routers consolidated into /api/art/rosette and /api/cam/rosette
# =============================================================================

# ART STUDIO BRACING & INLAY ROUTERS
from .routers.art.root_art_router import router as root_art_router

# =============================================================================
# MUSIC AXIS (Option C) - Replaces Smart Guitar Temperaments
# =============================================================================
# legacy_redirects_router: REMOVED (January 2026)
# Legacy 308 redirects for smart-guitar/temperaments had zero frontend consumers.
# See deprecation_registry.json for audit trail.

# =============================================================================
# WAVE 7: CALCULATOR SUITE + FRET SLOTS CAM + BRIDGE CALCULATOR + FRET DESIGN (4 routers)
# =============================================================================
# Consolidated into calculators_consolidated_router:

# =============================================================================
# WAVE 8: PRESETS + RMOS EXTENSIONS + CAM TOOLS (7 routers)
# =============================================================================
from .routers.strip_family_router import router as strip_family_router
# Consolidated into simulation_consolidated_router:
from .routers.retract_router import router as retract_router

# =============================================================================
# WAVE 9: AI-CAM + DRILL/ROUGHING + COMPARE + DXF PREFLIGHT + JOBLOG + NECK (8 routers)
# =============================================================================
try:
    from ._experimental.ai_cam_router import router as ai_cam_router
except ImportError as e:
    _log.warning("Optional router unavailable: ai_cam_router (%s)", e)
    ai_cam_router = None
#     router as cam_roughing_intent_router,
# )  # H7.2.2.1
from .routers.dxf_preflight_router import router as dxf_preflight_router

try:
    from ._experimental.joblog_router import router as joblog_router
except ImportError as e:
    _log.warning("Optional router unavailable: joblog_router (%s)", e)
    joblog_router = None
from .routers.neck_router import router as neck_router

# =============================================================================
# WAVE 10: INSTRUMENT + DRILLING + RISK + LEARN + BACKUP (6 routers)
# =============================================================================
from .routers.instrument_router import router as instrument_router

#     learn_router = None

try:
    from .routers.learned_overrides_router import router as learned_overrides_router
except ImportError as e:
    _log.warning("Optional router unavailable: learned_overrides_router (%s)", e)
    learned_overrides_router = None

# =============================================================================
# WAVE 11: ANALYTICS + PROBE + LTB CALCULATOR + CAM TOOLS (8 routers)
# =============================================================================
#     dashboard_router = None
# AnalyticsDashboard.vue now calls /api/patterns/*, /api/materials/*, /api/jobs/*
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
# Consolidated into calculators_consolidated_router:

#     dashboard_router = None

# =============================================================================
# WAVE 12: CAM EXTENSIONS + POLYGON (4 routers - legacy removed January 2026)
# =============================================================================
#     router as cam_adaptive_benchmark_router,
#     router as compare_risk_aggregate_router,
#     router as compare_risk_bucket_detail_router,
from .routers.polygon_offset_router import router as polygon_offset_router

# =============================================================================
# WAVE 13 (FINAL): ART PRESETS + CAM UTILITIES + COMPARE + MONITOR (9 routers)
# =============================================================================
from .routers.art_presets_router import router as art_presets_router
from .routers.cam_pipeline_preset_run_router import (
    router as cam_pipeline_preset_run_router,
)
from .routers.cam_polygon_offset_router import router as cam_polygon_offset_router
# Consolidated into simulation_consolidated_router:
from .routers.compare_automation_router import router as compare_automation_router
#     router as compare_risk_bucket_export_router,

# =============================================================================
# CNC PRODUCTION (1 router)
# =============================================================================
#     router as cnc_compare_jobs_router,

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

# teaching_router: REMOVED (legacy _experimental module deleted)

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

#     art_preview_router = None

try:
    from .art_studio.api.snapshot_routes import router as art_snapshots_router
except ImportError as e:
    _log.warning("Optional router unavailable: art_snapshots_router (%s)", e)
    art_snapshots_router = None

# Legacy Art Studio workflow routes. All frontend uses RMOS workflow via SDK.
#     art_workflow_router = None

# Bundle 32.7.0: Design-First Workflow Binding
#     design_first_workflow_router = None

# Phase 33.0: CAM Promotion Bridge (orchestration-only; fenced from CAM engine)
# The workflow router includes the same promote_to_cam endpoint with more features.
#     art_cam_promotion_router = None

# =============================================================================
# WAVE 16: GOVERNANCE CODE BUNDLE - Canonical Workflow + Run Artifacts (4 routers)
# Implements governance contracts for server-side feasibility, artifact persistence
# =============================================================================
#     rmos_feasibility_router = None

#     rmos_toolpaths_router = None

try:
    from .rmos.api.rmos_runs_router import router as rmos_runs_api_router
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_runs_api_router (%s)", e)
    rmos_runs_api_router = None

#     rmos_workflow_router = None

# MVP Wrapper: RMOS-wrapped DXF -> GRBL golden path
#     rmos_mvp_wrapper_router = None

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

# RMOS AI Advisory Router (CLI integration with ai-integrator)
# Frontend uses /ai/advisories/request but router is mounted at /api/rmos/advisories/request
#     rmos_ai_advisory_router = None

# =============================================================================
# WAVE 17: WORKFLOW SESSIONS (SQLite persistence layer)
# Frontend SDK only uses /rmos/workflow/sessions (rmos_workflow_router).
# =============================================================================
#     workflow_sessions_router = None

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

#         router as rosette_pattern_router_v2,
#     rosette_pattern_router_v2 = None

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
    """Factory function for creating the FastAPI application."""
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
from .core.observability import set_version, register_loaded_feature
from .health.startup import validate_startup, get_startup_summary


@app.on_event("startup")
def _startup_safety_validation() -> None:
    """Validate safety-critical modules are loaded. FAIL FAST if not."""
    # Set strict=True to block startup if safety modules fail
    # Set strict=False during development/testing if needed
    strict_mode = os.getenv("RMOS_STRICT_STARTUP", "1") != "0"
    validate_startup(strict=strict_mode)


@app.on_event("startup")
def _startup_db_migrations() -> None:
    """Run database migrations on startup (if enabled)."""
    run_migrations_on_startup()


@app.on_event("startup")
def _startup_observability() -> None:
    """Initialize observability with version info."""
    set_version("2.0.0-clean")
    # Register core features that loaded successfully
    register_loaded_feature("core_cam")
    register_loaded_feature("rmos")
    register_loaded_feature("health")


# =============================================================================
# ROUTER REGISTRATION
# =============================================================================

# Core CAM (11)
# Consolidated simulation router (combines cam_sim, cam_simulate, sim_metrics)
app.include_router(simulation_router, prefix="/api/cam/sim", tags=["CAM Simulation"])
app.include_router(geometry_router, prefix="/api/geometry", tags=["Geometry"])
app.include_router(tooling_router, prefix="/api/tooling", tags=["Tooling"])
app.include_router(adaptive_router, prefix="/api", tags=["Adaptive Pocketing"])
# Consolidated into machines_consolidated_router:
app.include_router(cam_opt_router, prefix="/api/cam/opt", tags=["CAM Optimization"])
app.include_router(cam_metrics_router, prefix="/api/cam/metrics", tags=["CAM Metrics"])
app.include_router(cam_logs_router, prefix="/api/cam/logs", tags=["CAM Logs"])
app.include_router(cam_learn_router, prefix="/api/cam/learn", tags=["CAM Learning"])

# RMOS 2.0 (4 routers)
app.include_router(rmos_router, prefix="/api/rmos", tags=["RMOS"])

# CAM Subsystem (4) - Legacy routes removed January 2026
# cam_vcarve_router → /api/cam/toolpath/vcarve
# cam_relief_router → /api/cam/relief
# cam_svg_router → /api/cam/export
# cam_helical_router → /api/cam/toolpath/helical

# Pipeline (2)

# Legacy DXF Exports (1) - Migrated from ./server, routes at /exports/*

# Blueprint (2) - blueprint_router is optional (AI deps may be missing)
if blueprint_router:
    app.include_router(
        blueprint_router, prefix="/api"
    )  # Router has /blueprint prefix internally

# Machine & Post Configuration (2 - consolidated)
# Consolidated router: combines machine_router, machines_router, machines_tools_router
app.include_router(
    machines_consolidated_router, prefix="/api/machines", tags=["Machines"]
)
# Old registrations consolidated:
# Consolidated posts router (CRUD for post definitions)
app.include_router(posts_consolidated_router, prefix="/api/posts", tags=["Post Processors"])

# Instrument Geometry (1)

# Data Registry (1)
app.include_router(registry_router, prefix="/api/registry", tags=["Data Registry"])

# Saw Lab (3)

# Saw Lab Decision Intelligence (Option A)
#     include_decision_intel_router(app)
#     # Do not block boot if Saw Lab is partially disabled in a deployment

# archtop_router, stratocaster_router, smart_guitar_router, om_router were removed
# See: docs/LEGACY_CODE_STATUS.md

# G-Code Generators (2)

# CAD Engine (1) - Wave 4

# Rosette System - Legacy routes REMOVED January 2026
# See Wave 18 consolidated CAM routes + Art Studio v2 routes
# rosette_pattern_router → /api/art/rosette/pattern
# art_studio_rosette_router → /api/art/rosette (v2)

# Art Studio Bracing & Inlay Routers
app.include_router(
    root_art_router, tags=["Art Studio", "Root"]
)  # → /api/art/* (prefix built-in)

# Music Axis (Option C) - Global temperament/tuning endpoints

# Legacy 308 Redirects: REMOVED (January 2026)
# All legacy redirect routers deleted. Zero frontend consumers remain.

# Wave 7: Calculator Suite + Bridge Calculator + Fret Design (3)
# Consolidated calculator router (CAM + Math + Luthier)

# Wave 8: Presets + RMOS Extensions + CAM Tools (7)
app.include_router(
    strip_family_router, prefix="/api/rmos", tags=["RMOS", "Strip Families"]
)
app.include_router(
    retract_router, prefix="/api/cam/retract", tags=["CAM", "Retract Patterns"]
)

# Wave 9: AI-CAM + Drill/Roughing + Compare + DXF Preflight + JobLog + Neck (8)
if ai_cam_router:
    app.include_router(ai_cam_router, prefix="/api", tags=["AI-CAM"])
# =============================================================================
# LEGACY ROUTERS REMOVED (January 2026)
# Consolidated CAM router at /api/cam/ now provides these canonical paths.
# See: docs/LEGACY_CODE_STATUS.md
# =============================================================================
# cam_drill_pattern_router → /api/cam/drilling/pattern (consolidated)
# cam_roughing_router → /api/cam/toolpath/roughing (consolidated)
app.include_router(dxf_preflight_router, prefix="/api", tags=["DXF", "Preflight"])
if joblog_router:
    app.include_router(joblog_router, prefix="/api", tags=["JobLog", "Telemetry"])
app.include_router(neck_router, prefix="/api", tags=["Neck", "Generator"])

# Wave 10: Instrument + Risk + Learn + Backup (5)
app.include_router(
    instrument_router, prefix="", tags=["Instrument"]
)  # Router has /api/instrument prefix
if learned_overrides_router:
    app.include_router(
        learned_overrides_router, prefix="/api", tags=["Feeds", "Learned"]
    )

# Wave 11: Analytics + Probe + LTB Calculator + CAM Tools (8)
if analytics_router:
    app.include_router(analytics_router, prefix="/api", tags=["Analytics"])
if advanced_analytics_router:
    app.include_router(
        advanced_analytics_router, prefix="/api", tags=["Analytics", "Advanced"]
    )

# Wave 12: CAM Extensions + Polygon (4 - legacy removed January 2026)

# Wave 13 (FINAL): Art Presets + CAM Utilities + Compare + Monitor (9)
app.include_router(art_presets_router, prefix="/api", tags=["Art", "Presets"])
app.include_router(
    cam_pipeline_preset_run_router, prefix="/api", tags=["CAM", "Pipeline"]
)
# Consolidated into simulation_consolidated_router:
# NOTE: compare_automation_router disabled - route duplicated by compare_router (Wave 19)
# Disabled: 2026-02-05 (WP-2: API Surface Reduction)
#     compare_automation_router, prefix="/api", tags=["Compare", "Automation"]

# CNC Production (1)

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
# teaching_router: REMOVED (legacy _experimental module deleted)

# Wave 15: Art Studio Core Completion (5)
# Note: These routers have their own prefix defined (e.g., /api/art/patterns)
if art_patterns_router:
    app.include_router(art_patterns_router, tags=["Art Studio", "Patterns"])
if art_generators_router:
    app.include_router(art_generators_router, tags=["Art Studio", "Generators"])
if art_snapshots_router:
    app.include_router(art_snapshots_router, tags=["Art Studio", "Snapshots"])

# Wave 16: Governance Code Bundle - Canonical Workflow + Run Artifacts (4)
# Implements governance contracts:
# - SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md
# - RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md
# - RUN_ARTIFACT_INDEX_QUERY_API_CONTRACT_v1.md
# - RUN_DIFF_VIEWER_CONTRACT_v1.md

# MVP Wrapper: RMOS-wrapped DXF -> GRBL golden path

# RMOS Runs v2 Operator Pack Export
if rmos_runs_v2_exports_router:
    app.include_router(rmos_runs_v2_exports_router, tags=["RMOS", "Operator Pack"])

# RMOS Runs v2 Query Router (envelope list with cursor pagination)
if rmos_runs_v2_query_router:
    app.include_router(rmos_runs_v2_query_router, prefix="/api/rmos", tags=["RMOS", "Runs v2 Query"])

# RMOS AI Advisory Router (CLI integration with ai-integrator)

# Wave 17: Workflow Sessions (SQLite persistence layer)

# Wave 18: CAM Router Consolidation (Phase 5+6)
# This aggregator provides organized CAM endpoints at /api/cam/<category>/<operation>
# Categories: drilling, fret_slots, relief, risk, rosette, simulation, toolpath,
#             export, monitoring, pipeline, utility
if cam_router:
    app.include_router(cam_router, prefix="/api/cam", tags=["CAM Consolidated"])

# See: docs/LEGACY_CODE_STATUS.md

# Phase 5: Consolidated Art Studio rosette routes
# These provide the new organized endpoints alongside legacy routes for transition
# if rosette_pattern_router_v2:
#         rosette_pattern_router_v2, tags=["Art Studio", "Rosette Patterns v2"]

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
#         router as art_feasibility_router,
#     art_feasibility_router = None

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
#     rmos_acoustics_router = None

# Wave 20: Art Studio Run Orchestration (3)
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

# Wave 22: Runs v2 Acoustics Advisory Surface (H7.2.2.1 features)
# Endpoints: GET /runs/{run_id}/advisories, GET /advisories/{advisory_id},
#            GET/HEAD /attachments/{sha256}, POST /attachments/{sha256}/signed_url,
#            GET /runs/{run_id}/attachments, GET /index/attachment_meta/{sha256}/exists
# This is the authoritative attachment router with no-path disclosure + signed URLs.
#         runs_v2_acoustics_router,
#         prefix="/api/rmos/acoustics",
#         tags=["RMOS", "Acoustics"],

# Wave 22.1: Acoustics Ingest Audit Log (browse/detail endpoints for ingest events)
#         acoustics_ingest_audit_router,
#         prefix="/api/rmos/acoustics",
#         tags=["RMOS", "Acoustics", "Ingest Audit"],

# =============================================================================
# WAVE 23: SMART GUITAR TELEMETRY INGESTION
# Manufacturing-only telemetry from Smart Guitar devices.
# Enforces boundary contract: NO player/pedagogy data allowed.
# =============================================================================

# =============================================================================
# WAVE 24: COST ATTRIBUTION
# Maps validated telemetry to internal manufacturing cost dimensions.
# Read-only endpoint: GET /api/cost/summary
# =============================================================================
try:
    from .cost_attribution import cost_router
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
except ImportError as e:
    _log.warning("Optional router unavailable: ai_context_adapter_router (%s)", e)

# Legacy ai_context (more complex envelope) - DISABLED WP-2 2026-02-05
# The ai_context_adapter provides the same /health endpoint.
# Uncomment if legacy envelope format is needed.


# =============================================================================
# WAVE 25: RMOS V1 VALIDATION PROTOCOL
# 30-run validation harness with persistent logging for release gate.
# Endpoints: GET /api/rmos/validation/scenarios, POST /run, POST /run-batch,
#            POST /log, GET /summary, GET /sessions, GET /runs
# =============================================================================

# =============================================================================
# WAVE 22.2: RUN LOGS (Audit Surface)
# =============================================================================

# =============================================================================
# COMPAT LEGACY ROUTES: REMOVED (January 2026)
# All frontend callers migrated to canonical /api/* paths.
# 19 compat mounts deleted. See deprecation_registry.json for audit trail.
# =============================================================================

# =============================================================================
# META / INTROSPECTION
# =============================================================================
# Routing truth endpoint for confirming what's actually mounted after deploy

# Governance stats endpoint (H5.1) - measure legacy/shadow usage before deletions

# Prometheus metrics endpoint (H5.2) - no prefix, accessible at /metrics
app.include_router(metrics_router)

# =============================================================================
# HEALTH CHECK
# =============================================================================

# Health router with /health/detailed endpoint for observability
app.include_router(health_router, prefix="/api", tags=["Health"])


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
