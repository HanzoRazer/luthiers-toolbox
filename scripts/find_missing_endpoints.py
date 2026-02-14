#!/usr/bin/env python3
"""
Find Missing Endpoints Harness

Scans frontend code for ALL API calls and compares against backend router definitions.
Reports any frontend calls that don't have matching backend endpoints.

This is a diagnostic tool for finding cascade errors from frontend-backend drift.

Usage:
    python scripts/find_missing_endpoints.py
    python scripts/find_missing_endpoints.py --verbose
"""

import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = REPO_ROOT / "packages" / "client" / "src"
BACKEND_DIR = REPO_ROOT / "services" / "api" / "app"
MANIFEST_FILE = BACKEND_DIR / "router_registry" / "manifest.py"


def extract_frontend_api_calls() -> Dict[str, List[str]]:
    """
    Scan frontend for API calls. Returns dict of {path: [source_files]}.

    Looks for:
    - fetch('/api/...') and fetch('/path/...')
    - SDK patterns like `${BASE}/runs` where BASE = "/rmos/acoustics"
    - Direct paths in SDK endpoint files
    """
    api_calls = defaultdict(list)

    # Patterns for direct API calls
    direct_patterns = [
        # fetch with string literal
        r'''fetch\s*\(\s*['""`]([^'""`\s\$]+)['""`]''',
        # Template literals: `${...}/path` or `/path/${...}`
        r'''fetch\s*\(\s*`([^`]+)`''',
        # .get/.post/.put/.delete
        r'''\.(?:get|post|put|delete|patch)\s*\(\s*['""`]([^'""`\s]+)['""`]''',
        r'''\.(?:get|post|put|delete|patch)\s*<[^>]+>\s*\(\s*['""`]([^'""`\s]+)['""`]''',
    ]

    # SDK BASE constant pattern
    sdk_base_pattern = r'''const\s+BASE\s*=\s*['""]([^'""]+)['"]'''

    for ext in ["*.vue", "*.ts", "*.js"]:
        for file_path in FRONTEND_DIR.rglob(ext):
            try:
                content = file_path.read_text(encoding="utf-8")
                rel_path = file_path.relative_to(FRONTEND_DIR)

                # Check for SDK BASE constant
                sdk_base = None
                base_match = re.search(sdk_base_pattern, content)
                if base_match:
                    sdk_base = base_match.group(1)

                # Extract all API paths
                for pattern in direct_patterns:
                    for match in re.finditer(pattern, content):
                        path = match.group(1)

                        # Skip non-API paths
                        if not path.startswith("/"):
                            continue
                        if path.startswith("//"):  # URLs
                            continue

                        # Handle template literals
                        if "${" in path:
                            # Extract static parts
                            # e.g., `${BASE}/runs` with BASE="/rmos/acoustics" -> /rmos/acoustics/runs
                            if sdk_base and "${BASE}" in path:
                                path = path.replace("${BASE}", sdk_base)
                            else:
                                # Keep the template but mark path params
                                path = re.sub(r'\$\{[^}]+\}', '{param}', path)

                        # Clean query params
                        path = path.split("?")[0].split("#")[0]

                        # Normalize
                        path = path.rstrip("/")
                        if not path:
                            continue

                        # Add /api prefix if missing (interceptor adds it)
                        if not path.startswith("/api") and not path.startswith("/_"):
                            path = "/api" + path

                        api_calls[path].append(str(rel_path))

            except (OSError, UnicodeDecodeError) as e:
                print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
                continue

    return dict(api_calls)


