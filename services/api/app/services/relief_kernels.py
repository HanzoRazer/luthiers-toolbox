"""Relief carving kernels for heightmap processing and toolpath generation."""

from __future__ import annotations

from math import sqrt, hypot
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image

from ..schemas.relief import (
    ReliefMapFromHeightfieldIn,
    ReliefMapFromHeightfieldOut,
    ReliefCellStats,
    ReliefRasterToolpathIn,
    ReliefFinishingIn,
    ReliefMove,
    ReliefOverlay,
    ReliefToolpathOut,
    ReliefToolpathStats,
)


def _load_heightmap(path: Path) -> np.ndarray:
    """Load a grayscale heightmap (0..255) as a numpy array of floats in [0,1]."""
    img = Image.open(path).convert("L")
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return arr


def _apply_smoothing(arr: np.ndarray, sigma: float) -> np.ndarray:
    """Apply separable box blur approximation for Gaussian smoothing."""
    if sigma <= 0:
        return arr

    # Use a 1D box kernel of radius ~sigma
    radius = max(1, int(round(sigma)))
    size = radius * 2 + 1
    kernel = np.ones(size, dtype=np.float32) / size

    # Blur rows
    tmp = np.apply_along_axis(
        lambda m: np.convolve(m, kernel, mode="same"), axis=1, arr=arr
    )
    # Blur columns
    out = np.apply_along_axis(
        lambda m: np.convolve(m, kernel, mode="same"), axis=0, arr=tmp
    )
    return out


def load_heightmap_to_map(payload: ReliefMapFromHeightfieldIn) -> ReliefMapFromHeightfieldOut:
    """Convert a grayscale heightmap into a Z grid with physical units."""
    path = Path(payload.heightmap_path)
    if not path.exists():
        raise FileNotFoundError(f"Heightmap not found: {path}")

    gray = _load_heightmap(path)
    if payload.smooth_sigma > 0:
        gray = _apply_smoothing(gray, payload.smooth_sigma)

    # Map [0,1] -> [z_min, z_max] (note: z_max may be below z_min)
    z_min = float(payload.z_min)
    z_max = float(payload.z_max)
    z = z_min + (z_max - z_min) * gray

    height, width = z.shape

    z_min_grid = float(z.min())
    z_max_grid = float(z.max())
    z_mean = float(z.mean())
    z_std = float(z.std())

    stats = ReliefCellStats(
        width=width,
        height=height,
        z_min=z_min_grid,
        z_max=z_max_grid,
        z_mean=z_mean,
        z_std=z_std,
    )

    # Represent as nested Python lists for Pydantic
    z_grid_list: List[List[float]] = z.tolist()

    return ReliefMapFromHeightfieldOut(
        width=width,
        height=height,
        origin_x=0.0,
        origin_y=0.0,
        cell_size_xy=payload.sample_pitch_xy,
        z_min=z_min_grid,
        z_max=z_max_grid,
        z_grid=z_grid_list,
        stats=stats,
        units=payload.units,
    )


def _compute_xy_slope_deg(
    z: np.ndarray, cell_size_xy: float
) -> np.ndarray:
    """Compute approximate slope angle (degrees) at each cell using central differences."""
    # Central differences for gradient
    dz_dx = np.zeros_like(z)
    dz_dy = np.zeros_like(z)

    dz_dx[:, 1:-1] = (z[:, 2:] - z[:, :-2]) / (2 * cell_size_xy)
    dz_dx[:, 0] = (z[:, 1] - z[:, 0]) / cell_size_xy
    dz_dx[:, -1] = (z[:, -1] - z[:, -2]) / cell_size_xy

    dz_dy[1:-1, :] = (z[2:, :] - z[:-2, :]) / (2 * cell_size_xy)
    dz_dy[0, :] = (z[1, :] - z[0, :]) / cell_size_xy
    dz_dy[-1, :] = (z[-1, :] - z[-2, :]) / cell_size_xy

    mag = np.sqrt(dz_dx**2 + dz_dy**2)
    # Slope angle in radians, then degrees
    slope_rad = np.arctan(mag)
    slope_deg = np.degrees(slope_rad)
    return slope_deg


# WP-3: _build_slope_overlays and _clip_roi_indices extracted to relief_helpers.py
from .relief_helpers import (  # noqa: E402
    _build_slope_overlays as _build_slope_overlays,
    _clip_roi_indices as _clip_roi_indices,
)


