#!/usr/bin/env python3
"""
Legacy Endpoint Usage Gate

Scans codebase for references to legacy endpoints and enforces a usage budget.
Used to track and reduce legacy endpoint usage over time.

Environment variables:
    ENDPOINT_TRUTH_FILE: Path to routing truth JSON file
    LEGACY_USAGE_BUDGET: Maximum allowed legacy endpoint references (default: 100)
    LEGACY_SCAN_PATHS: Colon-separated paths to scan (default: app:tests)

Usage:
    python check_legacy_endpoint_usage.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


def load_truth_file(path: Path) -> Dict[str, Any]:
    """Load routing truth JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_legacy_endpoints(truth: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract legacy endpoints from truth file."""
    routes = truth.get("routes", [])
    return [r for r in routes if r.get("status") == "legacy"]


def scan_file_for_endpoints(
    file_path: Path,
    endpoints: List[str],
) -> List[Tuple[str, int, str]]:
    """Scan a file for references to legacy endpoints."""
    matches = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            for endpoint in endpoints:
                # Look for endpoint in strings or comments
                if endpoint in line:
                    matches.append((str(file_path), i, endpoint))
    except Exception:
        pass
    return matches


def scan_directories(
    scan_paths: List[Path],
    endpoints: List[str],
) -> List[Tuple[str, int, str]]:
    """Scan all Python files in given paths for legacy endpoint usage."""
    all_matches = []
    for scan_path in scan_paths:
        if not scan_path.exists():
            continue
        for py_file in scan_path.rglob("*.py"):
            matches = scan_file_for_endpoints(py_file, endpoints)
            all_matches.extend(matches)
    return all_matches


def main() -> int:
    """Run the legacy endpoint usage gate."""
    print("=" * 60)
    print("Legacy Endpoint Usage Gate")
    print("=" * 60)

    # Load configuration from environment
    truth_file = Path(os.environ.get("ENDPOINT_TRUTH_FILE", "routing_truth.json"))
    budget = int(os.environ.get("LEGACY_USAGE_BUDGET", "100"))
    scan_paths_str = os.environ.get("LEGACY_SCAN_PATHS", "app:tests")
    scan_paths = [Path(p) for p in scan_paths_str.split(":") if p]

    print(f"Truth file: {truth_file}")
    print(f"Budget: {budget}")
    print(f"Scan paths: {scan_paths}")
    print()

    # Load truth and get legacy endpoints
    if not truth_file.exists():
        print(f"ERROR: Truth file not found: {truth_file}")
        return 1

    truth = load_truth_file(truth_file)
    legacy_routes = get_legacy_endpoints(truth)
    legacy_paths = [r["path"] for r in legacy_routes]

    print(f"Found {len(legacy_routes)} legacy endpoint(s) in truth file")
    for route in legacy_routes:
        successor = route.get("successor", "none")
        print(f"  - {route['path']} -> {successor}")
    print()

    # Scan for usage
    matches = scan_directories(scan_paths, legacy_paths)
    usage_count = len(matches)

    print(f"Legacy endpoint references found: {usage_count}")
    if matches:
        # Group by file
        by_file: Dict[str, List[Tuple[int, str]]] = {}
        for file_path, line_no, endpoint in matches:
            by_file.setdefault(file_path, []).append((line_no, endpoint))

        for file_path, refs in sorted(by_file.items()):
            print(f"  {file_path}:")
            for line_no, endpoint in refs:
                print(f"    L{line_no}: {endpoint}")
    print()

    # Check against budget
    if usage_count > budget:
        print(f"FAIL: Legacy usage ({usage_count}) exceeds budget ({budget})")
        return 1

    remaining = budget - usage_count
    print(f"OK: Legacy usage ({usage_count}) within budget ({budget})")
    print(f"    Remaining budget: {remaining}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
