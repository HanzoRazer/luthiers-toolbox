"""
Arc Reconstructor — Standalone Gap Bridging with Arc/Polyline Output
=====================================================================

Three-tier gap reconstruction for guitar body outlines.
Standalone implementation — no production dependencies.

Tier 1: Radius measured from adjacent chain (most accurate)
Tier 2: Radius computed from spherical arch formula
Tier 3: Radius from zone lookup table (fallback)

Author: Production Shop
Date: 2026-04-15
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple


# ─── Section A: Data Structures ────────────────────────────────────────────────

@dataclass
class Point:
    """2D point with optional metadata."""
    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class Chain:
    """A sequence of connected points forming a contour segment."""
    points: List[Point]
    layer: str = "BODY"
    is_closed: bool = False

    @property
    def start(self) -> Optional[Point]:
        return self.points[0] if self.points else None

    @property
    def end(self) -> Optional[Point]:
        return self.points[-1] if self.points else None

    def length_mm(self) -> float:
        if len(self.points) < 2:
            return 0.0
        total = 0.0
        for i in range(len(self.points) - 1):
            total += self.points[i].distance_to(self.points[i + 1])
        return total


class GapZone(Enum):
    """Body zone classification for radius lookup."""
    UPPER_BOUT = "upper_bout"
    WAIST = "waist"
    LOWER_BOUT = "lower_bout"
    HORN_TIP = "horn_tip"
    CUTAWAY = "cutaway"
    UNKNOWN = "unknown"


@dataclass
class Gap:
    """A gap between chain endpoints that needs bridging."""
    start: Point
    end: Point
    chain_idx: int
    zone: GapZone = GapZone.UNKNOWN

    @property
    def distance_mm(self) -> float:
        return self.start.distance_to(self.end)


@dataclass
class ReconstructionResult:
    """Result of gap reconstruction."""
    chains: List[Chain]
    gaps_found: int
    gaps_bridged: int
    tier_usage: dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    duplicates_removed: int = 0


# ─── Section B: Polyline Consolidation ─────────────────────────────────────────

def angle_between(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
    """
    Angle between two vectors in degrees.
    Returns 0-180 (unsigned angle).
    """
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
    if mag1 < 1e-9 or mag2 < 1e-9:
        return 0.0
    cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_angle))


def segment_vector(p1: Tuple[float, float], p2: Tuple[float, float]) -> Tuple[float, float]:
    """Vector from p1 to p2."""
    return (p2[0] - p1[0], p2[1] - p1[1])


def is_continuation(
    prev_seg: Tuple[float, float],
    curr_seg: Tuple[float, float],
    dist_tol: float = 1.5,
    angle_tol: float = 20.0,
) -> bool:
    """
    Check if current segment continues the polyline direction.

    Args:
        prev_seg: Previous segment vector
        curr_seg: Current segment vector
        dist_tol: Maximum segment length ratio deviation (not used here, for future)
        angle_tol: Maximum angle deviation in degrees

    Returns:
        True if segments are directionally coherent
    """
    angle = angle_between(prev_seg, curr_seg)
    return angle <= angle_tol


def consolidate_polyline(
    points: List[Tuple[float, float]],
    angle_tol: float = 20.0,
) -> List[List[Tuple[float, float]]]:
    """
    Consolidate a sequence of points into polyline runs.

    Splits where direction changes exceed angle_tol.

    Args:
        points: Input points as (x, y) tuples
        angle_tol: Maximum angle change to continue a run (degrees)

    Returns:
        List of polyline runs, each a list of (x, y) tuples
    """
    if len(points) < 2:
        return [points] if points else []

    runs = []
    current_run = [points[0], points[1]]
    prev_seg = segment_vector(points[0], points[1])

    for i in range(2, len(points)):
        curr_seg = segment_vector(points[i - 1], points[i])

        if is_continuation(prev_seg, curr_seg, angle_tol=angle_tol):
            current_run.append(points[i])
        else:
            # Direction changed — start new run
            runs.append(current_run)
            current_run = [points[i - 1], points[i]]

        prev_seg = curr_seg

    # Add final run
    if current_run:
        runs.append(current_run)

    return runs


def chain_to_polylines(chain: Chain, angle_tol: float = 20.0) -> List[List[Tuple[float, float]]]:
    """Convert a Chain to consolidated polyline runs."""
    points = [p.as_tuple() for p in chain.points]
    return consolidate_polyline(points, angle_tol=angle_tol)


# ─── Section C: Circle and Arc Fitting ─────────────────────────────────────────


# ─── Section D: Spherical Arch Geometry ────────────────────────────────────────

def falloff(R: float, D: float) -> float:
    """
    Height drop at distance D from apex of a sphere of radius R.

    For a spherical arch (like an acoustic guitar back), this gives the
    vertical drop from the high point as you move horizontally.
    """
    if D >= R:
        return R
    return R - math.sqrt(R * R - D * D)


def radius_from_chord_sagitta(chord: float, sagitta: float) -> float:
    """
    Compute radius of a circular arc from chord length and sagitta (height).

    Formula: R = (c^2)/(8h) + h/2
    """
    if sagitta <= 0:
        return float('inf')
    return (chord * chord) / (8 * sagitta) + sagitta / 2


def compute_radius_from_spherical_arch(
    chord_mm: float,
    distance_from_high_point_mm: float,
    arch_radius_mm: float,
) -> float:
    """
    Compute the body edge radius at a given position on a spherical arch.

    Uses the difference in falloff heights across the chord to derive
    the local arc radius.

    Args:
        chord_mm: The chord length (gap distance) to bridge
        distance_from_high_point_mm: Distance from arch apex to gap midpoint
        arch_radius_mm: The spherical arch radius (e.g., 25-foot = 7620mm)

    Returns:
        Local arc radius in mm, or inf if effectively flat
    """
    D = distance_from_high_point_mm
    h1 = falloff(arch_radius_mm, D)
    h2 = falloff(arch_radius_mm, D + chord_mm)
    sagitta = abs(h2 - h1)
    if sagitta < 0.01:
        return float('inf')
    return radius_from_chord_sagitta(chord_mm, sagitta)


# ─── Section E: Zone Classification ────────────────────────────────────────────

def classify_zone_by_y(
    y: float,
    body_height: float,
    is_acoustic: bool = True,
) -> GapZone:
    """
    Classify a gap's body zone based on Y coordinate.

    Zones are defined as fractions of body height:
    - Upper bout: 0-35% (acoustic) or 0-20% (electric, horn tips)
    - Waist: 35-55% (acoustic) or 20-45% (electric, cutaway region)
    - Lower bout: 55-100% (acoustic) or 45-100% (electric)

    Args:
        y: Y coordinate of gap midpoint
        body_height: Total body height in mm
        is_acoustic: True for acoustic body shapes

    Returns:
        GapZone classification
    """
    if body_height <= 0:
        return GapZone.UNKNOWN

    y_fraction = y / body_height

    if is_acoustic:
        if y_fraction < 0.35:
            return GapZone.UPPER_BOUT
        elif y_fraction < 0.55:
            return GapZone.WAIST
        else:
            return GapZone.LOWER_BOUT
    else:
        # Electric body shape
        if y_fraction < 0.15:
            return GapZone.HORN_TIP
        elif y_fraction < 0.45:
            return GapZone.CUTAWAY
        else:
            return GapZone.LOWER_BOUT

def fit_circle_3pts(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
) -> Optional[Tuple[float, float, float]]:
    """
    Fit a circle through three points.

    Returns:
        (center_x, center_y, radius) or None if collinear
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    # Determinant for collinearity check
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        return None  # Collinear points

    ux = ((x1**2 + y1**2) * (y2 - y3) + (x2**2 + y2**2) * (y3 - y1) + (x3**2 + y3**2) * (y1 - y2)) / d
    uy = ((x1**2 + y1**2) * (x3 - x2) + (x2**2 + y2**2) * (x1 - x3) + (x3**2 + y3**2) * (x2 - x1)) / d

    radius = math.sqrt((x1 - ux)**2 + (y1 - uy)**2)
    return (ux, uy, radius)


