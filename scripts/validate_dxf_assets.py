#!/usr/bin/env python3
"""
DXF Asset Validation Gate

Checks every DXF under instrument_geometry/ against the contract of its asset
class, as declared in services/api/app/ci/dxf_catalog_registry.json. The
classification, version policy and quarantine records are shared with the
DXF Validation Gate (app/ci/check_dxf_files.py) through
services/api/app/ci/dxf_catalog_policy.py, so the two gates cannot disagree
about a file.

This gate evaluates the clauses that need only ezdxf (its CI job installs
nothing else):
1. readable, nonempty, geometry_present
2. version_allowed: stored catalog files are R12 (AC1009) only; R2000 is
   paid-tier output of the canonical vectorizer, not a catalog format
3. closed_outline (manufacturing_body class): a closed contour on an outline
   layer bounds that layer; closed R12 LINE chains count, CIRCLE never does

Preflight and topology clauses are evaluated by the DXF Validation Gate.
Bounds and point counts are reported for information only; nothing here
compares bounds against instrument specs.

A file on a quarantine record is QUARANTINED (manufacturing authority
BLOCKED) only while it fails exactly the clauses its record declares.

Usage:
    python scripts/validate_dxf_assets.py
    python scripts/validate_dxf_assets.py --strict  # also fail on quarantined files
    python scripts/validate_dxf_assets.py --json    # JSON output

Exit codes:
    0 = every file PASSED or is QUARANTINED
    1 = one or more files FAILED, or a quarantine record names a missing asset
    2 = quarantined files present (only with --strict)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import ezdxf
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False
    print("WARNING: ezdxf not installed. Install with: pip install ezdxf", file=sys.stderr)

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_ROOT = REPO_ROOT / "services" / "api" / "app" / "instrument_geometry"
POLICY_PATH = REPO_ROOT / "services" / "api" / "app" / "ci" / "dxf_catalog_policy.py"


def _load_policy():
    """Import the shared policy module by path (the job installs only ezdxf)."""
    spec = importlib.util.spec_from_file_location("dxf_catalog_policy", POLICY_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["dxf_catalog_policy"] = module
    spec.loader.exec_module(module)
    return module


policy = _load_policy()

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

GATE_CLAUSES = frozenset({"readable", "nonempty", "geometry_present", "version_allowed", "closed_outline"})
BASE_CONTRACT = ["readable", "nonempty", "geometry_present", "version_allowed"]

# Minimum points for a "production quality" outline (informational)
MIN_POINTS_PRODUCTION = 50


# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------

@dataclass
class DXFIssue:
    """Single validation issue."""
    severity: str  # ERROR, QUARANTINED, WARNING
    message: str
    category: str  # clause name, quarantine, or geometry


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
    status: str = "PASS"
    asset: Optional[str] = None
    asset_class: Optional[str] = None
    issues: List[DXFIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status != "FAIL"

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
            "asset": self.asset,
            "asset_class": self.asset_class,
            "status": self.status,
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
    quarantined: int
    failed: int
    warnings: int
    orphan_records: List[str] = field(default_factory=list)
    results: List[DXFValidationResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "passed": self.passed,
            "quarantined": self.quarantined,
            "failed": self.failed,
            "warnings": self.warnings,
            "orphan_records": self.orphan_records,
            "results": [r.to_dict() for r in self.results],
        }


# -----------------------------------------------------------------------------
# Validation Functions
# -----------------------------------------------------------------------------

def _clause_failures(doc: Any, entities: List[Any], contract: List[str],
                     class_spec: Dict[str, Any], registry: Dict[str, Any]) -> Dict[str, List[str]]:
    """Failures of the ezdxf-only clauses, in contract order."""
    reference = set(class_spec.get("reference_layers", []))
    checks = {
        "nonempty": lambda: None if entities else "DXF modelspace is empty (no entities found)",
        "geometry_present": lambda: policy.check_geometry_present(entities),
        "version_allowed": lambda: policy.check_version(doc.dxfversion, registry),
        "closed_outline": lambda: policy.check_closed_outline(
            [e for e in entities if e.dxf.layer not in reference], class_spec).failure,
    }
    failures: Dict[str, List[str]] = {}
    for clause in contract:
        problem = checks[clause]() if clause in checks else None
        if problem:
            failures[clause] = [problem]
            if clause in ("nonempty", "geometry_present"):
                break
    return failures


def _entity_points(entity: Any) -> List[Tuple[float, float]]:
    kind = entity.dxftype()
    if kind == "LWPOLYLINE":
        return [(p[0], p[1]) for p in entity.get_points(format="xy")]
    if kind == "POLYLINE":
        return [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
    if kind == "LINE":
        return [(entity.dxf.start.x, entity.dxf.start.y), (entity.dxf.end.x, entity.dxf.end.y)]
    return []


def _fill_metrics(result: DXFValidationResult, entities: List[Any]) -> None:
    """Informational metrics: closed polylines, point count, bounds."""
    points: List[Tuple[float, float]] = []
    for entity in entities:
        points.extend(_entity_points(entity))
    result.total_entities = len(entities)
    result.closed_polylines = sum(
        1 for e in entities
        if (e.dxftype() == "LWPOLYLINE" and e.closed) or (e.dxftype() == "POLYLINE" and e.is_closed)
    )
    result.point_count = len(points)
    if points:
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        result.bounds = {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys),
                         "width": max(xs) - min(xs), "height": max(ys) - min(ys)}
    if 0 < result.point_count < MIN_POINTS_PRODUCTION:
        result.issues.append(DXFIssue(
            "WARNING",
            f"Low point count ({result.point_count}). Production quality needs {MIN_POINTS_PRODUCTION}+ points.",
            "geometry",
        ))


def _apply_verdict(result: DXFValidationResult, verdict: Any) -> None:
    result.status = verdict.status
    severity = {"FAIL": "ERROR", "QUARANTINED": "QUARANTINED"}.get(verdict.status)
    for clause, messages in verdict.failures.items():
        for message in messages:
            result.issues.append(DXFIssue(severity or "ERROR", message, clause))
    for message in verdict.messages:
        result.issues.append(DXFIssue(severity or "ERROR", message, "quarantine"))


def validate_dxf_file(path: Path, registry: Optional[Dict[str, Any]] = None,
                      asset_class: Optional[str] = None) -> DXFValidationResult:
    """Validate one DXF against its asset-class contract and quarantine record.

    `asset_class` overrides registry classification (used by tests for files
    outside the catalog).
    """
    registry = registry or policy.load_registry()
    result = DXFValidationResult(str(path), path.name, "UNKNOWN", 0, 0, 0, None)
    result.asset = policy.relative_asset(path, CATALOG_ROOT)
    result.asset_class = asset_class or policy.classify(result.asset, registry)
    contract = policy.contract_for(result.asset_class, registry) if result.asset_class else BASE_CONTRACT
    spec = registry["asset_classes"].get(result.asset_class, {}) if result.asset_class else {}
    if not HAS_EZDXF:
        failures = {"readable": ["ezdxf not installed - cannot validate"]}
    else:
        failures = _read_and_check(path, result, contract, spec, registry)
    evaluated = set(contract) & GATE_CLAUSES
    _apply_verdict(result, policy.judge(result.asset, result.asset_class, failures, evaluated, registry))
    return result


def _read_and_check(path: Path, result: DXFValidationResult, contract: List[str],
                    spec: Dict[str, Any], registry: Dict[str, Any]) -> Dict[str, List[str]]:
    try:
        doc = ezdxf.readfile(str(path))
    except Exception as exc:  # unreadable is a failure, not a crash of the gate
        return {"readable": [f"Failed to read DXF: {type(exc).__name__}: {exc}"]}
    result.dxf_version = doc.dxfversion
    entities = list(doc.modelspace())
    _fill_metrics(result, entities)
    return _clause_failures(doc, entities, contract, spec, registry)


def find_dxf_files(root: Path) -> List[Path]:
    """Find all DXF files under the given root."""
    return list(root.rglob("*.dxf"))


def validate_all(root: Path) -> ValidationReport:
    """Validate all DXF files under the given root."""
    registry = policy.load_registry()
    results = [validate_dxf_file(p, registry) for p in sorted(find_dxf_files(root))]
    return ValidationReport(
        total_files=len(results),
        passed=sum(1 for r in results if r.status == "PASS"),
        quarantined=sum(1 for r in results if r.status == "QUARANTINED"),
        failed=sum(1 for r in results if r.status == "FAIL"),
        warnings=sum(1 for r in results if r.warning_count > 0 and r.passed),
        orphan_records=policy.orphan_records(registry, CATALOG_ROOT),
        results=results,
    )


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

_ICONS = {"PASS": "✓", "QUARANTINED": "#", "FAIL": "✗"}
_PREFIX = {"ERROR": "  !", "QUARANTINED": "  #", "WARNING": "  ~"}


def _print_result(result: DXFValidationResult) -> None:
    print(f"{_ICONS[result.status]} [{result.status}] {result.filename}")
    print(f"   Class: {result.asset_class} | Version: {result.dxf_version} | "
          f"Entities: {result.total_entities} | Closed polys: {result.closed_polylines} | "
          f"Points: {result.point_count}")
    if result.bounds:
        print(f"   Bounds: {result.bounds['width']:.1f} x {result.bounds['height']:.1f} (drawing units)")
    for issue in result.issues:
        print(f"   {_PREFIX[issue.severity]} [{issue.severity}] {issue.message}")


def print_report(report: ValidationReport, verbose: bool = False) -> None:
    """Print human-readable validation report."""
    print("=" * 70)
    print("DXF Asset Validation Report")
    print("=" * 70)
    print(f"Total files: {report.total_files}")
    print(f"Passed: {report.passed}")
    print(f"Quarantined: {report.quarantined} (manufacturing authority BLOCKED)")
    print(f"Failed: {report.failed}")
    print(f"With warnings: {report.warnings}")
    print()
    for result in report.results:
        _print_result(result)
        if verbose or result.issues:
            print()
    for asset in report.orphan_records:
        print(f"✗ quarantine record for missing asset: {asset}")
    print("=" * 70)
    failed = report.failed + len(report.orphan_records)
    print(f"FAILED: {failed} problem(s)" if failed else
          f"PASSED: {report.passed} passed, {report.quarantined} quarantined")


def _find_root(root_arg: Optional[Path]) -> Optional[Path]:
    if root_arg:
        return root_arg
    candidates = [
        CATALOG_ROOT,
        Path.cwd() / "services" / "api" / "app" / "instrument_geometry",
        Path.cwd() / "app" / "instrument_geometry",
    ]
    return next((c for c in candidates if c.exists()), None)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate DXF files in instrument_geometry/")
    parser.add_argument("--root", type=Path, default=None,
                        help="Root directory to search (default: auto-detect)")
    parser.add_argument("--strict", action="store_true", help="Fail on quarantined files (exit code 2)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    root = _find_root(args.root)
    if not root or not root.exists():
        print(f"ERROR: Could not find instrument_geometry directory ({root})", file=sys.stderr)
        return 1

    report = validate_all(root)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_report(report, verbose=args.verbose)

    if report.failed or report.orphan_records:
        return 1
    if args.strict and report.quarantined:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
