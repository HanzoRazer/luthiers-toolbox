"""
Route Governance Tests

Enforces architectural rules:
1. Component Router Rule (COMPONENT_ROUTER_RULE_v1.md):
   - No scattered endpoints across multiple routers
   - Single canonical prefix per domain

2. Fortran Rule (STRUCTURAL_MILESTONE_EXECUTIVE_SUMMARY.md):
   - No inline math computations in routers
   - Routers must delegate to math modules

These tests scan OpenAPI paths and router source files, failing if rules are violated.
Run as part of CI to prevent architectural drift.
"""

import pytest
import re
import ast
from pathlib import Path
from fastapi.testclient import TestClient


# =============================================================================
# GOVERNANCE RULES CONFIGURATION
# =============================================================================

# Domain keywords and their canonical prefixes
# Format: { "keyword": ("/canonical/prefix", ["/allowed/exception/pattern", ...]) }
DOMAIN_RULES = {
    "fret": (
        "/api/fret",
        [
            "/api/cam/fret_slots",      # CAM operations are separate
            "/api/registry/",           # Registry endpoints (fret_formulas)
            "/api/instrument_geometry", # Legacy (being migrated)
        ],
    ),
    "neck": (
        "/api/neck",
        [
            "/api/cam/neck",            # CAM operations
            "/api/instrument/",         # Legacy instrument router
        ],
    ),
    "bridge": (
        "/api/bridge",
        [
            "/api/cam/bridge",          # CAM operations
            "/api/instrument/",         # Legacy instrument router
            "/api/guitar/archtop",      # Archtop-specific bridge
            "/api/instrument_geometry", # Legacy
        ],
    ),
    "archtop": (
        "/api/guitar/archtop",
        [],
    ),
    "stratocaster": (
        "/api/guitar/stratocaster",
        [],
    ),
}


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def openapi_paths():
    """Get all API paths from OpenAPI schema."""
    from app.main import app
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return list(response.json().get("paths", {}).keys())


# =============================================================================
# GOVERNANCE TESTS
# =============================================================================

class TestComponentRouterRule:
    """
    Tests for Component Router Rule compliance.

    Rule: Any instrument subdomain with >2 endpoints MUST have a
    dedicated component router with a single canonical prefix.
    """

    def test_no_scattered_fret_routes(self, openapi_paths):
        """
        RULE: All fret routes must be under /api/fret/* or allowed exceptions.

        Prevents regression to scattered fret endpoints across:
        - instrument_geometry_router
        - ltb_calculator_router
        - instrument_router
        - temperament_router
        """
        violations = []
        canonical, exceptions = DOMAIN_RULES["fret"]

        for path in openapi_paths:
            if "fret" in path.lower():
                # Check if it's under canonical prefix
                if path.startswith(canonical):
                    continue
                # Check if it's an allowed exception
                if any(path.startswith(exc) for exc in exceptions):
                    continue
                # It's a violation
                violations.append(path)

        if violations:
            pytest.fail(
                f"Scattered fret routes found (violates COMPONENT_ROUTER_RULE_v1):\n"
                f"  Expected prefix: {canonical}\n"
                f"  Violations:\n" +
                "\n".join(f"    - {v}" for v in violations)
            )

    def test_no_scattered_neck_routes(self, openapi_paths):
        """All neck routes must be under /api/neck/*."""
        violations = []
        canonical, exceptions = DOMAIN_RULES["neck"]

        for path in openapi_paths:
            # Only check paths with 'neck' as a segment, not substring
            if "/neck" in path or path.endswith("/neck"):
                if path.startswith(canonical):
                    continue
                if any(path.startswith(exc) for exc in exceptions):
                    continue
                violations.append(path)

        if violations:
            pytest.fail(
                f"Scattered neck routes found:\n"
                f"  Expected prefix: {canonical}\n"
                f"  Violations:\n" +
                "\n".join(f"    - {v}" for v in violations)
            )

    def test_no_scattered_bridge_routes(self, openapi_paths):
        """All bridge routes must be under /api/bridge/* or CAM exceptions."""
        violations = []
        canonical, exceptions = DOMAIN_RULES["bridge"]

        for path in openapi_paths:
            if "/bridge" in path:
                if path.startswith(canonical):
                    continue
                if any(path.startswith(exc) for exc in exceptions):
                    continue
                # Ignore instrument_geometry bridge endpoint (grandfathered)
                if "/instrument_geometry/" in path:
                    continue
                violations.append(path)

        if violations:
            pytest.fail(
                f"Scattered bridge routes found:\n"
                f"  Expected prefix: {canonical}\n"
                f"  Violations:\n" +
                "\n".join(f"    - {v}" for v in violations)
            )