def fit_arc_segment(
    points: List[Tuple[float, float]],
    tolerance_mm: float = 1.0,
    max_error_mm: float = 2.5,
) -> Optional[Tuple[Tuple[float, float], float, float, float]]:
    """
    Fit an arc to a sequence of points.

    Uses three-point circle fit with first, middle, last points,
    then validates all points lie within tolerance.

    Args:
        points: Sequence of (x, y) points
        tolerance_mm: Mean error threshold
        max_error_mm: Maximum single-point error threshold

    Returns:
        (center, radius, mean_error, max_error) or None if fit fails
    """
    if len(points) < 3:
        return None

    # Use first, middle, last for initial fit
    p1 = points[0]
    p2 = points[len(points) // 2]
    p3 = points[-1]

    fit = fit_circle_3pts(p1, p2, p3)
    if fit is None:
        return None

    cx, cy, radius = fit

    # Validate all points against the fitted circle
    errors = []
    for px, py in points:
        dist_to_center = math.sqrt((px - cx)**2 + (py - cy)**2)
        error = abs(dist_to_center - radius)
        errors.append(error)

    mean_error = sum(errors) / len(errors)
    max_err = max(errors)

    if mean_error > tolerance_mm or max_err > max_error_mm:
        return None

    return ((cx, cy), radius, mean_error, max_err)


def calculate_bulge(
    center: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
) -> float:
    """
    Calculate bulge value for an arc segment from p1 to p2 around center.

    Bulge = tan(sweep_angle / 4)
    Positive bulge = counterclockwise arc
    Negative bulge = clockwise arc

    Args:
        center: Arc center (cx, cy)
        p1: Start point of segment
        p2: End point of segment

    Returns:
        Bulge value for the vertex at p1
    """
    cx, cy = center

    # Angles from center to each point
    angle1 = math.atan2(p1[1] - cy, p1[0] - cx)
    angle2 = math.atan2(p2[1] - cy, p2[0] - cx)

    # Sweep angle (counterclockwise from p1 to p2)
    sweep = angle2 - angle1

    # Normalize to [-pi, pi] then determine direction
    while sweep > math.pi:
        sweep -= 2 * math.pi
    while sweep < -math.pi:
        sweep += 2 * math.pi

    # Bulge = tan(sweep / 4)
    bulge = math.tan(sweep / 4)

    return bulge


def promote_chain_to_arcs(
    chain: Chain,
    angle_tol: float = 45.0,
    tolerance_mm: float = 1.0,
    max_error_mm: float = 2.5,
) -> List[Tuple[Tuple[float, float], float]]:
    """
    Fit arcs to consecutive segments of a chain.

    Returns list of (point, bulge) tuples for POLYLINE vertices.

    Args:
        chain: Chain to process
        angle_tol: Max angle change (degrees) for consolidating segments
        tolerance_mm: Arc fit mean error threshold
        max_error_mm: Arc fit max single-point error

    Returns:
        List of ((x, y), bulge) tuples. Use bulge=0 for straight segments.
    """
    if len(chain.points) < 3:
        # Too few points, return as straight segments (bulge=0)
        return [((p.x, p.y), 0.0) for p in chain.points]

    # First, consolidate points into groups that fit arcs
    points = [p.as_tuple() for p in chain.points]
    result = []

    i = 0
    while i < len(points):
        # Try to fit an arc starting from this point
        best_end = i + 2  # Minimum 3 points for arc
        best_fit = None

        # Greedy: extend as far as possible while arc fit holds
        for j in range(i + 3, min(i + 50, len(points) + 1)):  # Max 50 points per arc
            segment = points[i:j]
            fit = fit_arc_segment(segment, tolerance_mm, max_error_mm)
            if fit is not None:
                best_end = j
                best_fit = fit
            else:
                break  # Arc fit failed, stop extending

        if best_fit is not None:
            # We have a valid arc from i to best_end-1
            center, radius, _, _ = best_fit
            segment = points[i:best_end]

            # Add vertices with bulge values
            for k in range(len(segment) - 1):
                p1 = segment[k]
                p2 = segment[k + 1]
                bulge = calculate_bulge(center, p1, p2)
                result.append((p1, bulge))

            # Last point of segment (bulge for next segment, or 0 if end)
            i = best_end - 1  # Continue from last point of this arc
        else:
            # No arc fit, add as straight segment
            result.append((points[i], 0.0))
            i += 1

    # Add final point with bulge=0
    if points and (not result or result[-1][0] != points[-1]):
        result.append((points[-1], 0.0))

    return result


def measure_radius_from_chain(
    chain: Chain,
    tolerance_mm: float = 1.0,
    max_error_mm: float = 2.5,
) -> Optional[float]:
    """
    Attempt to measure a consistent radius from a chain's curvature.

    Returns:
        Measured radius in mm, or None if chain is not arc-like
    """
    if len(chain.points) < 5:
        return None

    # Sample points along the chain
    points = [p.as_tuple() for p in chain.points]
    result = fit_arc_segment(points, tolerance_mm, max_error_mm)

    if result is None:
        return None

    _, radius, _, _ = result
    return radius


# ─── Step 0: Deduplication ─────────────────────────────────────────────────────

def deduplicate_lines(
    chains: List[Chain],
    tolerance_mm: float = 0.5,
) -> List[Chain]:
    """
    Remove duplicate and near-duplicate chains produced by edge detection.

    Two chains are duplicates if all their endpoints match within tolerance.
    Keep the longest chain from each duplicate group.
    """
    if not chains:
        return chains

    kept = []
    skip = set()

    for i, chain_a in enumerate(chains):
        if i in skip:
            continue

        duplicates = [i]

        for j, chain_b in enumerate(chains):
            if j <= i or j in skip:
                continue

            # Quick bbox check before detailed comparison
            if not _bboxes_overlap(chain_a, chain_b, tolerance_mm):
                continue

            if _chains_are_duplicates(chain_a, chain_b, tolerance_mm):
                duplicates.append(j)
                skip.add(j)

        # Keep longest chain from duplicate group
        best = max(duplicates, key=lambda idx: chains[idx].length_mm())
        kept.append(chains[best])

    return kept


def _chains_are_duplicates(
    a: Chain,
    b: Chain,
    tolerance_mm: float,
) -> bool:
    """
    Two chains are duplicates if their start/end points match within tolerance,
    and their total lengths are within 10% of each other.
    """
    # Length similarity check
    la, lb = a.length_mm(), b.length_mm()
    if la < 1e-6 or lb < 1e-6:
        return False
    if abs(la - lb) / max(la, lb) > 0.10:
        return False

    # Endpoint match - try both orientations
    a_start, a_end = a.points[0], a.points[-1]
    b_start, b_end = b.points[0], b.points[-1]

    forward = (
        a_start.distance_to(b_start) <= tolerance_mm and
        a_end.distance_to(b_end) <= tolerance_mm
    )
    reverse = (
        a_start.distance_to(b_end) <= tolerance_mm and
        a_end.distance_to(b_start) <= tolerance_mm
    )

    return forward or reverse


def _bboxes_overlap(a: Chain, b: Chain, margin: float) -> bool:
    """Quick rejection test before detailed comparison."""
    ax = [p.x for p in a.points]
    ay = [p.y for p in a.points]
    bx = [p.x for p in b.points]
    by = [p.y for p in b.points]

    return not (
        max(ax) + margin < min(bx) or
        min(ax) - margin > max(bx) or
        max(ay) + margin < min(by) or
        min(ay) - margin > max(by)
    )


# ─── Section F: ArcReconstructor Class ─────────────────────────────────────────

class ArcReconstructor:
    """
    Three-tier gap reconstruction for guitar body outlines.

    Tier 1: Radius measured from adjacent chain (most accurate)
    Tier 2: Radius computed from spherical arch formula
    Tier 3: Radius from zone lookup table (fallback)
    """

    # Default radii by zone (mm) - used for Tier 3 fallback
    DEFAULT_RADII = {
        GapZone.UPPER_BOUT: 150.0,
        GapZone.WAIST: 80.0,
        GapZone.LOWER_BOUT: 200.0,
        GapZone.HORN_TIP: 30.0,
        GapZone.CUTAWAY: 50.0,
        GapZone.UNKNOWN: 100.0,
    }

    def __init__(
        self,
        min_gap_mm: float = 0.5,
        max_gap_mm: float = 50.0,
        arch_radius_mm: Optional[float] = None,
        body_height_mm: Optional[float] = None,
        is_acoustic: bool = True,
        arc_points_per_mm: float = 0.5,
        spec_name: Optional[str] = None,
    ):
        """
        Initialize the arc reconstructor.

        Args:
            min_gap_mm: Minimum gap size to consider for bridging
            max_gap_mm: Maximum gap size to bridge (larger = structural issue)
            arch_radius_mm: Spherical arch radius for Tier 2 (e.g., 635mm for 25-foot)
            body_height_mm: Body height for zone classification
            is_acoustic: True for acoustic body shapes
            arc_points_per_mm: Point density for generated arcs
            spec_name: Instrument spec for Tier 0 reference outline (e.g., "dreadnought")
        """
        self.min_gap_mm = min_gap_mm
        self.max_gap_mm = max_gap_mm
        self.arch_radius_mm = arch_radius_mm
        self.body_height_mm = body_height_mm
        self.is_acoustic = is_acoustic
        self.arc_points_per_mm = arc_points_per_mm
        self.spec_name = spec_name

        # Initialize Tier 0 reference outline bridge if spec provided
        self.ref_bridge = None
        if spec_name:
            try:
                from reference_outline_bridge import ReferenceOutlineBridge
                self.ref_bridge = ReferenceOutlineBridge(spec_name=spec_name)
            except Exception as e:
                print(f"Warning: Could not load reference outline for {spec_name}: {e}")

    def complete(self, chains: List[Chain]) -> ReconstructionResult:
        """
        Complete gaps in chains using three-tier arc reconstruction.

        Args:
            chains: Input chains (typically from DXF BODY layer)

        Returns:
            ReconstructionResult with bridged chains and tier usage stats
        """
        tier_usage = {"tier0_reference": 0, "tier1_measured": 0, "tier2_spherical": 0, "tier3_lookup": 0}
        errors = []

        # Step 0: Remove duplicates from edge detection noise
        original_count = len(chains)
        chains = deduplicate_lines(chains, tolerance_mm=0.5)
        dedup_removed = original_count - len(chains)

        # Step 0.5: Align reference outline if available
        if self.ref_bridge:
            all_points = [(p.x, p.y) for c in chains for p in c.points]
            if all_points:
                self.ref_bridge.align_to_extracted(all_points)

        # Step 1: Detect gaps
        gaps = self._detect_gaps(chains)

        # Step 2: Measure radii from chains that look arc-like
        measured_radii = {}
        for i, chain in enumerate(chains):
            radius = measure_radius_from_chain(chain)
            if radius is not None and radius < 5000:  # Sanity check
                measured_radii[i] = radius

        # Step 3: Bridge each gap
        bridged_chains = []
        for i, chain in enumerate(chains):
            new_chain = Chain(points=list(chain.points), layer=chain.layer)

            # Find gaps for this chain
            chain_gaps = [g for g in gaps if g.chain_idx == i]
            for gap in chain_gaps:
                bridge_points = None
                tier_used = None

                # Tier 0: Try reference outline first
                if self.ref_bridge:
                    start_pt = (gap.start.x, gap.start.y)
                    end_pt = (gap.end.x, gap.end.y)
                    ref_points = self.ref_bridge.bridge_gap(start_pt, end_pt)
                    if ref_points:
                        bridge_points = ref_points
                        tier_used = "tier0_reference"

                # Tiers 1-3: Fall back to arc generation
                if bridge_points is None:
                    radius, tier_used = self._get_radius_for_gap(gap, i, measured_radii)
                    bridge_points = self._generate_arc_points(gap, radius)

                tier_usage[tier_used] += 1

                if bridge_points:
                    # Append bridge points to chain
                    new_chain.points.extend([Point(x, y) for x, y in bridge_points])
                    # Close the loop by appending the start point
                    new_chain.points.append(Point(gap.end.x, gap.end.y))
                    new_chain.is_closed = True

            bridged_chains.append(new_chain)

        return ReconstructionResult(
            chains=bridged_chains,
            gaps_found=len(gaps),
            gaps_bridged=sum(tier_usage.values()),
            tier_usage=tier_usage,
            errors=errors,
            duplicates_removed=dedup_removed,
        )

    def _detect_gaps(self, chains: List[Chain]) -> List[Gap]:
        """
        Detect gaps in chain endpoints that need bridging.

        Only detects WITHIN-CHAIN gaps where a contour is almost closed
        but has a small gap between start and end. Does NOT bridge
        between different chains (those are separate contours).

        Chains that are already closed (start == end) are skipped.
        """
        gaps = []

        for i, chain in enumerate(chains):
            if len(chain.points) < 2:
                continue

            start = chain.start
            end = chain.end
            if not start or not end:
                continue

            # Check if this chain has a gap between its start and end
            dist = start.distance_to(end)

            # Skip already-closed chains (start == end)
            if dist < self.min_gap_mm:
                continue

            # Only bridge if gap is within acceptable range
            if dist <= self.max_gap_mm:
                mid_y = (start.y + end.y) / 2
                zone = GapZone.UNKNOWN
                if self.body_height_mm:
                    zone = classify_zone_by_y(mid_y, self.body_height_mm, self.is_acoustic)

                gaps.append(Gap(
                    start=end,
                    end=start,
                    chain_idx=i,
                    zone=zone,
                ))

        return gaps

    def _get_radius_for_gap(
        self,
        gap: Gap,
        chain_idx: int,
        measured_radii: dict,
    ) -> Tuple[float, str]:
        """
        Get radius for a gap using three-tier priority.

        Tier 1: Measured from adjacent chain (most accurate)
        Tier 2: Computed from spherical arch formula
        Tier 3: Zone lookup table (fallback)
        """
        # Tier 1: measured from adjacent chain
        for neighbor in [chain_idx - 1, chain_idx + 1]:
            if neighbor in measured_radii:
                return measured_radii[neighbor], "tier1_measured"

        # Tier 2: spherical arch formula
        if self.arch_radius_mm and self.body_height_mm:
            mid_y = (gap.start.y + gap.end.y) / 2
            high_point_y = self.body_height_mm * 0.5  # Assume apex at center
            D = abs(mid_y - high_point_y)
            R = compute_radius_from_spherical_arch(
                chord_mm=gap.distance_mm,
                distance_from_high_point_mm=D,
                arch_radius_mm=self.arch_radius_mm,
            )
            if R < 5000:  # Sanity check - not effectively flat
                return R, "tier2_spherical"

        # Tier 3: zone lookup
        return self.DEFAULT_RADII.get(gap.zone, 200.0), "tier3_lookup"

    def _circle_center(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        radius: float,
        concave: bool = True,
    ) -> Optional[Tuple[float, float]]:
        """
        Find circle center given two points and radius.

        Args:
            p1: Start point
            p2: End point
            radius: Arc radius
            concave: If True, center is on the "inside" of the body curve

        Returns:
            Center point or None if chord > 2*radius
        """
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2

        chord = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        if chord > 2 * radius:
            return None  # Impossible arc

        # Distance from midpoint to center
        h = math.sqrt(radius**2 - (chord / 2)**2)

        # Perpendicular direction
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.sqrt(dx**2 + dy**2)
        if length < 1e-9:
            return None

        # Perpendicular unit vector
        px = -dy / length
        py = dx / length

        # Choose side based on concave flag
        if concave:
            return (mx + h * px, my + h * py)
        else:
            return (mx - h * px, my - h * py)

    def _generate_arc_points(
        self,
        gap: Gap,
        radius: float,
    ) -> List[Tuple[float, float]]:
        """
        Generate arc points to bridge a gap.

        Args:
            gap: The gap to bridge
            radius: Arc radius to use

        Returns:
            List of (x, y) points along the arc (excluding endpoints)
        """
        p1 = gap.start.as_tuple()
        p2 = gap.end.as_tuple()

        center = self._circle_center(p1, p2, radius, concave=True)
        if center is None:
            # Fallback: try larger radius
            center = self._circle_center(p1, p2, radius * 2, concave=True)
            if center is None:
                return []  # Cannot bridge

        cx, cy = center

        # Calculate start and end angles
        start_angle = math.atan2(p1[1] - cy, p1[0] - cx)
        end_angle = math.atan2(p2[1] - cy, p2[0] - cx)

        # Normalize sweep direction (always go the short way)
        sweep = end_angle - start_angle
        while sweep > math.pi:
            sweep -= 2 * math.pi
        while sweep < -math.pi:
            sweep += 2 * math.pi

        # Number of points based on arc length
        arc_length = abs(sweep) * radius
        num_points = max(2, int(arc_length * self.arc_points_per_mm))

        # Generate intermediate points (exclude endpoints)
        points = []
        for i in range(1, num_points):
            t = i / num_points
            angle = start_angle + t * sweep
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append((x, y))

        return points


# ─── Section G: DXF I/O ────────────────────────────────────────────────────────

def _deduplicate_raw_lines(
    lines: List[Tuple[Tuple[float, float], Tuple[float, float]]],
    tolerance_mm: float = 0.3,
) -> Tuple[List[Tuple[Tuple[float, float], Tuple[float, float]]], int]:
    """
    Remove parallel duplicate lines produced by edge detection.

    Parallel lines within tolerance_mm are considered duplicates.
    Returns (deduplicated_lines, num_removed).
    """
    if not lines:
        return lines, 0

    def line_direction(line):
        dx = line[1][0] - line[0][0]
        dy = line[1][1] - line[0][1]
        length = math.sqrt(dx**2 + dy**2)
        if length < 1e-9:
            return (0, 0), 0
        return (dx/length, dy/length), length

    def lines_parallel(l1, l2):
        d1, len1 = line_direction(l1)
        d2, len2 = line_direction(l2)
        if len1 < 0.1 or len2 < 0.1:
            return False
        # Dot product - parallel if close to 1 or -1
        dot = abs(d1[0]*d2[0] + d1[1]*d2[1])
        return dot > 0.99

    def midpoint(line):
        return ((line[0][0] + line[1][0])/2, (line[0][1] + line[1][1])/2)

    def midpoint_distance(l1, l2):
        m1, m2 = midpoint(l1), midpoint(l2)
        return math.sqrt((m1[0]-m2[0])**2 + (m1[1]-m2[1])**2)

    # Group lines by approximate direction (angle buckets)
    kept = []
    removed = 0
    skip = set()

    for i, line_a in enumerate(lines):
        if i in skip:
            continue

        # Find all parallel duplicates
        duplicates = [i]
        for j, line_b in enumerate(lines):
            if j <= i or j in skip:
                continue
            if lines_parallel(line_a, line_b):
                dist = midpoint_distance(line_a, line_b)
                if dist < tolerance_mm:
                    duplicates.append(j)
                    skip.add(j)

        # Keep the longest line from the cluster
        if len(duplicates) > 1:
            best = max(duplicates, key=lambda idx: line_direction(lines[idx])[1])
            removed += len(duplicates) - 1
        else:
            best = duplicates[0]

        kept.append(lines[best])

    return kept, removed


def load_chains_from_dxf(
    dxf_path: str,
    layer_filter: Optional[str] = "BODY",
    deduplicate_lines: bool = True,
) -> List[Chain]:
    """
    Load chains from a DXF file.

    Args:
        dxf_path: Path to DXF file
        layer_filter: Only load entities from this layer (None = all layers)
        deduplicate_lines: Remove parallel duplicate lines before chaining

    Returns:
        List of Chain objects
    """
    import ezdxf

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    # First pass: collect raw lines grouped by layer
    lines_by_layer = {}
    for entity in msp:
        if entity.dxftype() != "LINE":
            continue
        entity_layer = entity.dxf.layer
        if layer_filter and entity_layer != layer_filter:
            continue
        start = (entity.dxf.start.x, entity.dxf.start.y)
        end = (entity.dxf.end.x, entity.dxf.end.y)
        if entity_layer not in lines_by_layer:
            lines_by_layer[entity_layer] = []
        lines_by_layer[entity_layer].append((start, end))

    # Deduplicate parallel lines (per layer)
    total_removed = 0
    if deduplicate_lines:
        for layer_name in lines_by_layer:
            raw_lines = lines_by_layer[layer_name]
            if raw_lines:
                deduped, removed = _deduplicate_raw_lines(raw_lines, tolerance_mm=0.3)
                lines_by_layer[layer_name] = deduped
                total_removed += removed
        if total_removed > 0:
            print(f"  Line-level dedup: removed {total_removed} parallel duplicates")

    # Second pass: consolidate lines into chains (per layer)
    chains = []

    for layer_name, raw_lines in lines_by_layer.items():
        current_points = []

        for start, end in raw_lines:
            # Check if this continues the current chain
            if current_points:
                last = current_points[-1]
                dist_to_start = math.sqrt((last[0] - start[0])**2 + (last[1] - start[1])**2)
                dist_to_end = math.sqrt((last[0] - end[0])**2 + (last[1] - end[1])**2)

                if dist_to_start < 0.01:
                    # Continues forward
                    current_points.append(end)
                    continue
                elif dist_to_end < 0.01:
                    # Continues backward
                    current_points.append(start)
                    continue

            # New chain
            if current_points:
                chains.append(Chain(
                    points=[Point(x, y) for x, y in current_points],
                    layer=layer_name,
                ))
            current_points = [start, end]

        # Add final chain for this layer
        if current_points:
            chains.append(Chain(
                points=[Point(x, y) for x, y in current_points],
                layer=layer_name,
            ))

    return chains


def chains_to_dxf(
    chains: List[Chain],
    output_path: str,
    use_polyline: bool = True,
    use_arc: bool = False,
    promote_arcs: bool = False,
    arc_tolerance_mm: float = 1.0,
    arc_max_error_mm: float = 2.5,
) -> dict:
    """
    Write chains to a DXF file.

    Args:
        chains: Chains to write
        output_path: Output DXF path
        use_polyline: Write as POLYLINE entities (else LINE)
        use_arc: Write detected arcs as ARC entities (experimental, deprecated)
        promote_arcs: Fit arcs and write POLYLINE with bulge values
        arc_tolerance_mm: Mean error threshold for arc fitting
        arc_max_error_mm: Max single-point error for arc fitting

    Returns:
        Dict with entity counts and arc stats
    """
    import ezdxf

    # Create R12 document for maximum compatibility
    doc = ezdxf.new(dxfversion="R12")
    msp = doc.modelspace()

    # Create layers
    layers_seen = set()
    for chain in chains:
        if chain.layer not in layers_seen:
            doc.layers.add(chain.layer, dxfattribs={"color": 7})
            layers_seen.add(chain.layer)

    counts = {"polyline": 0, "line": 0, "arc": 0, "arc_segments": 0, "straight_segments": 0}

    for chain in chains:
        if len(chain.points) < 2:
            continue

        if promote_arcs and len(chain.points) >= 3:
            # Promote to arc segments with bulge values
            promoted = promote_chain_to_arcs(
                chain,
                tolerance_mm=arc_tolerance_mm,
                max_error_mm=arc_max_error_mm,
            )

            # Create POLYLINE and add vertices with bulge
            polyline = msp.add_polyline2d(
                [],
                dxfattribs={"layer": chain.layer},
                close=chain.is_closed,
            )

            for (x, y), bulge in promoted:
                polyline.append_vertices([(x, y)], dxfattribs={"bulge": bulge})
                if abs(bulge) > 0.001:
                    counts["arc_segments"] += 1
                else:
                    counts["straight_segments"] += 1

            counts["polyline"] += 1

        elif use_polyline and len(chain.points) >= 3:
            # Write as old-style POLYLINE (R12 compatible), no bulge
            points = [p.as_tuple() for p in chain.points]
            msp.add_polyline2d(
                points,
                dxfattribs={"layer": chain.layer},
                close=chain.is_closed,
            )
            counts["polyline"] += 1
            counts["straight_segments"] += len(points) - 1
        else:
            # Write as LINE segments
            points = [p.as_tuple() for p in chain.points]
            for i in range(len(points) - 1):
                msp.add_line(
                    points[i],
                    points[i + 1],
                    dxfattribs={"layer": chain.layer},
                )
                counts["line"] += 1
                counts["straight_segments"] += 1

    doc.saveas(output_path)
    return counts


# ─── Verification block ────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Section A tests
    p1 = Point(0, 0)
    p2 = Point(3, 4)
    assert abs(p1.distance_to(p2) - 5.0) < 0.001, "Distance calculation failed"

    chain = Chain(points=[p1, p2])
    assert chain.start == p1
    assert chain.end == p2
    assert abs(chain.length_mm() - 5.0) < 0.001

    gap = Gap(start=p1, end=p2, chain_idx=0)
    assert abs(gap.distance_mm - 5.0) < 0.001

    print("Section A: ALL PASS")

    # Section B tests
    # 100 points on a circle — should consolidate to few polylines
    pts = [(100 * math.cos(math.radians(i)), 100 * math.sin(math.radians(i)))
           for i in range(100)]
    result = consolidate_polyline(pts, angle_tol=20.0)
    print(f"Section B: 100 circle pts -> {len(result)} polylines (expect 1-10)")
    assert len(result) < 10, f"Too many polylines: {len(result)}"
    print("Section B: ALL PASS")

    # Section C tests - perfect circle: three points at 0, 90, 180 degrees on R=50
    p1 = (50, 0)
    p2 = (0, 50)
    p3 = (-50, 0)
    fit = fit_circle_3pts(p1, p2, p3)
    assert fit is not None, "fit_circle_3pts returned None"
    cx, cy, r = fit
    print(f"Section C: Center: ({cx:.1f}, {cy:.1f})  R: {r:.1f}  (expect 0,0,50)")
    assert abs(cx) < 0.1, f"Center X off: {cx}"
    assert abs(cy) < 0.1, f"Center Y off: {cy}"
    assert abs(r - 50) < 0.1, f"Radius off: {r}"
    print("Section C: ALL PASS")

    # Section D tests - spherical arch formulas
    # Known values from body_side_arc_solver.py verification
    R = 26.225 * 25.4  # 666.12mm
    D = 8.0 * 25.4     # 203.2mm (center of 16-inch body)
    f = falloff(R, D)
    print(f"Section D: Falloff at center: {f:.2f}mm (expect ~31.75mm)")
    assert abs(f - 31.75) < 1.0, f"Falloff off: {f}"

    # Sagitta formula round-trip
    chord = 94.2
    sagitta = 47.1
    R_calc = radius_from_chord_sagitta(chord, sagitta)
    print(f"Section D: R from chord/sagitta: {R_calc:.1f}mm (expect ~47.1mm)")
    assert abs(R_calc - 47.1) < 1.0, f"Radius from sagitta off: {R_calc}"
    print("Section D: ALL PASS")

    # Section E tests - zone classification
    # Acoustic: test all three zones
    assert classify_zone_by_y(100, 500, is_acoustic=True) == GapZone.UPPER_BOUT
    assert classify_zone_by_y(220, 500, is_acoustic=True) == GapZone.WAIST
    assert classify_zone_by_y(400, 500, is_acoustic=True) == GapZone.LOWER_BOUT
    # Electric: test horn tip
    assert classify_zone_by_y(50, 500, is_acoustic=False) == GapZone.HORN_TIP
    print("Section E: Zone classification: ALL PASS")

    # Section F test - basic ArcReconstructor instantiation
    recon = ArcReconstructor(
        arch_radius_mm=635.0,
        body_height_mm=500.0,
        is_acoustic=True,
    )
    print("Section F: ArcReconstructor instantiation: OK")

    # Section G test - ezdxf available
    import ezdxf
    print(f"Section G: ezdxf {ezdxf.__version__} available: OK")

    print("\n=== All sections verified ===\n")


# ─── Section H: Test Harness and Entry Point ───────────────────────────────────

def create_visual_test_dxf(output_path: str) -> str:
    """
    Create a synthetic guitar body outline with deliberate gaps for visual testing.

    Creates:
    1. A guitar body shape (upper bout, waist, lower bout)
    2. Deliberate gaps at key positions
    3. Returns path to the created DXF
    """
    import ezdxf

    doc = ezdxf.new(dxfversion="R12")
    msp = doc.modelspace()
    doc.layers.add("BODY", dxfattribs={"color": 7})

    # Guitar body dimensions (simplified dreadnought-like shape)
    body_height = 500.0
    upper_bout_width = 280.0
    waist_width = 220.0
    lower_bout_width = 380.0

    # Create body outline with gaps
    # Upper bout arc (left side) - with gap
    points_upper_left = []
    for i in range(0, 80):  # Stop at 80 to create gap
        angle = math.radians(90 + i)
        x = -waist_width/2 + (upper_bout_width/2 - waist_width/2) * math.cos(angle) * 0.8
        y = body_height * 0.15 + 80 * math.sin(angle)
        points_upper_left.append((x, y))

    if len(points_upper_left) >= 2:
        msp.add_polyline2d(points_upper_left, dxfattribs={"layer": "BODY"})

    # Upper bout arc (right side) - continues after gap
    points_upper_right = []
    for i in range(100, 180):  # Start at 100 to show gap from 80-100
        angle = math.radians(90 + i)
        x = waist_width/2 + (upper_bout_width/2 - waist_width/2) * math.cos(angle) * 0.8
        y = body_height * 0.15 + 80 * math.sin(angle)
        points_upper_right.append((x, y))

    if len(points_upper_right) >= 2:
        msp.add_polyline2d(points_upper_right, dxfattribs={"layer": "BODY"})

    # Waist section (left side) - with gap
    points_waist_left = []
    for i in range(0, 40):
        t = i / 50.0
        x = -waist_width/2 - 20 * math.sin(t * math.pi)
        y = body_height * 0.3 + t * body_height * 0.2
        points_waist_left.append((x, y))

    if len(points_waist_left) >= 2:
        msp.add_polyline2d(points_waist_left, dxfattribs={"layer": "BODY"})

    # Lower bout arc (simplified ellipse, left half) - with gap
    points_lower_left = []
    for i in range(90, 250):  # Partial arc with gap
        angle = math.radians(i)
        x = lower_bout_width/2 * math.cos(angle) * 0.9
        y = body_height * 0.7 + 120 * math.sin(angle) * 0.8
        points_lower_left.append((x, y))

    if len(points_lower_left) >= 2:
        msp.add_polyline2d(points_lower_left, dxfattribs={"layer": "BODY"})

    # Lower bout arc (right half) - after gap
    points_lower_right = []
    for i in range(270, 400):
        angle = math.radians(i)
        x = lower_bout_width/2 * math.cos(angle) * 0.9
        y = body_height * 0.7 + 120 * math.sin(angle) * 0.8
        points_lower_right.append((x, y))

    if len(points_lower_right) >= 2:
        msp.add_polyline2d(points_lower_right, dxfattribs={"layer": "BODY"})

    doc.saveas(output_path)
    return output_path


def create_simple_gap_test_dxf(output_path: str) -> str:
    """
    Create a simple circle with a visible gap for clear visual testing.
    """
    import ezdxf

    doc = ezdxf.new(dxfversion="R12")
    msp = doc.modelspace()
    doc.layers.add("BODY", dxfattribs={"color": 7})

    # Circle with 20-degree gap (visible)
    radius = 100.0
    points = []
    for i in range(0, 340):  # 0 to 340 degrees, leaving 20-degree gap
        angle = math.radians(i)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        points.append((x, y))

    msp.add_polyline2d(points, dxfattribs={"layer": "BODY"})
    doc.saveas(output_path)
    return output_path


# Test file paths (absolute paths for reliability)
TEST_FILES = {
    "dreadnought": "C:/Users/thepr/Downloads/luthiers-toolbox/phase4_output/dreadnought_200dpi_gap_joined.dxf",
    "om": "C:/Users/thepr/Downloads/luthiers-toolbox/phase4_output/om_acoustic_gap_joined.dxf",
    "melody_maker": "C:/Users/thepr/Downloads/luthiers-toolbox/phase4_output/melody_maker_gap_joined.dxf",
}

# Arch radius reference (mm)
ARCH_RADII = {
    "dreadnought": 635.0,   # 25-foot
    "om": 711.0,            # 28-inch
    "jumbo": 635.0,         # 25-foot
    "parlour": 762.0,       # 30-inch
    "classical": None,      # flat
    "melody_maker": None,   # flat (electric)
}

# Body heights (mm)
BODY_HEIGHTS = {
    "dreadnought": 520.0,
    "om": 476.0,
    "melody_maker": 450.0,
}


def test_reconstructor_synthetic() -> bool:
    """
    Synthetic test: circle with 10% gap.

    Creates a circle, removes 10% of points to create a gap,
    then verifies the reconstructor bridges it.
    """
    print("\n" + "=" * 60)
    print("SYNTHETIC TEST: Circle with 10% gap")
    print("=" * 60)

    # Generate circle with 360 points
    radius = 100.0
    num_points = 360
    gap_start = 324  # ~90% through the circle
    gap_end = 360    # 10% gap

    # Create circle points with gap
    circle_points = []
    for i in range(num_points):
        if gap_start <= i < gap_end:
            continue  # Skip these points to create gap
        angle = math.radians(i)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        circle_points.append(Point(x, y))

    chain = Chain(points=circle_points, layer="BODY")
    print(f"Original chain: {len(chain.points)} points")

    # Run reconstructor
    recon = ArcReconstructor(
        min_gap_mm=1.0,
        max_gap_mm=100.0,
        body_height_mm=200.0,
        is_acoustic=False,
    )
    result = recon.complete([chain])

    print(f"Gaps found: {result.gaps_found}")
    print(f"Gaps bridged: {result.gaps_bridged}")
    print(f"Tier usage: {result.tier_usage}")

    if result.chains:
        print(f"Reconstructed chain: {len(result.chains[0].points)} points")

    # Verify
    success = result.gaps_found >= 1 and result.gaps_bridged >= 1
    if success:
        tier_used = [k for k, v in result.tier_usage.items() if v > 0]
        print(f"Tier used: {tier_used[0] if tier_used else 'none'}")
        print("Circle successfully reconstructed")
    else:
        print("FAILED: Gap not bridged")

    return success


def run_on_dxf(
    input_path: str,
    output_path: str,
    arch_radius_mm: Optional[float] = None,
    body_height_mm: Optional[float] = None,
    is_acoustic: bool = True,
) -> bool:
    """
    Run arc reconstruction on a DXF file.

    Args:
        input_path: Input DXF file
        output_path: Output DXF file
        arch_radius_mm: Spherical arch radius for Tier 2
        body_height_mm: Body height for zone classification
        is_acoustic: True for acoustic body shapes

    Returns:
        True if successful
    """
    print(f"\nProcessing: {input_path}")
    print(f"Output: {output_path}")

    # Load chains
    chains = load_chains_from_dxf(input_path, layer_filter="BODY")
    print(f"Loaded {len(chains)} chains from BODY layer")

    if not chains:
        # Try without layer filter
        chains = load_chains_from_dxf(input_path, layer_filter=None)
        print(f"Loaded {len(chains)} chains (all layers)")

    if not chains:
        print("ERROR: No chains found in DXF")
        return False

    total_points = sum(len(c.points) for c in chains)
    print(f"Total points: {total_points}")

    # Run reconstructor
    recon = ArcReconstructor(
        min_gap_mm=0.5,
        max_gap_mm=50.0,
        arch_radius_mm=arch_radius_mm,
        body_height_mm=body_height_mm,
        is_acoustic=is_acoustic,
    )
    result = recon.complete(chains)

    print(f"Duplicates removed: {result.duplicates_removed}")
    print(f"Chains after dedup: {len(result.chains)}")
    print(f"Gaps found: {result.gaps_found}")
    print(f"Gaps bridged: {result.gaps_bridged}")
    print(f"Tier usage: {result.tier_usage}")

    # Write output
    counts = chains_to_dxf(
        result.chains,
        output_path,
        use_polyline=True,
        use_arc=False,
    )
    print(f"Written: {counts}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Arc Reconstructor - Three-tier gap bridging for guitar body outlines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python arc_reconstructor.py --synthetic
  python arc_reconstructor.py --input dxf_file.dxf --output result.dxf
  python arc_reconstructor.py --spec dreadnought
        """,
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Run synthetic circle test",
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Input DXF file path",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output DXF file path",
    )
    parser.add_argument(
        "--spec",
        type=str,
        choices=list(TEST_FILES.keys()),
        help="Use preset test file and parameters",
    )
    parser.add_argument(
        "--arch-radius",
        type=float,
        help="Spherical arch radius in mm (for Tier 2)",
    )
    parser.add_argument(
        "--body-height",
        type=float,
        help="Body height in mm (for zone classification)",
    )
    parser.add_argument(
        "--acoustic",
        action="store_true",
        default=True,
        help="Acoustic body shape (default: True)",
    )
    parser.add_argument(
        "--electric",
        action="store_true",
        help="Electric body shape",
    )

    args = parser.parse_args()

    # No args = run unit tests
    if not any([args.synthetic, args.input, args.spec]):
        print("Running section verification tests...\n")
        # Re-run the verification block
        exec(compile(open(__file__).read(), __file__, "exec"), {"__name__": "__main__"})
        return

    # Synthetic test
    if args.synthetic:
        success = test_reconstructor_synthetic()
        exit(0 if success else 1)

    # Spec-based test
    if args.spec:
        if args.spec not in TEST_FILES:
            print(f"Unknown spec: {args.spec}")
            exit(1)

        input_path = TEST_FILES[args.spec]
        output_dir = Path(__file__).parent / "results"
        output_path = str(output_dir / f"{args.spec}_reconstructed.dxf")

        arch_radius = args.arch_radius or ARCH_RADII.get(args.spec)
        body_height = args.body_height or BODY_HEIGHTS.get(args.spec, 500.0)
        is_acoustic = not args.electric and args.spec not in ["melody_maker"]

        success = run_on_dxf(
            input_path=input_path,
            output_path=output_path,
            arch_radius_mm=arch_radius,
            body_height_mm=body_height,
            is_acoustic=is_acoustic,
        )
        exit(0 if success else 1)

    # Custom input/output
    if args.input:
        if not args.output:
            print("ERROR: --output required with --input")
            exit(1)

        is_acoustic = not args.electric
        success = run_on_dxf(
            input_path=args.input,
            output_path=args.output,
            arch_radius_mm=args.arch_radius,
            body_height_mm=args.body_height,
            is_acoustic=is_acoustic,
        )
        exit(0 if success else 1)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main()
    else:
        # Run section verification tests
        exec(open(__file__).read())
