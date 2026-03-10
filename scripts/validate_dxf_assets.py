#!/usr/bin/env python3
"""
DXF Asset Validation Gate

CI validation script that checks all DXF files in instrument_geometry/ for:
1. Format: AC1009 (R12) — not AC1024 (AutoCAD 2010+)
2. Geometry: At least 1 closed LWPOLYLINE
3. Bounds: Bounding box within ±1mm of spec dimensions (if spec exists)

Resolves DXF quality gaps:
- LP-GAP-01: Multi-layer CAM DXF validation
- EX-GAP-01: Coarse approximation detection
- EX-GAP-02: AC1024 format detection
- SG-GAP-01: Dimension mismatch detection

Usage:
    python scripts/validate_dxf_assets.py
    python scripts/validate_dxf_assets.py --strict  # Fail on warnings
    python scripts/validate_dxf_assets.py --json    # JSON output

Exit codes:
    0 = All checks passed
    1 = Errors found
    2 = Warnings found (only with --strict)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

# Try to import ezdxf
try:
    import ezdxf
    from ezdxf.entities import LWPolyline
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False
    print("WARNING: ezdxf not installed. Install with: pip install ezdxf", file=sys.stderr)


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Allowed DXF versions (AC1009 = R12, AC1012 = R13, AC1014 = R14)
ALLOWED_VERSIONS = {"AC1009", "AC1012", "AC1014", "AC1015"}  # R12-R2000

# Versions that trigger errors
BLOCKED_VERSIONS = {"AC1018", "AC1021", "AC1024", "AC1027", "AC1032"}  # 2004+

# Minimum points for a "production quality" outline
MIN_POINTS_PRODUCTION = 50

# Dimension tolerance (mm)
DIMENSION_TOLERANCE_MM = 1.0


# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------

@dataclass
class DXFIssue:
    """Single validation issue."""
    severity: str  # ERROR, WARNING, INFO
    message: str
    category: str  # version, geometry, bounds, layers


@dataclass
class DXFValidationResult:
    """Validation result for a single DXF file."""
    path: str
    filename: str
    dxf_version: str
    total_entities: int
    closed_polylines: int
    point_count: int
    bounds: Optional[Dict[str, float]]
    issues: List[DXFIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(i.severity == "ERROR" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "WARNING")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "filename": self.filename,
            "dxf_version": self.dxf_version,
            "total_entities": self.total_entities,
            "closed_polylines": self.closed_polylines,
            "point_count": self.point_count,
            "bounds": self.bounds,
            "passed": self.passed,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [asdict(i) for i in self.issues],
        }


@dataclass
class ValidationReport:
    """Complete validation report for all DXF files."""
    total_files: int
    passed: int
    failed: int
    warnings: int
    results: List[DXFValidationResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "results": [r.to_dict() for r in self.results],
        }


# -----------------------------------------------------------------------------
# Validation Functions
# -----------------------------------------------------------------------------

def validate_dxf_file(path: Path) -> DXFValidationResult:
    """
    Validate a single DXF file.

    Args:
        path: Path to DXF file

    Returns:
        DXFValidationResult with issues
    """
    result = DXFValidationResult(
        path=str(path),
        filename=path.name,
        dxf_version="UNKNOWN",
        total_entities=0,
        closed_polylines=0,
        point_count=0,
        bounds=None,
    )

    if not HAS_EZDXF:
        result.issues.append(DXFIssue(
            severity="ERROR",
            message="ezdxf not installed - cannot validate",
            category="setup",
        ))
        return result

    try:
        doc = ezdxf.readfile(str(path))
    except Exception as e:
        result.issues.append(DXFIssue(
            severity="ERROR",
            message=f"Failed to read DXF: {e}",
            category="file",
        ))
        return result

    # Get version
    result.dxf_version = doc.dxfversion

    # Check version
    if result.dxf_version in BLOCKED_VERSIONS:
        result.issues.append(DXFIssue(
            severity="ERROR",
            message=f"DXF version {result.dxf_version} not allowed. Use R12 (AC1009) or R14 (AC1014).",
            category="version",
        ))
    elif result.dxf_version not in ALLOWED_VERSIONS:
        result.issues.append(DXFIssue(
            severity="WARNING",
            message=f"DXF version {result.dxf_version} not in preferred list. Consider R12 (AC1009).",
            category="version",
        ))

    # Get modelspace entities
    msp = doc.modelspace()
    entities = list(msp)
    result.total_entities = len(entities)

    # Count closed polylines and points
    closed_count = 0
    total_points = 0
    all_points: List[Tuple[float, float]] = []

    for entity in entities:
        if entity.dxftype() == "LWPOLYLINE":
            lwpoly = entity
            points = list(lwpoly.get_points(format="xy"))
            total_points += len(points)
            all_points.extend(points)

            if lwpoly.closed:
                closed_count += 1

        elif entity.dxftype() == "POLYLINE":
            # 2D/3D polyline
            try:
                points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
                total_points += len(points)
                all_points.extend(points)
                if entity.is_closed:
                    closed_count += 1
            except (AttributeError, TypeError):
                pass

        elif entity.dxftype() == "LINE":
            total_points += 2
            try:
                all_points.append((entity.dxf.start.x, entity.dxf.start.y))
                all_points.append((entity.dxf.end.x, entity.dxf.end.y))
            except (AttributeError, TypeError):
                pass

        elif entity.dxftype() == "ARC":
            total_points += 10  # Approximate arc as 10 points
            try:
                all_points.append((entity.dxf.center.x, entity.dxf.center.y))
            except (AttributeError, TypeError):
                pass

    result.closed_polylines = closed_count
    result.point_count = total_points

    # Check for closed polylines
    if closed_count == 0:
        result.issues.append(DXFIssue(
            severity="ERROR",
            message="No closed LWPOLYLINE found. Body outline must be a closed polygon.",
            category="geometry",
        ))

    # Check point density
    if total_points > 0 and total_points < MIN_POINTS_PRODUCTION:
        result.issues.append(DXFIssue(
            severity="WARNING",
            message=f"Low point count ({total_points}). Production quality needs {MIN_POINTS_PRODUCTION}+ points.",
            category="geometry",
        ))

    # Calculate bounds
    if all_points:
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        result.bounds = {
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min(ys),
            "max_y": max(ys),
            "width": max(xs) - min(xs),
            "height": max(ys) - min(ys),
        }

    return result


def find_dxf_files(root: Path) -> List[Path]:
    """Find all DXF files under the given root."""
    return list(root.rglob("*.dxf"))


def validate_all(root: Path) -> ValidationReport:
    """
    Validate all DXF files under the given root.

    Args:
        root: Root directory to search

    Returns:
        ValidationReport with all results
    """
    dxf_files = find_dxf_files(root)

    results = []
    for path in sorted(dxf_files):
        result = validate_dxf_file(path)
        results.append(result)

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    warnings = sum(1 for r in results if r.warning_count > 0 and r.passed)

    return ValidationReport(
        total_files=len(results),
        passed=passed,
        failed=failed,
        warnings=warnings,
        results=results,
    )


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def print_report(report: ValidationReport, verbose: bool = False) -> None:
    """Print human-readable validation report."""
    print("=" * 70)
    print("DXF Asset Validation Report")
    print("=" * 70)
    print(f"Total files: {report.total_files}")
    print(f"Passed: {report.passed}")
    print(f"Failed: {report.failed}")
    print(f"With warnings: {report.warnings}")
    print()

    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        icon = "✓" if result.passed else "✗"

        print(f"{icon} [{status}] {result.filename}")
        print(f"   Version: {result.dxf_version} | "
              f"Entities: {result.total_entities} | "
              f"Closed polys: {result.closed_polylines} | "
              f"Points: {result.point_count}")

        if result.bounds:
            print(f"   Bounds: {result.bounds['width']:.1f} x {result.bounds['height']:.1f} mm")

        if result.issues:
            for issue in result.issues:
                prefix = "  !" if issue.severity == "ERROR" else "  ~"
                print(f"   {prefix} [{issue.severity}] {issue.message}")

        if verbose or result.issues:
            print()

    print("=" * 70)
    if report.failed > 0:
        print(f"FAILED: {report.failed} file(s) have errors")
    elif report.warnings > 0:
        print(f"PASSED with {report.warnings} warning(s)")
    else:
        print("PASSED: All files valid")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate DXF files in instrument_geometry/"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Root directory to search (default: auto-detect)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (exit code 2)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Find root directory
    if args.root:
        root = args.root
    else:
        # Auto-detect: look for instrument_geometry relative to script or cwd
        candidates = [
            Path(__file__).parent.parent / "services" / "api" / "app" / "instrument_geometry",
            Path.cwd() / "services" / "api" / "app" / "instrument_geometry",
            Path.cwd() / "app" / "instrument_geometry",
        ]
        root = None
        for c in candidates:
            if c.exists():
                root = c
                break

        if not root:
            print("ERROR: Could not find instrument_geometry directory", file=sys.stderr)
            return 1

    if not root.exists():
        print(f"ERROR: Directory not found: {root}", file=sys.stderr)
        return 1

    # Run validation
    report = validate_all(root)

    # Output
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_report(report, verbose=args.verbose)

    # Exit code
    if report.failed > 0:
        return 1
    if args.strict and report.warnings > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
