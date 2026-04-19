#!/usr/bin/env python3
"""
DXF Consolidator — Convert raw vectorizer LINE dumps to clean LWPOLYLINE output

Problem: Vectorizer outputs 300K-600K LINE entities across hundreds of numbered
layers (contour_0, contour_1, ...). Each contour should be ONE closed LWPOLYLINE,
not thousands of LINE segments.

This module:
1. Reads raw vectorizer DXF (LINE entities on contour_N layers)
2. Consolidates LINE chains into LWPOLYLINE per layer
3. Area-ranks contours by bounding box
4. Promotes largest to BODY_OUTLINE layer
5. Classifies children inside body as CAVITY
6. Outputs clean DXF with semantic layers

Author: Production Shop
Date: 2026-04-16
Sprint: 9 — InstrumentBodyGenerator
"""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import ezdxf
from ezdxf.entities import Line


@dataclass
class ContourInfo:
    """Metadata for a single contour layer."""
    layer_name: str
    lines: List[Line] = field(default_factory=list)
    points: List[Tuple[float, float]] = field(default_factory=list)
    min_x: float = float('inf')
    max_x: float = float('-inf')
    min_y: float = float('inf')
    max_y: float = float('-inf')
    is_closed: bool = False

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)

    def contains(self, other: 'ContourInfo') -> bool:
        """Check if this contour's bounding box contains another."""
        return (self.min_x <= other.min_x and self.max_x >= other.max_x and
                self.min_y <= other.min_y and self.max_y >= other.max_y)


@dataclass
class ConsolidationResult:
    """Result of DXF consolidation."""
    input_lines: int
    input_layers: int
    output_polylines: int
    body_outline_layer: str
    cavity_layers: List[str]
    discarded_layers: List[str]
    output_path: str


