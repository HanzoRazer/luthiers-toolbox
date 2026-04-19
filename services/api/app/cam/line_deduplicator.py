#!/usr/bin/env python3
"""
LINE Entity Deduplicator — Remove parallel binding-offset duplicates

Removes near-duplicate LINE chains that represent binding offsets in blueprints.
Two chains are duplicates if their bounding boxes are nearly identical in size
and offset by a consistent distance (typical binding thickness 2-6mm).

Works on LINE entities only — no entity type conversion.
Preserves R12 format and Fusion 360 compatibility.

Author: Production Shop
Date: 2026-04-17
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import ezdxf

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationResult:
    """Result of LINE deduplication."""
    input_lines: int
    output_lines: int
    duplicates_removed: int
    chains_analyzed: int
    output_path: str


def _round_point(x: float, y: float, precision: int = 1) -> Tuple[float, float]:
    """Round point coordinates for matching."""
    return (round(x, precision), round(y, precision))


def _build_chains_from_lines(
    lines: List[Tuple[Tuple[float, float], Tuple[float, float], str]],
    precision: int = 1,
) -> List[List[Tuple[float, float]]]:
    """
    Build connected chains from LINE segment endpoints.

    Args:
        lines: List of (start_point, end_point, handle) tuples
        precision: Decimal places for point matching

    Returns:
        List of point chains
    """
    if not lines:
        return []

    # Build adjacency map
    adj: Dict[Tuple[float, float], List[Tuple[Tuple[float, float], int]]] = defaultdict(list)

    for i, (start, end, _) in enumerate(lines):
        p1 = _round_point(start[0], start[1], precision)
        p2 = _round_point(end[0], end[1], precision)
        adj[p1].append((p2, i))
        adj[p2].append((p1, i))

    visited_lines: Set[int] = set()
    chains = []

    for start_pt in adj:
        unvisited = [(pt, idx) for pt, idx in adj[start_pt] if idx not in visited_lines]
        if not unvisited:
            continue

        chain = [start_pt]
        current = start_pt

        while True:
            connections = [(pt, idx) for pt, idx in adj[current] if idx not in visited_lines]
            if not connections:
                break

            next_pt, line_idx = connections[0]
            visited_lines.add(line_idx)
            chain.append(next_pt)
            current = next_pt

        if len(chain) >= 2:
            chains.append(chain)

    return chains


def _chain_bounds(chain: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    """Return (min_x, min_y, max_x, max_y) for a point chain."""
    xs = [p[0] for p in chain]
    ys = [p[1] for p in chain]
    return min(xs), min(ys), max(xs), max(ys)


def _find_duplicate_chains(
    chains: List[List[Tuple[float, float]]],
    offset_tolerance_mm: float = 6.0,
    size_tolerance_mm: float = 5.0,
) -> Set[int]:
    """
    Find indices of duplicate chains that should be removed.

    Two chains are duplicates if:
    1. Their bounding boxes have nearly identical dimensions (< size_tolerance)
    2. One is consistently inset from the other by binding thickness (2-6mm)

    Returns indices of inner (smaller) chains to remove.
    """
    if len(chains) < 2:
        return set()

    bounds = [_chain_bounds(c) for c in chains]
    dims = [(b[2] - b[0], b[3] - b[1]) for b in bounds]  # (width, height)

    to_remove: Set[int] = set()

    for i in range(len(chains)):
        if i in to_remove:
            continue
        for j in range(len(chains)):
            if i == j or j in to_remove:
                continue

            w_i, h_i = dims[i]
            w_j, h_j = dims[j]

            # Skip tiny or degenerate chains
            if w_i < 1 or h_i < 1 or w_j < 1 or h_j < 1:
                continue

            # Check if dimensions are similar (within tolerance)
            w_diff = abs(w_i - w_j)
            h_diff = abs(h_i - h_j)

            if w_diff > size_tolerance_mm or h_diff > size_tolerance_mm:
                continue

            # Check offset distance (is one inset from the other?)
            b_i, b_j = bounds[i], bounds[j]

            # Calculate inset from i to j
            offsets = [
                b_j[0] - b_i[0],  # left inset
                b_i[2] - b_j[2],  # right inset
                b_j[1] - b_i[1],  # bottom inset
                b_i[3] - b_j[3],  # top inset
            ]

            # If j is consistently inset from i by binding thickness, remove j
            min_offset = 2.0  # Minimum binding thickness
            if all(min_offset <= off <= offset_tolerance_mm for off in offsets):
                to_remove.add(j)
                logger.debug(f"Marking chain {j} as duplicate of {i} (offset ~{sum(offsets)/4:.1f}mm)")

    return to_remove


def deduplicate_parallel_lines(
    input_path: str,
    output_path: str,
    offset_tolerance_mm: float = 6.0,
    size_tolerance_mm: float = 5.0,
    target_layers: Optional[List[str]] = None,
) -> DeduplicationResult:
    """
    Remove near-duplicate LINE chains that represent binding offsets.

    Two chains are duplicates if their bounding boxes are nearly identical
    in size (< size_tolerance) and offset by a consistent distance
    (< offset_tolerance, typical binding thickness 2-6mm).

    Keep the outer (larger bounding box) chain, discard the inner.
    Works on LINE entities only — no entity type conversion.
    Preserves R12 format and Fusion 360 compatibility.

    Args:
        input_path: Path to input DXF (R12 with LINE entities)
        output_path: Path for output DXF
        offset_tolerance_mm: Maximum offset to consider as binding duplicate (default 6mm)
        size_tolerance_mm: Maximum dimension difference for size matching (default 5mm)
        target_layers: Layer names to apply deduplication (default: ["BODY", "BODY_OUTLINE"])

    Returns:
        DeduplicationResult with statistics
    """
    if target_layers is None:
        target_layers = ["BODY", "BODY_OUTLINE"]

    doc = ezdxf.readfile(input_path)
    msp = doc.modelspace()

    # Collect LINE entities by layer
    layer_lines: Dict[str, List[Tuple[Tuple[float, float], Tuple[float, float], str]]] = defaultdict(list)
    all_line_handles: Set[str] = set()

    for entity in msp:
        if entity.dxftype() == "LINE":
            layer = entity.dxf.layer
            start = (entity.dxf.start.x, entity.dxf.start.y)
            end = (entity.dxf.end.x, entity.dxf.end.y)
            handle = entity.dxf.handle
            layer_lines[layer].append((start, end, handle))
            all_line_handles.add(handle)

    input_lines = len(all_line_handles)
    handles_to_remove: Set[str] = set()
    total_chains = 0

    # Process target layers for deduplication
    for layer in target_layers:
        if layer not in layer_lines:
            continue

        lines = layer_lines[layer]
        chains = _build_chains_from_lines(lines)
        total_chains += len(chains)

        if len(chains) < 2:
            continue

        # Find duplicate chain indices
        duplicate_indices = _find_duplicate_chains(
            chains, offset_tolerance_mm, size_tolerance_mm
        )

        if not duplicate_indices:
            continue

        # Map chain indices back to line handles
        # Rebuild chain membership
        adj: Dict[Tuple[float, float], List[Tuple[Tuple[float, float], int]]] = defaultdict(list)
        for i, (start, end, handle) in enumerate(lines):
            p1 = _round_point(start[0], start[1])
            p2 = _round_point(end[0], end[1])
            adj[p1].append((p2, i))
            adj[p2].append((p1, i))

        visited_lines: Set[int] = set()
        chain_to_line_indices: List[Set[int]] = []

        for start_pt in adj:
            unvisited = [(pt, idx) for pt, idx in adj[start_pt] if idx not in visited_lines]
            if not unvisited:
                continue

            chain_line_indices: Set[int] = set()
            current = start_pt

            while True:
                connections = [(pt, idx) for pt, idx in adj[current] if idx not in visited_lines]
                if not connections:
                    break

                next_pt, line_idx = connections[0]
                visited_lines.add(line_idx)
                chain_line_indices.add(line_idx)
                current = next_pt

            if chain_line_indices:
                chain_to_line_indices.append(chain_line_indices)

        # Collect handles of lines in duplicate chains
        for chain_idx in duplicate_indices:
            if chain_idx < len(chain_to_line_indices):
                for line_idx in chain_to_line_indices[chain_idx]:
                    if line_idx < len(lines):
                        handles_to_remove.add(lines[line_idx][2])

    duplicates_removed = len(handles_to_remove)

    # Remove duplicate LINE entities
    if handles_to_remove:
        for handle in handles_to_remove:
            try:
                entity = doc.entitydb.get(handle)
                if entity:
                    msp.delete_entity(entity)
            except Exception as e:
                logger.warning(f"Failed to remove entity {handle}: {e}")

    # Save output
    doc.saveas(output_path)

    output_lines = input_lines - duplicates_removed

    logger.info(
        f"LINE deduplication: {input_lines} → {output_lines} "
        f"({duplicates_removed} duplicates removed from {total_chains} chains)"
    )

    return DeduplicationResult(
        input_lines=input_lines,
        output_lines=output_lines,
        duplicates_removed=duplicates_removed,
        chains_analyzed=total_chains,
        output_path=output_path,
    )
