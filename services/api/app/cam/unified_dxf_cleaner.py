#!/usr/bin/env python3
"""
Unified DXF Cleaner for Guitar Projects
========================================

Handles both POLYLINE and LINE entities:
- LINE entities: grouped into connected chains, filtered by length
- POLYLINE entities: filtered by length, closed if needed

Algorithm for LINE entities:
1. Build adjacency graph of LINE endpoints (tolerance 0.1mm)
2. Trace chains by following connections
3. Keep only closed or near-closed chains above minimum length
4. Output as LINE entities (R12 compatible)

BLUEPRINT DXF EXPORT RULE (Fusion compatibility)
------------------------------------------------
Output format: R12 (AC1009)
Geometry entities: LINE only
Avoid: LWPOLYLINE in the Fusion-facing blueprint path

Reason: LWPOLYLINE requires DXF R2000+. Even when the code creates
an R12 document, attempting to write LWPOLYLINE causes ezdxf errors
or produces files that Fusion 360 rejects or freezes on. LINE entities
are universally supported and work reliably with Fusion's DXF import.

This rule applies to:
- write_selected_chains()
- clean_file()
- Any future DXF output in the blueprint pipeline

All DXF document creation uses dxf_compat.create_document() per governance.

Author: Production Shop
"""

from __future__ import annotations

import argparse
import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

import ezdxf
from ezdxf.entities import LWPolyline

from app.util.dxf_compat import create_document
from app.util.dxf_lifecycle_guard import (
    DxfLifecycleContext,
    assert_dxf_lifecycle_context,
)

logger = logging.getLogger(__name__)


@dataclass
class Point:
    """2D point with tolerance-based equality."""
    x: float
    y: float

    def __hash__(self):
        # Round to tolerance for hashing
        return hash((round(self.x, 1), round(self.y, 1)))

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return abs(self.x - other.x) < 0.1 and abs(self.y - other.y) < 0.1

    def distance_to(self, other: "Point") -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class LineSegment:
    """A LINE entity represented as two endpoints."""
    start: Point
    end: Point

    def length(self) -> float:
        return self.start.distance_to(self.end)

    def other_end(self, point: Point) -> Point:
        """Given one endpoint, return the other."""
        if abs(point.x - self.start.x) < 0.1 and abs(point.y - self.start.y) < 0.1:
            return self.end
        return self.start


@dataclass
class Chain:
    """A connected sequence of LINE segments."""
    points: List[Point] = field(default_factory=list)

    def is_closed(self, tolerance: float = 1.0) -> bool:
        """Check if chain forms a closed loop."""
        if len(self.points) < 3:
            return False
        return self.points[0].distance_to(self.points[-1]) < tolerance

    def length(self) -> float:
        """Total length of chain."""
        total = 0.0
        for i in range(len(self.points) - 1):
            total += self.points[i].distance_to(self.points[i + 1])
        return total

    def as_polyline_points(self) -> List[Tuple[float, float]]:
        """Convert to list of (x, y) tuples for LWPOLYLINE."""
        return [p.as_tuple() for p in self.points]


@dataclass
class CleanResult:
    """Result from cleaning operation."""
    success: bool = True
    original_entity_count: int = 0
    cleaned_entity_count: int = 0
    contours_found: int = 0
    chains_found: int = 0
    discarded_short: int = 0
    discarded_open: int = 0
    output_path: Optional[Path] = None
    error: Optional[str] = None


