# services/api/app/instrument_geometry/body/centerline.py

"""
Body Centerline Calculator (PHYS-02)

Computes the geometric centerline/midline from body outline data.

For symmetric bodies (Strat, Les Paul), centerline is simply width/2.
For asymmetric bodies (Explorer, Flying V), this module computes the
true symmetry axis which may be angled or offset from the geometric center.

This is a critical dependency for PHYS-01 (pickup position calculator) because
pickup cavities must be positioned relative to the body centerline, not just
raw outline coordinates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class BodySymmetry(str, Enum):
    """Body symmetry classification."""
    SYMMETRIC = "symmetric"      # Strat, LP, Tele - symmetric about centerline
    ASYMMETRIC = "asymmetric"    # Explorer, Flying V - requires axis computation
    OFFSET = "offset"            # Control cavity offsets centerline
    UNKNOWN = "unknown"


@dataclass
class CenterlineResult:
    """Result of centerline calculation."""

    # Basic centerline (X coordinate for symmetric bodies)
    centerline_x_mm: float

    # For asymmetric bodies: angle of symmetry axis from vertical (degrees)
    # 0 = vertical (standard), positive = tilted clockwise
    axis_angle_deg: float

    # Symmetry classification
    symmetry: BodySymmetry

    # Bounding box
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    # Confidence/quality metrics
    symmetry_score: float  # 0-1, how symmetric the outline is
    notes: List[str]

    @property
    def width_mm(self) -> float:
        """Total body width."""
        return self.x_max - self.x_min

    @property
    def height_mm(self) -> float:
        """Total body height (length)."""
        return self.y_max - self.y_min

    def to_dict(self) -> Dict[str, Any]:
        return {
            "centerline_x_mm": round(self.centerline_x_mm, 2),
            "axis_angle_deg": round(self.axis_angle_deg, 2),
            "symmetry": self.symmetry.value,
            "width_mm": round(self.width_mm, 2),
            "height_mm": round(self.height_mm, 2),
            "bounds": {
                "x_min": round(self.x_min, 2),
                "x_max": round(self.x_max, 2),
                "y_min": round(self.y_min, 2),
                "y_max": round(self.y_max, 2),
            },
            "symmetry_score": round(self.symmetry_score, 3),
            "notes": self.notes,
        }


# =============================================================================
# CORE CALCULATIONS
# =============================================================================

def compute_bounding_box(
    outline: List[Tuple[float, float]]
) -> Tuple[float, float, float, float]:
    """
    Compute bounding box from outline points.

    Returns:
        Tuple of (x_min, x_max, y_min, y_max)
    """
    if not outline:
        return (0.0, 0.0, 0.0, 0.0)

    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]

    return (min(xs), max(xs), min(ys), max(ys))


def compute_centroid(
    outline: List[Tuple[float, float]]
) -> Tuple[float, float]:
    """
    Compute geometric centroid of outline polygon.

    Uses the standard centroid formula for a non-self-intersecting polygon.
    """
    if not outline or len(outline) < 3:
        return (0.0, 0.0)

    n = len(outline)
    cx = 0.0
    cy = 0.0
    signed_area = 0.0

    for i in range(n):
        x0, y0 = outline[i]
        x1, y1 = outline[(i + 1) % n]

        cross = x0 * y1 - x1 * y0
        signed_area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross

    signed_area *= 0.5

    if abs(signed_area) < 1e-10:
        # Degenerate polygon - use bounding box center
        x_min, x_max, y_min, y_max = compute_bounding_box(outline)
        return ((x_min + x_max) / 2, (y_min + y_max) / 2)

    cx /= (6.0 * signed_area)
    cy /= (6.0 * signed_area)

    return (cx, cy)


def compute_symmetry_score(
    outline: List[Tuple[float, float]],
    centerline_x: float,
    tolerance_mm: float = 2.0,
) -> float:
    """
    Compute how symmetric an outline is about a given centerline.

    For each point on the left of centerline, finds the closest point
    on the right and measures the Y difference. Returns a score 0-1
    where 1 is perfectly symmetric.

    Args:
        outline: Body outline points
        centerline_x: X coordinate of proposed centerline
        tolerance_mm: Maximum X offset to consider as "on the centerline"

    Returns:
        Symmetry score from 0 (asymmetric) to 1 (perfectly symmetric)
    """
    if not outline or len(outline) < 6:
        return 0.0

    # Separate points into left and right of centerline
    left_points = [(x, y) for x, y in outline if x < centerline_x - tolerance_mm]
    right_points = [(x, y) for x, y in outline if x > centerline_x + tolerance_mm]

    if not left_points or not right_points:
        return 0.5  # Can't determine symmetry

    total_error = 0.0
    count = 0

    for lx, ly in left_points:
        # Mirror X coordinate across centerline
        mirror_x = 2 * centerline_x - lx

        # Find closest point on right side at similar Y
        best_dist = float('inf')
        for rx, ry in right_points:
            if abs(ry - ly) < 20.0:  # Within 20mm vertically
                dist = math.sqrt((rx - mirror_x) ** 2 + (ry - ly) ** 2)
                best_dist = min(best_dist, dist)

        if best_dist < float('inf'):
            total_error += best_dist
            count += 1

    if count == 0:
        return 0.5

    avg_error = total_error / count

    # Convert error to score (0-1)
    # 0mm error = 1.0, 10mm error ≈ 0.5, 20mm+ error ≈ 0
    score = max(0.0, 1.0 - (avg_error / 20.0))

    return score


def compute_principal_axis(
    outline: List[Tuple[float, float]]
) -> Tuple[float, float, float]:
    """
    Compute principal axis of the outline using PCA-like approach.

    For asymmetric bodies like Explorer or Flying V, this finds the
    axis of maximum variance which is typically the "natural" centerline.

    Returns:
        Tuple of (axis_x, axis_y, angle_deg) where (axis_x, axis_y) is
        a unit vector along the principal axis, and angle_deg is the
        angle from vertical (0 = vertical, positive = clockwise).
    """
    if not outline or len(outline) < 3:
        return (0.0, 1.0, 0.0)  # Default: vertical axis

    cx, cy = compute_centroid(outline)

    # Compute covariance matrix
    cxx = 0.0
    cyy = 0.0
    cxy = 0.0

    for x, y in outline:
        dx = x - cx
        dy = y - cy
        cxx += dx * dx
        cyy += dy * dy
        cxy += dx * dy

    n = len(outline)
    cxx /= n
    cyy /= n
    cxy /= n

    # Compute eigenvector of larger eigenvalue
    # For 2x2 matrix [[cxx, cxy], [cxy, cyy]]
    trace = cxx + cyy
    det = cxx * cyy - cxy * cxy

    # Eigenvalues: (trace ± sqrt(trace² - 4*det)) / 2
    discriminant = trace * trace - 4 * det
    if discriminant < 0:
        discriminant = 0

    sqrt_disc = math.sqrt(discriminant)
    lambda1 = (trace + sqrt_disc) / 2

    # Eigenvector for lambda1
    if abs(cxy) > 1e-10:
        vx = lambda1 - cyy
        vy = cxy
    elif abs(cxx - lambda1) < 1e-10:
        vx = 1.0
        vy = 0.0
    else:
        vx = 0.0
        vy = 1.0

    # Normalize
    length = math.sqrt(vx * vx + vy * vy)
    if length > 1e-10:
        vx /= length
        vy /= length

    # Ensure axis points "up" (positive Y direction preferred)
    if vy < 0:
        vx = -vx
        vy = -vy

    # Angle from vertical (0,1)
    angle_rad = math.atan2(vx, vy)
    angle_deg = math.degrees(angle_rad)

    return (vx, vy, angle_deg)


# =============================================================================
# PUBLIC API
# =============================================================================

def compute_body_centerline(
    outline: List[Tuple[float, float]],
    assume_symmetric: bool = True,
) -> CenterlineResult:
    """
    Compute body centerline from outline points.

    This is the main API for PHYS-02. For most guitar bodies (Strat, LP, Tele),
    the centerline is simply the midpoint of the bounding box width. For
    asymmetric bodies (Explorer, Flying V), this computes the true symmetry axis.

    Args:
        outline: List of (x, y) points forming the body outline polygon.
                 Points should be in mm, counterclockwise from start point.
        assume_symmetric: If True, use simple bounding box center for centerline.
                         If False, compute principal axis for asymmetric bodies.

    Returns:
        CenterlineResult with centerline position, symmetry info, and bounds.

    Example:
        >>> from .outlines import get_body_outline
        >>> outline = get_body_outline("stratocaster")
        >>> result = compute_body_centerline(outline)
        >>> print(f"Centerline at X={result.centerline_x_mm}mm")
    """
    if not outline or len(outline) < 3:
        return CenterlineResult(
            centerline_x_mm=0.0,
            axis_angle_deg=0.0,
            symmetry=BodySymmetry.UNKNOWN,
            x_min=0.0,
            x_max=0.0,
            y_min=0.0,
            y_max=0.0,
            symmetry_score=0.0,
            notes=["Empty or invalid outline"],
        )

    # Compute bounding box
    x_min, x_max, y_min, y_max = compute_bounding_box(outline)

    # Simple centerline: midpoint of width
    simple_centerline = (x_min + x_max) / 2

    if assume_symmetric:
        # For most guitars, this is correct
        symmetry_score = compute_symmetry_score(outline, simple_centerline)

        if symmetry_score > 0.8:
            symmetry = BodySymmetry.SYMMETRIC
        elif symmetry_score > 0.5:
            symmetry = BodySymmetry.OFFSET
        else:
            symmetry = BodySymmetry.ASYMMETRIC

        return CenterlineResult(
            centerline_x_mm=simple_centerline,
            axis_angle_deg=0.0,
            symmetry=symmetry,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
            symmetry_score=symmetry_score,
            notes=[
                f"Simple centerline (assume_symmetric=True)",
                f"Symmetry score: {symmetry_score:.2f}",
            ],
        )

    # Compute principal axis for asymmetric bodies
    axis_x, axis_y, axis_angle = compute_principal_axis(outline)

    # Centroid
    cx, cy = compute_centroid(outline)

    # For centerline_x, project centroid onto vertical
    centerline_x = cx

    # Compute symmetry about this axis
    symmetry_score = compute_symmetry_score(outline, centerline_x)

    # Determine symmetry type
    if abs(axis_angle) < 2.0 and symmetry_score > 0.8:
        symmetry = BodySymmetry.SYMMETRIC
    elif abs(axis_angle) < 5.0:
        symmetry = BodySymmetry.OFFSET
    else:
        symmetry = BodySymmetry.ASYMMETRIC

    return CenterlineResult(
        centerline_x_mm=centerline_x,
        axis_angle_deg=axis_angle,
        symmetry=symmetry,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        symmetry_score=symmetry_score,
        notes=[
            f"Principal axis analysis (assume_symmetric=False)",
            f"Axis angle: {axis_angle:.2f}°",
            f"Centroid: ({cx:.1f}, {cy:.1f})",
        ],
    )


def compute_symmetry_axis(
    outline: List[Tuple[float, float]]
) -> Tuple[float, float]:
    """
    Compute the symmetry axis for asymmetric bodies.

    Returns the X position and angle of the axis about which the body
    is most symmetric. For Explorer and Flying V, this accounts for
    the angled body shape.

    Args:
        outline: Body outline points in mm

    Returns:
        Tuple of (x_position_mm, angle_degrees)

    This is a convenience wrapper around compute_body_centerline()
    for cases where only the axis info is needed.
    """
    result = compute_body_centerline(outline, assume_symmetric=False)
    return (result.centerline_x_mm, result.axis_angle_deg)


# =============================================================================
# KNOWN BODY PROFILES
# =============================================================================

# Symmetry characteristics for known body styles
# This allows skipping expensive computation for well-known shapes
KNOWN_SYMMETRY: Dict[str, BodySymmetry] = {
    # Symmetric bodies
    "stratocaster": BodySymmetry.SYMMETRIC,
    "telecaster": BodySymmetry.SYMMETRIC,
    "les_paul": BodySymmetry.SYMMETRIC,
    "sg": BodySymmetry.SYMMETRIC,
    "j45": BodySymmetry.SYMMETRIC,
    "dreadnought": BodySymmetry.SYMMETRIC,
    "jumbo": BodySymmetry.SYMMETRIC,
    "classical": BodySymmetry.SYMMETRIC,
    "om_000": BodySymmetry.SYMMETRIC,

    # Asymmetric bodies
    "gibson_explorer": BodySymmetry.ASYMMETRIC,
    "flying_v": BodySymmetry.ASYMMETRIC,
    "jackson_rhoads": BodySymmetry.ASYMMETRIC,
    "bc_rich_warlock": BodySymmetry.ASYMMETRIC,

    # Offset bodies (subtle asymmetry)
    "jazzmaster": BodySymmetry.OFFSET,
    "jaguar": BodySymmetry.OFFSET,
    "mustang": BodySymmetry.OFFSET,
}


def get_known_symmetry(model_id: str) -> Optional[BodySymmetry]:
    """
    Get known symmetry type for a body model.

    Returns None if model is not in the known list.
    """
    key = model_id.lower().replace("-", "_").replace(" ", "_")
    return KNOWN_SYMMETRY.get(key)


def compute_body_centerline_for_model(
    outline: List[Tuple[float, float]],
    model_id: str,
) -> CenterlineResult:
    """
    Compute centerline with model-specific optimization.

    Uses known symmetry information to avoid expensive computation
    for well-known body styles.
    """
    known = get_known_symmetry(model_id)

    if known == BodySymmetry.SYMMETRIC:
        return compute_body_centerline(outline, assume_symmetric=True)
    elif known in (BodySymmetry.ASYMMETRIC, BodySymmetry.OFFSET):
        return compute_body_centerline(outline, assume_symmetric=False)
    else:
        # Unknown model - auto-detect
        result = compute_body_centerline(outline, assume_symmetric=True)
        if result.symmetry_score < 0.7:
            # Low symmetry - recompute with axis analysis
            return compute_body_centerline(outline, assume_symmetric=False)
        return result