class TestNoDoublePrefix:
    """
    Tests for malformed route prefixes.

    Catches bugs like /api/api/... which indicate incorrect router registration.
    """

    def test_no_double_api_prefix(self, openapi_paths):
        """No routes should have /api/api/ (double prefix bug)."""
        violations = [p for p in openapi_paths if "/api/api/" in p]

        if violations:
            pytest.fail(
                f"Double /api/api/ prefix found (router registration bug):\n" +
                "\n".join(f"    - {v}" for v in violations)
            )


class TestNoDuplicatePrefixes:
    """
    Tests that no domain has duplicate prefixes.

    Example violation: /api/fret/table AND /api/calculators/fret/table
    """

    def test_fret_design_consolidated(self, openapi_paths):
        """
        Fret DESIGN endpoints should only appear under /api/fret/*.

        Excludes: CAM operations, registry, legacy endpoints.
        """
        # These are the fret design paths that MUST be under /api/fret
        design_keywords = ["/fret/position", "/fret/table", "/fretboard", "/fan_fret"]

        violations = []
        for path in openapi_paths:
            for keyword in design_keywords:
                if keyword in path and not path.startswith("/api/fret"):
                    # Skip known exceptions
                    if any(exc in path for exc in ["/cam/", "/registry/"]):
                        continue
                    violations.append(path)

        if violations:
            pytest.fail(
                f"Fret design endpoints outside /api/fret/* (should be consolidated):\n" +
                "\n".join(f"    - {v}" for v in set(violations))
            )


class TestOpenAPIPathSnapshot:
    """
    Golden test for fret router paths.

    Prevents accidental addition/removal of endpoints.
    Update EXPECTED_FRET_PATHS when intentionally changing the API.
    """

    EXPECTED_FRET_PATHS = [
        "/api/fret/position",
        "/api/fret/table",
        "/api/fret/board/outline",
        "/api/fret/board/slots",
        "/api/fret/radius/compound",
        "/api/fret/radius/presets",
        "/api/fret/fan/calculate",
        "/api/fret/fan/validate",
        "/api/fret/fan/presets",
        "/api/fret/staggered",
        "/api/fret/temperaments",
        "/api/fret/scales/presets",
        "/api/fret/health",
    ]

    def test_fret_router_paths_stable(self, openapi_paths):
        """Verify fret router endpoints haven't changed unexpectedly."""
        actual_fret_paths = sorted([
            p for p in openapi_paths
            if p.startswith("/api/fret")
        ])
        expected = sorted(self.EXPECTED_FRET_PATHS)

        missing = set(expected) - set(actual_fret_paths)
        unexpected = set(actual_fret_paths) - set(expected)

        errors = []
        if missing:
            errors.append(f"Missing endpoints:\n" + "\n".join(f"    - {p}" for p in missing))
        if unexpected:
            errors.append(f"Unexpected endpoints:\n" + "\n".join(f"    - {p}" for p in unexpected))

        if errors:
            pytest.fail(
                "Fret router paths changed (update EXPECTED_FRET_PATHS if intentional):\n" +
                "\n".join(errors)
            )


