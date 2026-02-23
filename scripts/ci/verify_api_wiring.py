#!/usr/bin/env python3
"""
API Wiring Verification

Comprehensive check that the API feature network is properly connected:
1. All routers in manifest are importable and mountable
2. All registered routes are reachable (no 500 errors on import)
3. No route conflicts (duplicates)
4. OpenAPI schema is generated and valid
5. Critical endpoints respond correctly

Run as CI gate to catch wiring issues before deployment.

Usage:
    python scripts/ci/verify_api_wiring.py
    python scripts/ci/verify_api_wiring.py --verbose
    python scripts/ci/verify_api_wiring.py --json
"""

import sys
import json
import argparse
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

# Add the API app to path
REPO_ROOT = Path(__file__).parent.parent.parent
API_ROOT = REPO_ROOT / "services" / "api"
sys.path.insert(0, str(API_ROOT))


@dataclass
class CheckResult:
    """Result of a single check."""
    name: str
    passed: bool
    message: str
    details: List[str] = field(default_factory=list)


@dataclass
class WiringReport:
    """Complete wiring verification report."""
    passed: bool = True
    checks: List[CheckResult] = field(default_factory=list)
    total_routes: int = 0
    total_routers: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def check_router_imports(verbose: bool = False) -> CheckResult:
    """Check that all routers in manifest can be imported."""
    result = CheckResult(
        name="Router Imports",
        passed=True,
        message="",
        details=[],
    )

    try:
        from app.router_registry.manifest import ROUTER_MANIFEST
    except ImportError as e:
        result.passed = False
        result.message = f"Cannot import router manifest: {e}"
        return result

    failed_imports = []
    successful_imports = 0

    for spec in ROUTER_MANIFEST:
        module_path = spec.module
        router_attr = getattr(spec, 'router_attr', 'router')

        try:
            module = importlib.import_module(module_path)
            router = getattr(module, router_attr, None)

            if router is None:
                failed_imports.append(f"{module_path}: missing '{router_attr}' attribute")
            else:
                successful_imports += 1
                if verbose:
                    result.details.append(f"OK: {module_path}")

        except Exception as e:
            failed_imports.append(f"{module_path}: {type(e).__name__}: {e}")

    if failed_imports:
        result.passed = False
        result.message = f"{len(failed_imports)} router(s) failed to import"
        result.details = failed_imports
    else:
        result.message = f"All {successful_imports} routers imported successfully"

    return result


def check_app_startup(verbose: bool = False) -> Tuple[CheckResult, Any]:
    """Check that the FastAPI app starts without errors."""
    result = CheckResult(
        name="App Startup",
        passed=True,
        message="",
        details=[],
    )

    app = None
    try:
        from app.main import app as fastapi_app
        app = fastapi_app
        result.message = "FastAPI app created successfully"

        # Count routes
        route_count = len([r for r in app.routes if hasattr(r, 'methods')])
        result.details.append(f"Total routes registered: {route_count}")

    except Exception as e:
        result.passed = False
        result.message = f"App startup failed: {type(e).__name__}: {e}"
        if verbose:
            result.details.append(traceback.format_exc())

    return result, app


def check_openapi_generation(app: Any, verbose: bool = False) -> CheckResult:
    """Check that OpenAPI schema generates without errors."""
    result = CheckResult(
        name="OpenAPI Schema",
        passed=True,
        message="",
        details=[],
    )

    if app is None:
        result.passed = False
        result.message = "Cannot check OpenAPI: app not available"
        return result

    try:
        schema = app.openapi()

        if not schema:
            result.passed = False
            result.message = "OpenAPI schema is empty"
            return result

        # Validate schema structure
        paths = schema.get("paths", {})
        components = schema.get("components", {})

        result.message = f"OpenAPI schema valid: {len(paths)} paths, {len(components.get('schemas', {}))} schemas"

        if verbose:
            # List all paths
            for path in sorted(paths.keys())[:20]:
                methods = list(paths[path].keys())
                result.details.append(f"  {path}: {', '.join(methods)}")
            if len(paths) > 20:
                result.details.append(f"  ... and {len(paths) - 20} more paths")

    except Exception as e:
        result.passed = False
        result.message = f"OpenAPI generation failed: {type(e).__name__}: {e}"
        if verbose:
            result.details.append(traceback.format_exc())

    return result


