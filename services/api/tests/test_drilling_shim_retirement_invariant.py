"""WP-002-C3 - drilling shim retirement: route-mount invariant.

The deprecated ``drilling_consolidated_router`` aggregate wrapper is retired from
``cam/routers/drilling/__init__`` wiring; the package now builds its aggregate from the
three focused sub-routers directly (drill_modal / drill_pattern / drilling_preview) plus
the separately-mounted intent_router. This must be a wiring change only: every drilling
endpoint path, method, and tag stays available.

The compatibility module remains importable with a deprecation warning so downstream
branches/scripts do not fail at import time while they migrate; it must not be
reintroduced into package wiring.

Note: the package exposes SIX endpoints. The retired shim aggregated three sub-routers
(five routes); intent_router (/intent-gcode) is mounted directly by the package and was
never part of the shim.
"""
from __future__ import annotations

import importlib
import sys
import warnings

from fastapi import APIRouter


# suffix -> (methods, tag substring that must be present case-insensitively or None)
EXPECTED_ROUTES = {
    "/gcode": ({"POST"}, "drilling"),
    "/info": ({"GET"}, "drilling"),
    "/pattern/gcode": ({"POST"}, "drilling"),
    "/pattern/info": ({"GET"}, "drilling"),
    "/preview": ({"POST"}, "drilling"),
    "/intent-gcode": ({"POST"}, None),
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


def test_drilling_package_still_mounts_all_6_endpoints():
    from app.cam.routers.drilling import router as drilling_pkg_router

    paths = _paths(drilling_pkg_router)
    missing = {suffix for suffix in EXPECTED_ROUTES if not any(path.endswith(suffix) for path in paths)}
    assert not missing, f"drilling endpoints missing after shim retirement: {sorted(missing)}"

    for suffix, (methods, tag) in EXPECTED_ROUTES.items():
        matched = [
            metadata for path, metadata in paths.items()
            if path == suffix or path.endswith(suffix)
        ]
        assert matched, f"drilling endpoint not mounted: {suffix}"
        assert methods.issubset(matched[0]["methods"]), (
            f"{suffix}: expected methods {methods}, got {matched[0]['methods']}"
        )
        if tag is not None:
            tags_lower = {t.lower() for t in matched[0]["tags"]}
            assert tag in tags_lower, f"{suffix}: missing '{tag}' tag (got {matched[0]['tags']})"


def test_deprecated_drilling_shim_module_remains_import_compatible():
    sys.modules.pop("app.cam.routers.drilling.drilling_consolidated_router", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        shim = importlib.import_module("app.cam.routers.drilling.drilling_consolidated_router")

    assert isinstance(shim.router, APIRouter)
    assert any(
        item.category is DeprecationWarning
        and "drilling_consolidated_router is deprecated" in str(item.message)
        for item in caught
    )


def test_drilling_package_no_longer_imports_the_shim():
    import app.cam.routers.drilling as drilling_pkg

    # Sub-routers are exposed directly by the package.
    for sub in ("drill_router", "pattern_router", "preview_router"):
        assert hasattr(drilling_pkg, sub), f"sub-router missing from package: {sub}"

    # The package builds its aggregate from the sub-routers, not the retired shim.
    # Inspect import statements only (an explanatory comment may still name the shim).
    import inspect

    source = inspect.getsource(drilling_pkg)
    import_lines = [
        line for line in source.splitlines()
        if line.lstrip().startswith(("import ", "from "))
    ]
    assert not any("drilling_consolidated_router" in line for line in import_lines), (
        "package __init__ must not import the retired consolidation shim"
    )
