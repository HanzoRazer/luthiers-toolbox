#!/usr/bin/env python3
"""
Route Conflict Detector

Statically analyzes all routers to detect duplicate route paths.
Run as CI gate to prevent route shadowing bugs.

Usage:
    python scripts/ci/check_route_conflicts.py
    python scripts/ci/check_route_conflicts.py --verbose
"""

import ast
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

# Repo root
REPO_ROOT = Path(__file__).parent.parent.parent
API_ROOT = REPO_ROOT / "services" / "api" / "app"


@dataclass
class RouteInfo:
    """Information about a single route."""
    method: str
    path: str
    full_path: str
    file: Path
    line: int
    function_name: str


@dataclass
class RouterSpec:
    """Router specification from manifest."""
    module: str
    prefix: str
    router_attr: str = "router"


def parse_manifest() -> List[RouterSpec]:
    """Parse router_registry/manifest.py to get all router specs."""
    manifest_path = API_ROOT / "router_registry" / "manifest.py"

    if not manifest_path.exists():
        print(f"Warning: Manifest not found at {manifest_path}")
        return []

    specs = []
    content = manifest_path.read_text(encoding="utf-8")

    # Use regex to extract RouterSpec entries
    # Pattern matches RouterSpec( ... module="...", prefix="...", ... )
    pattern = r'RouterSpec\s*\(\s*([^)]+)\)'

    for match in re.finditer(pattern, content, re.DOTALL):
        block = match.group(1)

        # Extract module
        module_match = re.search(r'module\s*=\s*["\']([^"\']+)["\']', block)
        if not module_match:
            continue
        module = module_match.group(1)

        # Extract prefix (default to "")
        prefix_match = re.search(r'prefix\s*=\s*["\']([^"\']*)["\']', block)
        prefix = prefix_match.group(1) if prefix_match else ""

        # Extract router_attr (default to "router")
        attr_match = re.search(r'router_attr\s*=\s*["\']([^"\']+)["\']', block)
        router_attr = attr_match.group(1) if attr_match else "router"

        specs.append(RouterSpec(module=module, prefix=prefix, router_attr=router_attr))

    return specs


def module_to_path(module: str) -> Optional[Path]:
    """Convert module path to file path."""
    # app.routers.foo -> services/api/app/routers/foo.py
    if not module.startswith("app."):
        return None

    rel_path = module.replace(".", "/")

    # Try as file
    file_path = REPO_ROOT / "services" / "api" / f"{rel_path}.py"
    if file_path.exists():
        return file_path

    # Try as package (__init__.py)
    init_path = REPO_ROOT / "services" / "api" / rel_path / "__init__.py"
    if init_path.exists():
        return init_path

    return None


def extract_router_prefix(content: str) -> str:
    """Extract internal router prefix from APIRouter(prefix=...) calls."""
    # Look for router = APIRouter(prefix="/some/path")
    # or router = APIRouter(..., prefix="/some/path", ...)
    patterns = [
        r'router\s*=\s*APIRouter\s*\([^)]*prefix\s*=\s*["\']([^"\']+)["\']',
        r'APIRouter\s*\(\s*prefix\s*=\s*["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    return ""


def extract_routes_from_file(file_path: Path, manifest_prefix: str) -> List[RouteInfo]:
    """Extract all route definitions from a Python file."""
    routes = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return routes

    # Check for internal router prefix (takes precedence over manifest prefix)
    internal_prefix = extract_router_prefix(content)

    # Use internal prefix if it exists and looks like a full path,
    # otherwise combine manifest prefix with internal prefix
    if internal_prefix.startswith("/api"):
        prefix = internal_prefix
    elif internal_prefix:
        prefix = manifest_prefix + internal_prefix
    else:
        prefix = manifest_prefix

    # Parse AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Warning: Syntax error in {file_path}: {e}")
        return routes

    # Find all decorated functions
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            route_info = parse_route_decorator(decorator, node, file_path, prefix)
            if route_info:
                routes.append(route_info)

    return routes


def parse_route_decorator(
    decorator: ast.expr,
    func: ast.FunctionDef,
    file_path: Path,
    prefix: str
) -> Optional[RouteInfo]:
    """Parse a route decorator and extract route info."""

    # Handle @router.get("/path") style
    if isinstance(decorator, ast.Call):
        if isinstance(decorator.func, ast.Attribute):
            attr = decorator.func
            if isinstance(attr.value, ast.Name) and attr.value.id == "router":
                method = attr.attr.upper()
                if method in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"):
                    # Get the path argument
                    if decorator.args:
                        arg = decorator.args[0]
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            path = arg.value
                            full_path = normalize_path(prefix + path)
                            return RouteInfo(
                                method=method,
                                path=path,
                                full_path=full_path,
                                file=file_path,
                                line=decorator.lineno,
                                function_name=func.name,
                            )

    return None


def normalize_path(path: str) -> str:
    """Normalize a path for comparison."""
    # Remove trailing slash
    path = path.rstrip("/")
    # Ensure leading slash
    if not path.startswith("/"):
        path = "/" + path
    # Collapse double slashes
    while "//" in path:
        path = path.replace("//", "/")
    return path


def find_conflicts(routes: List[RouteInfo]) -> Dict[Tuple[str, str], List[RouteInfo]]:
    """Find routes with the same method and full path."""
    by_key: Dict[Tuple[str, str], List[RouteInfo]] = defaultdict(list)

    for route in routes:
        # Normalize path params for comparison
        # /foo/{id} and /foo/{bar} are the same route
        normalized = re.sub(r'\{[^}]+\}', '{param}', route.full_path)
        key = (route.method, normalized)
        by_key[key].append(route)

    # Filter to only conflicts (2+ routes)
    return {k: v for k, v in by_key.items() if len(v) > 1}


def relative_path(path: Path) -> str:
    """Get path relative to repo root."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("=" * 60)
    print("Route Conflict Detector")
    print("=" * 60)
    print()

    # Parse manifest
    specs = parse_manifest()
    print(f"Found {len(specs)} router specs in manifest")

    # Extract routes from all routers
    all_routes: List[RouteInfo] = []
    routers_scanned = 0

    for spec in specs:
        file_path = module_to_path(spec.module)
        if not file_path:
            if verbose:
                print(f"  Skip: {spec.module} (file not found)")
            continue

        routes = extract_routes_from_file(file_path, spec.prefix)
        all_routes.extend(routes)
        routers_scanned += 1

        if verbose and routes:
            print(f"  {spec.module}: {len(routes)} routes")

    print(f"Scanned {routers_scanned} routers, found {len(all_routes)} total routes")
    print()

    # Find conflicts
    conflicts = find_conflicts(all_routes)

    if not conflicts:
        print("[PASS] No route conflicts detected")
        print()
        return 0

    # Report conflicts
    print(f"[FAIL] Found {len(conflicts)} route conflicts:")
    print()

    exit_code = 0
    for (method, path), routes in sorted(conflicts.items()):
        print(f"CONFLICT: {method} {path}")
        print("-" * 50)

        for i, route in enumerate(routes):
            winner = " <- WINS (registered last)" if i == len(routes) - 1 else " <- SHADOWED"
            print(f"  {relative_path(route.file)}:{route.line}")
            print(f"    Function: {route.function_name}()")
            print(f"    Route: {route.path}{winner}")

        print()
        exit_code = 1

    print("=" * 60)
    print("To fix: Rename one of the conflicting routes to a unique path")
    print("=" * 60)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