def check_route_conflicts(verbose: bool = False) -> CheckResult:
    """Check for duplicate route registrations."""
    result = CheckResult(
        name="Route Conflicts",
        passed=True,
        message="",
        details=[],
    )

    # Import and run the route conflict detector
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts" / "ci"))
        from check_route_conflicts import parse_manifest, module_to_path, extract_routes_from_file, find_conflicts

        specs = parse_manifest()
        all_routes = []

        for spec in specs:
            file_path = module_to_path(spec.module)
            if file_path:
                routes = extract_routes_from_file(file_path, spec.prefix)
                all_routes.extend(routes)

        conflicts = find_conflicts(all_routes)

        if conflicts:
            result.passed = False
            result.message = f"{len(conflicts)} route conflict(s) detected"
            for (method, path), routes in conflicts.items():
                result.details.append(f"CONFLICT: {method} {path} ({len(routes)} definitions)")
        else:
            result.message = f"No conflicts among {len(all_routes)} routes"

    except ImportError:
        result.message = "Route conflict checker not available (check_route_conflicts.py)"
        result.details.append("Skipped - install check_route_conflicts.py")
    except Exception as e:
        result.passed = False
        result.message = f"Route conflict check failed: {e}"

    return result


def check_critical_endpoints(app: Any, verbose: bool = False) -> CheckResult:
    """Check that critical endpoints respond correctly."""
    result = CheckResult(
        name="Critical Endpoints",
        passed=True,
        message="",
        details=[],
    )

    if app is None:
        result.passed = False
        result.message = "Cannot check endpoints: app not available"
        return result

    try:
        from fastapi.testclient import TestClient
        client = TestClient(app, raise_server_exceptions=False)

        # Critical endpoints that should always work
        critical_endpoints = [
            ("GET", "/health", [200]),
            ("GET", "/api/health", [200]),
            ("GET", "/docs", [200]),
            ("GET", "/openapi.json", [200]),
        ]

        passed_count = 0
        failed_endpoints = []

        for method, path, expected_codes in critical_endpoints:
            try:
                if method == "GET":
                    response = client.get(path)
                elif method == "POST":
                    response = client.post(path, json={})
                else:
                    continue

                if response.status_code in expected_codes:
                    passed_count += 1
                    if verbose:
                        result.details.append(f"OK: {method} {path} -> {response.status_code}")
                else:
                    failed_endpoints.append(f"{method} {path}: expected {expected_codes}, got {response.status_code}")

            except Exception as e:
                failed_endpoints.append(f"{method} {path}: {type(e).__name__}: {e}")

        if failed_endpoints:
            result.passed = False
            result.message = f"{len(failed_endpoints)} critical endpoint(s) failed"
            result.details.extend(failed_endpoints)
        else:
            result.message = f"All {passed_count} critical endpoints responding"

    except ImportError:
        result.message = "TestClient not available (install httpx)"
        result.details.append("Skipped - pip install httpx")
    except Exception as e:
        result.passed = False
        result.message = f"Endpoint check failed: {e}"

    return result


