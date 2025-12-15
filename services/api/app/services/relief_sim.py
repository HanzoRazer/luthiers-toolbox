# File: services/api/app/services/relief_sim.py
# Phase 24.3: Relief Simulation Bridge Service

from __future__ import annotations

from math import hypot
from typing import List, Tuple

import numpy as np

from ..schemas.relief import ReliefMove
from ..schemas.relief_sim import (
    ReliefSimIn,
    ReliefSimOut,
    ReliefSimIssue,
    ReliefSimOverlayOut,
    ReliefSimStats,
)


def _moves_to_segments(moves: List[ReliefMove]) -> List[Tuple[float, float, float, float, float]]:
    """
    Convert moves into XY segments with depth information.
    Returns list of (x0, y0, x1, y1, z_mid).
    """
    segments: List[Tuple[float, float, float, float, float]] = []

    prev_x = None
    prev_y = None
    prev_z = None

    for mv in moves:
        if mv.x is None or mv.y is None:
            # rapid Z-only or incomplete move
            prev_x = mv.x if mv.x is not None else prev_x
            prev_y = mv.y if mv.y is not None else prev_y
            prev_z = mv.z if mv.z is not None else prev_z
            continue

        x = mv.x
        y = mv.y
        z = mv.z if mv.z is not None else prev_z

        if prev_x is not None and prev_y is not None and prev_z is not None:
            if (x, y) != (prev_x, prev_y):
                z_mid = (float(z) + float(prev_z)) / 2.0
                segments.append((prev_x, prev_y, x, y, z_mid))

        prev_x, prev_y, prev_z = x, y, z

    return segments


def _estimate_grid_bounds(
    segments: List[Tuple[float, float, float, float, float]],
    cell_size_xy: float,
    margin: float = 1.0,
):
    if not segments:
        return 0, 0, 0.0, 0.0

    xs = []
    ys = []
    for x0, y0, x1, y1, _ in segments:
        xs.extend([x0, x1])
        ys.extend([y0, y1])

    min_x = min(xs) - margin
    max_x = max(xs) + margin
    min_y = min(ys) - margin
    max_y = max(ys) + margin

    width = max(1, int((max_x - min_x) / cell_size_xy) + 1)
    height = max(1, int((max_y - min_y) / cell_size_xy) + 1)

    return width, height, min_x, min_y