def plan_relief_roughing(payload: ReliefRasterToolpathIn) -> ReliefToolpathOut:
    """Generate simple raster roughing over the relief map with multiple Z passes."""
    z_grid = np.asarray(payload.z_grid, dtype=np.float32)
    h, w = z_grid.shape

    min_i, max_i, min_j, max_j = _clip_roi_indices(
        w,
        h,
        payload.cell_size_xy,
        payload.origin_x,
        payload.origin_y,
        payload.roi_min_x,
        payload.roi_max_x,
        payload.roi_min_y,
        payload.roi_max_y,
    )

    # Rough down to the minimum Z in the ROI region
    roi_z = z_grid[min_j : max_j + 1, min_i : max_i + 1]
    z_min = float(roi_z.min())
    safe_z = payload.safe_z
    stepdown = abs(payload.stepdown)

    # Depths for passes: [safe_z -> z_level_0, ..., z_min]
    passes: List[float] = []
    current = 0.0
    while current > z_min:
        current -= stepdown
        if current < z_min:
            current = z_min
        passes.append(current)

    moves: List[ReliefMove] = []
    total_xy = 0.0
    feed_xy = payload.feed_xy

    # Simple serpentine raster in Y (rows) at each depth
    for depth in passes:
        # Rapid to safe above start of stripe
        y0 = payload.origin_y + min_j * payload.cell_size_xy
        x_start = payload.origin_x + min_i * payload.cell_size_xy
        moves.append(ReliefMove(code="G0", z=safe_z))
        moves.append(ReliefMove(code="G0", x=x_start, y=y0))
        moves.append(ReliefMove(code="G1", z=depth, f=payload.feed_z))

        direction = 1
        for j in range(min_j, max_j + 1):
            y = payload.origin_y + j * payload.cell_size_xy
            if direction == 1:
                i_range = range(min_i, max_i + 1)
            else:
                i_range = range(max_i, min_i - 1, -1)

            x_prev: float | None = None
            y_prev: float | None = None
            for i in i_range:
                x = payload.origin_x + i * payload.cell_size_xy
                moves.append(ReliefMove(code="G1", x=x, y=y, z=depth, f=feed_xy))

                if x_prev is not None and y_prev is not None:
                    total_xy += hypot(x - x_prev, y - y_prev)

                x_prev, y_prev = x, y

            direction *= -1

        # Retract at end of depth pass
        moves.append(ReliefMove(code="G0", z=safe_z))

    est_time_s = total_xy / max(feed_xy, 1e-6) * 60.0  # feed in units/min

    slope_deg = _compute_xy_slope_deg(z_grid, payload.cell_size_xy)
    overlays = _build_slope_overlays(
        z=z_grid,
        slope_deg=slope_deg,
        cell_size_xy=payload.cell_size_xy,
        origin_x=payload.origin_x,
        origin_y=payload.origin_y,
        high_thresh=45.0,
        med_thresh=25.0,
    )

    stats = ReliefToolpathStats(
        move_count=len(moves),
        length_xy=total_xy,
        min_z=float(z_min),
        max_z=0.0,
        est_time_s=est_time_s,
    )

    return ReliefToolpathOut(
        moves=moves,
        overlays=overlays,
        stats=stats,
        units=payload.units,
    )


def _map_slope_to_scallop(
    slope_deg: float,
    slope_low: float,
    slope_high: float,
    scallop_min: float,
    scallop_max: float,
) -> float:
    """Map local slope angle (deg) to a scallop height in [scallop_min, scallop_max]."""
    if slope_deg <= slope_low:
        return scallop_max
    if slope_deg >= slope_high:
        return scallop_min
    t = (slope_deg - slope_low) / max(slope_high - slope_low, 1e-6)
    return scallop_max + (scallop_min - scallop_max) * t


