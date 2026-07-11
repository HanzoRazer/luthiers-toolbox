"""WP-002-C1 - probe shim retirement: route-mount invariant.

The deprecated ``probe_consolidated_router`` aggregate wrapper is retired from
``probe/__init__`` wiring; the package now mounts the six focused sub-routers directly
(boss / corner / pocket / surface_z / vise_square / setup). This must be a wiring
change only: every probe endpoint path, method, and probe tag stays available.

The compatibility module remains importable with a deprecation warning so downstream
branches/scripts do not fail at import time while they migrate. The package-level
``probe_router`` re-export remains removed.
"""
from __future__ import annotations

import importlib
import sys
import warnings

from fastapi import APIRouter


EXPECTED_ROUTES = {
    "/boss/gcode": {"POST"},
    "/boss/gcode/download": {"POST"},
    "/boss/gcode/download_governed": {"POST"},
    "/corner/gcode": {"POST"},
    "/corner/gcode/download": {"POST"},
    "/corner/gcode/download_governed": {"POST"},
    "/pocket/gcode": {"POST"},
    "/pocket/gcode/download": {"POST"},
    "/pocket/gcode/download_governed": {"POST"},
    "/surface_z/gcode": {"POST"},
    "/surface_z/gcode/download": {"POST"},
    "/surface_z/gcode/download_governed": {"POST"},
    "/vise_square/gcode": {"POST"},
    "/vise_square/gcode/download": {"POST"},
    "/vise_square/gcode/download_governed": {"POST"},
    "/setup_sheet/svg": {"POST"},
    "/patterns": {"GET"},
}


def _paths(router):
    paths = {}
    for route in router.routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths[path] = {
                "methods": set(getattr(route, "methods", set()) or set()),
                "tags": list(getattr(route, "tags", []) or []),
            }
            continue

        included_router = getattr(route, "original_router", None)
        include_context = getattr(route, "include_context", None)
        include_prefix = getattr(include_context, "prefix", "") if include_context else ""
        if included_router is not None:
            for sub_path, metadata in _paths(included_router).items():
                paths[f"{include_prefix}{sub_path}"] = metadata
    return paths


def test_probe_package_still_mounts_all_17_endpoints():
    from app.routers.probe import router as probe_pkg_router

    paths = _paths(probe_pkg_router)
    missing = {suffix for suffix in EXPECTED_ROUTES if not any(path.endswith(suffix) for path in paths)}
    assert not missing, f"probe endpoints missing after shim retirement: {sorted(missing)}"

    for suffix, methods in EXPECTED_ROUTES.items():
        matched = [metadata for path, metadata in paths.items() if path.endswith(suffix)]
        assert matched, f"probe endpoint not mounted: {suffix}"
        assert matched[0]["methods"] == methods
        assert "probe" in matched[0]["tags"]


def test_deprecated_probe_shim_module_remains_import_compatible():
    sys.modules.pop("app.routers.probe.probe_consolidated_router", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        shim = importlib.import_module("app.routers.probe.probe_consolidated_router")

    assert isinstance(shim.router, APIRouter)
    assert any(
        item.category is DeprecationWarning
        and "probe_consolidated_router is deprecated" in str(item.message)
        for item in caught
    )


def test_aggregate_probe_router_reexport_removed():
    import app.routers.probe as probe_pkg

    assert not hasattr(probe_pkg, "probe_router")
    for sub in (
        "boss_router",
        "corner_router",
        "pocket_router",
        "surface_z_router",
        "vise_square_router",
        "setup_router",
    ):
        assert hasattr(probe_pkg, sub), f"sub-router missing from package: {sub}"
