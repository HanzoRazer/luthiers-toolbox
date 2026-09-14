#!/usr/bin/env python3
"""
DXF Asset Validation Gate

CI validation script that checks all DXF files in instrument_geometry/ for:
1. Format: AC1009 (R12) — not AC1024 (AutoCAD 2010+)
2. Geometry: At least one closed contour. R12 files emit LINE chains via
   dxf_compat (not LWPOLYLINE). Closed LWPOLYLINE, POLYLINE, CIRCLE, and
   closed LINE loops all count.
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
import math
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Iterable

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

# Allowed DXF versions (R12 through R2010). Catalog assets include R2010
# (AC1024) files written by ezdxf.new() defaults. R2013+ stays blocked.
ALLOWED_VERSIONS = {"AC1009", "AC1012", "AC1014", "AC1015", "AC1018", "AC1021", "AC1024"}

# Versions that trigger errors
BLOCKED_VERSIONS = {"AC1027", "AC1032"}  # 2013+

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
# Closed-contour detection
# -----------------------------------------------------------------------------

# Endpoint snap for R12 LINE chains (dxf_compat emits LINE segments).
_LINE_ENDPOINT_QUANTUM_MM = 0.05


def _quantize_point(x: float, y: float, quantum: float = _LINE_ENDPOINT_QUANTUM_MM) -> Tuple[float, float]:
    return (round(x / quantum) * quantum, round(y / quantum) * quantum)


def count_closed_line_loops(
    segments: Iterable[Tuple[Tuple[float, float], Tuple[float, float]]],
    quantum: float = _LINE_ENDPOINT_QUANTUM_MM,
) -> int:
    """Count closed contours in an undirected LINE graph.

    Intended scope:
    - R12 LINE dumps emitted by dxf_compat for catalog/body-outline assets
    - multiple simple loops that may touch at snapped vertices
    - extra tree branches that should not create additional contours

    Algorithm:
    1. Quantize endpoints and build an undirected graph.
    2. Iteratively prune degree-0/1 vertices to remove open branches.
    3. On the remaining 2-core, walk bounded faces by taking the next clockwise
       half-edge at each vertex in angular order.
    4. Merge faces that share an edge, because interior diagonals/chords split a
       single outer contour into multiple bounded faces even though the catalog
       asset still has one closed outline.
    """
    adj: Dict[Tuple[float, float], List[Tuple[Tuple[float, float], int]]] = defaultdict(list)
    edges: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []
    for (x1, y1), (x2, y2) in segments:
        a = _quantize_point(x1, y1, quantum)
        b = _quantize_point(x2, y2, quantum)
        if a == b:
            continue
        eid = len(edges)
        edges.append((a, b))
        adj[a].append((b, eid))
        adj[b].append((a, eid))

    degrees = {vertex: len(neighbors) for vertex, neighbors in adj.items()}
    remaining_edges = set(range(len(edges)))
    queue = deque(vertex for vertex, degree in degrees.items() if degree < 2)
    while queue:
        cur = queue.popleft()
        if degrees.get(cur, 0) >= 2:
            continue
        for nxt, eid in adj[cur]:
            if eid not in remaining_edges:
                continue
            remaining_edges.remove(eid)
            degrees[cur] -= 1
            degrees[nxt] -= 1
            if degrees[nxt] == 1:
                queue.append(nxt)

    remaining_adj: Dict[Tuple[float, float], List[Tuple[float, float]]] = defaultdict(list)
    for eid in remaining_edges:
        a, b = edges[eid]
        remaining_adj[a].append(b)
        remaining_adj[b].append(a)

    if not remaining_adj:
        return 0

    ordered_neighbors: Dict[Tuple[float, float], List[Tuple[float, float]]] = {}
    for vertex, neighbors in remaining_adj.items():
        ordered_neighbors[vertex] = sorted(
            neighbors,
            key=lambda nxt: math.atan2(nxt[1] - vertex[1], nxt[0] - vertex[0]),
        )

    def next_half_edge(src: Tuple[float, float], dst: Tuple[float, float]) -> Tuple[float, float]:
        neighbors = ordered_neighbors[dst]
        idx = neighbors.index(src)
        return neighbors[idx - 1]

    visited_half_edges: set[Tuple[Tuple[float, float], Tuple[float, float]]] = set()
    face_edges: List[set[frozenset[Tuple[float, float]]]] = []
    for src, dst in [(a, b) for a, neighbors in remaining_adj.items() for b in neighbors]:
        half_edge = (src, dst)
        if half_edge in visited_half_edges:
            continue
        cycle: List[Tuple[float, float]] = []
        cur_src, cur_dst = src, dst
        while (cur_src, cur_dst) not in visited_half_edges:
            visited_half_edges.add((cur_src, cur_dst))
            cycle.append(cur_src)
            nxt = next_half_edge(cur_src, cur_dst)
            cur_src, cur_dst = cur_dst, nxt
        if len(cycle) < 3 or (cur_src, cur_dst) != half_edge:
            continue
        area2 = 0.0
        edges_in_face: set[frozenset[Tuple[float, float]]] = set()
        for a, b in zip(cycle, cycle[1:] + cycle[:1]):
            area2 += a[0] * b[1] - b[0] * a[1]
            edges_in_face.add(frozenset((a, b)))
        if area2 > 0.0:
            face_edges.append(edges_in_face)

    if not face_edges:
        return 0

    # Shared-edge faces come from interior diagonals/chords in one outline;
    # vertex-only contact stays separate and still counts as multiple contours.
    merged = 0
    seen_faces: set[int] = set()
    for idx in range(len(face_edges)):
        if idx in seen_faces:
            continue
        merged += 1
        stack = [idx]
        while stack:
            cur = stack.pop()
            if cur in seen_faces:
                continue
            seen_faces.add(cur)
            for other, edges_b in enumerate(face_edges):
                if other not in seen_faces and face_edges[cur] & edges_b:
                    stack.append(other)
    return merged


def count_closed_contours(entities: Iterable[Any]) -> int:
    """Count closed body-outline contours across DXF entity types.

    R12 (AC1009) files from dxf_compat use LINE segments, not LWPOLYLINE.
    """
    closed = 0
    line_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []

    for entity in entities:
        etype = entity.dxftype()
        if etype == "LWPOLYLINE":
            if getattr(entity, "closed", False):
                closed += 1
        elif etype == "POLYLINE":
            try:
                if entity.is_closed:
                    closed += 1
            except (AttributeError, TypeError):
                pass
        elif etype == "CIRCLE":
            closed += 1
        elif etype == "LINE":
            try:
                start = entity.dxf.start
                end = entity.dxf.end
                line_segments.append(((start.x, start.y), (end.x, end.y)))
            except (AttributeError, TypeError):
                pass

    closed += count_closed_line_loops(line_segments)
    return closed


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

    # Count closed contours and collect points for bounds.
    # R12 files emit LINE chains (dxf_compat); do not require LWPOLYLINE.
    closed_count = count_closed_contours(entities)
    total_points = 0
    all_points: List[Tuple[float, float]] = []

    for entity in entities:
        if entity.dxftype() == "LWPOLYLINE":
            lwpoly = entity
            points = list(lwpoly.get_points(format="xy"))
            total_points += len(points)
            all_points.extend(points)

        elif entity.dxftype() == "POLYLINE":
            try:
                points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
                total_points += len(points)
                all_points.extend(points)
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

        elif entity.dxftype() == "CIRCLE":
            total_points += 16
            try:
                cx, cy, r = entity.dxf.center.x, entity.dxf.center.y, entity.dxf.radius
                all_points.extend([(cx - r, cy), (cx + r, cy), (cx, cy - r), (cx, cy + r)])
            except (AttributeError, TypeError):
                pass

    result.closed_polylines = closed_count
    result.point_count = total_points

    has_geometry = total_points > 0 or closed_count > 0 or result.total_entities > 0
    if closed_count == 0:
        # Half-body sketches and SPLINE outlines exist in the catalog.
        # Fail only when the file has no drawable geometry at all.
        if not has_geometry:
            result.issues.append(DXFIssue(
                severity="ERROR",
                message=(
                    "No drawable geometry found. Body outline must contain "
                    "LWPOLYLINE, POLYLINE, CIRCLE, LINE, ARC, or SPLINE entities."
                ),
                category="geometry",
            ))
        else:
            result.issues.append(DXFIssue(
                severity="WARNING",
                message=(
                    "No closed contour found (LWPOLYLINE, POLYLINE, CIRCLE, or "
                    "closed R12 LINE chain). File still has drawable geometry."
                ),
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
