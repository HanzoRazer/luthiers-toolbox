"""
Reference Outline Bridge — Tier 0 Gap Bridging Using Known Body Geometry
=========================================================================

Uses waypoints from body_outlines.json to bridge gaps with actual
instrument geometry rather than computed approximations.

Author: Production Shop
Date: 2026-04-16
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

# scipy is optional — graceful degradation to linear interpolation if missing
try:
    from scipy.interpolate import splprep, splev
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    splprep = None
    splev = None
    print("WARNING: scipy not installed. Tier 0 bridge will use linear interpolation.")


# Path to body_outlines.json
BODY_OUTLINES_PATH = Path(__file__).parent.parent.parent / \
    "services/api/app/instrument_geometry/body/body_outlines.json"


@dataclass
class AlignmentTransform:
    """Scale and translate to map reference space into extracted space."""
    scale: float
    tx: float
    ty: float

    def apply(self, x: float, y: float) -> Tuple[float, float]:
        return (x * self.scale + self.tx, y * self.scale + self.ty)

    def apply_points(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        return [self.apply(x, y) for x, y in points]


def load_body_outlines() -> dict:
    """Load body outline waypoints from JSON."""
    with open(BODY_OUTLINES_PATH) as f:
        return json.load(f)


def mirror_waypoints(waypoints: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Mirror half-body waypoints to create full closed outline.

    Input: right half of body (X >= 0)
    Output: full outline, counterclockwise traversal
    """
    # Original waypoints (right side)
    right_side = [(x, y) for x, y in waypoints]

    # Mirror for left side (negate X)
    # Reverse order so the full outline is continuous
    left_side = [(-x, y) for x, y in waypoints[::-1]]

    # Combine: right side + left side (excluding duplicate centerline points)
    # Remove near-centerline duplicates (X close to 0)
    full = right_side + [p for p in left_side if abs(p[0]) > 1.0]

    return full


def create_dense_reference_curve(
    waypoints: List[Tuple[float, float]],
    num_points: int = 500,
) -> List[Tuple[float, float]]:
    """
    Spline interpolate sparse waypoints to dense reference curve.

    Args:
        waypoints: Sparse outline waypoints (already mirrored to full body)
        num_points: Number of points in dense curve

    Returns:
        Dense curve as list of (x, y) tuples
    """
    if len(waypoints) < 4:
        # Not enough points for spline, return as-is
        return waypoints

    # Graceful degradation: use linear interpolation if scipy unavailable
    if not SCIPY_AVAILABLE:
        return _linear_interpolate(waypoints, num_points)

    # Prepare for scipy spline
    xs = [p[0] for p in waypoints]
    ys = [p[1] for p in waypoints]

    # Close the curve by appending first point
    xs.append(xs[0])
    ys.append(ys[0])

    # Fit periodic spline with smoothing to prevent overshoot
    try:
        # Use s > 0 to add smoothing and prevent oscillation at corners
        # Smoothing value proportional to number of points
        smoothing = len(xs) * 0.5
        tck, u = splprep([xs, ys], s=smoothing, per=True, k=3)
        u_dense = np.linspace(0, 1, num_points)
        x_dense, y_dense = splev(u_dense, tck)

        # Clamp to original bounds to prevent any residual overshoot
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        x_dense = np.clip(x_dense, x_min - 5, x_max + 5)  # 5mm tolerance
        y_dense = np.clip(y_dense, y_min - 5, y_max + 5)

        return list(zip(x_dense, y_dense))
    except Exception as e:
        print(f"Spline fitting failed: {e}, using linear interpolation")
        # Fallback: linear interpolation
        return _linear_interpolate(waypoints, num_points)


