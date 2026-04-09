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
4. Convert to LWPOLYLINE for clean output

Author: Production Shop
"""

from __future__ import annotations

import argparse
import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import ezdxf
from ezdxf.entities import LWPolyline

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
            newdoc = ezdxf.new("R12")
            newmsp = newdoc.modelspace()

            # Add chains as LWPOLYLINE
            for i, chain in enumerate(kept_chains):
                points = chain.as_polyline_points()
                # Close the loop if it's a closed chain
                if chain.is_closed(self.closure_tolerance) and len(points) > 2:
                    # Don't duplicate the closing point for closed polylines
                    if points[0] != points[-1]:
                        points = points  # Keep as-is, set closed flag

                newmsp.add_lwpolyline(
                    points,
                    dxfattribs={
                        "layer": f"contour_{i}" if not preserve_layers else "body_outline",
                        "closed": chain.is_closed(self.closure_tolerance),
                    }
                )
                result.contours_found += 1

            # Add kept polylines
            for i, points in enumerate(kept_polylines):
                newmsp.add_lwpolyline(
                    points,
                    dxfattribs={
                        "layer": f"polyline_{i}" if not preserve_layers else "body_outline",
                        "closed": True,
                    }
                )
                result.contours_found += 1

            result.cleaned_entity_count = result.contours_found

            # Save output
            output_path.parent.mkdir(parents=True, exist_ok=True)
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
