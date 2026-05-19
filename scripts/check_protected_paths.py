#!/usr/bin/env python3
"""
Governance Protected Path Check Script

Detects changes to protected paths in staged files and requires
explicit governance approval via environment variable.

Usage:
    python scripts/check_protected_paths.py

Environment:
    GOVERNANCE_APPROVED_CHANGE=1  - Approve changes to protected paths

Exit codes:
    0 - No violations (or approved)
    1 - Protected path modified without approval

Part of MRP-1A Governance Enforcement Infrastructure.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def load_manifest() -> dict:
    """Load the governance manifest."""
    manifest_path = Path(__file__).parent.parent / "docs" / "governance" / "governance_manifest.json"
    if not manifest_path.exists():
        print(f"[WARN] Governance manifest not found: {manifest_path}")
        return {"protected_systems": []}

    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_staged_files() -> list[str]:
    """Get list of staged files using git diff --cached."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        files = result.stdout.strip().split("\n")
        return [f for f in files if f]
    except subprocess.CalledProcessError:
        return []


def normalize_path(path: str) -> str:
    """Normalize path separators to forward slashes."""
    return path.replace("\\", "/")


def file_matches_protected_path(file_path: str, protected_paths: list[str]) -> bool:
    """Check if a file matches any protected path pattern."""
    file_path = normalize_path(file_path)

    for protected in protected_paths:
        protected = normalize_path(protected)

        # Directory match (ends with /)
        if protected.endswith("/"):
            if file_path.startswith(protected) or file_path.startswith(protected.rstrip("/")):
                return True
        # Exact file match
        elif file_path == protected:
            return True
        # File under protected directory
        elif file_path.startswith(protected + "/"):
            return True

    return False


def check_protected_paths() -> int:
    """
    Main check function.

    Returns:
        0 if no violations or approved
        1 if violations found without approval
    """
    # Check for approval
    approved = os.environ.get("GOVERNANCE_APPROVED_CHANGE") == "1"

    # Load manifest
    manifest = load_manifest()
    protected_systems = manifest.get("protected_systems", [])

    if not protected_systems:
        return 0

    # Get staged files
    staged_files = get_staged_files()
    if not staged_files:
        return 0

    # Check each staged file against protected paths
    violations = []

    for staged_file in staged_files:
        for system in protected_systems:
            system_id = system.get("id", "UNKNOWN")
            paths = system.get("paths", [])
            governance_doc = system.get("governance_doc", "")

            if file_matches_protected_path(staged_file, paths):
                violations.append({
                    "file": staged_file,
                    "system": system_id,
                    "governance_doc": governance_doc,
                    "protection_level": system.get("protection_level", "UNKNOWN")
                })

    if not violations:
        return 0

    # If approved, allow with notice
    if approved:
        print("[INFO] Governance approval detected (GOVERNANCE_APPROVED_CHANGE=1)")
        print(f"[INFO] Allowing changes to {len(violations)} protected file(s):")
        for v in violations:
            print(f"  - {v['file']} ({v['system']})")
        return 0

    # Report violations
    print("[FAIL] Protected system modified without approval:")
    print()

    for v in violations:
        print(f"  System: {v['system']}")
        print(f"  File: {v['file']}")
        print(f"  Protection level: {v['protection_level']}")
        print(f"  Governance doc: {v['governance_doc']}")
        print()

    print("To approve these changes, set:")
    print("  GOVERNANCE_APPROVED_CHANGE=1")
    print()
    print("Or review the governance documentation before proceeding.")

    return 1


if __name__ == "__main__":
    sys.exit(check_protected_paths())
