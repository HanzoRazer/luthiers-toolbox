"""
Topology Recovery — DXF Contour Reconstruction
===============================================

Recovers contour topology from DXF primitives:
- LINE/LWPOLYLINE/POLYLINE/ARC extraction
- Endpoint chaining
- Closed vs open contour detection
- Gap statistics

Reuses existing contour_reconstructor.py infrastructure.

DEV ORDER 1A-WORKFLOW: IBG Workflow Pipeline

Author: Production Shop
Date: 2026-05-18
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ContourCandidate:
    """
    A contour candidate extracted from DXF.

    Attributes:
        contour_id: Unique identifier
        points: List of (x, y) points
        is_closed: Whether contour forms a closed loop
        area_mm2: Area in mm² (0 if open)
        perimeter_mm: Perimeter length
        bounding_box: (min_x, min_y, max_x, max_y)
        gap_distance: Distance to close if near-closed
        source_entities: Number of source entities
    """
    contour_id: str
    points: List[Tuple[float, float]]
    is_closed: bool
    area_mm2: float
    perimeter_mm: float
    bounding_box: Tuple[float, float, float, float]
    gap_distance: float = 0.0
    source_entities: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contour_id": self.contour_id,
            "point_count": len(self.points),
            "is_closed": self.is_closed,
            "area_mm2": self.area_mm2,
            "perimeter_mm": self.perimeter_mm,
            "bounding_box": self.bounding_box,
            "gap_distance": self.gap_distance,
            "source_entities": self.source_entities,
        }


@dataclass
class TopologyStats:
    """
    Statistics about recovered topology.

    Attributes:
        total_entities: Total DXF entities processed
        lines_found: LINE entities
        polylines_found: LWPOLYLINE + POLYLINE entities
        arcs_found: ARC entities
        circles_found: CIRCLE entities
        closed_contours: Number of closed loops
        open_contours: Number of open chains
        near_closed_contours: Open contours with small gap
        total_points: Total points extracted
        max_gap_mm: Largest gap in near-closed contours
        avg_gap_mm: Average gap in near-closed contours
    """
    total_entities: int = 0
    lines_found: int = 0
    polylines_found: int = 0
    arcs_found: int = 0
    circles_found: int = 0
    closed_contours: int = 0
    open_contours: int = 0
    near_closed_contours: int = 0
    total_points: int = 0
    max_gap_mm: float = 0.0
    avg_gap_mm: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_entities": self.total_entities,
            "lines_found": self.lines_found,
            "polylines_found": self.polylines_found,
            "arcs_found": self.arcs_found,
            "circles_found": self.circles_found,
            "closed_contours": self.closed_contours,
            "open_contours": self.open_contours,
            "near_closed_contours": self.near_closed_contours,
            "total_points": self.total_points,
            "max_gap_mm": self.max_gap_mm,
            "avg_gap_mm": self.avg_gap_mm,
        }


@dataclass
class TopologyRecoveryResult:
    """
    Result of topology recovery.

    Attributes:
        success: Whether recovery succeeded
        contours: List of contour candidates
        stats: Topology statistics
        warnings: List of warnings
        errors: List of errors
    """
    success: bool
    contours: List[ContourCandidate] = field(default_factory=list)
    stats: TopologyStats = field(default_factory=TopologyStats)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "contour_count": len(self.contours),
            "contours": [c.to_dict() for c in self.contours],
            "stats": self.stats.to_dict(),
            "warnings": self.warnings,
            "errors": self.errors,
        }


def compute_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def compute_perimeter(points: List[Tuple[float, float]]) -> float:
    """Compute perimeter of a point sequence."""
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(len(points) - 1):
        total += compute_distance(points[i], points[i + 1])
    return total


def compute_area(points: List[Tuple[float, float]]) -> float:
    """Compute signed area using shoelace formula."""
    if len(points) < 3:
        return 0.0
    area = 0.0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area / 2.0)


def compute_bounding_box(points: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    """Compute bounding box of points."""
    if not points:
        return (0.0, 0.0, 0.0, 0.0)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def recover_topology(
    dxf_bytes: bytes,
    tolerance: float = 1.0,
    near_closed_threshold: float = 5.0,
    min_points: int = 3,
) -> TopologyRecoveryResult:
    """
    Recover contour topology from DXF bytes.

    Uses existing contour_reconstructor infrastructure where possible.

    Args:
        dxf_bytes: Raw DXF file bytes
        tolerance: Endpoint matching tolerance in mm
        near_closed_threshold: Max gap to consider "near-closed" in mm
        min_points: Minimum points for a valid contour

    Returns:
        TopologyRecoveryResult with contours and statistics
    """
    warnings = []
    errors = []
    contours = []
    stats = TopologyStats()

    # Try using existing reconstructor
    try:
        from app.cam.contour_reconstructor import reconstruct_contours_from_dxf

        result = reconstruct_contours_from_dxf(
            dxf_bytes=dxf_bytes,
            layer_name="0",  # Try default layer
            tolerance=tolerance,
            min_loop_points=min_points,
        )

        warnings.extend(result.warnings)

        # Convert loops to ContourCandidate
        for i, loop in enumerate(result.loops):
            points = loop.pts
            if len(points) < min_points:
                continue

            # Check if closed
            gap = compute_distance(points[0], points[-1]) if points else 0.0
            is_closed = gap < tolerance

            contours.append(ContourCandidate(
                contour_id=f"loop_{i:03d}",
                points=points,
                is_closed=is_closed,
                area_mm2=compute_area(points) if is_closed else 0.0,
                perimeter_mm=compute_perimeter(points),
                bounding_box=compute_bounding_box(points),
                gap_distance=gap if not is_closed else 0.0,
                source_entities=result.stats.get("edges_built", 0),
            ))

        stats.closed_contours = sum(1 for c in contours if c.is_closed)
        stats.open_contours = sum(1 for c in contours if not c.is_closed)
        stats.near_closed_contours = sum(
            1 for c in contours
            if not c.is_closed and c.gap_distance < near_closed_threshold
        )
        stats.total_points = sum(len(c.points) for c in contours)
        stats.lines_found = result.stats.get("lines_found", 0)
        stats.total_entities = result.stats.get("edges_built", 0)

        if contours:
            gaps = [c.gap_distance for c in contours if c.gap_distance > 0]
            stats.max_gap_mm = max(gaps) if gaps else 0.0
            stats.avg_gap_mm = sum(gaps) / len(gaps) if gaps else 0.0

        return TopologyRecoveryResult(
            success=len(contours) > 0,
            contours=contours,
            stats=stats,
            warnings=warnings,
        )

    except ImportError:
        warnings.append("contour_reconstructor not available, using fallback")

    except Exception as e:
        warnings.append(f"contour_reconstructor failed: {e}, using fallback")

    # Fallback: Direct entity extraction
    return _fallback_topology_recovery(
        dxf_bytes, tolerance, near_closed_threshold, min_points
    )


def _fallback_topology_recovery(
    dxf_bytes: bytes,
    tolerance: float,
    near_closed_threshold: float,
    min_points: int,
) -> TopologyRecoveryResult:
    """Fallback topology recovery using direct ezdxf parsing."""
    import tempfile
    from pathlib import Path

    warnings = []
    errors = []
    contours = []
    stats = TopologyStats()

    try:
        import ezdxf
    except ImportError:
        return TopologyRecoveryResult(
            success=False,
            errors=["ezdxf not available"],
        )

    # Write to temp file
    try:
        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
            f.write(dxf_bytes)
            temp_path = f.name

        try:
            doc = ezdxf.readfile(temp_path)
            msp = doc.modelspace()

            # Extract entities
            all_segments = []

            for entity in msp:
                entity_type = entity.dxftype()
                stats.total_entities += 1

                if entity_type == "LINE":
                    stats.lines_found += 1
                    start = (entity.dxf.start.x, entity.dxf.start.y)
                    end = (entity.dxf.end.x, entity.dxf.end.y)
                    all_segments.append([start, end])

                elif entity_type in ("LWPOLYLINE", "POLYLINE"):
                    stats.polylines_found += 1
                    if entity_type == "LWPOLYLINE":
                        points = [(p[0], p[1]) for p in entity.get_points()]
                    else:
                        points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]

                    if points:
                        # Check if closed
                        is_closed = getattr(entity, "closed", False) or (
                            entity_type == "LWPOLYLINE" and entity.closed
                        )
                        if is_closed and points[0] != points[-1]:
                            points.append(points[0])

                        if len(points) >= min_points:
                            gap = compute_distance(points[0], points[-1])
                            contours.append(ContourCandidate(
                                contour_id=f"poly_{len(contours):03d}",
                                points=points,
                                is_closed=gap < tolerance,
                                area_mm2=compute_area(points) if gap < tolerance else 0.0,
                                perimeter_mm=compute_perimeter(points),
                                bounding_box=compute_bounding_box(points),
                                gap_distance=gap if gap >= tolerance else 0.0,
                                source_entities=1,
                            ))

                elif entity_type == "ARC":
                    stats.arcs_found += 1
                    # Sample arc to points
                    cx, cy = entity.dxf.center.x, entity.dxf.center.y
                    r = entity.dxf.radius
                    start_angle = math.radians(entity.dxf.start_angle)
                    end_angle = math.radians(entity.dxf.end_angle)
                    if end_angle < start_angle:
                        end_angle += 2 * math.pi

                    arc_points = []
                    num_pts = max(8, int((end_angle - start_angle) / (math.pi / 16)))
                    for i in range(num_pts + 1):
                        angle = start_angle + (end_angle - start_angle) * i / num_pts
                        arc_points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

                    all_segments.append(arc_points)

                elif entity_type == "CIRCLE":
                    stats.circles_found += 1
                    cx, cy = entity.dxf.center.x, entity.dxf.center.y
                    r = entity.dxf.radius
                    points = []
                    for i in range(65):
                        angle = 2 * math.pi * i / 64
                        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

                    contours.append(ContourCandidate(
                        contour_id=f"circle_{len(contours):03d}",
                        points=points,
                        is_closed=True,
                        area_mm2=math.pi * r * r,
                        perimeter_mm=2 * math.pi * r,
                        bounding_box=(cx - r, cy - r, cx + r, cy + r),
                        gap_distance=0.0,
                        source_entities=1,
                    ))

            # Chain LINE segments into contours
            if all_segments and stats.lines_found > 0:
                chained = _chain_segments(all_segments, tolerance)
                for i, chain in enumerate(chained):
                    if len(chain) >= min_points:
                        gap = compute_distance(chain[0], chain[-1])
                        contours.append(ContourCandidate(
                            contour_id=f"chain_{i:03d}",
                            points=chain,
                            is_closed=gap < tolerance,
                            area_mm2=compute_area(chain) if gap < tolerance else 0.0,
                            perimeter_mm=compute_perimeter(chain),
                            bounding_box=compute_bounding_box(chain),
                            gap_distance=gap if gap >= tolerance else 0.0,
                            source_entities=len(all_segments),
                        ))

        finally:
            Path(temp_path).unlink(missing_ok=True)

    except Exception as e:
        errors.append(f"Fallback topology recovery failed: {e}")
        return TopologyRecoveryResult(success=False, errors=errors)

    # Update stats
    stats.closed_contours = sum(1 for c in contours if c.is_closed)
    stats.open_contours = sum(1 for c in contours if not c.is_closed)
    stats.near_closed_contours = sum(
        1 for c in contours
        if not c.is_closed and c.gap_distance < near_closed_threshold
    )
    stats.total_points = sum(len(c.points) for c in contours)

    if contours:
        gaps = [c.gap_distance for c in contours if c.gap_distance > 0]
        stats.max_gap_mm = max(gaps) if gaps else 0.0
        stats.avg_gap_mm = sum(gaps) / len(gaps) if gaps else 0.0

    return TopologyRecoveryResult(
        success=len(contours) > 0,
        contours=contours,
        stats=stats,
        warnings=warnings,
        errors=errors,
    )


def _chain_segments(
    segments: List[List[Tuple[float, float]]],
    tolerance: float,
) -> List[List[Tuple[float, float]]]:
    """Chain line segments by matching endpoints."""
    if not segments:
        return []

    # Simple greedy chaining
    chains = []
    used = set()

    for i, seg in enumerate(segments):
        if i in used:
            continue

        chain = list(seg)
        used.add(i)

        # Extend chain by finding matching endpoints
        changed = True
        while changed:
            changed = False
            for j, other in enumerate(segments):
                if j in used:
                    continue

                # Check if other connects to chain end
                chain_end = chain[-1]
                other_start = other[0]
                other_end = other[-1]

                if compute_distance(chain_end, other_start) < tolerance:
                    chain.extend(other[1:])
                    used.add(j)
                    changed = True
                elif compute_distance(chain_end, other_end) < tolerance:
                    chain.extend(reversed(other[:-1]))
                    used.add(j)
                    changed = True

        chains.append(chain)

    return chains
