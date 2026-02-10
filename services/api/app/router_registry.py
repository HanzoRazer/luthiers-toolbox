"""Router Registry — Centralized router loading and health tracking."""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter

_log = logging.getLogger(__name__)

@dataclass
class RouterSpec:
    """Specification for a router to load."""

    module: str  # Full module path, e.g., "app.routers.health_router"
    router_attr: str = "router"  # Attribute name in module
    prefix: str = ""  # URL prefix
    tags: List[str] = field(default_factory=list)
    required: bool = False  # If True, failure blocks startup
    enabled: bool = True  # If False, skip loading
    category: str = "misc"  # For grouping in health reports

# Track loading status
_loaded_routers: Dict[str, bool] = {}
_router_errors: Dict[str, str] = {}

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
        module="app.routers.geometry_router",
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
        module="app.routers.adaptive_router",
        prefix="/api",
        tags=["Adaptive Pocketing"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.cam_opt_router",
        prefix="/api/cam/opt",
        tags=["CAM Optimization"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.cam_metrics_router",
        prefix="/api/cam/metrics",
        tags=["CAM Metrics"],
        category="cam_core",
    ),
    RouterSpec(
        module="app.routers.cam_logs_router",
        prefix="/api/cam/logs",
        tags=["CAM Logs"],
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
        module="app.routers.blueprint_router",
        prefix="/api",
        tags=["Blueprint"],
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
]

def _try_load_router(spec: RouterSpec) -> Optional[APIRouter]:
    """Attempt to load a single router from its spec."""
    if not spec.enabled:
        _log.debug("Router disabled: %s", spec.module)
        _loaded_routers[spec.module] = False
        return None

    try:
        module = importlib.import_module(spec.module)
        router = getattr(module, spec.router_attr)
        _loaded_routers[spec.module] = True
        _log.info("✓ Loaded router: %s", spec.module)
        return router
    except ImportError as e:
        _loaded_routers[spec.module] = False
        _router_errors[spec.module] = str(e)
        if spec.required:
            _log.error("✗ REQUIRED router failed: %s (%s)", spec.module, e)
            raise
        else:
            _log.warning("⚠ Optional router unavailable: %s (%s)", spec.module, e)
        return None
    except AttributeError as e:
        _loaded_routers[spec.module] = False
        _router_errors[spec.module] = f"No '{spec.router_attr}' attribute: {e}"
        if spec.required:
            _log.error("✗ REQUIRED router missing attribute: %s.%s", spec.module, spec.router_attr)
            raise
        else:
            _log.warning("⚠ Router attribute not found: %s.%s", spec.module, spec.router_attr)
        return None

def load_all_routers() -> List[Tuple[APIRouter, str, List[str]]]:
    """Load all routers from the manifest.

    Returns:
        List of (router, prefix, tags) tuples for successfully loaded routers.

    Raises:
        ImportError: If a required router fails to load.
    """
    _log.info("=" * 60)
    _log.info("ROUTER REGISTRY: Loading %d routers...", len(ROUTER_MANIFEST))
    _log.info("=" * 60)

    loaded: List[Tuple[APIRouter, str, List[str]]] = []

    for spec in ROUTER_MANIFEST:
        router = _try_load_router(spec)
        if router is not None:
            loaded.append((router, spec.prefix, spec.tags))

    success_count = sum(1 for v in _loaded_routers.values() if v)
    fail_count = sum(1 for v in _loaded_routers.values() if not v)

    _log.info("-" * 60)
    _log.info("Router loading complete: %d loaded, %d skipped/failed", success_count, fail_count)
    _log.info("=" * 60)

    return loaded

def get_router_health() -> Dict[str, Any]:
    """Get health summary of all routers.

    Returns:
        Dict with router loading status for health endpoints.
    """
    by_category: Dict[str, Dict[str, bool]] = {}
    for spec in ROUTER_MANIFEST:
        cat = spec.category
        if cat not in by_category:
            by_category[cat] = {}
        by_category[cat][spec.module] = _loaded_routers.get(spec.module, False)

    return {
        "total": len(ROUTER_MANIFEST),
        "loaded": sum(1 for v in _loaded_routers.values() if v),
        "failed": sum(1 for v in _loaded_routers.values() if not v),
        "by_category": {
            cat: {
                "loaded": sum(1 for v in routers.values() if v),
                "total": len(routers),
            }
            for cat, routers in by_category.items()
        },
        "errors": _router_errors,
    }

def get_loaded_routers() -> Dict[str, bool]:
    """Return dict of module -> loaded status."""
    return _loaded_routers.copy()