class DxfConsolidator:
    """Consolidates raw LINE DXF into clean LWPOLYLINE output."""

    def __init__(
        self,
        min_area_mm2: float = 500.0,      # Raised: filter small noise
        cavity_min_area_mm2: float = 200.0,  # Raised: only significant cavities
    ):
        """
        Args:
            min_area_mm2: Minimum bounding box area to keep a contour
            cavity_min_area_mm2: Minimum area for cavity classification
        """
        self.min_area_mm2 = min_area_mm2
        self.cavity_min_area_mm2 = cavity_min_area_mm2

    def consolidate(self, input_path: str, output_path: str) -> ConsolidationResult:
        """
        Consolidate raw LINE DXF to clean LWPOLYLINE output.

        Args:
            input_path: Path to raw vectorizer DXF
            output_path: Path for consolidated output

        Returns:
            ConsolidationResult with statistics
        """
        # Step 1: Load and group by layer
        contours = self._load_contours(input_path)
        input_lines = sum(len(c.lines) for c in contours.values())
        input_layers = len(contours)

        print(f"Loaded: {input_lines:,} lines across {input_layers} layers")

        # Step 2: Build point chains for each contour
        for layer, contour in contours.items():
            self._build_point_chain(contour)

        # Step 3: Area-rank and classify
        ranked = sorted(contours.values(), key=lambda c: c.area, reverse=True)

        # Largest = body outline
        body = ranked[0] if ranked else None

        # Identify cavities (inside body, above min area)
        cavities = []
        discarded = []

        for contour in ranked[1:]:
            if contour.area < self.min_area_mm2:
                discarded.append(contour.layer_name)
            elif body and body.contains(contour) and contour.area >= self.cavity_min_area_mm2:
                cavities.append(contour)
            else:
                discarded.append(contour.layer_name)

        print(f"Classification: 1 body, {len(cavities)} cavities, {len(discarded)} discarded")

        # Step 4: Write output
        self._write_output(output_path, body, cavities)

        return ConsolidationResult(
            input_lines=input_lines,
            input_layers=input_layers,
            output_polylines=1 + len(cavities),
            body_outline_layer="BODY_OUTLINE",
            cavity_layers=[f"CAVITY_{i}" for i in range(len(cavities))],
            discarded_layers=discarded,
            output_path=output_path,
        )

    def _load_contours(self, path: str) -> Dict[str, ContourInfo]:
        """Load LINE entities grouped by layer."""
        doc = ezdxf.readfile(path)
        msp = doc.modelspace()

        contours: Dict[str, ContourInfo] = {}

        for entity in msp:
            if entity.dxftype() != "LINE":
                continue

            layer = entity.dxf.layer
            if layer not in contours:
                contours[layer] = ContourInfo(layer_name=layer)

            c = contours[layer]
            c.lines.append(entity)

            # Update bounds
            for pt in [entity.dxf.start, entity.dxf.end]:
                c.min_x = min(c.min_x, pt.x)
                c.max_x = max(c.max_x, pt.x)
                c.min_y = min(c.min_y, pt.y)
                c.max_y = max(c.max_y, pt.y)

        return contours

    def _build_point_chain(self, contour: ContourInfo) -> None:
        """Convert LINE entities to ordered point chain."""
        if not contour.lines:
            return

        # Build adjacency map
        # Each point maps to list of (other_point, line_index)
        adj: Dict[Tuple[float, float], List[Tuple[Tuple[float, float], int]]] = defaultdict(list)

        for i, line in enumerate(contour.lines):
            p1 = (round(line.dxf.start.x, 3), round(line.dxf.start.y, 3))
            p2 = (round(line.dxf.end.x, 3), round(line.dxf.end.y, 3))
            adj[p1].append((p2, i))
            adj[p2].append((p1, i))

        # Find a starting point (prefer endpoint with only one connection)
        start = None
        for pt, connections in adj.items():
            if len(connections) == 1:
                start = pt
                break

        if start is None and adj:
            start = next(iter(adj.keys()))

        if start is None:
            return

        # Walk the chain
        visited_lines = set()
        chain = [start]
        current = start

        while True:
            connections = adj.get(current, [])
            next_pt = None

            for pt, line_idx in connections:
                if line_idx not in visited_lines:
                    visited_lines.add(line_idx)
                    next_pt = pt
                    break

            if next_pt is None:
                break

            chain.append(next_pt)
            current = next_pt

        contour.points = chain

        # Check if closed
        if len(chain) >= 3:
            dist = ((chain[0][0] - chain[-1][0])**2 + (chain[0][1] - chain[-1][1])**2)**0.5
            contour.is_closed = dist < 1.0  # Within 1mm

    def _write_output(
        self,
        output_path: str,
        body: Optional[ContourInfo],
        cavities: List[ContourInfo],
    ) -> None:
        """Write consolidated DXF with semantic layers."""
        # Use R2000 for LWPOLYLINE support (R12 only has LINE)
        doc = ezdxf.new("R2000")
        msp = doc.modelspace()

        # Add layers
        doc.layers.add("BODY_OUTLINE", dxfattribs={"color": 1})  # Red
        doc.layers.add("CENTERLINE", dxfattribs={"color": 5})    # Blue

        for i in range(len(cavities)):
            doc.layers.add(f"CAVITY_{i}", dxfattribs={"color": 3})  # Green

        # Write body outline
        if body and body.points:
            self._write_polyline(msp, body.points, "BODY_OUTLINE", body.is_closed)

            # Add centerline
            center_x = (body.min_x + body.max_x) / 2
            msp.add_line(
                (center_x, body.min_y),
                (center_x, body.max_y),
                dxfattribs={"layer": "CENTERLINE"}
            )

            print(f"Body: {body.width:.0f}x{body.height:.0f}mm, {len(body.points)} pts, closed={body.is_closed}")

        # Write cavities
        for i, cavity in enumerate(cavities):
            if cavity.points:
                self._write_polyline(msp, cavity.points, f"CAVITY_{i}", cavity.is_closed)
                print(f"Cavity {i}: {cavity.width:.0f}x{cavity.height:.0f}mm, {len(cavity.points)} pts")

        doc.saveas(output_path)
        print(f"Saved: {output_path}")

    def _write_polyline(
        self,
        msp,
        points: List[Tuple[float, float]],
        layer: str,
        closed: bool,
    ) -> None:
        """Write points as LWPOLYLINE."""
        if len(points) < 2:
            return

        # Round points for precision
        rounded = [(round(p[0], 3), round(p[1], 3)) for p in points]

        # Write as LWPOLYLINE (requires R2000+)
        msp.add_lwpolyline(
            rounded,
            close=closed,
            dxfattribs={"layer": layer}
        )


def consolidate_dxf(input_path: str, output_path: str = None) -> ConsolidationResult:
    """Convenience function to consolidate a DXF file."""
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_consolidated{ext}"

    consolidator = DxfConsolidator()
    return consolidator.consolidate(input_path, output_path)


# ─── CLI ──────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import sys

    test_files = [
        r"C:\Users\thepr\Downloads\luthiers-toolbox\benchmark_outputs\plano cuatro venezolano_restored.dxf",
        r"C:\Users\thepr\Downloads\luthiers-toolbox\benchmark_exports\melody_maker_body.dxf",
        r"C:\Users\thepr\Downloads\luthiers-toolbox\benchmark_exports\dreadnought_body.dxf",
    ]

    print("=== DXF Consolidator ===\n")

    for input_path in test_files:
        if not os.path.exists(input_path):
            print(f"Not found: {input_path}\n")
            continue

        name = os.path.basename(input_path)
        output_path = os.path.join(
            os.path.dirname(__file__),
            f"{os.path.splitext(name)[0]}_consolidated.dxf"
        )

        print(f"Processing: {name}")
        try:
            result = consolidate_dxf(input_path, output_path)
            print(f"  {result.input_lines:,} lines → {result.output_polylines} polylines")
            print(f"  Body: {result.body_outline_layer}")
            print(f"  Cavities: {len(result.cavity_layers)}")
            print(f"  Discarded: {len(result.discarded_layers)} layers")
        except Exception as e:
            print(f"  Error: {e}")
        print()