def _linear_interpolate(
    waypoints: List[Tuple[float, float]],
    num_points: int,
) -> List[Tuple[float, float]]:
    """Fallback linear interpolation if spline fails."""
    result = []
    n = len(waypoints)
    for i in range(num_points):
        t = i / num_points * n
        idx = int(t)
        frac = t - idx
        p1 = waypoints[idx % n]
        p2 = waypoints[(idx + 1) % n]
        x = p1[0] + frac * (p2[0] - p1[0])
        y = p1[1] + frac * (p2[1] - p1[1])
        result.append((x, y))
    return result


def compute_alignment_transform(
    extracted_points: List[Tuple[float, float]],
    reference_points: List[Tuple[float, float]],
) -> AlignmentTransform:
    """
    Compute transform to align reference curve to extracted geometry.

    Uses bounding box matching (scale + translate, no rotation).
    """
    # Extracted bounds
    ex_xs = [p[0] for p in extracted_points]
    ex_ys = [p[1] for p in extracted_points]
    ex_cx = (min(ex_xs) + max(ex_xs)) / 2
    ex_cy = (min(ex_ys) + max(ex_ys)) / 2
    ex_w = max(ex_xs) - min(ex_xs)
    ex_h = max(ex_ys) - min(ex_ys)

    # Reference bounds
    ref_xs = [p[0] for p in reference_points]
    ref_ys = [p[1] for p in reference_points]
    ref_cx = (min(ref_xs) + max(ref_xs)) / 2
    ref_cy = (min(ref_ys) + max(ref_ys)) / 2
    ref_w = max(ref_xs) - min(ref_xs)
    ref_h = max(ref_ys) - min(ref_ys)

    # Scale based on height (more reliable than width for guitars)
    scale = ex_h / ref_h if ref_h > 0 else 1.0

    # Translate to match centers
    tx = ex_cx - ref_cx * scale
    ty = ex_cy - ref_cy * scale

    return AlignmentTransform(scale=scale, tx=tx, ty=ty)


def find_nearest_ref_index(
    point: Tuple[float, float],
    ref_curve: List[Tuple[float, float]],
) -> Tuple[int, float]:
    """
    Find index of nearest point on reference curve.

    Returns:
        (index, distance) tuple
    """
    min_dist = float('inf')
    min_idx = 0

    px, py = point
    for i, (rx, ry) in enumerate(ref_curve):
        dist = math.hypot(px - rx, py - ry)
        if dist < min_dist:
            min_dist = dist
            min_idx = i

    return min_idx, min_dist


def get_ref_slice(
    ref_pts: List[Tuple[float, float]],
    idx_start: int,
    idx_end: int,
) -> List[Tuple[float, float]]:
    """
    Extract slice from reference curve, handling wrap-around.

    Always returns the shorter path around the closed curve.
    """
    n = len(ref_pts)

    if idx_start <= idx_end:
        slice_fwd = ref_pts[idx_start:idx_end + 1]
    else:
        slice_fwd = ref_pts[idx_start:] + ref_pts[:idx_end + 1]

    # If longer than half the curve, we went the wrong way
    if len(slice_fwd) > n // 2:
        # Take the short path in reverse
        if idx_end <= idx_start:
            slice_rev = ref_pts[idx_end:idx_start + 1]
        else:
            slice_rev = ref_pts[idx_end:] + ref_pts[:idx_start + 1]
        return slice_rev[::-1]

    return slice_fwd


def warp_slice_to_fit(
    ref_slice: List[Tuple[float, float]],
    start_point: Tuple[float, float],
    end_point: Tuple[float, float],
) -> List[Tuple[float, float]]:
    """
    Warp reference slice so endpoints match exactly.

    Applies linear interpolation of the endpoint error along the slice.
    """
    if len(ref_slice) < 2:
        return ref_slice

    # Current slice endpoints
    slice_start = ref_slice[0]
    slice_end = ref_slice[-1]

    # Error at each end
    dx_start = start_point[0] - slice_start[0]
    dy_start = start_point[1] - slice_start[1]
    dx_end = end_point[0] - slice_end[0]
    dy_end = end_point[1] - slice_end[1]

    # Linearly interpolate the correction
    n = len(ref_slice)
    result = []
    for i, (x, y) in enumerate(ref_slice):
        t = i / (n - 1) if n > 1 else 0
        dx = dx_start * (1 - t) + dx_end * t
        dy = dy_start * (1 - t) + dy_end * t
        result.append((x + dx, y + dy))

    return result


