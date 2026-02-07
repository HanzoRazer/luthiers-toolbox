"""
Legacy Usage Gate (CI)

Scans frontend code for API endpoint usage and reports/fails if legacy endpoints
are still being called.

Exit codes:
  0 = No legacy endpoints used (or all within budget)
  1 = Legacy endpoints used, under budget (warning)
  2 = Legacy endpoints used, over budget (fail)

Usage:
  python -m app.ci.legacy_usage_gate [--fail-on-any] [--budget N]

Options:
  --fail-on-any    Fail immediately if any legacy endpoint is used
  --budget N       Allow up to N legacy endpoint usages before failing (default: 0)
  --json           Output JSON report instead of text
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


# =============================================================================
# Legacy Route Definitions
# =============================================================================

# Mapping of legacy path patterns to their canonical replacements
# Format: (legacy_pattern, canonical_replacement, notes)
LEGACY_ROUTES: List[Tuple[str, str, str]] = [
    # CAM Legacy Routes
    (r"^/api/cam/vcarve", "/api/cam/toolpath/vcarve", "Wave 18 consolidated"),
    (r"^/api/cam/helical", "/api/cam/toolpath/helical", "Wave 18 consolidated"),
    (r"^/api/cam/svg", "/api/cam/export", "Wave 18 consolidated"),
    (r"^/api/cam/biarc", "/api/cam/toolpath/biarc", "Wave 18 consolidated"),
    (r"^/api/cam/roughing(?!/gcode_intent)", "/api/cam/toolpath/roughing", "Wave 18 consolidated (use roughing_gcode_intent for H7.2)"),
    (r"^/api/cam/drill(?!/pattern)", "/api/cam/drilling", "Wave 18 consolidated"),

    # Note: These are proxies (same code), but we want to track usage for consolidation
    # (r"^/api/cam/fret_slots", "/api/cam/fret_slots", "Proxy - same code"),
    # (r"^/api/cam/relief", "/api/cam/relief", "Proxy - same code"),
    # (r"^/api/cam/drilling", "/api/cam/drilling", "Proxy - same code"),
    # (r"^/api/cam/risk", "/api/cam/risk", "Proxy - same code"),

    # Rosette Legacy Routes
    (r"^/api/rosette(?!/manufacturing)", "/api/cam/rosette or /api/art/rosette", "Multi-lane consolidation"),
    (r"^/api/rosette-patterns", "/api/art/rosette/pattern", "Art Studio v2"),

    # Compare Legacy Routes
    # Note: /api/compare/* paths now correctly routed through consolidated router
    # No compare legacy paths to flag - all point to same implementation

    # Art Studio Legacy Workflow
    (r"^/api/art-studio/workflow", "/api/rmos/workflow", "Use RMOS workflow"),
    (r"^/api/art-studio/rosette", "/api/art/rosette", "Art Studio v2"),
]


@dataclass
class LegacyUsage:
    """Record of a legacy endpoint usage in frontend code."""
    frontend_path: str
    line_number: int
    api_path: str
    canonical: str
    notes: str


@dataclass
class LegacyUsageReport:
    """Summary report of legacy endpoint usage."""
    total_api_paths: int = 0
    legacy_usages: List[LegacyUsage] = field(default_factory=list)
    unique_legacy_paths: Set[str] = field(default_factory=set)
    files_with_legacy: Set[str] = field(default_factory=set)

    @property
    def legacy_count(self) -> int:
        return len(self.legacy_usages)

    @property
    def unique_legacy_count(self) -> int:
        return len(self.unique_legacy_paths)

    def to_dict(self) -> Dict:
        return {
            "total_api_paths": self.total_api_paths,
            "legacy_count": self.legacy_count,
            "unique_legacy_count": self.unique_legacy_count,
            "files_with_legacy": sorted(self.files_with_legacy),
            "unique_legacy_paths": sorted(self.unique_legacy_paths),
            "usages": [
                {
                    "file": u.frontend_path,
                    "line": u.line_number,
                    "api_path": u.api_path,
                    "canonical": u.canonical,
                    "notes": u.notes,
                }
                for u in self.legacy_usages
            ],
        }


# =============================================================================
# Scanning Logic
# =============================================================================

API_RE = re.compile(r"""["'`](\/api\/[A-Za-z0-9_\-\/{}:.?=&]+)["'`]""")

DEFAULT_FRONTEND_ROOTS = [
    "packages/client/src",
    "packages/sdk/src",
]


def _is_legacy_path(path: str) -> Optional[Tuple[str, str]]:
    """
    Check if a path matches a legacy pattern.
    Returns (canonical_replacement, notes) if legacy, None otherwise.
    """
    for pattern, canonical, notes in LEGACY_ROUTES:
        if re.match(pattern, path):
            return (canonical, notes)
    return None


def scan_for_legacy_usage(roots: List[str] | None = None) -> LegacyUsageReport:
    """
    Scan frontend code for legacy API endpoint usage.
    """
    roots = roots or DEFAULT_FRONTEND_ROOTS
    report = LegacyUsageReport()
    all_paths: Set[str] = set()

    for root in roots:
        if not os.path.isdir(root):
            continue

        for base, _, files in os.walk(root):
            for fn in files:
                if not fn.endswith((".ts", ".tsx", ".js", ".jsx", ".vue")):
                    continue

                fp = os.path.join(base, fn)
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except OSError:  # WP-1: narrowed from except Exception
                    continue

                for line_num, line in enumerate(lines, 1):
                    for m in API_RE.finditer(line):
                        api_path = m.group(1)
                        all_paths.add(api_path)

                        legacy_info = _is_legacy_path(api_path)
                        if legacy_info:
                            canonical, notes = legacy_info
                            usage = LegacyUsage(
                                frontend_path=fp,
                                line_number=line_num,
                                api_path=api_path,
                                canonical=canonical,
                                notes=notes,
                            )
                            report.legacy_usages.append(usage)
                            report.unique_legacy_paths.add(api_path)
                            report.files_with_legacy.add(fp)

    report.total_api_paths = len(all_paths)
    return report


# =============================================================================
# CLI Entry Point
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check frontend for legacy API endpoint usage"
    )
    parser.add_argument(
        "--fail-on-any",
        action="store_true",
        help="Fail immediately if any legacy endpoint is used",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=0,
        help="Allow up to N legacy endpoint usages before failing (default: 0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON report instead of text",
    )
    parser.add_argument(
        "--roots",
        nargs="+",
        default=None,
        help="Frontend root directories to scan",
    )
    args = parser.parse_args()

    report = scan_for_legacy_usage(args.roots)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print("=" * 60)
        print("Legacy Endpoint Usage Report")
        print("=" * 60)
        print(f"Total API paths scanned: {report.total_api_paths}")
        print(f"Legacy usages found: {report.legacy_count}")
        print(f"Unique legacy paths: {report.unique_legacy_count}")
        print(f"Files with legacy usage: {len(report.files_with_legacy)}")
        print()

        if report.legacy_usages:
            print("Legacy Usages:")
            print("-" * 60)
            for usage in report.legacy_usages:
                print(f"  {usage.frontend_path}:{usage.line_number}")
                print(f"    Path: {usage.api_path}")
                print(f"    Use:  {usage.canonical}")
                print(f"    Note: {usage.notes}")
                print()
        else:
            print("No legacy endpoint usages found.")

    # Determine exit code
    if report.legacy_count == 0:
        if not args.json:
            print("[legacy_usage_gate] OK - No legacy endpoints used")
        return 0

    if args.fail_on_any or report.legacy_count > args.budget:
        if not args.json:
            print(f"[legacy_usage_gate] FAIL - {report.legacy_count} legacy usages (budget: {args.budget})")
        return 2

    if not args.json:
        print(f"[legacy_usage_gate] WARN - {report.legacy_count} legacy usages (within budget: {args.budget})")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
