#!/usr/bin/env python3
"""
Routing Truth Gate (Offline / Direct Import)

Ensures services/api/app/data/endpoint_truth.json matches the live FastAPI routing table.

This version imports the app directly (no server startup required), making it faster
for local development and simpler in CI.

Compares path + method pairs:
  truth routes[]  vs  app.router.routes (APIRoute)

Notes:
- HEAD is ignored (FastAPI/Starlette often exposes HEAD implicitly for GET).
- By default, we only enforce /api/* paths (canonical surface). This prevents /docs, /openapi.json,
  /health, etc. from causing drift unless you explicitly want them in the truth file.
- Deprecated routes are expected to exist until sunset date.
- Routes past sunset date generate warnings.

Usage:
    python scripts/governance/check_routing_truth.py

Env overrides:
    ROUTING_TRUTH_FILE              (default services/api/app/data/endpoint_truth.json)
    ROUTING_TRUTH_ENFORCE_API_ONLY  (default true - only check /api/* paths)
    ROUTING_TRUTH_FAIL_PAST_SUNSET  (default false - fail if deprecated route is past sunset)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Set, Tuple

# Will be populated after sys.path adjustment
APIRoute = None

TRUTH_FILE = Path(os.getenv("ROUTING_TRUTH_FILE", "services/api/app/data/endpoint_truth.json"))

# Canonical import for your repo layout
APP_IMPORT = "app.main:app"

# If True, only enforce canonical /api/* routes (recommended for your schema)
ENFORCE_API_PREFIX_ONLY = os.getenv("ROUTING_TRUTH_ENFORCE_API_ONLY", "true").lower() in {"1", "true", "yes"}

# If True, fail when deprecated routes are past sunset
FAIL_PAST_SUNSET = os.getenv("ROUTING_TRUTH_FAIL_PAST_SUNSET", "false").lower() in {"1", "true", "yes"}

# Ignore method noise
IGNORED_METHODS = {"HEAD", "OPTIONS"}


Pair = Tuple[str, str]  # (METHOD, PATH)


def _die(msg: str) -> int:
    print(f"[FAIL] {msg}")
    return 1


def _warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _add_services_api_to_path() -> None:
    """
    Ensure `import app.main` works in CI from repo root.
    """
    # Try to find repo root relative to this script
    script_path = Path(__file__).resolve()
    
    # scripts/governance/check_routing_truth.py -> repo root
    repo_root = script_path.parents[2]
    services_api = repo_root / "services" / "api"
    
    if services_api.exists():
        sys.path.insert(0, str(services_api))
    else:
        # Fallback: assume we're already in services/api or it's in PYTHONPATH
        pass


def _load_app():
    global APIRoute
    from fastapi.routing import APIRoute as _APIRoute
    APIRoute = _APIRoute
    
    module_path, app_name = APP_IMPORT.split(":")
    module = __import__(module_path, fromlist=[app_name])
    return getattr(module, app_name)


def _parse_sunset(sunset_str: str | None) -> date | None:
    """Parse ISO date string to date object."""
    if not sunset_str:
        return None
    try:
        return date.fromisoformat(sunset_str)
    except ValueError:
        return None


def _truth_pairs(truth: dict) -> Tuple[Set[Pair], list]:
    """
    Returns (set of (METHOD, PATH) pairs, list of sunset warnings)
    """
    routes = truth.get("routes", [])
    out: Set[Pair] = set()
    warnings: list = []
    today = date.today()

    for r in routes:
        path = r.get("path")
        methods = r.get("methods", [])
        if not path or not isinstance(methods, list):
            continue

        if ENFORCE_API_PREFIX_ONLY and not str(path).startswith("/api"):
            # Truth file should be canonical; skip non-canonical if present
            continue

        # Check sunset date for deprecated routes
        if r.get("deprecated"):
            sunset = _parse_sunset(r.get("sunset"))
            if sunset and sunset < today:
                warnings.append(f"Route {path} is past sunset date ({r.get('sunset')})")

        for m in methods:
            if not m:
                continue
            mm = str(m).upper()
            if mm in IGNORED_METHODS:
                continue
            out.add((mm, str(path)))

    return out, warnings


def _actual_pairs(app) -> Set[Pair]:
    out: Set[Pair] = set()

    for route in app.router.routes:
        if not isinstance(route, APIRoute):
            continue

        path = route.path

        if ENFORCE_API_PREFIX_ONLY and not str(path).startswith("/api"):
            continue

        for m in route.methods or []:
            mm = str(m).upper()
            if mm in IGNORED_METHODS:
                continue
            out.add((mm, str(path)))

    return out


def main() -> int:
    if not TRUTH_FILE.exists():
        return _die(f"Truth file not found at {TRUTH_FILE}")

    # Make imports work from repo root
    _add_services_api_to_path()

    truth = _load_json(TRUTH_FILE)

    # Lightweight schema sanity
    if "routes" not in truth or not isinstance(truth["routes"], list):
        return _die("endpoint_truth.json missing required `routes` list")

    print(f"Loading FastAPI app from {APP_IMPORT}...")
    try:
        app = _load_app()
    except Exception as e:
        return _die(f"Failed to import app: {e}")

    truth_set, sunset_warnings = _truth_pairs(truth)
    actual_set = _actual_pairs(app)

    missing = truth_set - actual_set
    undocumented = actual_set - truth_set

    exit_code = 0

    # Report sunset warnings
    for w in sunset_warnings:
        _warn(w)
        if FAIL_PAST_SUNSET:
            exit_code = 1

    if missing:
        print("\n[FAIL] Missing routes (declared in truth but not implemented):")
        for method, path in sorted(missing):
            print(f"  {method:<6} {path}")
        exit_code = 1

    if undocumented:
        print("\n[WARN] Undocumented routes (implemented but not in truth):")
        for method, path in sorted(undocumented):
            print(f"  {method:<6} {path}")
        # Undocumented is warning by default, not failure

    # Summary
    print(f"\n--- Routing Truth Summary ---")
    print(f"Truth file: {TRUTH_FILE}")
    print(f"API prefix only: {ENFORCE_API_PREFIX_ONLY}")
    print(f"Truth routes: {len(truth_set)}")
    print(f"Actual routes: {len(actual_set)}")
    print(f"Missing: {len(missing)}")
    print(f"Undocumented: {len(undocumented)}")
    print(f"Sunset warnings: {len(sunset_warnings)}")

    if not missing and not (sunset_warnings and FAIL_PAST_SUNSET):
        print("\n[OK] Routing truth matches live app.")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