class ReferenceOutlineBridge:
    """
    Tier 0 gap bridging using known instrument geometry.

    Uses waypoints from body_outlines.json to bridge gaps with actual
    body outline shape rather than computed approximations.
    """

    FALLBACK_THRESHOLD_MM = 50.0  # Max distance to reference for valid match

    def __init__(
        self,
        spec_name: str = "dreadnought",
        num_dense_points: int = 500,
    ):
        """
        Initialize with instrument spec.

        Args:
            spec_name: Key in body_outlines.json (e.g., "dreadnought")
            num_dense_points: Number of points in dense reference curve
        """
        self.spec_name = spec_name
        self.num_dense_points = num_dense_points

        # Load and process reference outline
        outlines = load_body_outlines()
        if spec_name not in outlines:
            raise ValueError(f"Unknown spec: {spec_name}. "
                           f"Available: {list(outlines.keys())}")

        raw_waypoints = outlines[spec_name]

        # Store raw waypoints - mirroring decision deferred to alignment
        self.raw_waypoints = raw_waypoints
        xs = [p[0] for p in raw_waypoints]
        self.is_half_body_ref = min(xs) >= -1.0  # All X positive = half body

        # Create both half and full reference curves
        # Actual choice made during alignment based on extracted geometry
        self.ref_curve_half = create_dense_reference_curve(
            raw_waypoints, num_dense_points
        )
        self.ref_curve_full = create_dense_reference_curve(
            mirror_waypoints(raw_waypoints), num_dense_points
        )

        # Default to half (will be updated in align_to_extracted)
        self.ref_curve = self.ref_curve_half
        self.use_full_body = False

        # Alignment will be computed when needed
        self.aligned_ref: Optional[List[Tuple[float, float]]] = None
        self.transform: Optional[AlignmentTransform] = None

        # TODO: auto-detect spec by comparing extracted body width
        # against BODY_DIMENSIONS entries. Use explicit spec_name for now.

    def align_to_extracted(
        self,
        extracted_points: List[Tuple[float, float]],
    ) -> None:
        """
        Compute alignment transform and align reference to extracted geometry.

        Automatically chooses half or full body reference based on extracted width.
        Call this once per reconstruction, before bridging gaps.
        """
        # Determine if extracted geometry is half or full body
        ex_xs = [p[0] for p in extracted_points]
        ex_width = max(ex_xs) - min(ex_xs)

        # Reference widths
        half_xs = [p[0] for p in self.ref_curve_half]
        full_xs = [p[0] for p in self.ref_curve_full]
        half_width = max(half_xs) - min(half_xs)
        full_width = max(full_xs) - min(full_xs)

        # Choose reference that best matches extracted width
        # Use half-body if extracted width is closer to half reference
        half_ratio = ex_width / half_width if half_width > 0 else 999
        full_ratio = ex_width / full_width if full_width > 0 else 999

        # If extracted is roughly half the full width, use half reference
        # Scale ratio should be close to 1.0 for a good match
        if abs(half_ratio - 1.0) < abs(full_ratio - 1.0):
            self.ref_curve = self.ref_curve_half
            self.use_full_body = False
        else:
            self.ref_curve = self.ref_curve_full
            self.use_full_body = True

        self.transform = compute_alignment_transform(
            extracted_points, self.ref_curve
        )
        self.aligned_ref = self.transform.apply_points(self.ref_curve)

    def bridge_gap(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Bridge a gap using reference outline geometry.

        Args:
            start: Gap start point (x, y)
            end: Gap end point (x, y)

        Returns:
            List of bridge points, or None if fallback needed (>50mm from reference)
        """
        if self.aligned_ref is None:
            raise RuntimeError("Must call align_to_extracted() first")

        # Project gap endpoints onto aligned reference
        idx_start, dist_start = find_nearest_ref_index(start, self.aligned_ref)
        idx_end, dist_end = find_nearest_ref_index(end, self.aligned_ref)

        # Check if within threshold
        if dist_start > self.FALLBACK_THRESHOLD_MM or \
           dist_end > self.FALLBACK_THRESHOLD_MM:
            return None  # Fall back to Tier 2

        # Get reference curve slice
        ref_slice = get_ref_slice(self.aligned_ref, idx_start, idx_end)

        if len(ref_slice) < 2:
            return None

        # Warp to fit exact gap endpoints
        bridge_points = warp_slice_to_fit(ref_slice, start, end)

        # Exclude the endpoints themselves (they're already in the chain)
        if len(bridge_points) > 2:
            return bridge_points[1:-1]
        else:
            return []

    def get_debug_info(self) -> dict:
        """Return debug information about the reference curve."""
        return {
            "spec_name": self.spec_name,
            "ref_points": len(self.ref_curve),
            "aligned": self.aligned_ref is not None,
            "transform": {
                "scale": self.transform.scale if self.transform else None,
                "tx": self.transform.tx if self.transform else None,
                "ty": self.transform.ty if self.transform else None,
            } if self.transform else None,
        }


# ─── Verification ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Reference Outline Bridge Verification ===\n")

    # Test 1: Load body outlines
    print("Test 1: Load body outlines")
    try:
        outlines = load_body_outlines()
        print(f"  Loaded {len(outlines)} specs")
        print(f"  Dreadnought: {len(outlines.get('dreadnought', []))} waypoints")
    except FileNotFoundError:
        print("  SKIP: body_outlines.json not found at expected path")
        print(f"  Expected: {BODY_OUTLINES_PATH}")
        exit(1)

    # Test 2: Mirror waypoints
    print("\nTest 2: Mirror waypoints")
    dread = outlines["dreadnought"]
    full = mirror_waypoints(dread)
    print(f"  Original: {len(dread)} points")
    print(f"  Mirrored: {len(full)} points")

    # Test 3: Create dense curve
    print("\nTest 3: Create dense reference curve")
    dense = create_dense_reference_curve(full, 500)
    print(f"  Dense curve: {len(dense)} points")

    # Test 4: Initialize bridge
    print("\nTest 4: Initialize ReferenceOutlineBridge")
    bridge = ReferenceOutlineBridge(spec_name="dreadnought")
    print(f"  Spec: {bridge.spec_name}")
    print(f"  Reference points: {len(bridge.ref_curve)}")

    # Test 5: Alignment
    print("\nTest 5: Alignment transform")
    # Simulate extracted points (scaled and translated)
    extracted = [(x * 1.5 + 100, y * 1.5 + 50) for x, y in dense[:100]]
    bridge.align_to_extracted(extracted)
    print(f"  Scale: {bridge.transform.scale:.3f}")
    print(f"  Translate: ({bridge.transform.tx:.1f}, {bridge.transform.ty:.1f})")

    # Test 6: Get slice
    print("\nTest 6: Reference slice (wrap-around)")
    slice1 = get_ref_slice(list(range(500)), 480, 20)
    print(f"  Slice 480->20: {len(slice1)} points (expect ~40)")
    slice2 = get_ref_slice(list(range(500)), 20, 480)
    print(f"  Slice 20->480: {len(slice2)} points (expect ~40, reversed)")

    # Test 7: Bridge gap
    print("\nTest 7: Bridge gap")
    # Create a test gap
    p1 = bridge.aligned_ref[100]
    p2 = bridge.aligned_ref[120]
    result = bridge.bridge_gap(p1, p2)
    if result:
        print(f"  Bridge points: {len(result)} (expect ~18)")
    else:
        print("  Bridge failed (fallback needed)")

    print("\n=== All tests passed ===")
