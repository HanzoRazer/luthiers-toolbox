"""Live route walk and OpenAPI reconciliation for the manufacturing inventory.

CI-only. Production routers must not import this module.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_CONVERTER = re.compile(r"\{([^{}:]+):[^{}]+\}")
_SKIP_METHODS = frozenset({"HEAD", "OPTIONS"})
_FRAMEWORK_PATHS = frozenset({
    "/docs",
    "/redoc",
    "/openapi.json",
    "/docs/oauth2-redirect",
})


def normalize_path(path: str) -> str:
    """``{file_path:path}`` and ``{id:int}`` both become ``{name}``."""
    return _CONVERTER.sub(r"{\1}", path or "")


@dataclass(frozen=True)
class LiveRoute:
    method: str
    path: str
    route_name: str
    endpoint: object
    response_model: object
    include_in_schema: bool
    route_type: str


@dataclass(frozen=True)
class UnresolvedRoute:
    type_name: str
    prefix: str


def _methods_of(route, type_name: str) -> set[str]:
    methods = getattr(route, "methods", None)
    if methods:
        return set(methods)
    if "WebSocket" in type_name:
        return {"WEBSOCKET"}
    return set()


def walk_live(routes, prefix: str = "") -> tuple[list[LiveRoute], list[UnresolvedRoute]]:
    """Descend ``_IncludedRouter`` nodes. A null path with children is a mount."""
    resolved: list[LiveRoute] = []
    unresolved: list[UnresolvedRoute] = []
    for route in routes:
        type_name = type(route).__name__
        if type_name == "_IncludedRouter":
            context = getattr(route, "include_context", None)
            original = getattr(route, "original_router", None)
            if original is None:
                unresolved.append(UnresolvedRoute(type_name, prefix))
                continue
            child = prefix + (getattr(context, "prefix", "") or "")
            nested, missed = walk_live(original.routes, child)
            resolved.extend(nested)
            unresolved.extend(missed)
            continue
        path = getattr(route, "path", None)
        if path is None:
            nested_routes = getattr(route, "routes", None)
            if nested_routes:
                nested, missed = walk_live(nested_routes, prefix)
                resolved.extend(nested)
                unresolved.extend(missed)
            else:
                unresolved.append(UnresolvedRoute(type_name, prefix))
            continue
        full = normalize_path(prefix + path)
        endpoint = getattr(route, "endpoint", None)
        model = getattr(route, "response_model", None)
        include = bool(getattr(route, "include_in_schema", True))
        route_name = str(getattr(route, "name", "") or "")
        for method in _methods_of(route, type_name):
            if method in _SKIP_METHODS:
                continue
            resolved.append(LiveRoute(
                method, full, route_name, endpoint, model, include, type_name,
            ))
    return resolved, unresolved


def naive_walk(routes) -> list[tuple[str, str]]:
    """Direct children only. Nested routers disappear. The negative witness."""
    found: list[tuple[str, str]] = []
    for route in routes:
        path = getattr(route, "path", None)
        if not path:
            continue
        for method in _methods_of(route, type(route).__name__):
            if method in _SKIP_METHODS:
                continue
            found.append((method, normalize_path(path)))
    return found


def openapi_operations(schema: dict) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for path, operations in schema.get("paths", {}).items():
        normalized = normalize_path(path)
        for method in operations:
            verb = method.upper()
            if verb in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                found.add((verb, normalized))
    return found


def reconcile(live: list[LiveRoute], schema: dict) -> list[str]:
    """Return unexpected live/OpenAPI differences. Empty means they reconcile."""
    documented = openapi_operations(schema)
    live_http = {
        (route.method, route.path)
        for route in live
        if route.method != "WEBSOCKET"
    }
    problems: list[str] = []
    for method, path in sorted(live_http - documented):
        route = next(item for item in live if item.method == method and item.path == path)
        if path in _FRAMEWORK_PATHS or not route.include_in_schema:
            continue
        problems.append(f"live-only {method} {path}")
    for method, path in sorted(documented - live_http):
        problems.append(f"openapi-only {method} {path}")
    return problems