# =============================================================================
# FORTRAN RULE: NO INLINE MATH IN ROUTERS
# =============================================================================

# Routers that are grandfathered (pre-cleanup) or have legitimate exceptions
# NOTE: When you fix a router, REMOVE IT from this list to enable enforcement
FORTRAN_RULE_EXCEPTIONS = {
    # Grandfathered routers with remaining inline math (lower priority cleanup)
    # TODO: Extract sine wave math to geometry module
    "adaptive_preview_router.py",
    # TODO: Extract neck angle math to instrument_geometry
    "archtop_router.py",
    # TODO: Extract circle pattern math to geometry/arc_utils
    "cam_drill_pattern_router.py",
    # TODO: Extract remaining arc tessellation to cam/biarc_math
    "cam_post_v155_router.py",
    "cam_post_v160_router.py",
    "cam_post_v161_router.py",
    # TODO: Extract arc angle calculations to geometry/arc_utils
    "geometry_router.py",
    # Test/utility routers
    "health_router.py",
}

# Math patterns that indicate inline computation (violations)
INLINE_MATH_PATTERNS = [
    # Trigonometric computations
    (r'\bmath\.sin\s*\(', "math.sin() - use geometry/arc_utils or instrument_geometry"),
    (r'\bmath\.cos\s*\(', "math.cos() - use geometry/arc_utils or instrument_geometry"),
    (r'\bmath\.tan\s*\(', "math.tan() - use geometry/arc_utils"),
    (r'\bmath\.atan2?\s*\(', "math.atan/atan2() - use geometry/arc_utils"),
    # Exponential/power computations (fret math)
    (r'\b2\s*\*\*\s*\(-?\s*\w+\s*/\s*12\)', "2^(-fret/12) - use fret_math.py"),
    (r'\bmath\.pow\s*\(', "math.pow() - extract to math module"),
    # Hardcoded pi
    (r'\b3\.14159', "Hardcoded pi - use math.pi"),
    # Circle/arc formulas
    (r'\b2\s*\*\s*(?:math\.)?pi\s*\*\s*\w+', "Circle formula - use geometry/arc_utils"),
]

# Allowed math imports (stdlib conversions, not algorithms)
ALLOWED_MATH_USAGE = [
    "math.hypot",      # Distance calculation (stdlib, not algorithm)
    "math.radians",    # Unit conversion
    "math.degrees",    # Unit conversion
    "math.pi",         # Constant (allowed when passed to functions)
    "math.sqrt",       # When used for simple distance, not algorithm
    "math.floor",      # Rounding
    "math.ceil",       # Rounding
    "math.isnan",      # Validation
    "math.isinf",      # Validation
]


