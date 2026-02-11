"""
Technical Debt Gates - Automated enforcement of decomposition targets.

These tests fail CI if code quality regresses. Ratchet pattern:
- Targets only tighten over time
- History tracked in metrics/debt_history.json
"""

import ast
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest

# =============================================================================
# Configuration
# =============================================================================

APP_ROOT = Path(__file__).parent.parent / "app"
METRICS_DIR = Path(__file__).parent.parent / "metrics"

# Targets (ratchet down over time)
TARGET_MAX_ENDPOINTS = 564  # Current: 564, goal: 400 (was 577)
TARGET_MAX_GOD_OBJECTS = 10  # All reviewed and acceptable
TARGET_MAX_BARE_EXCEPT = 1  # Current: 1, goal: 0
TARGET_MAX_LARGE_FILES = 9  # Current: 9, goal: 5
TARGET_MAX_DUPLICATE_ROUTES = 53  # Current: 53, goal: 0 (was 54)
GOD_OBJECT_THRESHOLD = 15  # Methods per class

# Acceptable god objects (reviewed and documented)
ACCEPTABLE_GOD_OBJECTS = {
    "Registry",  # Unified Data Facade pattern
    "LTBFinancialCalculator",  # HP 12C calculator model
    "LTBFractionCalculator",  # Calculator model
    "LTBScientificCalculator",  # Calculator model
    "LTBLuthierCalculator",  # Calculator model
    "LTBBasicCalculator",  # Calculator model
    "RunStoreV2",  # Refactored, delegation wrappers remain
    "LearnedOverridesStore",  # Cohesive ML domain store
    "SQLiteJobLogStore",  # Repository pattern
    "RegistryProductsMixin",  # Mixin for Registry
}


# =============================================================================
# Helpers
# =============================================================================

def count_endpoints() -> int:
    """Count all @router.{method}() decorators."""
    count = 0
    pattern = re.compile(r'@router\.(get|post|put|patch|delete)\(')

    for pyfile in APP_ROOT.rglob("*.py"):
        try:
            content = pyfile.read_text(encoding="utf-8")
            count += len(pattern.findall(content))
        except (OSError, UnicodeDecodeError):
            continue

    return count


def count_bare_except() -> int:
    """Count bare except: clauses."""
    count = 0
    pattern = re.compile(r'except\s*:')

    for pyfile in APP_ROOT.rglob("*.py"):
        try:
            content = pyfile.read_text(encoding="utf-8")
            count += len(pattern.findall(content))
        except (OSError, UnicodeDecodeError):
            continue

    return count


def count_large_files(threshold: int = 500) -> List[Tuple[Path, int]]:
    """Find files exceeding line threshold."""
    large = []

    for pyfile in APP_ROOT.rglob("*.py"):
        try:
            lines = len(pyfile.read_text(encoding="utf-8").splitlines())
            if lines > threshold:
                large.append((pyfile, lines))
        except (OSError, UnicodeDecodeError):
            continue

    return sorted(large, key=lambda x: -x[1])


def find_god_objects() -> List[Tuple[str, str, int]]:
    """Find classes with more than GOD_OBJECT_THRESHOLD methods."""
    results = []

    for pyfile in APP_ROOT.rglob("*.py"):
        if "test" in str(pyfile).lower():
            continue

        try:
            tree = ast.parse(pyfile.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [
                        n for n in node.body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]
                    if len(methods) > GOD_OBJECT_THRESHOLD:
                        results.append((node.name, str(pyfile), len(methods)))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue

    return sorted(results, key=lambda x: -x[2])


def find_duplicate_routes() -> List[Dict]:
    """Find duplicate route paths across routers."""
    route_paths: Dict[str, List[str]] = {}

    # Pattern to extract route definitions
    route_pattern = re.compile(
        r'@router\.(get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']'
    )

    for pyfile in APP_ROOT.rglob("*.py"):
        try:
            content = pyfile.read_text(encoding="utf-8")
            for match in route_pattern.finditer(content):
                method, path = match.groups()
                key = f"{method.upper()} {path}"
                if key not in route_paths:
                    route_paths[key] = []
                route_paths[key].append(str(pyfile.relative_to(APP_ROOT)))
        except (OSError, UnicodeDecodeError):
            continue

    # Find duplicates
    duplicates = []
    for route, files in route_paths.items():
        if len(files) > 1:
            duplicates.append({"route": route, "files": files})

    return duplicates