def extract_backend_routes() -> Set[str]:
    """
    Extract all registered routes from the backend.
    Parses the router manifest and router files.
    """
    routes = set()

    # Parse manifest for router modules
    if MANIFEST_FILE.exists():
        content = MANIFEST_FILE.read_text(encoding="utf-8")

        # Extract RouterSpec entries
        # Pattern: module="...", prefix="..."
        specs = re.findall(
            r'RouterSpec\s*\([^)]*module\s*=\s*["\']([^"\']+)["\'][^)]*prefix\s*=\s*["\']([^"\']*)["\']',
            content,
            re.DOTALL
        )

        for module, prefix in specs:
            # Try to find the router file and extract its routes
            module_path = module.replace(".", "/") + ".py"
            router_file = BACKEND_DIR.parent / module_path

            if router_file.exists():
                try:
                    router_content = router_file.read_text(encoding="utf-8")

                    # Find @router.get/post/etc decorators
                    route_patterns = [
                        r'@router\.(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                    ]

                    for pattern in route_patterns:
                        for match in re.finditer(pattern, router_content):
                            route_path = match.group(1)
                            full_path = (prefix + route_path).replace("//", "/")
                            routes.add(full_path)

                except (OSError, UnicodeDecodeError):
                    pass

    # Also scan all router files directly
    for router_file in BACKEND_DIR.rglob("*router*.py"):
        try:
            content = router_file.read_text(encoding="utf-8")

            # Find APIRouter prefix
            prefix_match = re.search(r'APIRouter\s*\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', content)
            router_prefix = prefix_match.group(1) if prefix_match else ""

            # Find route decorators
            for match in re.finditer(r'@router\.(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', content):
                route_path = match.group(1)
                full_path = (router_prefix + route_path).replace("//", "/")
                if not full_path.startswith("/api"):
                    full_path = "/api" + full_path
                routes.add(full_path)

        except (OSError, UnicodeDecodeError):
            continue

    return routes


def normalize_for_matching(path: str) -> str:
    """Normalize path for matching (replace IDs with placeholders)."""
    # Replace UUIDs, hex strings, numeric IDs
    normalized = re.sub(r'/[a-f0-9]{8,}(?:-[a-f0-9]{4,})*', '/{id}', path)
    normalized = re.sub(r'/\d+', '/{id}', normalized)
    normalized = re.sub(r'/\{[^}]+\}', '/{id}', normalized)
    return normalized


def paths_match(frontend_path: str, backend_path: str) -> bool:
    """Check if a frontend path matches a backend route (considering params)."""
    if frontend_path == backend_path:
        return True

    # Normalize both
    norm_front = normalize_for_matching(frontend_path)
    norm_back = normalize_for_matching(backend_path)

    if norm_front == norm_back:
        return True

    # Try segment-by-segment match
    front_parts = frontend_path.strip("/").split("/")
    back_parts = backend_path.strip("/").split("/")

    if len(front_parts) != len(back_parts):
        return False

    for fp, bp in zip(front_parts, back_parts):
        # Backend param like {run_id} matches anything
        if bp.startswith("{") and bp.endswith("}"):
            continue
        # Frontend param placeholder
        if fp == "{param}" or fp == "{id}":
            continue
        if fp != bp:
            return False

    return True


def find_missing_endpoints(verbose: bool = False) -> Tuple[List[str], List[str]]:
    """
    Find frontend API calls without matching backend routes.
    Returns (missing, matched).
    """
    print("=" * 70)
    print("FRONTEND-BACKEND ENDPOINT VALIDATION")
    print("=" * 70)
    print()

    print("Scanning frontend for API calls...")
    frontend_calls = extract_frontend_api_calls()
    print(f"  Found {len(frontend_calls)} unique API paths")

    print("Scanning backend for registered routes...")
    backend_routes = extract_backend_routes()
    print(f"  Found {len(backend_routes)} registered routes")
    print()

    missing = []
    matched = []

    for path, sources in sorted(frontend_calls.items()):
        found = False
        for route in backend_routes:
            if paths_match(path, route):
                found = True
                matched.append(path)
                if verbose:
                    print(f"  OK: {path}")
                    if path != route:
                        print(f"      -> matches {route}")
                break

        if not found:
            missing.append(path)

    return missing, matched


def main():
    parser = argparse.ArgumentParser(description="Find missing API endpoints")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show matched endpoints too")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    missing, matched = find_missing_endpoints(verbose=args.verbose)

    if args.json:
        print(json.dumps({
            "missing": missing,
            "matched": matched,
            "missing_count": len(missing),
            "matched_count": len(matched),
        }, indent=2))
        sys.exit(1 if missing else 0)

    print()
    print("=" * 70)
    print(f"MISSING ENDPOINTS ({len(missing)})")
    print("=" * 70)

    if missing:
        # Group by prefix for readability
        by_prefix = defaultdict(list)
        for path in missing:
            parts = path.split("/")
            if len(parts) >= 3:
                prefix = "/".join(parts[:4])
            else:
                prefix = path
            by_prefix[prefix].append(path)

        for prefix in sorted(by_prefix.keys()):
            paths = by_prefix[prefix]
            print(f"\n{prefix}* ({len(paths)} endpoints)")
            for p in sorted(paths):
                print(f"  - {p}")
    else:
        print("  None! All frontend calls have matching backend routes.")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Matched:  {len(matched)}")
    print(f"  Missing:  {len(missing)}")
    print()

    if missing:
        print("ACTION REQUIRED: Create stub routers for missing endpoints")
        print("or fix frontend to use correct paths.")
        sys.exit(1)
    else:
        print("SUCCESS: All frontend API calls have matching backend endpoints.")
        sys.exit(0)


if __name__ == "__main__":
    main()