def plan_relief_finishing(payload: ReliefFinishingIn) -> ReliefToolpathOut:
    """Generate finishing raster toolpath with scallop-based stepover for ball nose."""
    z_grid = np.asarray(payload.z_grid, dtype=np.float32)
    h, w = z_grid.shape

    min_i, max_i, min_j, max_j = _clip_roi_indices(
        w,
        h,
        payload.cell_size_xy,
        payload.origin_x,
        payload.origin_y,
        payload.roi_min_x,
        payload.roi_max_x,
        payload.roi_min_y,
        payload.roi_max_y,
    )

    safe_z = payload.safe_z
    tool_radius = payload.tool_d / 2.0
    safe_margin = 0.2  # mm
    moves: List[ReliefMove] = []
    total_xy = 0.0
    min_z = float(z_grid[min_j : max_j + 1, min_i : max_i + 1].min())
    max_z = float(z_grid[min_j : max_j + 1, min_i : max_i + 1].max())
    feed_xy = payload.feed_xy

    # Compute global slope map (needed for both dynamic and overlay generation)
    slope_deg_grid = _compute_xy_slope_deg(z_grid, payload.cell_size_xy)

    if not payload.use_dynamic_scallop:
        # Original uniform scallop approach
        scallop = max(payload.scallop_height, 1e-6)
        stepover_approx = sqrt(max(8.0 * tool_radius * scallop, 1e-6))
        pitch = max(stepover_approx, payload.cell_size_xy)
        step_samples = max(int(round(pitch / payload.cell_size_xy)), 1)

        if payload.pattern == "RasterX":
            row_indices = range(min_j, max_j + 1, step_samples)
        else:
            col_indices = range(min_i, max_i + 1, step_samples)
    else:
        # Dynamic scallop: vary stepover by local slope
        def build_row_indices():
            """Build adaptive row indices based on average slope per row."""
            indices = []
            j = min_j
            while j <= max_j:
                indices.append(j)
                # Compute average slope for this row
                row_slopes = slope_deg_grid[j, min_i : max_i + 1]
                avg_slope = float(np.mean(row_slopes))
                # Map slope to scallop
                scallop_here = _map_slope_to_scallop(
                    avg_slope,
                    payload.slope_low_deg,
                    payload.slope_high_deg,
                    payload.scallop_min,
                    payload.scallop_max,
                )
                # Compute stepover
                stepover_here = sqrt(max(8.0 * tool_radius * scallop_here, 1e-6))
                pitch_here = max(stepover_here, payload.cell_size_xy)
                step_samples_here = max(int(round(pitch_here / payload.cell_size_xy)), 1)
                j += step_samples_here
            return indices

        def build_col_indices():
            """Build adaptive column indices based on average slope per column."""
            indices = []
            i = min_i
            while i <= max_i:
                indices.append(i)
                col_slopes = slope_deg_grid[min_j : max_j + 1, i]
                avg_slope = float(np.mean(col_slopes))
                scallop_here = _map_slope_to_scallop(
                    avg_slope,
                    payload.slope_low_deg,
                    payload.slope_high_deg,
                    payload.scallop_min,
                    payload.scallop_max,
                )
                stepover_here = sqrt(max(8.0 * tool_radius * scallop_here, 1e-6))
                pitch_here = max(stepover_here, payload.cell_size_xy)
                step_samples_here = max(int(round(pitch_here / payload.cell_size_xy)), 1)
                i += step_samples_here
            return indices

        if payload.pattern == "RasterX":
            row_indices = build_row_indices()
        else:
            col_indices = build_col_indices()

    # Generate toolpath moves
    if payload.pattern == "RasterX":
        # Scan in X, step in Y
        for idx, j in enumerate(row_indices):
            y = payload.origin_y + j * payload.cell_size_xy
            # Rapid up high
            moves.append(ReliefMove(code="G0", z=safe_z))

            # Start X depending on direction
            direction = 1 if idx % 2 == 0 else -1
            if direction == 1:
                start_i = min_i
                end_i = max_i
                i_range = range(min_i, max_i + 1)
            else:
                start_i = max_i
                end_i = min_i
                i_range = range(max_i, min_i - 1, -1)

            x_start = payload.origin_x + start_i * payload.cell_size_xy
            # Move to XY above start
            moves.append(ReliefMove(code="G0", x=x_start, y=y))

            # Plunge near local surface Z (take cell at start)
            z_plunge = float(z_grid[j, start_i]) + safe_margin
            moves.append(ReliefMove(code="G1", z=z_plunge, f=payload.feed_z))

            x_prev: float | None = None
            y_prev: float | None = None
            for i in i_range:
                x = payload.origin_x + i * payload.cell_size_xy
                z_target = float(z_grid[j, i])
                moves.append(ReliefMove(code="G1", x=x, y=y, z=z_target, f=feed_xy))

                if x_prev is not None and y_prev is not None:
                    total_xy += hypot(x - x_prev, y - y_prev)
                x_prev, y_prev = x, y

            moves.append(ReliefMove(code="G0", z=safe_z))
    else:
        # RasterY (orthogonal)
        for idx, i in enumerate(col_indices):
            x = payload.origin_x + i * payload.cell_size_xy
            moves.append(ReliefMove(code="G0", z=safe_z))

            direction = 1 if idx % 2 == 0 else -1
            if direction == 1:
                start_j = min_j
                end_j = max_j
                j_range = range(min_j, max_j + 1)
            else:
                start_j = max_j
                end_j = min_j
                j_range = range(max_j, min_j - 1, -1)

            y_start = payload.origin_y + start_j * payload.cell_size_xy
            moves.append(ReliefMove(code="G0", x=x, y=y_start))

            z_plunge = float(z_grid[start_j, i]) + safe_margin
            moves.append(ReliefMove(code="G1", z=z_plunge, f=payload.feed_z))

            x_prev: float | None = None
            y_prev: float | None = None
            for j in j_range:
                y = payload.origin_y + j * payload.cell_size_xy
                z_target = float(z_grid[j, i])
                moves.append(ReliefMove(code="G1", x=x, y=y, z=z_target, f=feed_xy))
                if x_prev is not None and y_prev is not None:
                    total_xy += hypot(x - x_prev, y - y_prev)
                x_prev, y_prev = x, y

            moves.append(ReliefMove(code="G0", z=safe_z))

    est_time_s = total_xy / max(feed_xy, 1e-6) * 60.0

    overlays = _build_slope_overlays(
        z=z_grid,
        slope_deg=slope_deg_grid,
        cell_size_xy=payload.cell_size_xy,
        origin_x=payload.origin_x,
        origin_y=payload.origin_y,
        high_thresh=50.0,
        med_thresh=30.0,
    )

    stats = ReliefToolpathStats(
        move_count=len(moves),
        length_xy=total_xy,
        min_z=min_z,
        max_z=max_z,
        est_time_s=est_time_s,
    )

    return ReliefToolpathOut(
        moves=moves,
        overlays=overlays,
        stats=stats,
        units=payload.units,
    )