def _rasterize_segments_to_grid(
    segments: List[Tuple[float, float, float, float, float]],
    cell_size_xy: float,
    origin_x: float,
    origin_y: float,
    stock_thickness: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns:
      floor_depth: 2D array of min Z (most negative) per cell
      load_accum: 2D array of accumulated load index per cell
    """
    width, height, min_x, min_y = _estimate_grid_bounds(segments, cell_size_xy)
    # Use local origin offset so arrays stay compact
    grid_origin_x = origin_x if origin_x != 0.0 else min_x
    grid_origin_y = origin_y if origin_y != 0.0 else min_y

    floor_depth = np.full((height, width), 0.0, dtype=np.float32)
    load_accum = np.zeros((height, width), dtype=np.float32)
    visited = np.zeros((height, width), dtype=bool)

    for x0, y0, x1, y1, z_mid in segments:
        seg_len = hypot(x1 - x0, y1 - y0)
        if seg_len <= 1e-6:
            continue

        # sample along segment
        steps = max(1, int(seg_len / (cell_size_xy * 0.5)))
        dz = z_mid  # approximate constant depth along segment

        for k in range(steps + 1):
            t = k / steps
            xs = x0 + (x1 - x0) * t
            ys = y0 + (y1 - y0) * t

            i = int((xs - grid_origin_x) / cell_size_xy)
            j = int((ys - grid_origin_y) / cell_size_xy)
            if i < 0 or j < 0 or i >= width or j >= height:
                continue

            # update floor_depth: we keep the minimum (most negative) Z
            current = floor_depth[j, i]
            visited[j, i] = True
            if dz < current:
                floor_depth[j, i] = dz

            # approximate local path length contribution
            # each sample contributes seg_len / steps length
            local_len = seg_len / steps
            # load index ~ |depth| * path length
            load_accum[j, i] += abs(dz) * local_len

    # Any unvisited cells should have floor_depth = 0 (no cut)
    floor_depth[~visited] = 0.0

    # thickness = stock_thickness + depth (Z negative)
    # when no cut, depth=0, thickness=stock_thickness
    return floor_depth, load_accum


def run_relief_sim_bridge(payload: ReliefSimIn) -> ReliefSimOut:
    """
    Approximate material removal & load distribution on a grid.
    Produces:
      - issues: thin floor, over depth, high load
      - overlays: load heatmap + thin floor points
    """
    segments = _moves_to_segments(payload.moves)

    if not segments:
        # No cutting, zero stats
        stats = ReliefSimStats(
            cell_count=0,
            avg_floor_thickness=payload.stock_thickness,
            min_floor_thickness=payload.stock_thickness,
            max_load_index=0.0,
            avg_load_index=0.0,
            total_removed_volume=0.0,
        )
        return ReliefSimOut(issues=[], overlays=[], stats=stats)

    floor_depth, load_accum = _rasterize_segments_to_grid(
        segments,
        cell_size_xy=payload.cell_size_xy,
        origin_x=payload.origin_x,
        origin_y=payload.origin_y,
        stock_thickness=payload.stock_thickness,
    )

    # thickness = stock_thickness + floor_depth (floor_depth <= 0)
    floor_thickness = payload.stock_thickness + floor_depth
    # removed volume ~ sum(|depth| * cell_area) over cut region
    cell_area = payload.cell_size_xy * payload.cell_size_xy
    removed_volume = float(np.sum(np.abs(np.minimum(floor_depth, 0.0))) * cell_area)

    # Normalized load index: scale so median of non-zero cells ~ 1.0
    load_flat = load_accum.flatten()
    nonzero_load = load_flat[load_flat > 1e-6]
    if nonzero_load.size > 0:
        median_load = float(np.median(nonzero_load))
        scale = 1.0 / max(median_load, 1e-6)
    else:
        scale = 1.0

    norm_load = load_accum * scale
    max_load = float(norm_load.max())
    avg_load = float(norm_load[load_accum > 1e-6].mean()) if nonzero_load.size > 0 else 0.0

    avg_floor_thickness = float(floor_thickness.mean())
    min_floor_thickness = float(floor_thickness.min())

    stats = ReliefSimStats(
        cell_count=int(floor_thickness.size),
        avg_floor_thickness=avg_floor_thickness,
        min_floor_thickness=min_floor_thickness,
        max_load_index=max_load,
        avg_load_index=avg_load,
        total_removed_volume=removed_volume,
    )

    issues: List[ReliefSimIssue] = []
    overlays: List[ReliefSimOverlayOut] = []

    h, w = floor_thickness.shape

    # produce issues + overlays
    for j in range(h):
        for i in range(w):
            thickness = float(floor_thickness[j, i])
            load_val = float(norm_load[j, i])

            if load_val <= 0.0 and thickness >= payload.stock_thickness - 1e-3:
                # untouched region
                continue

            x = payload.origin_x + i * payload.cell_size_xy
            y = payload.origin_y + j * payload.cell_size_xy
            depth = float(floor_depth[j, i])

            # Thin floor issue
            if thickness < payload.min_floor_thickness:
                severity = "high" if thickness < payload.min_floor_thickness * 0.7 else "medium"
                issues.append(
                    ReliefSimIssue(
                        type="thin_floor",
                        severity=severity,  # type: ignore[arg-type]
                        x=x,
                        y=y,
                        z=depth,
                        note=f"Floor thickness {thickness:.2f} {payload.units} below threshold {payload.min_floor_thickness:.2f}",
                        extra_time_s=None,
                        meta={"thickness": thickness},
                    )
                )
                overlays.append(
                    ReliefSimOverlayOut(
                        type="thin_floor_zone",
                        x=x,
                        y=y,
                        z=depth,
                        intensity=None,
                        severity=severity,  # type: ignore[arg-type]
                        meta={"thickness": thickness},
                    )
                )

            # High-load hotspots
            if load_val >= payload.med_load_index:
                if load_val >= payload.high_load_index:
                    sev = "high"
                else:
                    sev = "medium"

                issues.append(
                    ReliefSimIssue(
                        type="high_load",
                        severity=sev,  # type: ignore[arg-type]
                        x=x,
                        y=y,
                        z=depth,
                        note=f"High load index {load_val:.2f}",
                        extra_time_s=None,
                        meta={"load_index": load_val},
                    )
                )

            # Always emit a load hotspot overlay for non-zero load
            if load_val > 0.0:
                # clamp to [0,1.5] then normalize to [0,1]
                intensity = min(load_val, 1.5) / 1.5
                overlays.append(
                    ReliefSimOverlayOut(
                        type="load_hotspot",
                        x=x,
                        y=y,
                        z=depth,
                        intensity=float(intensity),
                        severity=None,
                        meta={"load_index": load_val},
                    )
                )

    return ReliefSimOut(issues=issues, overlays=overlays, stats=stats)