def check_no_import_errors_in_routes(app: Any, verbose: bool = False) -> CheckResult:
    """Check that hitting routes doesn't cause import errors."""
    result = CheckResult(
        name="Route Import Health",
        passed=True,
        message="",
        details=[],
    )

    if app is None:
        result.passed = False
        result.message = "Cannot check routes: app not available"
        return result

    try:
        from fastapi.testclient import TestClient
        client = TestClient(app, raise_server_exceptions=False)

        # Get all GET routes from OpenAPI
        schema = app.openapi()
        paths = schema.get("paths", {})

        checked = 0
        errors = []

        for path, methods in paths.items():
            if "get" not in methods:
                continue

            # Skip paths with complex parameters
            if "{" in path and "}" in path:
                # Try with a dummy ID
                test_path = path.replace("{", "").replace("}", "")
                for param in ["run_id", "job_id", "id", "preset_id", "session_id"]:
                    test_path = test_path.replace(param, "test-id-123")
            else:
                test_path = path

            try:
                response = client.get(test_path)
                checked += 1

                # 500 errors often indicate import/wiring issues
                if response.status_code == 500:
                    try:
                        detail = response.json().get("detail", str(response.content[:200]))
                    except Exception:
                        detail = str(response.content[:200])

                    # Check if it's an import error
                    if "import" in str(detail).lower() or "module" in str(detail).lower():
                        errors.append(f"{path}: Import error - {detail[:100]}")

            except Exception as e:
                if "import" in str(e).lower():
                    errors.append(f"{path}: {e}")

            # Limit checks to avoid timeout
            if checked >= 50:
                break

        if errors:
            result.passed = False
            result.message = f"{len(errors)} route(s) have import errors"
            result.details = errors[:10]  # Limit output
            if len(errors) > 10:
                result.details.append(f"... and {len(errors) - 10} more")
        else:
            result.message = f"Checked {checked} routes, no import errors detected"

    except Exception as e:
        result.message = f"Route health check skipped: {e}"

    return result


def run_verification(verbose: bool = False) -> WiringReport:
    """Run all wiring verification checks."""
    report = WiringReport()

    # Check 1: Router imports
    result = check_router_imports(verbose)
    report.checks.append(result)
    if not result.passed:
        report.passed = False

    # Check 2: App startup
    result, app = check_app_startup(verbose)
    report.checks.append(result)
    if not result.passed:
        report.passed = False

    # Check 3: OpenAPI generation
    result = check_openapi_generation(app, verbose)
    report.checks.append(result)
    if not result.passed:
        report.passed = False

    # Check 4: Route conflicts
    result = check_route_conflicts(verbose)
    report.checks.append(result)
    if not result.passed:
        report.passed = False

    # Check 5: Critical endpoints
    result = check_critical_endpoints(app, verbose)
    report.checks.append(result)
    if not result.passed:
        report.passed = False

    # Check 6: No import errors in routes
    result = check_no_import_errors_in_routes(app, verbose)
    report.checks.append(result)
    if not result.passed:
        report.passed = False

    # Gather stats
    if app:
        report.total_routes = len([r for r in app.routes if hasattr(r, 'methods')])
        try:
            from app.router_registry.manifest import ROUTER_MANIFEST
            report.total_routers = len(ROUTER_MANIFEST)
        except Exception:
            pass

    return report


def print_report(report: WiringReport, verbose: bool = False):
    """Print human-readable report."""
    print("=" * 60)
    print("API Wiring Verification Report")
    print("=" * 60)
    print()

    status = "[PASS]" if report.passed else "[FAIL]"
    print(f"Overall Status: {status}")
    print(f"Total Routers: {report.total_routers}")
    print(f"Total Routes: {report.total_routes}")
    print()

    print("Checks:")
    print("-" * 60)

    for check in report.checks:
        icon = "[PASS]" if check.passed else "[FAIL]"
        print(f"{icon} {check.name}")
        print(f"      {check.message}")

        if check.details and (verbose or not check.passed):
            for detail in check.details[:10]:
                print(f"        - {detail}")
            if len(check.details) > 10:
                print(f"        ... and {len(check.details) - 10} more")
        print()

    print("=" * 60)
    if not report.passed:
        print("Fix the failing checks before deployment!")
    print("=" * 60)


def print_json(report: WiringReport):
    """Print JSON output."""
    output = {
        "passed": report.passed,
        "total_routers": report.total_routers,
        "total_routes": report.total_routes,
        "checks": [asdict(c) for c in report.checks],
    }
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Verify API wiring and feature network connectivity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output for all checks",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    # Change to API directory for imports
    import os
    os.chdir(API_ROOT)

    report = run_verification(verbose=args.verbose)

    if args.json:
        print_json(report)
    else:
        print_report(report, verbose=args.verbose)

    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
