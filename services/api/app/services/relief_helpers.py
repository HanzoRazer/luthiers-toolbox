"""Relief heightmap helper functions.

Extracted from relief_kernels.py (WP-3) for god-object decomposition.
"""

from __future__ import annotations

from typing import List, Tuple

from ..schemas.relief import ReliefOverlay

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore[assignment]


def _build_slope_overlays(
    z: "np.ndarray",
    slope_deg: "np.ndarray",
    origin_x: float,
    origin_y: float,
    cell_size_xy: float,
    high_thresh: float = 45.0,
    med_thresh: float = 25.0,
) -> List[ReliefOverlay]:
    """Generate overlays marking high-slope regions for backplot visualization."""
    overlays: List[ReliefOverlay] = []
    h, w = slope_deg.shape

    for j in range(h):
        for i in range(w):
            angle = float(slope_deg[j, i])
            if angle < med_thresh:
                continue
            z_val = float(z[j, i])
            x = origin_x + i * cell_size_xy
            y = origin_y + j * cell_size_xy

            if angle >= high_thresh:
                severity = "high"
            else:
                severity = "medium"

            overlays.append(
                ReliefOverlay(
                    type="slope_hotspot",
                    x=x,
                    y=y,
                    z=z_val,
                    slope_deg=angle,
                    severity=severity,  # type: ignore[arg-type]
                    meta={},
                )
            )

    return overlays


def _clip_roi_indices(
    width: int,
    height: int,
    cell_size_xy: float,
    origin_x: float,
    origin_y: float,
    roi_min_x: float | None,
    roi_max_x: float | None,
    roi_min_y: float | None,
    roi_max_y: float | None,
) -> Tuple[int, int, int, int]:
    """Convert optional ROI in physical coordinates to grid indices."""
    # Default to full extents
    min_i = 0
    max_i = width - 1
    min_j = 0
    max_j = height - 1

    if roi_min_x is not None:
        min_i = max(min_i, int((roi_min_x - origin_x) / cell_size_xy))
    if roi_max_x is not None:
        max_i = min(max_i, int((roi_max_x - origin_x) / cell_size_xy))

    if roi_min_y is not None:
        min_j = max(min_j, int((roi_min_y - origin_y) / cell_size_xy))
    if roi_max_y is not None:
        max_j = min(max_j, int((roi_max_y - origin_y) / cell_size_xy))

    min_i = max(0, min_i)
    max_i = min(width - 1, max_i)
    min_j = max(0, min_j)
    max_j = min(height - 1, max_j)

    return min_i, max_i, min_j, max_j
