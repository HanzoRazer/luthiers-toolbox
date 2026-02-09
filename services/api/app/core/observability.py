"""
Observability module for tracking application health and feature status.

Phase 6 of remediation plan:
- Track failed imports
- Track uptime
- Provide version info
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Module-level state (initialized at import time)
_startup_time: float = time.time()
_loaded_features: List[str] = []
_failed_features: List[Dict[str, str]] = []
_version: str = "0.1.0"  # Default version


@dataclass
class FeatureLoadResult:
    """Result of attempting to load a feature/router."""
    name: str
    success: bool
    error: Optional[str] = None


def register_loaded_feature(name: str) -> None:
    """Register a successfully loaded feature/router."""
    if name not in _loaded_features:
        _loaded_features.append(name)


def register_failed_feature(name: str, error: str) -> None:
    """Register a feature/router that failed to load."""
    _failed_features.append({"name": name, "error": error})
    logger.warning(f"Feature failed to load: {name} - {error}")


def get_loaded_features() -> List[str]:
    """Return list of successfully loaded features."""
    return _loaded_features.copy()


def get_failed_features() -> List[Dict[str, str]]:
    """Return list of features that failed to load."""
    return _failed_features.copy()


def get_uptime_seconds() -> float:
    """Return seconds since application startup."""
    return time.time() - _startup_time


def get_version() -> str:
    """Return application version."""
    return _version


def set_version(version: str) -> None:
    """Set application version (called during startup)."""
    global _version
    _version = version


def get_health_summary() -> Dict:
    """
    Return comprehensive health summary for /api/health/detailed.

    Returns:
        {
            "status": "ok" | "degraded",
            "uptime_seconds": float,
            "version": str,
            "features": {
                "loaded": [...],
                "loaded_count": int,
                "failed": [...],
                "failed_count": int
            }
        }
    """
    loaded = get_loaded_features()
    failed = get_failed_features()

    # Status is degraded if any features failed to load
    status = "ok" if len(failed) == 0 else "degraded"

    return {
        "status": status,
        "uptime_seconds": round(get_uptime_seconds(), 2),
        "version": get_version(),
        "features": {
            "loaded": loaded,
            "loaded_count": len(loaded),
            "failed": failed,
            "failed_count": len(failed)
        }
    }


def safe_import_router(import_fn, name: str):
    """
    Safely import and return a router, tracking success/failure.

    Usage:
        router = safe_import_router(
            lambda: from_module.router,
            "from_module"
        )
        if router:
            app.include_router(router, ...)

    Args:
        import_fn: Callable that returns the router
        name: Name for logging/tracking

    Returns:
        Router if successful, None if failed
    """
    try:
        router = import_fn()
        register_loaded_feature(name)
        return router
    except Exception as e:
        register_failed_feature(name, str(e))
        return None