class DXFCleaner:
    """
    Cleans raw DXF files by filtering to significant closed contours.

    Handles:
    - LWPOLYLINE/POLYLINE: filter by length, force closed
    - LINE: chain into connected sequences, filter by length and closure
    """

    def __init__(
        self,
        min_contour_length_mm: float = 100.0,
        endpoint_tolerance: float = 0.1,
        closure_tolerance: float = 1.0,
        keep_open_chains: bool = False,
    ):
        """
        Args:
            min_contour_length_mm: Minimum total length to keep a contour
            endpoint_tolerance: Maximum distance to consider endpoints connected
            closure_tolerance: Maximum gap to consider a chain "closed"
            keep_open_chains: If True, keep long open chains (not just closed loops)
        """
        self.min_contour_length_mm = min_contour_length_mm
        self.endpoint_tolerance = endpoint_tolerance
        self.closure_tolerance = closure_tolerance
        self.keep_open_chains = keep_open_chains

    def extract_chains(self, input_path: Path) -> Tuple[List[Chain], List[List[Tuple[float, float]]], int]:
        """
        Extract chains from DXF without filtering or writing.

        Returns:
            (chains_from_lines, polyline_points_list, original_entity_count)
        """
        doc = ezdxf.readfile(str(input_path))
        msp = doc.modelspace()

        all_entities = list(msp)
        original_count = len(all_entities)

        lines: List[LineSegment] = []
        polylines: List[LWPolyline] = []

        for e in all_entities:
            if e.dxftype() == "LINE":
                lines.append(LineSegment(
                    start=Point(e.dxf.start.x, e.dxf.start.y),
                    end=Point(e.dxf.end.x, e.dxf.end.y),
                ))
            elif e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
                polylines.append(e)

        # Chain LINE entities
        chains = self._chain_lines(lines) if lines else []

        # Extract polyline points
        polyline_pts = []
        for pl in polylines:
            points = list(pl.get_points("xy"))
            if len(points) >= 2:
                polyline_pts.append(points)

        return chains, polyline_pts, original_count

    def write_selected_chains(
        self,
        output_path: Path,
        chains: List[Chain],
        polyline_pts: Optional[List[List[Tuple[float, float]]]] = None,
        preserve_layers: bool = False,
    ) -> int:
        """
        Write pre-selected chains to output DXF.

        Uses LINE entities for R12 compatibility per CLAUDE.md standard.

        Args:
            output_path: Path for output DXF
            chains: Selected Chain objects to write
            polyline_pts: Optional polyline point lists to include
            preserve_layers: If True, use "body_outline" layer

        Returns:
            Number of contours written
        """
        newdoc = create_document(version="R12")
        newmsp = newdoc.modelspace()
        contours_written = 0

        for i, chain in enumerate(chains):
            points = chain.as_polyline_points()
            layer = f"contour_{i}" if not preserve_layers else "body_outline"

            # Write as LINE entities for R12 compatibility
            for j in range(len(points) - 1):
                newmsp.add_line(
                    points[j],
                    points[j + 1],
                    dxfattribs={"layer": layer},
                )

            # Close the loop if chain is closed
            if chain.is_closed(self.closure_tolerance) and len(points) > 2:
                newmsp.add_line(
                    points[-1],
                    points[0],
                    dxfattribs={"layer": layer},
                )

            contours_written += 1

        if polyline_pts:
            for i, points in enumerate(polyline_pts):
                layer = f"polyline_{i}" if not preserve_layers else "body_outline"

                # Write as LINE entities
                for j in range(len(points) - 1):
                    newmsp.add_line(
                        points[j],
                        points[j + 1],
                        dxfattribs={"layer": layer},
                    )

                # Close the loop
                if len(points) > 2:
                    newmsp.add_line(
                        points[-1],
                        points[0],
                        dxfattribs={"layer": layer},
                    )

                contours_written += 1

        output_path.parent.mkdir(parents=True, exist_ok=True)
        assert_dxf_lifecycle_context(
            DxfLifecycleContext(
                source_module=__name__,
                export_type="dxf-create-save",
                dxf_version="R12",
                lifecycle_status="COMPAT_ONLY",
                runtime_callable="runtime_service",
                authority_context="pipeline_stage",
                provenance_status="NO",
            )
        )
        newdoc.saveas(str(output_path))
        return contours_written

    def clean_file(
        self,
        input_path: Path,
        output_path: Path,
        preserve_layers: bool = False,
    ) -> CleanResult:
        """
        Clean a DXF file, keeping only significant closed contours.

        Args:
            input_path: Path to input DXF
            output_path: Path for cleaned output DXF
            preserve_layers: If True, preserve original layer names

        Returns:
            CleanResult with statistics
        """
        result = CleanResult()

        try:
            doc = ezdxf.readfile(str(input_path))
            msp = doc.modelspace()

            # Count original entities
            all_entities = list(msp)
            result.original_entity_count = len(all_entities)

            # Separate entity types
            lines: List[LineSegment] = []
            polylines: List[LWPolyline] = []

            for e in all_entities:
                if e.dxftype() == "LINE":
                    lines.append(LineSegment(
                        start=Point(e.dxf.start.x, e.dxf.start.y),
                        end=Point(e.dxf.end.x, e.dxf.end.y),
                    ))
                elif e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
                    polylines.append(e)

            logger.info(f"Found {len(lines)} LINE, {len(polylines)} POLYLINE entities")

            # Process LINE entities into chains
            kept_chains: List[Chain] = []
            if lines:
                chains = self._chain_lines(lines)
                result.chains_found = len(chains)

                for chain in chains:
                    chain_len = chain.length()
                    is_closed = chain.is_closed(self.closure_tolerance)

                    if chain_len < self.min_contour_length_mm:
                        result.discarded_short += 1
                        continue

                    if not is_closed and not self.keep_open_chains:
                        result.discarded_open += 1
                        continue

                    kept_chains.append(chain)

                logger.info(
                    f"Chains: {len(chains)} total, {len(kept_chains)} kept, "
                    f"{result.discarded_short} too short, {result.discarded_open} open"
                )

            # Process POLYLINE entities
            kept_polylines: List[List[Tuple[float, float]]] = []
            for pl in polylines:
                points = list(pl.get_points("xy"))
                if len(points) < 2:
                    continue

                # Calculate length
                length = sum(
                    math.sqrt(
                        (points[i + 1][0] - points[i][0]) ** 2 +
                        (points[i + 1][1] - points[i][1]) ** 2
                    )
                    for i in range(len(points) - 1)
                )

                if length >= self.min_contour_length_mm:
                    kept_polylines.append(points)

            logger.info(f"Polylines: {len(polylines)} total, {len(kept_polylines)} kept")

            # Create output document - R12 for maximum compatibility
            # Per CLAUDE.md: LINE entities only, no LWPOLYLINE
            newdoc = create_document(version="R12")
            newmsp = newdoc.modelspace()

            # Add chains as LINE entities (R12 compatible)
            for i, chain in enumerate(kept_chains):
                points = chain.as_polyline_points()
                layer = f"contour_{i}" if not preserve_layers else "body_outline"

                # Write consecutive LINE segments
                for j in range(len(points) - 1):
                    newmsp.add_line(
                        points[j],
                        points[j + 1],
                        dxfattribs={"layer": layer},
                    )

                # Close the loop if chain is closed
                if chain.is_closed(self.closure_tolerance) and len(points) > 2:
                    newmsp.add_line(
                        points[-1],
                        points[0],
                        dxfattribs={"layer": layer},
                    )

                result.contours_found += 1

            # Add kept polylines as LINE entities
            for i, points in enumerate(kept_polylines):
                layer = f"polyline_{i}" if not preserve_layers else "body_outline"

                for j in range(len(points) - 1):
                    newmsp.add_line(
                        points[j],
                        points[j + 1],
                        dxfattribs={"layer": layer},
                    )

                # Close the loop
                if len(points) > 2:
                    newmsp.add_line(
                        points[-1],
                        points[0],
                        dxfattribs={"layer": layer},
                    )

                result.contours_found += 1

            result.cleaned_entity_count = result.contours_found

            # Save output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            assert_dxf_lifecycle_context(
                DxfLifecycleContext(
                    source_module=__name__,
                    export_type="dxf-create-save",
                    dxf_version="R12",
                    lifecycle_status="COMPAT_ONLY",
                    runtime_callable="runtime_service",
                    authority_context="pipeline_stage",
                    provenance_status="NO",
                )
            )
            newdoc.saveas(str(output_path))
            result.output_path = output_path

            logger.info(
                f"Cleaned: {result.original_entity_count} → {result.cleaned_entity_count} entities, "
                f"{result.contours_found} contours"
            )

        except Exception as e:
            logger.exception("DXF cleaning failed")
            result.success = False
            result.error = str(e)

        return result

    def _chain_lines(self, lines: List[LineSegment]) -> List[Chain]:
        """
        Chain LINE segments into connected sequences.

        Algorithm:
        1. Build adjacency map: point -> list of segments containing that point
        2. Start from an unvisited segment
        3. Walk in both directions until dead end or loop
        4. Mark visited segments, repeat until all visited
        """
        if not lines:
            return []

        # Build adjacency: point -> segments
        point_to_segments: Dict[Tuple[int, int], List[int]] = defaultdict(list)

        def point_key(p: Point) -> Tuple[int, int]:
            """Quantize point to grid for lookup."""
            return (round(p.x * 10), round(p.y * 10))  # 0.1mm grid

        for i, seg in enumerate(lines):
            point_to_segments[point_key(seg.start)].append(i)
            point_to_segments[point_key(seg.end)].append(i)

        visited: Set[int] = set()
        chains: List[Chain] = []

        for start_idx in range(len(lines)):
            if start_idx in visited:
                continue

            # Start a new chain
            chain = Chain()
            seg = lines[start_idx]
            visited.add(start_idx)

            # Initialize with first segment
            chain.points.append(seg.start)
            chain.points.append(seg.end)

            # Extend forward from end
            current_point = seg.end
            while True:
                key = point_key(current_point)
                neighbors = [i for i in point_to_segments[key] if i not in visited]

                if not neighbors:
                    break

                # Take first unvisited neighbor
                next_idx = neighbors[0]
                visited.add(next_idx)
                next_seg = lines[next_idx]
                next_point = next_seg.other_end(current_point)
                chain.points.append(next_point)
                current_point = next_point

            # Extend backward from start
            current_point = seg.start
            while True:
                key = point_key(current_point)
                neighbors = [i for i in point_to_segments[key] if i not in visited]

                if not neighbors:
                    break

                next_idx = neighbors[0]
                visited.add(next_idx)
                next_seg = lines[next_idx]
                next_point = next_seg.other_end(current_point)
                chain.points.insert(0, next_point)
                current_point = next_point

            if len(chain.points) >= 2:
                chains.append(chain)

        return chains

    def generate_svg_preview(
        self,
        chains: List[Chain],
        width: int = 800,
        height: int = 600,
    ) -> str:
        """Generate SVG preview of cleaned contours."""
        if not chains:
            return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600"><text x="400" y="300" text-anchor="middle">No contours found</text></svg>'

        # Find bounds
        all_points = [p for c in chains for p in c.points]
        min_x = min(p.x for p in all_points)
        max_x = max(p.x for p in all_points)
        min_y = min(p.y for p in all_points)
        max_y = max(p.y for p in all_points)

        # Add padding
        padding = 20
        data_width = max_x - min_x or 1
        data_height = max_y - min_y or 1

        # Scale to fit
        scale = min((width - 2 * padding) / data_width, (height - 2 * padding) / data_height)

        def transform(p: Point) -> Tuple[float, float]:
            x = padding + (p.x - min_x) * scale
            y = height - padding - (p.y - min_y) * scale  # Flip Y
            return (x, y)

        paths = []
        colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c"]

        for i, chain in enumerate(chains):
            color = colors[i % len(colors)]
            points = [transform(p) for p in chain.points]

            d = f"M {points[0][0]:.1f} {points[0][1]:.1f}"
            for px, py in points[1:]:
                d += f" L {px:.1f} {py:.1f}"
            if chain.is_closed():
                d += " Z"

            paths.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"/>')

        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f8fafc"/>
  {"".join(paths)}
