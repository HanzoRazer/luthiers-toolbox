# Patch N14.0 - Toolpath core skeleton

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ToolpathSegment:
    """
    A single linear tool motion from (x_start, y_start, z_start) to
    (x_end, y_end, z_end) at a given feed rate.
    """
    x_start_mm: float
    y_start_mm: float
    z_start_mm: float
    x_end_mm: float
    y_end_mm: float
    z_end_mm: float
    feed_mm_per_min: float


@dataclass
class ToolpathPlan:
    """
    Minimal container for the toolpaths generated for a ring's slice batch.
    """
    ring_id: int
    segments: List[ToolpathSegment] = field(default_factory=list)


def build_linear_toolpaths(
    ring_id: int,
    slices: list[dict],
    feed_mm_per_min: float,
    origin_x_mm: float = 0.0,
    origin_y_mm: float = 0.0,
    z_depth_mm: float = -1.0,
) -> ToolpathPlan:
    """
    Skeleton toolpath generator.

    N14.x final behavior:
      - Use slice geometry (start/end coordinates) derived from rosette math.
      - Respect machine envelope, jig offset, and multi-pass depths.

    N14.0 skeleton behavior:
      - Generate 1D diagonal segments based on slice index.
      - This is only for internal wiring & simulation tests.
    """
    segments: list[ToolpathSegment] = []

    for s in slices:
        idx = s.get("slice_index", 0)
        # simple placeholder "geometry": a tiny diagonal whose position
        # is a function of slice index.
        offset = float(idx) * 2.0
        x0 = origin_x_mm + offset
        y0 = origin_y_mm
        x1 = origin_x_mm + offset
        y1 = origin_y_mm + 10.0

        segments.append(
            ToolpathSegment(
                x_start_mm=x0,
                y_start_mm=y0,
                z_start_mm=0.0,
                x_end_mm=x1,
                y_end_mm=y1,
                z_end_mm=z_depth_mm,
                feed_mm_per_min=feed_mm_per_min,
            )
        )

    return ToolpathPlan(ring_id=ring_id, segments=segments)
