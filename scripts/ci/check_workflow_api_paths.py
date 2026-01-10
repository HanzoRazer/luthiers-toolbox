#!/usr/bin/env python3
"""
Bundle 14: CI gate to prevent legacy API paths in workflow files.

Scans .github/workflows/**/*.yml for legacy route prefixes and fails CI
if any are found (unless explicitly ignored).

Usage:
    python scripts/ci/check_workflow_api_paths.py
    python scripts/ci/check_workflow_api_paths.py --root .github/workflows
    python scripts/ci/check_workflow_api_paths.py --ignore .github/workflows/.legacy_paths_ignore.txt
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

DEFAULT_SCAN_ROOT = ".github/workflows"

# Legacy roots we never want reintroduced
LEGACY_PREFIXES = [
    "/cam/",
    "/geometry/",
    "/tooling/",
    "/adaptive/",
    "/machine/",
    "/material/",
    "/feeds/",
    "/sim/",
]

# Allowed canonical root
CANONICAL_PREFIX = "/api/"


def _iter_workflow_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return root.rglob("*.yml")


def _load_ignore(ignore_path: Path) -> List[str]:
    if not ignore_path or not ignore_path.exists():
        return []
    lines = []
    for raw in ignore_path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        lines.append(s)
    return lines


def _is_ignored(file_rel: str, lineno: int, ignores: List[str]) -> bool:
    """
    Ignore format options:
      - exact file:line  (e.g., ".github/workflows/foo.yml:123")
      - exact file       (e.g., ".github/workflows/foo.yml")
    """
    key = f"{file_rel}:{lineno}"
    if key in ignores:
        return True
    if file_rel in ignores:
        return True
    return False


def _has_legacy_path(line: str) -> bool:
    """
    Check if a line contains a legacy API path.

    Legacy paths are routes like /cam/... that are NOT prefixed with /api.
    Canonical paths like /api/cam/... are allowed.
    File paths like services/api/app/cam/... are also allowed.
    """
    for pref in LEGACY_PREFIXES:
        idx = line.find(pref)
        while idx != -1:
            # Check if /api comes right before this prefix (URL path)
            # e.g., for "/api/cam/", idx would be 4, and "/api" would be at 0
            is_canonical = False
            if idx >= 4:
                before = line[idx - 4:idx]
                if before == "/api":
                    is_canonical = True
            
            # Also allow file paths like "services/api/app/cam/..."
            # These have /api/ somewhere before, but not directly adjacent
            if not is_canonical and "/api/" in line[:idx]:
                # It's a file path containing /api/ earlier
                is_canonical = True
            
            if not is_canonical:
                # This is a true legacy path
                return True
            
            # Check for next occurrence
            idx = line.find(pref, idx + 1)
    
    return False


def _scan_file(path: Path, ignores: List[str]) -> List[Tuple[str, int, str]]:
    rel = str(path.as_posix())
    findings: List[Tuple[str, int, str]] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for i, line in enumerate(text.splitlines(), start=1):
        # quick skip: if no "/" present
        if "/" not in line:
            continue

        if _is_ignored(rel, i, ignores):
            continue

        # Flag legacy prefixes if they appear as URL path segments
        # BUT allow canonical paths like /api/cam/...
        if _has_legacy_path(line):
            findings.append((rel, i, line.strip()))

    return findings


def main() -> int:
    # Ensure UTF-8 output on Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(
        description="CI gate: prevent legacy API paths in workflow files"
    )
    ap.add_argument(
        "--root",
        default=DEFAULT_SCAN_ROOT,
        help="Workflow directory to scan",
    )
    ap.add_argument(
        "--ignore",
        default=".github/workflows/.legacy_paths_ignore.txt",
        help="Ignore list file",
    )
    args = ap.parse_args()

    root = Path(args.root)
    ignore_path = Path(args.ignore)
    ignores = _load_ignore(ignore_path)

    all_findings: List[Tuple[str, int, str]] = []
    for f in _iter_workflow_files(root):
        all_findings.extend(_scan_file(f, ignores))

    if not all_findings:
        print("✅ Workflow API path gate: no legacy route prefixes found.")
        return 0

    print("❌ Workflow API path gate failed: legacy route prefixes detected.")
    print("   Canonical routes must use /api/…")
    print("")
    for rel, lineno, line in all_findings:
        print(f"- {rel}:{lineno}: {line}")
    print("")
    print("Fix: replace legacy paths with /api/... in workflows.")
    print("If a file is intentionally legacy during migration, add it to:")
    print(f"  {ignore_path.as_posix()}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
