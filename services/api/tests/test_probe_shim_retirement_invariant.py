"""WP-002-C1 — probe shim retirement: route-mount invariant.

The deprecated `probe_consolidated_router` aggregate wrapper was retired; `probe/__init__`
now mounts the six focused sub-routers directly (boss / corner / pocket / surface_z /
vise_square / setup). This must be a wiring change only — every probe endpoint path and
its behavior stays identical.

These tests guard that (a) all 17 probe endpoints remain mounted, (b) the deprecated shim
module is gone, and (c) the backward-compat aggregate re-export is removed.
"""
import importlib

import pytest


# The 17 endpoints the probe package must expose (suffixes, so the guard is robust to
# where the "/probe" prefix is applied in the router tree).
EXPECTED_SUFFIXES = {
    "/boss/gcode", "/boss/gcode/download", "/boss/gcode/download_governed",
    "/corner/gcode", "/corner/gcode/download", "/corner/gcode/download_governed",
    "/pocket/gcode", "/pocket/gcode/download", "/pocket/gcode/download_governed",
    "/surface_z/gcode", "/surface_z/gcode/download", "/surface_z/gcode/download_governed",
    "/vise_square/gcode", "/vise_square/gcode/download", "/vise_square/gcode/download_governed",
    "/setup_sheet/svg", "/patterns",
}


def _paths(router):
    return [p for p in (getattr(r, "path", None) for r in router.routes) if isinstance(p, str)]


def test_probe_package_still_mounts_all_17_endpoints():
    from app.routers.probe import router as probe_pkg_router
    paths = _paths(probe_pkg_router)
    missing = {sfx for sfx in EXPECTED_SUFFIXES if not any(p.endswith(sfx) for p in paths)}
    assert not missing, f"probe endpoints missing after shim retirement: {sorted(missing)}"


def test_deprecated_probe_shim_module_is_gone():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.routers.probe.probe_consolidated_router")


def test_aggregate_probe_router_reexport_removed():
    import app.routers.probe as probe_pkg
    # The backward-compat `probe_router` aggregate is removed; only the package router
    # and the focused sub-routers remain exported.
    assert not hasattr(probe_pkg, "probe_router")
    for sub in ("boss_router", "corner_router", "pocket_router",
                "surface_z_router", "vise_square_router", "setup_router"):
        assert hasattr(probe_pkg, sub), f"sub-router missing from package: {sub}"
