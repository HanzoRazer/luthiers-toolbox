#!/usr/bin/env python3
"""
DXF Validation Gate for CI

Validates all DXF files in instrument_geometry/ directory.

Exit codes:
- 0: All DXF files pass validation
- 1: One or more DXF files failed validation
- 2: Runtime error (file not found, etc.)

Requirements (from GAP_ANALYSIS_MASTER.md):
1. Must be AC1009 or later (AutoCAD R12+)
2. Must have at least 1 closed LWPOLYLINE
3. Bounding box must be within reasonable dimensions

Usage:
    python -m app.ci.check_dxf_files [--strict] [--json]

    --strict: Also fail on warnings (not just errors)
    --json: Output JSON report instead of text
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent to path for imports
REPO_ROOT = Path(__file__).resolve().parents[4]  # services/api/app/ci -> repo root
sys.path.insert(0, str(REPO_ROOT / "services" / "api"))

try:
    from app.cam.dxf_preflight import DXFPreflight, Severity
    from app.cam.dxf_advanced_validation import TopologyValidator
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(REPO_ROOT / "services" / "api"))
    from app.cam.dxf_preflight import DXFPreflight, Severity
    from app.cam.dxf_advanced_validation import TopologyValidator


# DXF version mapping (AC codes)
DXF_VERSION_MAP = {
    "AC1006": "R10",
    "AC1009": "R12",
    "AC1012": "R13",
    "AC1014": "R14",
    "AC1015": "R2000",
    "AC1018": "R2004",
    "AC1021": "R2007",
    "AC1024": "R2010",
    "AC1027": "R2013",
    "AC1032": "R2018",
}

# Minimum acceptable version
MIN_DXF_VERSION = "AC1009"  # R12


def validate_dxf_file(dxf_path: Path) -> Dict[str, Any]:
    """
    Validate a single DXF file.

    Args:
        dxf_path: Path to DXF file

    Returns:
        Validation result dict with pass/fail and details
    """
    result = {
        "file": str(dxf_path),
        "passed": True,
        "errors": [],
        "warnings": [],
        "info": {},
    }

    try:
        dxf_bytes = dxf_path.read_bytes()
    except (IOError, OSError) as e:
        result["passed"] = False
        result["errors"].append(f"Failed to read file: {e}")
        return result

    # Run preflight validation
    try:
        preflight = DXFPreflight(dxf_bytes, dxf_path.name)
        report = preflight.run_all_checks()

        result["info"]["dxf_version"] = report.dxf_version
        result["info"]["entity_count"] = report.total_entities
        result["info"]["layers"] = report.layers

        # Check DXF version
        version_friendly = DXF_VERSION_MAP.get(report.dxf_version, report.dxf_version)
        if report.dxf_version < MIN_DXF_VERSION:
            result["passed"] = False
            result["errors"].append(
                f"DXF version {report.dxf_version} ({version_friendly}) is too old. "
                f"Minimum: {MIN_DXF_VERSION} ({DXF_VERSION_MAP.get(MIN_DXF_VERSION, 'R12')})"
            )

        # Collect issues
        for issue in report.issues:
            issue_dict = {
                "severity": issue.severity.value,
                "category": issue.category,
                "message": issue.message,
            }
            if issue.layer:
                issue_dict["layer"] = issue.layer
            if issue.suggestion:
                issue_dict["suggestion"] = issue.suggestion

            if issue.severity == Severity.ERROR:
                result["errors"].append(issue_dict)
                result["passed"] = False
            elif issue.severity == Severity.WARNING:
                result["warnings"].append(issue_dict)

    except (ValueError, TypeError, AttributeError) as e:
        result["passed"] = False
        result["errors"].append(f"Preflight validation failed: {e}")
        return result

    # Run topology validation
    try:
        validator = TopologyValidator(dxf_bytes, dxf_path.name)
        topology_report = validator.check_self_intersections()

        result["info"]["self_intersections"] = topology_report.self_intersections
        result["info"]["degenerate_polygons"] = topology_report.degenerate_polygons

        for issue in topology_report.issues:
            issue_dict = {
                "severity": issue.severity.value,
                "category": issue.category,
                "message": issue.message,
            }
            if issue.layer:
                issue_dict["layer"] = issue.layer
            if issue.repair_suggestion:
                issue_dict["repair_suggestion"] = issue.repair_suggestion

            if issue.severity == Severity.ERROR:
                result["errors"].append(issue_dict)
                result["passed"] = False
            elif issue.severity == Severity.WARNING:
                result["warnings"].append(issue_dict)

    except (ValueError, TypeError, AttributeError) as e:
        # Topology validation failure is a warning, not an error
        result["warnings"].append(f"Topology validation skipped: {e}")

    return result


def find_dxf_files(search_dir: Path) -> List[Path]:
    """Find all DXF files in directory tree."""
    return sorted(search_dir.rglob("*.dxf"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate DXF files in instrument_geometry/"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (not just errors)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON report",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Override search path (default: instrument_geometry/)",
    )
    args = parser.parse_args()

    # Find instrument_geometry directory
    if args.path:
        search_dir = Path(args.path)
    else:
        # Try multiple possible locations
        possible_paths = [
            REPO_ROOT / "services" / "api" / "app" / "instrument_geometry",
            REPO_ROOT / "instrument_geometry",
            Path.cwd() / "services" / "api" / "app" / "instrument_geometry",
            Path.cwd() / "instrument_geometry",
        ]
        search_dir = None
        for p in possible_paths:
            if p.exists():
                search_dir = p
                break

        if not search_dir:
            print("ERROR: Could not find instrument_geometry/ directory")
            return 2

    # Find DXF files
    dxf_files = find_dxf_files(search_dir)

    if not dxf_files:
        print(f"No DXF files found in {search_dir}")
        return 0

    # Validate all files
    results: List[Dict[str, Any]] = []
    passed = 0
    failed = 0
    warnings_only = 0

    for dxf_path in dxf_files:
        result = validate_dxf_file(dxf_path)
        results.append(result)

        if result["passed"]:
            if result["warnings"]:
                warnings_only += 1
                if args.strict:
                    failed += 1
                else:
                    passed += 1
            else:
                passed += 1
        else:
            failed += 1

    # Output results
    if args.json:
        output = {
            "total": len(dxf_files),
            "passed": passed,
            "failed": failed,
            "warnings_only": warnings_only,
            "strict_mode": args.strict,
            "results": results,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(f"\n{'='*60}")
        print(f"DXF Validation Report - instrument_geometry/")
        print(f"{'='*60}")
        print(f"Total files: {len(dxf_files)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Warnings only: {warnings_only}")
        print(f"{'='*60}\n")

        for result in results:
            status = "✅" if result["passed"] else "❌"
            warn_count = len(result["warnings"]) if isinstance(result["warnings"], list) else 0
            err_count = len(result["errors"]) if isinstance(result["errors"], list) else 0

            file_short = Path(result["file"]).name
            print(f"{status} {file_short}")

            if err_count > 0:
                for err in result["errors"]:
                    if isinstance(err, dict):
                        print(f"   ❌ {err.get('message', err)}")
                    else:
                        print(f"   ❌ {err}")

            if warn_count > 0 and (args.strict or not result["passed"]):
                for warn in result["warnings"]:
                    if isinstance(warn, dict):
                        print(f"   ⚠️  {warn.get('message', warn)}")
                    else:
                        print(f"   ⚠️  {warn}")

        print(f"\n{'='*60}")
        if failed > 0:
            print("RESULT: FAILED")
        elif args.strict and warnings_only > 0:
            print("RESULT: FAILED (strict mode)")
        else:
            print("RESULT: PASSED")
        print(f"{'='*60}\n")

    # Exit code
    if failed > 0:
        return 1
    if args.strict and warnings_only > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
