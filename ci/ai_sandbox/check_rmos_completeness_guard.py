#!/usr/bin/env python3
"""
RMOS Completeness Guard Enforcement

Verifies that RunArtifact creation goes through validate_and_persist(),
which enforces required invariants (feasibility_sha256, risk_level).

This prevents bypass of the completeness guard that could break the audit trail.

Usage:
    python ci/ai_sandbox/check_rmos_completeness_guard.py
"""

import ast
import pathlib
import sys
from typing import List, Set

ROOT = pathlib.Path(__file__).resolve().parents[2]
RMOS_DIR = ROOT / "services" / "api" / "app" / "rmos"
SERVICES_DIR = ROOT / "services" / "api" / "app" / "services"

# The canonical entry point for run creation
CANONICAL_ENTRY = "validate_and_persist"

# Direct creation functions that should NOT be called outside of store.py
GUARDED_FUNCTIONS: Set[str] = {
    "RunArtifact",  # Direct model instantiation
    "create_run_artifact",  # Internal function
    "_create_artifact",  # Internal function
}

# Files that ARE allowed to use guarded functions (the implementation itself)
IMPLEMENTATION_FILES: Set[str] = {
    "store.py",  # The store implements the guard
    "schemas.py",  # Schema definitions
    "compat.py",  # Compatibility layer
    "migration_utils.py",  # Migration tools
}

# Files that bridge domains and need direct access
BRIDGE_ALLOWLIST: Set[str] = {
    "saw_lab_service.py",  # Uses validate_and_persist correctly
    "rmos_run_service.py",  # Uses validate_and_persist correctly
}

# Pre-existing violations (grandfathered, tracked for cleanup)
# TODO: Migrate these to use validate_and_persist()
LEGACY_EXCEPTIONS: Set[str] = {
    "rosette_rmos_adapter.py",  # TODO: Refactor to use validate_and_persist
    "rmos_toolpaths_router.py",  # TODO: Refactor to use validate_and_persist
}


def check_file(path: pathlib.Path) -> List[str]:
    """Check a single file for completeness guard bypass."""
    violations = []

    # Skip implementation, bridge, and legacy exception files
    if path.name in IMPLEMENTATION_FILES or path.name in BRIDGE_ALLOWLIST:
        return violations
    if path.name in LEGACY_EXCEPTIONS:
        return violations  # Grandfathered, tracked via TODO

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        return violations

    rel_path = path.relative_to(ROOT)

    # Track if file imports from runs_v2
    imports_runs_v2 = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if "runs_v2" in module or "runs" in module:
                imports_runs_v2 = True
                break

    if not imports_runs_v2:
        return violations

    # Check for direct use of guarded functions
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = None

            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name in GUARDED_FUNCTIONS:
                violations.append(
                    f"{rel_path}:{node.lineno}: "
                    f"direct use of {func_name}() bypasses completeness guard. "
                    f"Use {CANONICAL_ENTRY}() instead."
                )

    return violations


def check_validate_and_persist_exists() -> List[str]:
    """Verify the completeness guard function exists and has required checks."""
    violations = []

    store_path = RMOS_DIR / "runs_v2" / "store.py"
    if not store_path.exists():
        violations.append(f"CRITICAL: {store_path.relative_to(ROOT)} not found")
        return violations

    source = store_path.read_text(encoding="utf-8")

    # Check for required function
    if "def validate_and_persist" not in source:
        violations.append(
            f"{store_path.relative_to(ROOT)}: "
            f"missing {CANONICAL_ENTRY}() function"
        )

    # Check for required invariant checks
    required_checks = [
        ("feasibility_sha256", "feasibility hash check"),
        ("risk_level", "risk level check"),
        ("CompletenessViolation", "violation handling"),
    ]

    for pattern, description in required_checks:
        if pattern not in source:
            violations.append(
                f"{store_path.relative_to(ROOT)}: "
                f"missing {description} in completeness guard"
            )

    return violations


def main() -> int:
    """Run the completeness guard check."""
    errors = []
    checked = 0

    # First, verify the guard itself exists
    errors.extend(check_validate_and_persist_exists())

    # Check RMOS files for bypass attempts
    if RMOS_DIR.exists():
        for py_file in RMOS_DIR.rglob("*.py"):
            checked += 1
            errors.extend(check_file(py_file))

    # Check services files for bypass attempts
    if SERVICES_DIR.exists():
        for py_file in SERVICES_DIR.rglob("*.py"):
            checked += 1
            errors.extend(check_file(py_file))

    if errors:
        print("[FAIL] RMOS completeness guard violations detected:")
        print()
        for e in errors:
            print(f"  {e}")
        print()
        print(f"Checked {checked} files, found {len(errors)} violations.")
        print()
        print("All RunArtifact creation must go through validate_and_persist().")
        print("This ensures feasibility_sha256 and risk_level are always present.")
        print()
        print("See: docs/governance/RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md")
        return 1

    print(f"[PASS] RMOS completeness guard check passed. ({checked} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
