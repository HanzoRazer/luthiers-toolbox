# Patch N14.0 - CNC simulation skeleton

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .cnc_toolpath import ToolpathPlan


@dataclass
class CNCSimulationResult:
    passes: int
    estimated_runtime_sec: float
    max_feed_mm_per_min: float
    envelope_ok: bool


def simulate_toolpaths(
    toolpaths: ToolpathPlan,
    default_passes: int = 1,
    feed_scaling_factor: float = 1.0,
) -> CNCSimulationResult:
    """
    Very simple runtime estimator and envelope check.

    N14.x final behavior:
      - integrate distance along all segments
      - account for multi-pass Z depths

    N14.0 skeleton behavior:
      - uses a linear heuristic: runtime ~ sum(1 / feed) with a scalar.
    """
    if not toolpaths.segments:
        return CNCSimulationResult(
            passes=0,
            estimated_runtime_sec=0.0,
            max_feed_mm_per_min=0.0,
            envelope_ok=True,
        )

    max_feed = 0.0
    heuristic_sum = 0.0

    for seg in toolpaths.segments:
        feed = seg.feed_mm_per_min
        if feed <= 0:
            continue
        if feed > max_feed:
            max_feed = feed
        heuristic_sum += 1.0 / feed

    # Just an arbitrary scaling so numbers are nonzero/nonsilly.
    estimated_runtime_sec = heuristic_sum * 1000.0 * feed_scaling_factor

    return CNCSimulationResult(
        passes=default_passes,
        estimated_runtime_sec=estimated_runtime_sec,
        max_feed_mm_per_min=max_feed,
        envelope_ok=True,
    )
