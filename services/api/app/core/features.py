"""
Feature registry for API router management.

Phase 2 of remediation plan:
- Explicit feature registration (replaces silent try/except)
- /api/features endpoint support
- Integration with observability module
"""
from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .observability import register_loaded_feature, register_failed_feature

logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """Configuration for a single feature/router."""
    name: str
    module_path: str
    router_attr: str = "router"
    prefix: str = ""
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    optional: bool = False  # If True, failure to load doesn't block startup


# Feature registry - organized by category
FEATURES: Dict[str, FeatureConfig] = {
    # Core CAM
    "simulation": FeatureConfig(
        name="simulation",
        module_path="app.routers.simulation_consolidated_router",
        prefix="/api/cam/sim",
        tags=["CAM Simulation"],
    ),
    "geometry": FeatureConfig(
        name="geometry",
        module_path="app.routers.geometry_router",
        prefix="/api/geometry",
        tags=["Geometry"],
    ),
    "tooling": FeatureConfig(
        name="tooling",
        module_path="app.routers.tooling_router",
        prefix="/api/tooling",
        tags=["Tooling"],
    ),
    "adaptive": FeatureConfig(
        name="adaptive",
        module_path="app.routers.adaptive_router",
        prefix="/api",
        tags=["Adaptive Pocketing"],
    ),

    # RMOS
    "rmos_core": FeatureConfig(
        name="rmos_core",
        module_path="app.rmos",
        router_attr="rmos_router",
        prefix="/api/rmos",
        tags=["RMOS"],
    ),

    # Health
    "health": FeatureConfig(
        name="health",
        module_path="app.routers.health_router",
        prefix="/api",
        tags=["Health"],
    ),

    # Optional features
    "blueprint": FeatureConfig(
        name="blueprint",
        module_path="app.routers.blueprint_router",
        prefix="/api",
        tags=["Blueprint"],
        optional=True,
    ),
    "vision": FeatureConfig(
        name="vision",
        module_path="app.vision.router",
        prefix="",  # Router has internal prefix
        tags=["Vision"],
        optional=True,
    ),
    "cam_consolidated": FeatureConfig(
        name="cam_consolidated",
        module_path="app.cam.routers",
        router_attr="cam_router",
        prefix="/api/cam",
        tags=["CAM Consolidated"],
        optional=True,
    ),
    "compare_consolidated": FeatureConfig(
        name="compare_consolidated",
        module_path="app.compare.routers",
        router_attr="compare_router",
        prefix="/api/compare",
        tags=["Compare Consolidated"],
        optional=True,
    ),
}


@dataclass
class LoadedFeature:
    """Result of loading a feature."""
    config: FeatureConfig
    router: Any
    route_count: int = 0


_loaded_features: Dict[str, LoadedFeature] = {}
_failed_features: Dict[str, str] = {}


def load_feature(config: FeatureConfig) -> Optional[Any]:
    """
    Load a single feature's router.

    Returns the router if successful, None if failed.
    Tracks success/failure in observability module.
    """
    try:
        module = importlib.import_module(config.module_path)
        router = getattr(module, config.router_attr)

        # Count routes
        route_count = len([r for r in router.routes if hasattr(r, 'path')])

        # Track success
        _loaded_features[config.name] = LoadedFeature(
            config=config,
            router=router,
            route_count=route_count,
        )
        register_loaded_feature(config.name)
        logger.info(f"Loaded feature: {config.name} ({route_count} routes)")

        return router

    except Exception as e:
        error_msg = str(e)
        _failed_features[config.name] = error_msg
        register_failed_feature(config.name, error_msg)

        if config.optional:
            logger.warning(f"Optional feature unavailable: {config.name} ({error_msg})")
        else:
            logger.error(f"Required feature failed to load: {config.name} ({error_msg})")
            raise

        return None


def get_feature_summary() -> Dict[str, Any]:
    """
    Return summary of all features for /api/features endpoint.
    """
    loaded = {}
    for name, feature in _loaded_features.items():
        loaded[name] = {
            "enabled": True,
            "routes": feature.route_count,
            "prefix": feature.config.prefix,
            "tags": feature.config.tags,
        }

    failed = {}
    for name, error in _failed_features.items():
        config = FEATURES.get(name)
        failed[name] = {
            "enabled": False,
            "reason": error,
            "optional": config.optional if config else True,
        }

    return {
        "loaded": loaded,
        "loaded_count": len(loaded),
        "failed": failed,
        "failed_count": len(failed),
        "total_routes": sum(f.route_count for f in _loaded_features.values()),
    }


def register_all_features(app) -> None:
    """
    Register all enabled features with the FastAPI app.

    This replaces the 40+ try/except blocks in main.py.
    """
    for name, config in FEATURES.items():
        if not config.enabled:
            continue

        router = load_feature(config)
        if router is not None:
            if config.prefix:
                app.include_router(router, prefix=config.prefix, tags=config.tags)
            else:
                app.include_router(router, tags=config.tags)
