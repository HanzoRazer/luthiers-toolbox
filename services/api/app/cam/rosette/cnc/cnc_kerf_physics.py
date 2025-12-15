# Patch N14.0 - Kerf physics skeleton

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Optional


@dataclass
class KerfPhysicsResult:
    kerf_mm: float
    kerf_angle_deg: float
    drift_total_deg: float


def compute_kerf_physics(
    kerf_mm: float,
    radius_mm: float,
    tile_count: Optional[int] = None,
) -> KerfPhysicsResult:
    """
    Compute basic kerf physics for a ring.

    N14.x final behavior:
      - Use tile_count to estimate cumulative angular drift.

    N14.0 skeleton behavior:
      - If tile_count is provided, drift_total_deg = kerf_angle_deg * tile_count.
      - Otherwise drift_total_deg is set to 0.
    """
    if radius_mm <= 0:
        # avoid division by zero; treat kerf_angle as zero for skeleton
        kerf_angle_deg = 0.0
    else:
        kerf_angle_deg = (kerf_mm / radius_mm) * (180.0 / pi)

    drift_total_deg = kerf_angle_deg * tile_count if tile_count else 0.0

    return KerfPhysicsResult(
        kerf_mm=kerf_mm,
        kerf_angle_deg=kerf_angle_deg,
        drift_total_deg=drift_total_deg,
    )