def save_metrics_snapshot():
    """Save current metrics to history file."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    history_path = METRICS_DIR / "debt_history.json"

    # Load existing history
    if history_path.exists():
        history = json.loads(history_path.read_text())
    else:
        history = []

    # Add current snapshot
    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": count_endpoints(),
        "bare_except": count_bare_except(),
        "large_files": len(count_large_files()),
        "god_objects": len(find_god_objects()),
    }
    history.append(snapshot)

    # Keep last 100 entries
    history = history[-100:]

    history_path.write_text(json.dumps(history, indent=2))
    return snapshot


# =============================================================================
# Tests
# =============================================================================

class TestEndpointConsolidation:
    """Ensure route count stays within limits."""

    def test_total_endpoints_under_target(self):
        """Total endpoints must not exceed target."""
        count = count_endpoints()
        assert count <= TARGET_MAX_ENDPOINTS, (
            f"Endpoint count {count} exceeds target {TARGET_MAX_ENDPOINTS}. "
            f"Consolidate routes before adding new ones."
        )

    def test_duplicate_routes_under_baseline(self):
        """Duplicate routes must not exceed baseline (legacy routers)."""
        duplicates = find_duplicate_routes()
        assert len(duplicates) <= TARGET_MAX_DUPLICATE_ROUTES, (
            f"Duplicate route count {len(duplicates)} exceeds baseline {TARGET_MAX_DUPLICATE_ROUTES}.\n"
            f"New duplicates found - consolidate before adding routes:\n" +
            "\n".join(f"  {d['route']}: {d['files']}" for d in duplicates[:10])
        )


class TestCodeQuality:
    """Ensure code quality metrics stay within limits."""

    def test_bare_except_count(self):
        """Bare except clauses must not exceed target."""
        count = count_bare_except()
        assert count <= TARGET_MAX_BARE_EXCEPT, (
            f"Bare except count {count} exceeds target {TARGET_MAX_BARE_EXCEPT}. "
            f"Use specific exception types."
        )

    def test_large_files_count(self):
        """Large files (>500 LOC) must not exceed target."""
        large = count_large_files()
        assert len(large) <= TARGET_MAX_LARGE_FILES, (
            f"Large file count {len(large)} exceeds target {TARGET_MAX_LARGE_FILES}.\n"
            f"Files to split:\n" +
            "\n".join(f"  {f.relative_to(APP_ROOT)}: {lines} lines" for f, lines in large[:5])
        )


class TestGodObjects:
    """Ensure god objects are reviewed and acceptable."""

    def test_god_object_count(self):
        """God objects must not exceed reviewed count."""
        god_objects = find_god_objects()
        assert len(god_objects) <= TARGET_MAX_GOD_OBJECTS, (
            f"God object count {len(god_objects)} exceeds target {TARGET_MAX_GOD_OBJECTS}.\n"
            f"New god objects need review:\n" +
            "\n".join(f"  {name}: {count} methods in {path}" for name, path, count in god_objects)
        )

    def test_no_unreviewed_god_objects(self):
        """All god objects must be in the acceptable list."""
        god_objects = find_god_objects()
        unreviewed = [
            (name, path, count)
            for name, path, count in god_objects
            if name not in ACCEPTABLE_GOD_OBJECTS
        ]
        assert len(unreviewed) == 0, (
            f"Unreviewed god objects found:\n" +
            "\n".join(f"  {name}: {count} methods in {path}" for name, path, count in unreviewed) +
            "\n\nAdd to ACCEPTABLE_GOD_OBJECTS after review, or refactor."
        )


class TestRatchetProgress:
    """Ensure metrics don't regress (ratchet pattern)."""

    @pytest.mark.skipif(
        not (METRICS_DIR / "debt_history.json").exists(),
        reason="No history file yet"
    )
    def test_endpoints_not_increasing(self):
        """Endpoint count should not increase."""
        history = json.loads((METRICS_DIR / "debt_history.json").read_text())
        if len(history) < 2:
            pytest.skip("Need at least 2 history entries")

        current = count_endpoints()
        previous = history[-1]["endpoints"]

        # Allow small variance (±5) for measurement differences
        assert current <= previous + 5, (
            f"Endpoint count increased from {previous} to {current}. "
            f"Consolidate before adding new routes."
        )


# =============================================================================
# Fixture to save metrics after test run
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def save_metrics_after_tests(request):
    """Save metrics snapshot after all tests complete."""
    yield
    # Only save if all debt tests passed
    if request.session.testsfailed == 0:
        try:
            save_metrics_snapshot()
        except Exception:
            pass  # Don't fail tests if metrics save fails
