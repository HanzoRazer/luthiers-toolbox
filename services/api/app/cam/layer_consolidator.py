#!/usr/bin/env python3
"""
Layer-Aware DXF Consolidator — Preserve existing layer structure

Consolidates LINE chains to LWPOLYLINE within each layer, preserving
semantic layer names (BODY, ANNOTATION, TITLE_BLOCK, etc.).

Includes parallel-line deduplication for BODY layers: removes inner
duplicate contours offset by binding thickness (2-6mm).

Author: Production Shop
Date: 2026-04-17
"""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import ezdxf


@dataclass
class LayerConsolidationResult:
    """Result of layer-aware consolidation."""
    input_lines: int
    input_layers: int
    output_polylines: int
    duplicates_removed: int
    layer_stats: Dict[str, Tuple[int, int]]  # layer -> (input_lines, output_polylines)
    output_path: str


def _chain_bounds(chain: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    """Return (min_x, min_y, max_x, max_y) for a point chain."""
    xs = [p[0] for p in chain]
    ys = [p[1] for p in chain]
    return min(xs), min(ys), max(xs), max(ys)


def _deduplicate_parallel_contours(
    chains: List[List[Tuple[float, float]]],
    offset_min_mm: float = 2.0,
    offset_max_mm: float = 6.0,
    size_tolerance: float = 0.02,
) -> Tuple[List[List[Tuple[float, float]]], int]:
    """
    Remove inner duplicate contours offset by binding thickness.

    Compares bounding boxes: if two contours have nearly identical dimensions
    and one is inset by 2-6mm (binding thickness), keep only the outer one.

    Returns:
        (filtered_chains, removed_count)
    """
    if len(chains) < 2:
        return chains, 0

    # Compute bounds for each chain
    bounds = [_chain_bounds(c) for c in chains]
    dims = [(b[2] - b[0], b[3] - b[1]) for b in bounds]  # (width, height)

    keep = [True] * len(chains)
    removed = 0

    for i in range(len(chains)):
        if not keep[i]:
            continue
        for j in range(len(chains)):
            if i == j or not keep[j]:
                continue

            w_i, h_i = dims[i]
            w_j, h_j = dims[j]

            # Check if dimensions are similar (within tolerance)
            if w_i == 0 or h_i == 0:
                continue
            w_diff = abs(w_i - w_j) / max(w_i, w_j)
            h_diff = abs(h_i - h_j) / max(h_i, h_j)

            if w_diff > size_tolerance or h_diff > size_tolerance:
                continue

            # Check offset distance (is one inset from the other?)
            b_i, b_j = bounds[i], bounds[j]
            offsets = [
                b_j[0] - b_i[0],  # left inset
                b_i[2] - b_j[2],  # right inset
                b_j[1] - b_i[1],  # bottom inset
                b_i[3] - b_j[3],  # top inset
            ]

            # If j is consistently inset from i by binding thickness, remove j
            if all(offset_min_mm <= off <= offset_max_mm for off in offsets):
                keep[j] = False
                removed += 1

    return [c for c, k in zip(chains, keep) if k], removed


class LayerConsolidator:
    """Consolidates LINE chains to LWPOLYLINE while preserving layer structure."""

    def __init__(
        self,
        precision: int = 1,
        close_tolerance_mm: float = 2.0,
        dedupe_body_layer: bool = True,
    ):
        """
        Args:
            precision: Decimal places for point matching (default 1 = 0.1mm)
            close_tolerance_mm: Max gap to consider chain closed
            dedupe_body_layer: Remove parallel duplicate contours on BODY layer
        """
        self.precision = precision
        self.close_tolerance = close_tolerance_mm
        self.dedupe_body = dedupe_body_layer

    def consolidate(
        self,
        input_path: str,
        output_path: str,
        body_layer_names: Optional[List[str]] = None,
    ) -> LayerConsolidationResult:
        """
        Consolidate LINE entities to LWPOLYLINE, preserving layer names.

        Args:
            input_path: Path to input DXF
            output_path: Path for output DXF
            body_layer_names: Layer names to apply deduplication (default: ["BODY"])

        Returns:
            LayerConsolidationResult with statistics
        """
        if body_layer_names is None:
            body_layer_names = ["BODY", "BODY_OUTLINE"]

        doc = ezdxf.readfile(input_path)
        msp = doc.modelspace()

        # Group lines by layer
        layer_lines: Dict[str, List] = defaultdict(list)
        for e in msp:
            if e.dxftype() == "LINE":
                layer_lines[e.dxf.layer].append(e)

        input_lines = sum(len(lines) for lines in layer_lines.values())

        # Create output document
        out_doc = ezdxf.new("R2000")
        out_msp = out_doc.modelspace()

        layer_stats = {}
        total_polylines = 0
        total_removed = 0

        for layer_name, lines in layer_lines.items():
            # Copy layer properties if not already present
            if layer_name not in out_doc.layers:
                try:
                    src_layer = doc.layers.get(layer_name)
                    out_doc.layers.add(
                        layer_name,
                        dxfattribs={"color": src_layer.color if src_layer else 7}
                    )
                except Exception:
                    out_doc.layers.add(layer_name)

            # Find all connected chains
            chains = self._find_all_chains(lines)

            # Deduplicate parallel contours on body layers
            removed = 0
            if self.dedupe_body and layer_name in body_layer_names:
                chains, removed = _deduplicate_parallel_contours(chains)
                total_removed += removed

            # Write each chain as LWPOLYLINE
            for chain in chains:
                if len(chain) < 2:
                    continue

                dist = (
                    (chain[0][0] - chain[-1][0])**2 +
                    (chain[0][1] - chain[-1][1])**2
                )**0.5
                closed = dist < self.close_tolerance

                out_msp.add_lwpolyline(
                    chain,
                    close=closed,
                    dxfattribs={"layer": layer_name}
                )
                total_polylines += 1

            layer_stats[layer_name] = (len(lines), len(chains))

        out_doc.saveas(output_path)

        return LayerConsolidationResult(
            input_lines=input_lines,
            input_layers=len(layer_lines),
            output_polylines=total_polylines,
            duplicates_removed=total_removed,
            layer_stats=layer_stats,
            output_path=output_path,
        )

    def _find_all_chains(self, lines: List) -> List[List[Tuple[float, float]]]:
        """Find all connected chains in a set of LINE entities."""
        if not lines:
            return []

        adj: Dict[Tuple[float, float], List[Tuple[Tuple[float, float], int]]] = defaultdict(list)

        for i, line in enumerate(lines):
            p1 = (
                round(line.dxf.start.x, self.precision),
                round(line.dxf.start.y, self.precision)
            )
            p2 = (
                round(line.dxf.end.x, self.precision),
                round(line.dxf.end.y, self.precision)
            )
            adj[p1].append((p2, i))
            adj[p2].append((p1, i))

        visited_lines = set()
        chains = []

        for start_pt in adj:
            unvisited = [
                (pt, idx) for pt, idx in adj[start_pt]
                if idx not in visited_lines
            ]
            if not unvisited:
                continue

            chain = [start_pt]
            current = start_pt

            while True:
                connections = [
                    (pt, idx) for pt, idx in adj[current]
                    if idx not in visited_lines
                ]
                if not connections:
                    break

                next_pt, line_idx = connections[0]
                visited_lines.add(line_idx)
                chain.append(next_pt)
                current = next_pt

            if len(chain) >= 2:
                chains.append(chain)

        return chains


def consolidate_preserving_layers(
    input_path: str,
    output_path: str = None,
    dedupe_body: bool = True,
) -> LayerConsolidationResult:
    """
    Consolidate a DXF while preserving layer structure.

    Args:
        input_path: Path to input DXF
        output_path: Optional output path (default: adds _consolidated suffix)
        dedupe_body: Remove parallel duplicate contours on BODY layer

    Returns:
        LayerConsolidationResult
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_consolidated{ext}"

    consolidator = LayerConsolidator(dedupe_body_layer=dedupe_body)
    return consolidator.consolidate(input_path, output_path)
