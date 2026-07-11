"""WP-002-C2 - retract shim retirement: route-mount invariant.

The deprecated ``retract_consolidated_router`` aggregate wrapper is retired from
``retract/__init__`` wiring; the package now builds its aggregate router from the three
focused sub-routers directly (info / apply / gcode). This must be a wiring change only:
every retract endpoint path, method, and Retract tag stays available.

The compatibility module remains importable with a deprecation warning so downstream
branches/scripts do not fail at import time while they migrate; it must not be
reintroduced into package wiring.
"""
from __future__ import annotations

import importlib
import sys
import warnings

from fastapi import APIRouter


EXPECTED_ROUTES = {
    "/strategies": {"GET"},
    "/estimate": {"POST"},
    "/apply": {"POST"},
    "/lead_in": {"POST"},
    "/gcode": {"POST"},
    "/gcode/download": {"POST"},
    "/gcode_governed": {"POST"},
    "/gcode/download_governed": {"POST"},
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


def test_retract_package_still_mounts_all_8_endpoints():
    from app.routers.retract import router as retract_pkg_router

    paths = _paths(retract_pkg_router)
    missing = {suffix for suffix in EXPECTED_ROUTES if not any(path.endswith(suffix) for path in paths)}
    assert not missing, f"retract endpoints missing after shim retirement: {sorted(missing)}"

    for suffix, methods in EXPECTED_ROUTES.items():
        matched = [
            metadata for path, metadata in paths.items()
            if path == suffix or path.endswith(suffix)
        ]
        assert matched, f"retract endpoint not mounted: {suffix}"
        assert methods.issubset(matched[0]["methods"]), (
            f"{suffix}: expected methods {methods}, got {matched[0]['methods']}"
        )
        assert "Retract" in matched[0]["tags"], f"{suffix}: missing Retract tag"


def test_deprecated_retract_shim_module_remains_import_compatible():
    sys.modules.pop("app.routers.retract.retract_consolidated_router", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        shim = importlib.import_module("app.routers.retract.retract_consolidated_router")

    assert isinstance(shim.router, APIRouter)
    assert any(
        item.category is DeprecationWarning
        and "retract_consolidated_router is deprecated" in str(item.message)
        for item in caught
    )


def test_retract_package_no_longer_imports_the_shim():
    import app.routers.retract as retract_pkg

    # Sub-routers are exposed directly by the package.
    for sub in ("info_router", "apply_router", "gcode_router"):
        assert hasattr(retract_pkg, sub), f"sub-router missing from package: {sub}"

    # The package builds its aggregate from the sub-routers, not the retired shim.
    # Inspect import statements only (an explanatory comment may still name the shim).
    import inspect

    source = inspect.getsource(retract_pkg)
    import_lines = [
        line for line in source.splitlines()
        if line.lstrip().startswith(("import ", "from "))
    ]
    assert not any("retract_consolidated_router" in line for line in import_lines), (
        "package __init__ must not import the retired consolidation shim"
    )
