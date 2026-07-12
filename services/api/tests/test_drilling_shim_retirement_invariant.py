"""WP-002-C3 - drilling shim retirement: route-mount invariant.

The deprecated ``drilling_consolidated_router`` aggregate wrapper is retired from
``cam/routers/drilling/__init__`` wiring; the package now builds its aggregate from the
three focused sub-routers directly (drill_modal / drill_pattern / drilling_preview) plus
the separately-mounted intent_router. This must be a wiring change only: every drilling
endpoint path, method, and tag stays available.

The compatibility module remains importable with a deprecation warning so downstream
branches/scripts do not fail at import time while they migrate; it must not be
reintroduced into package wiring.

Because the retirement duplicates the shim's aggregate composition inline in the package
``__init__`` (rather than importing it), an exact-parity guard asserts the inline
``_drilling_router`` and the retained shim aggregate never silently diverge.

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


def _normalized_routes(router):
    """Order-independent (path, methods, tags) tuples for exact-parity comparison.

    Drops framework-injected HEAD/OPTIONS and normalizes tag order/case so the comparison
    reflects the declared composition, not incidental traversal/order differences.
    """
    out = set()
    for path, metadata in _paths(router).items():
        methods = frozenset(
            m for m in metadata["methods"] if m not in {"HEAD", "OPTIONS"}
        )
        tags = tuple(sorted(t.lower() for t in metadata["tags"]))
        out.add((path, methods, tags))
    return out


def _import_shim():
    """Import the deprecated facade under a warnings guard (safe even under -W error)."""
    sys.modules.pop("app.cam.routers.drilling.drilling_consolidated_router", None)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return importlib.import_module(
            "app.cam.routers.drilling.drilling_consolidated_router"
        )


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


def test_inline_drilling_aggregate_matches_deprecated_shim_exactly():
    """Guarded duplication: the package's inline ``_drilling_router`` must stay structurally
    identical to the retained deprecated shim aggregate.

    The retirement duplicates the shim's composition inline in the package ``__init__`` while
    keeping the shim as an import bridge. This asserts the two never silently diverge: if a
    future change adds/removes/retags a sub-router in one place but not the other, this fails.
    Both aggregates exclude the separately-mounted ``intent_router`` by construction, so no
    ``/intent-gcode`` filtering is needed.
    """
    from app.cam.routers.drilling import _drilling_router

    shim = _import_shim()

    inline = _normalized_routes(_drilling_router)
    shim_routes = _normalized_routes(shim.router)

    assert inline == shim_routes, (
        "inline _drilling_router and deprecated shim aggregate diverged:\n"
        f"  only in inline package aggregate: {sorted(inline - shim_routes)}\n"
        f"  only in deprecated shim aggregate: {sorted(shim_routes - inline)}"
    )
    # Neither aggregate carries the separately-mounted intent lane.
    assert not any(path.endswith("/intent-gcode") for path, _m, _t in inline), (
        "the drilling aggregate must not include the /intent-gcode lane"
    )
    # Sanity: the aggregate is the five consolidated drilling routes (intent mounted separately).
    assert len(inline) == 5, f"expected 5 consolidated drilling routes, got {len(inline)}"


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