class TestFortranRule:
    """
    Tests for Fortran Rule compliance: "All math in subroutines"

    Routers should delegate calculations to math modules, not compute inline.
    This prevents duplicate implementations and ensures testable math.

    Canonical math modules:
    - geometry/arc_utils.py - Circles, arcs, tessellation
    - instrument_geometry/neck/fret_math.py - Fret calculations
    - instrument_geometry/body/parametric.py - Bezier, ellipse
    - cam/biarc_math.py - Fillets, arc fitting
    """

    @pytest.fixture(scope="class")
    def router_files(self):
        """
        Get all router Python files across all directories.

        Scans:
        - app/routers/*_router.py (main routers)
        - app/rmos/*_router.py (RMOS domain routers)
        - app/rmos/api/*_router.py (RMOS API routers)
        - app/rmos/api_*.py (RMOS API modules)
        - app/rmos/runs/api_*.py (RMOS runs API)
        - app/saw_lab/*_router.py (Saw Lab routers)
        """
        app_dir = Path(__file__).parent.parent / "app"
        if not app_dir.exists():
            pytest.skip("App directory not found")

        router_files = []

        # Main routers directory
        routers_dir = app_dir / "routers"
        if routers_dir.exists():
            router_files.extend(routers_dir.glob("*_router.py"))

        # RMOS domain routers
        rmos_dir = app_dir / "rmos"
        if rmos_dir.exists():
            router_files.extend(rmos_dir.glob("*_router.py"))
            router_files.extend(rmos_dir.glob("api_*.py"))
            # RMOS API subdirectory
            rmos_api_dir = rmos_dir / "api"
            if rmos_api_dir.exists():
                router_files.extend(rmos_api_dir.glob("*_router.py"))
            # RMOS runs subdirectory
            rmos_runs_dir = rmos_dir / "runs"
            if rmos_runs_dir.exists():
                router_files.extend(rmos_runs_dir.glob("api_*.py"))
            # RMOS runs_v2 subdirectory
            rmos_runs_v2_dir = rmos_dir / "runs_v2"
            if rmos_runs_v2_dir.exists():
                router_files.extend(rmos_runs_v2_dir.glob("api_*.py"))

        # Saw Lab routers
        saw_lab_dir = app_dir / "saw_lab"
        if saw_lab_dir.exists():
            router_files.extend(saw_lab_dir.glob("*_router.py"))

        return router_files

    def test_no_inline_math_in_routers(self, router_files):
        """
        RULE: Routers must not contain inline math computations.

        Violations trigger when router files contain math patterns
        that should be delegated to canonical math modules.
        """
        violations = []

        for router_path in router_files:
            if router_path.name in FORTRAN_RULE_EXCEPTIONS:
                continue

            content = router_path.read_text(encoding="utf-8")
            file_violations = []

            for pattern, message in INLINE_MATH_PATTERNS:
                matches = list(re.finditer(pattern, content))
                for match in matches:
                    # Find line number
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = content.split('\n')[line_num - 1].strip()

                    # Skip if it's in a comment
                    if line_content.startswith('#'):
                        continue
                    # Skip if it's in a docstring context (rough heuristic)
                    if '"""' in line_content or "'''" in line_content:
                        continue

                    file_violations.append(
                        f"  Line {line_num}: {message}\n"
                        f"    Code: {line_content[:80]}"
                    )

            if file_violations:
                violations.append(
                    f"\n{router_path.name}:\n" + "\n".join(file_violations)
                )

        if violations:
            pytest.fail(
                "Fortran Rule violations found (inline math in routers):\n"
                "Routers should delegate to math modules, not compute inline.\n"
                "\nCanonical modules:\n"
                "  - geometry/arc_utils.py\n"
                "  - instrument_geometry/neck/fret_math.py\n"
                "  - cam/biarc_math.py\n"
                "\nViolations:" + "".join(violations)
            )

    def test_no_hardcoded_pi(self, router_files):
        """
        RULE: No hardcoded pi values (3.14159, 3.1416, etc.)

        Always use math.pi for consistency and precision.
        """
        violations = []
        pi_pattern = re.compile(r'\b3\.14\d*')

        for router_path in router_files:
            content = router_path.read_text(encoding="utf-8")
            matches = list(pi_pattern.finditer(content))

            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line_content = content.split('\n')[line_num - 1].strip()

                # Skip comments
                if line_content.startswith('#'):
                    continue

                violations.append(
                    f"{router_path.name}:{line_num} - {line_content[:60]}"
                )

        if violations:
            pytest.fail(
                "Hardcoded pi values found (use math.pi instead):\n" +
                "\n".join(f"  - {v}" for v in violations)
            )


# =============================================================================
# UTILITY: Run standalone to check current state
# =============================================================================

if __name__ == "__main__":
    from app.main import app
    client = TestClient(app)
    response = client.get("/openapi.json")
    paths = list(response.json().get("paths", {}).keys())

    print("=== FRET ROUTES ===")
    for p in sorted(paths):
        if "fret" in p.lower():
            print(f"  {p}")

    print("\n=== ALL ROUTES ===")
    for p in sorted(paths):
        print(f"  {p}")