</svg>'''


# ---------------------------------------------------------------------------
# Geometry deduplication (Pass 1: utility only, NOT wired into the pipeline)
# ---------------------------------------------------------------------------
#
# Post-selection, pre-export cleanup that removes duplicate / near-duplicate
# geometry from already-selected chains. This is a cleanup layer ONLY:
#   - it does not score, select, or own chains
#   - it does not change the Chain / Point public boundary
#   - it does not change DXF export policy (R12 + LINE entities only)
#
# The dedup pass works on an internal flat `Segment` model (a single LINE with
# a layer label and two endpoints), dedupes at the segment level, then rebuilds
# chains from the survivors. Chains in this codebase carry no layer attribute,
# so chain-derived segments are layer-agnostic (a single bucket). The `layer`
# field on Segment / SegmentKey is exercised directly by the synthetic
# segment-level tests and is forward-looking for a future layered pipeline.


@dataclass(frozen=True)
class SegmentKey:
    """Quantized, layer-aware identity for a line segment.

    Endpoints are pre-canonicalized by the producer so that A->B and B->A map
    to the same key (the lexicographically smaller endpoint is stored first).
    """
    layer: str
    ax: int
    ay: int
    bx: int
    by: int


@dataclass
class Segment:
    """Internal flat representation of a single LINE for the dedup pass.

    Distinct from :class:`LineSegment` (the extraction-time primitive): this one
    carries a layer label and an optional debug `category` so the duplicate
    overlay can colour-code why a segment was removed. Not part of the public
    Chain/Point boundary.
    """
    layer: str
    start: Point
    end: Point
    # Debug-only classification, set during deduplication:
    # "retained" | "exact" | "reversed" | "near" | "overlap"
    category: str = "retained"

    def length(self) -> float:
        return self.start.distance_to(self.end)

    def as_tuples(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        return (self.start.as_tuple(), self.end.as_tuple())


@dataclass
class DeduplicationStats:
    """Per-category accounting for a deduplication pass."""
    input_segments: int
    output_segments: int
    exact_duplicates_removed: int
    reversed_duplicates_removed: int
    near_duplicates_removed: int
    overlap_duplicates_removed: int


def _quantize(value: float, tol: float) -> int:
    """Snap a coordinate to an integer grid of size `tol`."""
    return round(value / tol)


def _exact_q(value: float) -> int:
    """High-precision quantization used for exact/reverse detection.

    Fine enough (1e-6 mm) to treat only coordinate-identical points as equal,
    so genuine near-duplicates fall through to the tolerance-based pass.
    """
    return round(value / 1e-6)


def _directed_key(
    seg: Segment, qfn: Callable[[float], int], include_layer: bool
) -> Tuple:
    """Direction-preserving key (start then end, no canonical ordering)."""
    layer = seg.layer if include_layer else ""
    return (layer, qfn(seg.start.x), qfn(seg.start.y), qfn(seg.end.x), qfn(seg.end.y))


def _canonical_key(
    seg: Segment, qfn: Callable[[float], int], include_layer: bool
) -> SegmentKey:
    """Order-independent key: A->B and B->A collapse to the same SegmentKey."""
    layer = seg.layer if include_layer else ""
    a = (qfn(seg.start.x), qfn(seg.start.y))
    b = (qfn(seg.end.x), qfn(seg.end.y))
    if b < a:
        a, b = b, a
    return SegmentKey(layer=layer, ax=a[0], ay=a[1], bx=b[0], by=b[1])


def _is_zero_length(seg: Segment, tol: float) -> bool:
    return _quantize(seg.start.x, tol) == _quantize(seg.end.x, tol) and \
        _quantize(seg.start.y, tol) == _quantize(seg.end.y, tol)


def _dedupe_segments(
    segments: List[Segment],
    *,
    endpoint_tol_mm: float,
    overlap_tol_mm: float,
    angle_tol_deg: float,
    preserve_layers: bool,
) -> Tuple[List[Segment], DeduplicationStats]:
    """Core segment-level dedup. Detection order matches the handoff spec:

    1. zero-length removal
    2. exact duplicate removal
    3. reverse duplicate removal
    4. near-duplicate (tolerance) removal
    5. collinear overlap removal
    6. (chain reconstruction happens in the caller)
    """
    input_count = len(segments)
    stats = DeduplicationStats(
        input_segments=input_count,
        output_segments=0,
        exact_duplicates_removed=0,
        reversed_duplicates_removed=0,
        near_duplicates_removed=0,
        overlap_duplicates_removed=0,
    )

    # 1. zero-length removal (degenerate; not a duplicate category)
    work = [s for s in segments if not _is_zero_length(s, endpoint_tol_mm)]

    # 2 + 3. exact / reverse on a near-exact grid.
    # First occurrence of a canonical key wins; later ones are exact (same
    # direction as the winner) or reversed (opposite direction).
    rep_directed: Dict[SegmentKey, Tuple] = {}
    after_exact: List[Segment] = []
    for seg in work:
        ckey = _canonical_key(seg, _exact_q, preserve_layers)
        dkey = _directed_key(seg, _exact_q, preserve_layers)
        if ckey not in rep_directed:
            rep_directed[ckey] = dkey
            after_exact.append(seg)
            continue
        if dkey == rep_directed[ckey]:
            seg.category = "exact"
            stats.exact_duplicates_removed += 1
        else:
            seg.category = "reversed"
            stats.reversed_duplicates_removed += 1

    # 4. near-duplicate removal on the tolerance grid (survivors only).
    seen_near: Set[SegmentKey] = set()
    after_near: List[Segment] = []
    for seg in after_exact:
        nkey = _canonical_key(seg, lambda v: _quantize(v, endpoint_tol_mm), preserve_layers)
        if nkey in seen_near:
            seg.category = "near"
            stats.near_duplicates_removed += 1
            continue
        seen_near.add(nkey)
        after_near.append(seg)

    # 5. collinear overlap removal. Bucket by (layer, orientation, offset) so
    # only plausibly-collinear segments are compared, then drop any segment
    # fully covered by a longer collinear neighbour.
    after_overlap = _remove_collinear_overlaps(
        after_near,
        overlap_tol_mm=overlap_tol_mm,
        angle_tol_deg=angle_tol_deg,
        preserve_layers=preserve_layers,
        stats=stats,
    )

    stats.output_segments = len(after_overlap)
    return after_overlap, stats


def _remove_collinear_overlaps(
    segments: List[Segment],
    *,
    overlap_tol_mm: float,
    angle_tol_deg: float,
    preserve_layers: bool,
    stats: DeduplicationStats,
) -> List[Segment]:
    """Remove segments fully contained within a longer collinear neighbour.

    Conservative on purpose: only *full containment* (within overlap_tol_mm) is
    removed. Partial overlaps and merely-collinear-but-separate segments
    (handoff test "non-overlap collinear") are preserved so no real geometry is
    lost. O(n) per collinearity bucket rather than O(n^2) overall.
    """
    angle_tol_rad = math.radians(angle_tol_deg)

    buckets: Dict[Tuple, List[int]] = defaultdict(list)
    for idx, seg in enumerate(segments):
        dx = seg.end.x - seg.start.x
        dy = seg.end.y - seg.start.y
        theta = math.atan2(dy, dx) % math.pi
        ux, uy = math.cos(theta), math.sin(theta)
        nx, ny = -uy, ux
        offset = seg.start.x * nx + seg.start.y * ny
        layer = seg.layer if preserve_layers else ""
        # Quantize orientation and perpendicular offset into a collinearity cell.
        angle_bin = round(theta / max(angle_tol_rad, 1e-9))
        offset_bin = round(offset / overlap_tol_mm)
        buckets[(layer, angle_bin, offset_bin)].append(idx)

    removed: Set[int] = set()
    for idxs in buckets.values():
        if len(idxs) < 2:
            continue
        for i in range(len(idxs)):
            ai = idxs[i]
            if ai in removed:
                continue
            sa = segments[ai]
            for j in range(len(idxs)):
                if i == j:
                    continue
                bi = idxs[j]
                if bi in removed:
                    continue
                sb = segments[bi]
                # Drop sb if it lies fully on top of sa (sa at least as long).
                if sa.length() + 1e-9 >= sb.length() and _covers(sa, sb, overlap_tol_mm):
                    sb.category = "overlap"
                    removed.add(bi)
                    stats.overlap_duplicates_removed += 1

    return [s for i, s in enumerate(segments) if i not in removed]


def _covers(host: Segment, other: Segment, tol: float) -> bool:
    """True if both endpoints of `other` lie on `host` (within tol), i.e. the
    `other` segment is geometrically contained in `host`."""
    return _point_on_segment(host, other.start, tol) and \
        _point_on_segment(host, other.end, tol)


def _point_on_segment(seg: Segment, p: Point, tol: float) -> bool:
    """Perpendicular distance to the segment's line < tol AND the projection
    falls within the segment's extent (inclusive of a tol margin)."""
    ax, ay = seg.start.x, seg.start.y
    bx, by = seg.end.x, seg.end.y
    dx, dy = bx - ax, by - ay
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq < 1e-12:
        return p.distance_to(seg.start) < tol
    t = ((p.x - ax) * dx + (p.y - ay) * dy) / seg_len_sq
    if t < -tol / math.sqrt(seg_len_sq) or t > 1 + tol / math.sqrt(seg_len_sq):
        return False
    # Closest point on the infinite line.
    cx, cy = ax + t * dx, ay + t * dy
    perp = math.sqrt((p.x - cx) ** 2 + (p.y - cy) ** 2)
    return perp < tol


def _chain_to_segments(chain: Chain, layer: str, closure_tol: float) -> List[Segment]:
    """Explode a Chain into flat Segments, including the closing edge if the
    chain is closed (mirrors what write_selected_chains emits)."""
    pts = chain.points
    segs: List[Segment] = []
    for i in range(len(pts) - 1):
        segs.append(Segment(layer=layer, start=pts[i], end=pts[i + 1]))
    if chain.is_closed(closure_tol) and len(pts) > 2:
        segs.append(Segment(layer=layer, start=pts[-1], end=pts[0]))
    return segs


def _reconstruct_chains(segments: List[Segment], tol: float) -> List[Chain]:
    """Rebuild chains from surviving segments via endpoint adjacency.

    Mirrors DXFCleaner._chain_lines but uses the dedup tolerance for the grid so
    behaviour is consistent with the dedup pass. Distinct features that do not
    share endpoints stay distinct; a closed loop reconstructs with
    points[0] ~= points[-1] so Chain.is_closed stays true.
    """
    if not segments:
        return []

    grid = max(tol, 1e-9)

    def pkey(p: Point) -> Tuple[int, int]:
        return (round(p.x / grid), round(p.y / grid))

    point_to_segs: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    for i, seg in enumerate(segments):
        point_to_segs[pkey(seg.start)].append(i)
        point_to_segs[pkey(seg.end)].append(i)

    def other_end(seg: Segment, p: Point) -> Point:
        if pkey(seg.start) == pkey(p):
            return seg.end
        return seg.start

    visited: Set[int] = set()
    chains: List[Chain] = []
    for start_idx in range(len(segments)):
        if start_idx in visited:
            continue
        seg = segments[start_idx]
        visited.add(start_idx)
        chain = Chain()
        chain.points.append(seg.start)
        chain.points.append(seg.end)

        current = seg.end
        while True:
            neighbors = [i for i in point_to_segs[pkey(current)] if i not in visited]
            if not neighbors:
                break
            nxt = neighbors[0]
            visited.add(nxt)
            current = other_end(segments[nxt], current)
            chain.points.append(current)

        current = seg.start
        while True:
            neighbors = [i for i in point_to_segs[pkey(current)] if i not in visited]
            if not neighbors:
                break
            nxt = neighbors[0]
            visited.add(nxt)
            current = other_end(segments[nxt], current)
            chain.points.insert(0, current)

        if len(chain.points) >= 2:
            chains.append(chain)

    return chains


def deduplicate_chains(
    chains: List[Chain],
    *,
    endpoint_tol_mm: float = 0.05,
    overlap_tol_mm: float = 0.05,
    angle_tol_deg: float = 1.0,
    preserve_layers: bool = True,
    debug: bool = False,
) -> Tuple[List[Chain], DeduplicationStats]:
    """Remove duplicate / near-duplicate geometry from selected chains.

    Post-selection, pre-export cleanup. Explodes chains into flat segments,
    removes exact / reversed / near / collinear-overlap duplicates, then rebuilds
    chains from the survivors. Output is multiple valid chains (BODY_OUTLINE,
    NECK_POCKET, ... stay separate); it is NOT collapsed to a single contour.

    Chains carry no layer attribute in this codebase, so chain-derived segments
    are layer-agnostic. `preserve_layers` is threaded into the keys for the
    synthetic segment-level path and a future layered pipeline.

    Returns (deduplicated_chains, stats).
    """
    closure_tol = 1.0  # matches DXFCleaner default closure_tolerance
    segments: List[Segment] = []
    for chain in chains:
        if len(chain.points) < 2:
            continue
        segments.extend(_chain_to_segments(chain, layer="", closure_tol=closure_tol))

    kept, stats = _dedupe_segments(
        segments,
        endpoint_tol_mm=endpoint_tol_mm,
        overlap_tol_mm=overlap_tol_mm,
        angle_tol_deg=angle_tol_deg,
        preserve_layers=preserve_layers,
    )

    rebuilt = _reconstruct_chains(kept, endpoint_tol_mm)

    if debug:
        logger.debug(
            "deduplicate_chains: %d->%d segments "
            "(exact=%d reversed=%d near=%d overlap=%d), %d chains -> %d chains",
            stats.input_segments, stats.output_segments,
            stats.exact_duplicates_removed, stats.reversed_duplicates_removed,
            stats.near_duplicates_removed, stats.overlap_duplicates_removed,
            len(chains), len(rebuilt),
        )

    return rebuilt, stats


def build_duplicate_debug_svg(
    original_segments: List[Segment],
    duplicate_segments: List[Segment],
    *,
    width_mm: float,
    height_mm: float,
) -> str:
    """Debug-only SVG overlay marking retained vs duplicate geometry.

    Colour convention:
        black  = retained geometry
        red    = exact / reversed duplicate
        orange = near duplicate
        purple = collinear overlap duplicate

    Duplicate colour is chosen from each segment's `.category`. Y is flipped so
    the overlay reads in the same orientation as the DXF (y-up).
    """
    category_color = {
        "retained": "#000000",
        "exact": "#e11d48",     # red
        "reversed": "#e11d48",  # red
        "near": "#f97316",      # orange
        "overlap": "#a21caf",   # purple
    }

    def line_el(seg: Segment, color: str) -> str:
        (x1, y1), (x2, y2) = seg.as_tuples()
        return (
            f'<line x1="{x1:.4f}" y1="{y1:.4f}" x2="{x2:.4f}" y2="{y2:.4f}" '
            f'stroke="{color}" stroke-width="0.2" />'
        )

    parts: List[str] = []
    for seg in original_segments:
        parts.append(line_el(seg, category_color["retained"]))
    for seg in duplicate_segments:
        parts.append(line_el(seg, category_color.get(seg.category, "#e11d48")))

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width_mm:.4f}mm" height="{height_mm:.4f}mm" '
        f'viewBox="0 0 {width_mm:.4f} {height_mm:.4f}">\n'
        f'  <rect width="100%" height="100%" fill="#f8fafc"/>\n'
        f'  <g transform="translate(0,{height_mm:.4f}) scale(1,-1)">\n'
        f'    {"".join(parts)}\n'
        f'  </g>\n'
        f'</svg>'
    )


def main():
    """CLI entry point."""
    ap = argparse.ArgumentParser(description="Unified DXF Cleaner for Guitar Projects")
    ap.add_argument("--infile", required=True, help="Input DXF file")
    ap.add_argument("--out", required=True, help="Output DXF file")
    ap.add_argument("--min-length", type=float, default=100.0, help="Minimum contour length in mm")
    ap.add_argument("--preserve-layers", action="store_true", help="Preserve original layer names")
    ap.add_argument("--keep-open", action="store_true", help="Keep open chains (not just closed loops)")
    ap.add_argument("--tol", type=float, default=0.1, help="Endpoint tolerance in mm")
    args = ap.parse_args()

    cleaner = DXFCleaner(
        min_contour_length_mm=args.min_length,
        endpoint_tolerance=args.tol,
        keep_open_chains=args.keep_open,
    )

    result = cleaner.clean_file(
        Path(args.infile),
        Path(args.out),
        preserve_layers=args.preserve_layers,
    )

    if result.success:
        print(f"Cleaned: {result.original_entity_count} -> {result.cleaned_entity_count} entities")
        print(f"Contours found: {result.contours_found}")
        print(f"Discarded: {result.discarded_short} short, {result.discarded_open} open")
        print(f"Output: {result.output_path}")
    else:
        print(f"Error: {result.error}")
        exit(1)


if __name__ == "__main__":
    main()
