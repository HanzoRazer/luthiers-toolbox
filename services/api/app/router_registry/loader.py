"""Router loading functions."""

from __future__ import annotations

import importlib
import logging
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter

from .models import RouterSpec
from .manifest import ROUTER_MANIFEST

_log = logging.getLogger(__name__)

# Track loading status (module-level state)
_loaded_routers: Dict[str, bool] = {}
_router_errors: Dict[str, str] = {}


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


def get_loaded_routers() -> Dict[str, bool]:
    """Return dict of module -> loaded status."""
    return _loaded_routers.copy()


def get_router_errors() -> Dict[str, str]:
    """Return dict of module -> error message for failed routers."""
    return _router_errors.copy()
