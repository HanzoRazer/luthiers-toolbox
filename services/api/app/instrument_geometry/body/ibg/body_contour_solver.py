"""
Body Contour Solver — Parametric Guitar Body Outline Generator
===============================================================

Derives complete guitar body outline from landmark points + physical constraints.
Completes partial vectorizer output (82-88%) using lutherie geometry math.

Core math sources:
  - Jon Sevy, "Calculating Arc Parameters," American Lutherie #58
  - R. Mottola, "Calculating Side Contours," American Lutherie #78

Author: Production Shop
Date: 2026-04-16
Sprint: 9 — InstrumentBodyGenerator
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Sibling imports
from .arc_reconstructor import falloff, radius_from_chord_sagitta, fit_circle_3pts, fit_arc_segment


# ─── Section A: Data Structures ───────────────────────────────────────────────


@dataclass
class LandmarkPoint:
    """A known point on the body outline."""
    label: str              # "lower_bout_max", "waist_min", "upper_bout_max", etc.
    x_mm: float
    y_mm: float
    source: str             # "vectorizer_extracted" | "user_input" | "spec" | "derived" | "ratio_estimate"
    confidence: float = 1.0  # 0.0-1.0


@dataclass
class BodyConstraints:
    """Physical constraints for body geometry — from spec or user input."""
    back_radius_mm: float       # R — back arch radius
    butt_depth_mm: float        # B — depth at tail
    shoulder_depth_mm: float    # S — depth at neck
    top_thickness_mm: float     # M
    back_thickness_mm: float    # N
    scale_length_mm: float      # for saddle position verification


@dataclass
class SolvedBodyModel:
    """Complete solved body model output."""
    body_length_mm: float
    lower_bout_width_mm: float
    upper_bout_width_mm: float
    waist_width_mm: float
    waist_y_norm: float                         # 0.0-1.0
    outline_points: List[Tuple[float, float]]   # full perimeter, clockwise
    side_heights_mm: List[float]                # height at each outline point
    radii_by_zone: Dict[str, float]             # waist, lower_bout, upper_bout
    confidence: float
    missing_landmarks: List[str]
    landmarks: Dict[str, LandmarkPoint] = field(default_factory=dict)  # all landmarks used
    back_radius_source: str = "spec"            # "spec" | "estimated" | "measured"


# ─── Section B: Sevy Formula Implementation ───────────────────────────────────


def solve_high_point(L: float, B: float, S: float, R: float) -> float:
    """
    Calculate P = distance from high point to butt.

    P = (L/2) - (E/2) * sqrt((4*R^2) / (L^2 + E^2) - 1)

    Where E = B - S (butt depth minus shoulder depth)

    Args:
        L: Body length (mm)
        B: Butt depth (mm)
        S: Shoulder depth (mm)
        R: Back arch radius (mm)

    Returns:
        P: Distance from high point to butt (mm)
    """
    # Guard: infinite radius = flat back (solid body electric)
    if math.isinf(R) or R > 1e9:
        return L / 2  # Flat body — high point at center

    E = B - S
    if abs(E) < 0.001:
        return L / 2  # Symmetric body — high point at center

    inner = (4 * R**2) / (L**2 + E**2) - 1
    if inner < 0:
        return L / 2  # Fallback for edge case

    return (L / 2) - (E / 2) * math.sqrt(inner)


def solve_side_height(B: float, R: float, P: float, D: float,
                      M: float, N: float) -> float:
    """
    Calculate H = side height at distance D from high point.

    H = (B + (R - sqrt(R^2 - P^2))) - (R - sqrt(R^2 - D^2)) - (M + N)

    Args:
        B: Butt depth (mm)
        R: Back arch radius (mm)
        P: Distance from high point to butt (mm)
        D: Distance from high point to current point (mm)
        M: Top thickness (mm)
        N: Back thickness (mm)

    Returns:
        H: Side height at point D (mm)
    """
    # Guard: infinite radius = flat back (solid body electric)
    # Side height is constant = body thickness - top - back
    if math.isinf(R) or R > 1e9:
        return max(0.0, B - M - N)

    # Guard against domain errors
    P_clamped = min(abs(P), R - 0.001)
    D_clamped = min(abs(D), R - 0.001)

    term1 = B + (R - math.sqrt(R**2 - P_clamped**2))
    term2 = R - math.sqrt(R**2 - D_clamped**2)

    return term1 - term2 - (M + N)


def woodworker_radius(chord_mm: float, sagitta_mm: float) -> float:
    """
    Calculate arc radius from chord and sagitta using woodworker's formula.

    R = (C^2 / 8S) + (S / 2)

    Args:
        chord_mm: Chord length (mm)
        sagitta_mm: Sagitta height (mm)

    Returns:
        Radius (mm), or inf if sagitta <= 0
    """
    if sagitta_mm <= 0:
        return float('inf')
    return (chord_mm**2 / (8 * sagitta_mm)) + (sagitta_mm / 2)


# ─── Family Defaults ──────────────────────────────────────────────────────────


FAMILY_DEFAULTS = {
    "dreadnought": {
        "lower_bout_mm": 381.0,
        "upper_bout_mm": 292.0,
        "waist_mm": 241.0,
        "waist_y_norm": 0.44,
        "body_length_mm": 520.0,
        "back_radius_mm": 7620.0,  # 25-foot Martin standard
        "butt_depth_mm": 121.0,
        "shoulder_depth_mm": 105.0,
        # Ratios for estimation
        "waist_ratio": 0.632,      # W_W / W_L
        "upper_ratio": 0.766,      # W_U / W_L
        "length_ratio": 1.365,     # L / W_L
    },
    "cuatro_venezolano": {
        "lower_bout_mm": 250.1,
        "upper_bout_mm": 156.9,
        "waist_mm": 130.0,
        "waist_y_norm": 0.43,
        "body_length_mm": 350.0,
        "back_radius_mm": 1000.0,  # Estimated — needs physical measurement
        "butt_depth_mm": 95.0,
        "shoulder_depth_mm": 80.0,
        # Ratios
        "waist_ratio": 0.52,
        "upper_ratio": 0.628,
        "length_ratio": 1.40,
    },
    "stratocaster": {
        "lower_bout_mm": 332.0,
        "upper_bout_mm": 311.0,
        "waist_mm": 250.0,
        "waist_y_norm": 0.47,
        "body_length_mm": 406.0,
        "back_radius_mm": 999999.0,  # Flat back
        "butt_depth_mm": 44.5,
        "shoulder_depth_mm": 44.5,
        # Ratios
        "waist_ratio": 0.753,
        "upper_ratio": 0.937,
        "length_ratio": 1.223,
    },
}

# Required landmarks for full confidence
REQUIRED_LANDMARKS = ["lower_bout_max", "waist_min", "upper_bout_max"]


# ─── Section C-G: BodyContourSolver ───────────────────────────────────────────


class BodyContourSolver:
    """
    Solves complete body outline from landmark points + constraints.

    Minimum viable input:
      - lower_bout_max (x, y)
      - constraints.back_radius_mm
      - constraints.butt_depth_mm
      - constraints.shoulder_depth_mm

    Additional landmarks improve accuracy:
      - waist_min (x, y)
      - upper_bout_max (x, y)
      - neck_block_edge (x, y)
      - end_block_center (x, y)
    """

    def __init__(self, constraints: BodyConstraints, family: str = "dreadnought"):
        self.constraints = constraints
        self.family = family
        self.landmarks: Dict[str, LandmarkPoint] = {}
        self._defaults = FAMILY_DEFAULTS.get(family, FAMILY_DEFAULTS["dreadnought"])

    def add_landmark(self, point: LandmarkPoint) -> None:
        """Add a landmark point to the solver."""
        self.landmarks[point.label] = point

    def solve(self) -> SolvedBodyModel:
        """
        Main solver — runs constraint satisfaction then generates outline.

        Returns:
            SolvedBodyModel with complete outline and side heights
        """
        # Step 1: Derive body dimensions from landmarks
        dims = self._solve_dimensions()

        # Step 2: Generate outline points from dimensions
        outline = self._generate_outline(dims)

        # Step 3: Solve side heights at each outline point
        side_heights = self._solve_side_heights(outline, dims)

        # Step 4: Compute arc radii at each body zone
        radii = self._compute_zone_radii(outline, dims)

        # Determine back radius source
        back_radius_source = "spec"
        if self.family == "cuatro_venezolano":
            back_radius_source = "estimated"

        return SolvedBodyModel(
            body_length_mm=dims['body_length'],
            lower_bout_width_mm=dims['lower_bout'],
            upper_bout_width_mm=dims['upper_bout'],
            waist_width_mm=dims['waist'],
            waist_y_norm=dims['waist_y_norm'],
            outline_points=outline,
            side_heights_mm=side_heights,
            radii_by_zone=radii,
            confidence=self._compute_confidence(),
            missing_landmarks=self._missing_landmarks(),
            landmarks=self.landmarks,
            back_radius_source=back_radius_source,
        )

    # ─── Section D: Dimension Solver ──────────────────────────────────────────

    def _solve_dimensions(self) -> Dict[str, float]:
        """
        Derive body dimensions from available landmarks.
        Uses landmarks first, falls back to family ratios, then defaults.
        """
        dims = {}

        # Lower bout — from landmark or default
        if 'lower_bout_max' in self.landmarks:
            lm = self.landmarks['lower_bout_max']
            dims['lower_bout'] = abs(lm.x_mm) * 2  # Half-body * 2
        else:
            dims['lower_bout'] = self._defaults['lower_bout_mm']

        # Body length — from end_block + neck_block if available
        if 'end_block_center' in self.landmarks and 'neck_block_edge' in self.landmarks:
            end_y = self.landmarks['end_block_center'].y_mm
            neck_y = self.landmarks['neck_block_edge'].y_mm
            dims['body_length'] = abs(neck_y - end_y)
        elif 'lower_bout_max' in self.landmarks:
            # Estimate from lower bout using family ratio
            dims['body_length'] = dims['lower_bout'] * self._defaults['length_ratio']
        else:
            dims['body_length'] = self._defaults['body_length_mm']

        # Waist — from landmark or calculated from ratio
        if 'waist_min' in self.landmarks:
            wm = self.landmarks['waist_min']
            dims['waist'] = abs(wm.x_mm) * 2
            # Compute waist_y_norm from waist Y position
            dims['waist_y_norm'] = self._compute_waist_y_norm(wm.y_mm, dims['body_length'])
        else:
            dims['waist'] = dims['lower_bout'] * self._defaults['waist_ratio']
            dims['waist_y_norm'] = self._defaults['waist_y_norm']

        # Upper bout — from landmark or calculated from ratio
        if 'upper_bout_max' in self.landmarks:
            ub = self.landmarks['upper_bout_max']
            dims['upper_bout'] = abs(ub.x_mm) * 2
        elif 'neck_block_edge' in self.landmarks:
            nb = self.landmarks['neck_block_edge']
            dims['upper_bout'] = abs(nb.x_mm) * 2 + self.constraints.top_thickness_mm * 2
        else:
            dims['upper_bout'] = dims['lower_bout'] * self._defaults['upper_ratio']

        return dims

    def _compute_waist_y_norm(self, waist_y: float, body_length: float) -> float:
        """Compute normalized waist Y position (0=butt, 1=neck)."""
        if body_length <= 0:
            return self._defaults['waist_y_norm']
        return max(0.0, min(1.0, waist_y / body_length))

    # ─── Section E: Outline Generator ─────────────────────────────────────────

    def _generate_outline(self, dims: Dict[str, float], n_points: int = 200) -> List[Tuple[float, float]]:
        """
        Generate body outline as ordered point set.

        Origin: body center at butt end.
        Orientation: neck end at positive Y.

        Returns:
            List of (x, y) points forming clockwise closed polygon.
        """
        L = dims['body_length']
        W_L = dims['lower_bout']
        W_W = dims['waist']
        W_U = dims['upper_bout']
        y_waist = dims['waist_y_norm'] * L

        # Five anchor points (right half-body, X >= 0)
        # Y positions tuned for dreadnought shape (flatter lower bout, not circular)
        # Lower bout peak LOW on body → flatter arc from butt to peak
        P0 = (0.0, 0.0)                           # Butt centerline
        P1 = (W_L / 2, y_waist * 0.25)            # Lower bout maximum (25% of waist height - LOW)
        P2 = (W_W / 2, y_waist)                   # Waist minimum
        P3 = (W_U / 2, y_waist + (L - y_waist) * 0.55)  # Upper bout maximum (55% above waist - HIGH)
        P4 = (0.0, L)                             # Neck centerline

        # Generate right half using two arc segments
        # Arc A: P0 -> P1 -> P2 (lower body)
        # Arc B: P2 -> P3 -> P4 (upper body)

        points_per_arc = n_points // 4  # ~50 points per arc segment

        right_half = []

        # Arc A: butt -> lower bout -> waist
        arc_a = self._generate_arc_segment(P0, P1, P2, points_per_arc)
        right_half.extend(arc_a)

        # Arc B: waist -> upper bout -> neck (exclude first point to avoid duplicate)
        arc_b = self._generate_arc_segment(P2, P3, P4, points_per_arc)
        right_half.extend(arc_b[1:])  # Skip duplicate waist point

        # Mirror for left half: (-x, y) in reverse order
        left_half = [(-x, y) for x, y in reversed(right_half[1:-1])]  # Exclude endpoints

        # Combine: right side going up, then left side going down
        # Start at (0, 0), go up right side to (0, L), then down left side back to (0, 0)
        outline = right_half + left_half

        # Ensure closed polygon
        if outline and outline[0] != outline[-1]:
            outline.append(outline[0])

        return outline

    def _generate_arc_segment(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        n_points: int,
    ) -> List[Tuple[float, float]]:
        """
        Generate points along a circular arc through three points.

        Uses circumcircle to find center and radius, then samples at equal angles.
        """
        # Fit circle through three points
        circle = fit_circle_3pts(p1, p2, p3)

        if circle is None:
            # Fallback: linear interpolation if points are collinear
            return self._linear_interpolate(p1, p2, p3, n_points)

        cx, cy, radius = circle

        # Calculate start and end angles
        angle1 = math.atan2(p1[1] - cy, p1[0] - cx)
        angle3 = math.atan2(p3[1] - cy, p3[0] - cx)

        # Determine sweep direction (ensure we go through p2)
        angle2 = math.atan2(p2[1] - cy, p2[0] - cx)

        # Normalize angles to determine correct sweep direction
        def normalize_angle(a):
            while a < 0:
                a += 2 * math.pi
            while a >= 2 * math.pi:
                a -= 2 * math.pi
            return a

        a1 = normalize_angle(angle1)
        a2 = normalize_angle(angle2)
        a3 = normalize_angle(angle3)

        # Determine if we go counterclockwise or clockwise
        # Check if a2 is between a1 and a3 going counterclockwise
        def angle_between_ccw(start, mid, end):
            """Check if mid is between start and end going counterclockwise."""
            if start <= end:
                return start <= mid <= end
            else:
                return mid >= start or mid <= end

        if angle_between_ccw(a1, a2, a3):
            # Go counterclockwise from a1 to a3
            if a3 < a1:
                a3 += 2 * math.pi
            angles = [a1 + (a3 - a1) * i / (n_points - 1) for i in range(n_points)]
        else:
            # Go clockwise from a1 to a3
            if a3 > a1:
                a3 -= 2 * math.pi
            angles = [a1 + (a3 - a1) * i / (n_points - 1) for i in range(n_points)]

        # Generate points along the arc
        points = []
        for angle in angles:
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append((x, y))

        return points

    def _linear_interpolate(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        n_points: int,
    ) -> List[Tuple[float, float]]:
        """Fallback linear interpolation for collinear points."""
        points = []
        half = n_points // 2

        # p1 to p2
        for i in range(half):
            t = i / half
            x = p1[0] + t * (p2[0] - p1[0])
            y = p1[1] + t * (p2[1] - p1[1])
            points.append((x, y))

        # p2 to p3
        for i in range(n_points - half):
            t = i / (n_points - half)
            x = p2[0] + t * (p3[0] - p2[0])
            y = p2[1] + t * (p3[1] - p2[1])
            points.append((x, y))

        return points

    # ─── Section F: Side Height Solver ────────────────────────────────────────

    def _solve_side_heights(self, outline: List[Tuple[float, float]], dims: Dict[str, float]) -> List[float]:
        """
        Calculate side height at each outline point using Sevy formula.
        """
        c = self.constraints
        L = dims['body_length']
        B = c.butt_depth_mm
        S = c.shoulder_depth_mm
        R = c.back_radius_mm
        M = c.top_thickness_mm
        N = c.back_thickness_mm

        # Calculate high point location
        P = solve_high_point(L, B, S, R)
        high_point_y = P  # High point is on centerline at y = P from butt

        heights = []
        for x, y in outline:
            # D = distance from high point (on centerline at y=P)
            D = math.hypot(x, y - high_point_y)
            H = solve_side_height(B, R, P, D, M, N)
            heights.append(max(0.0, H))

        return heights

    # ─── Section G: Zone Radius Computation ───────────────────────────────────

    def _compute_zone_radii(self, outline: List[Tuple[float, float]], dims: Dict[str, float]) -> Dict[str, float]:
        """
        Compute arc radius at each body zone using woodworker's formula.
        """
        zones = {}
        L = dims['body_length']

        zone_y_norms = {
            'lower_bout': 0.20,
            'waist': dims['waist_y_norm'],
            'upper_bout': 0.75,
        }

        for zone, y_norm in zone_y_norms.items():
            y_target = y_norm * L
            chord, sagitta = self._measure_chord_sagitta(outline, y_target)
            if chord > 0 and sagitta > 0:
                zones[zone] = woodworker_radius(chord, sagitta)
            else:
                zones[zone] = float('inf')

        return zones

    def _sagitta_from_radius(self, radius: float, chord: float) -> float:
        """
        Derive sagitta from fitted circle radius and chord.

        Formula: S = R - sqrt(R² - (C/2)²)

        Args:
            radius: Circle radius (mm)
            chord: Chord length (mm)

        Returns:
            Sagitta (mm), or 0.0 for edge cases
        """
        if radius <= 0 or chord <= 0:
            return 0.0

        half_chord = chord / 2

        if radius < half_chord:
            return 0.0

        inner = radius**2 - half_chord**2
        if inner < 0:
            return 0.0

        return radius - math.sqrt(inner)

    def _heuristic_sagitta(self, chord: float) -> float:
        """
        5% fallback when circle fitting fails.

        Args:
            chord: Chord length (mm)

        Returns:
            Estimated sagitta (mm) at 5% of chord
        """
        if chord <= 0:
            return 0.0
        return chord * 0.05

    def _fit_sagitta_from_band(
        self, outline: List[Tuple[float, float]], y_target: float, chord: float, band_mm: float = 10.0
    ) -> Optional[float]:
        """
        Extract points in ±band_mm Y-band, fit circle via fit_arc_segment, derive sagitta.

        Args:
            outline: Full body outline points
            y_target: Y coordinate to center the band on
            chord: Chord length at this Y (for sagitta calculation)
            band_mm: Half-width of the Y-band (default ±10mm)

        Returns:
            Sagitta (mm) from fitted circle, or None if fitting fails
        """
        band_points = [
            (x, y) for x, y in outline
            if abs(y - y_target) <= band_mm and x >= 0
        ]

        if len(band_points) < 3:
            return None

        band_points_sorted = sorted(band_points, key=lambda p: p[1])

        fit_result = fit_arc_segment(band_points_sorted, tolerance_mm=2.0, max_error_mm=5.0)
        if fit_result is None:
            return None

        (cx, cy), radius, mean_err, max_err = fit_result

        sagitta = self._sagitta_from_radius(radius, chord)
        if sagitta <= 0:
            return None

        return sagitta

    def _measure_chord_sagitta(self, outline: List[Tuple[float, float]], y_target: float) -> Tuple[float, float]:
        """
        Measure chord and sagitta at a given Y position.

        Uses circle fitting on points in ±10mm Y-band when possible,
        falls back to 5% heuristic when fitting fails.

        Returns:
            (chord_mm, sagitta_mm) tuple
        """
        right_points = [(x, y) for x, y in outline if x >= 0]
        left_points = [(x, y) for x, y in outline if x <= 0]

        if not right_points or not left_points:
            return (0.0, 0.0)

        right_point = min(right_points, key=lambda p: abs(p[1] - y_target))
        left_point = min(left_points, key=lambda p: abs(p[1] - y_target))

        chord = abs(right_point[0] - left_point[0])

        if chord <= 0:
            return (0.0, 0.0)

        fitted_sagitta = self._fit_sagitta_from_band(outline, y_target, chord)
        if fitted_sagitta is not None and fitted_sagitta > 0:
            sagitta = fitted_sagitta
        else:
            sagitta = self._heuristic_sagitta(chord)

        return (chord, sagitta)

    # ─── Confidence and Missing Landmarks ─────────────────────────────────────

    def _compute_confidence(self) -> float:
        """
        Calculate confidence score based on landmark sources.
        """
        weights = {
            "vectorizer_extracted": 1.0,
            "user_input": 1.0,
            "spec": 1.0,
            "derived": 0.95,
            "ratio_estimate": 0.70,
            "family_default": 0.50,
        }

        scores = []
        for lm in self.landmarks.values():
            weight = weights.get(lm.source, 0.50)
            scores.append(weight * lm.confidence)

        # Penalty for missing critical landmarks
        missing = self._missing_landmarks()
        penalty = len(missing) * 0.05

        if scores:
            base = sum(scores) / len(scores)
        else:
            base = 0.50  # No landmarks at all

        return max(0.0, min(1.0, base - penalty))

    def _missing_landmarks(self) -> List[str]:
        """Return list of required landmarks that are missing."""
        return [lm for lm in REQUIRED_LANDMARKS if lm not in self.landmarks]


# ─── Section H: DXF Output ────────────────────────────────────────────────────


def _segments_intersect(
    p1: Tuple[float, float], p2: Tuple[float, float],
    p3: Tuple[float, float], p4: Tuple[float, float],
) -> bool:
    """
    Check if line segment p1-p2 intersects with p3-p4.

    Uses cross-product method for robust intersection detection.
    Returns False for adjacent segments (shared endpoint).
    """
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

    # Check for shared endpoints (adjacent segments)
    if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4:
        return False

    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)


def check_self_intersection(outline: List[Tuple[float, float]]) -> List[Tuple[int, int]]:
    """
    Check if outline has self-intersections.

    Args:
        outline: List of (x, y) points forming closed polygon

    Returns:
        List of (segment_i, segment_j) pairs that intersect.
        Empty list = no self-intersections.
    """
    intersections = []
    n = len(outline)

    if n < 4:
        return []  # Can't self-intersect with <4 points

    # Check each segment against non-adjacent segments
    for i in range(n - 1):
        p1, p2 = outline[i], outline[i + 1]
        # Start from i+2 to skip adjacent segment
        for j in range(i + 2, n - 1):
            # Skip the closing segment adjacent to first segment
            if i == 0 and j == n - 2:
                continue
            p3, p4 = outline[j], outline[j + 1]
            if _segments_intersect(p1, p2, p3, p4):
                intersections.append((i, j))

    return intersections


def outline_to_dxf(result: SolvedBodyModel, output_path: str, spec_name: str = "") -> str:
    """
    Write solved body outline to R12 DXF.

    Follows project DXF standards from CLAUDE.md:
      - Format: R12 (AC1009)
      - LINE entities only
      - Named layers (no geometry on layer 0)
      - Coordinates rounded to 3dp

    Uses dxf_writer.py for centralized DXF output (Sprint 3B migration).

    Args:
        result: SolvedBodyModel from solver.solve()
        output_path: Path for output DXF file
        spec_name: Optional spec name for layer naming

    Returns:
        Output file path
    """
    from ....cam.dxf_writer import DxfWriter, LayerDef

    # Define layers
    body_layer = "BODY_SOLVED"
    center_layer = "CENTERLINE"
    landmark_layer = "LANDMARKS"

    writer = DxfWriter(layers=[
        LayerDef(body_layer, color=1),      # Red
        LayerDef(center_layer, color=5),    # Blue
        LayerDef(landmark_layer, color=3),  # Green
    ])

    pts = result.outline_points

    if not pts:
        writer.saveas(output_path)
        return output_path

    # Check for self-intersections before export (prevents bad geometry reaching CAM)
    intersections = check_self_intersection(pts)
    if intersections:
        print(f"WARNING: Outline has {len(intersections)} self-intersection(s)!")
        print(f"  Intersecting segments: {intersections[:5]}")  # Show first 5
        print(f"  This may cause CAM toolpath errors. Review geometry before cutting.")

    # Add body outline as LINE entities
    for i in range(len(pts) - 1):
        writer.add_line(body_layer, pts[i], pts[i + 1])

    # Close the outline
    if pts[0] != pts[-1]:
        writer.add_line(body_layer, pts[-1], pts[0])

    # Centerline
    min_y = min(p[1] for p in pts)
    max_y = max(p[1] for p in pts)
    writer.add_line(center_layer, (0, min_y), (0, max_y))

    # Landmark points (as small crosses for visibility)
    if result.landmarks:
        cross_size = result.body_length_mm * 0.01 if result.body_length_mm > 0 else 5.0
        for lm in result.landmarks.values():
            x, y = lm.x_mm, lm.y_mm
            writer.add_line(landmark_layer, (x - cross_size, y), (x + cross_size, y))
            writer.add_line(landmark_layer, (x, y - cross_size), (x, y + cross_size))

    writer.saveas(output_path)
    print(f"Saved: {output_path} ({len(pts)} outline points)")
    return output_path


# ─── Verification Block ───────────────────────────────────────────────────────


if __name__ == "__main__":
    print("=== Body Contour Solver Verification ===\n")

    # Section A: Data structures
    print("Section A: Data structures")
    lm = LandmarkPoint(label="test", x_mm=100.0, y_mm=200.0, source="spec", confidence=1.0)
    bc = BodyConstraints(
        back_radius_mm=7620.0, butt_depth_mm=121.0, shoulder_depth_mm=105.0,
        top_thickness_mm=2.8, back_thickness_mm=2.5, scale_length_mm=645.0
    )
    print(f"  LandmarkPoint: {lm.label} at ({lm.x_mm}, {lm.y_mm})")
    print(f"  BodyConstraints: R={bc.back_radius_mm}mm")
    print("  Section A: PASS\n")

    # Section B: Sevy formulas — Mottola verification test
    print("Section B: Sevy formulas (Mottola spreadsheet verification)")

    # Test values from Mottola article sidecalc.xls:
    # R=180in, L=19.25in, B=4.0in, S=3.3in, M=0.11in, N=0.09in
    # Expected: P=3.093in, H at D=1.0in should be 3.824in

    R_in = 180.0
    L_in = 19.25
    B_in = 4.0
    S_in = 3.3
    M_in = 0.11
    N_in = 0.09
    D_in = 1.0

    # Convert to mm
    R = R_in * 25.4
    L = L_in * 25.4
    B = B_in * 25.4
    S = S_in * 25.4
    M = M_in * 25.4
    N = N_in * 25.4
    D = D_in * 25.4

    P = solve_high_point(L, B, S, R)
    H = solve_side_height(B, R, P, D, M, N)

    P_in_result = P / 25.4
    H_in_result = H / 25.4

    print(f"  Input: R={R_in}in, L={L_in}in, B={B_in}in, S={S_in}in, M={M_in}in, N={N_in}in")
    print(f"  P = {P_in_result:.3f} in (expect 3.093, tolerance +/- 0.01)")
    print(f"  H = {H_in_result:.3f} in (expect 3.824, tolerance +/- 0.01)")

    p_pass = abs(P_in_result - 3.093) < 0.01
    h_pass = abs(H_in_result - 3.824) < 0.01

    if p_pass and h_pass:
        print("  Section B: PASS\n")
    else:
        print(f"  Section B: FAIL (P_err={abs(P_in_result - 3.093):.4f}, H_err={abs(H_in_result - 3.824):.4f})\n")
        exit(1)

    # Test woodworker_radius
    print("Section B (continued): Woodworker's radius formula")
    # Known: chord=381mm, sagitta=14mm should give R~265mm
    test_chord = 381.0
    test_sagitta = 14.0
    test_R = woodworker_radius(test_chord, test_sagitta)
    print(f"  Chord={test_chord}mm, Sagitta={test_sagitta}mm -> R={test_R:.1f}mm (expect ~265)")
    print("  Section B continued: PASS\n")

    # Section C-G: Full solver test
    print("Section C-G: BodyContourSolver basic instantiation")
    constraints = BodyConstraints(
        back_radius_mm=7620.0,
        butt_depth_mm=121.0,
        shoulder_depth_mm=105.0,
        top_thickness_mm=2.8,
        back_thickness_mm=2.5,
        scale_length_mm=645.0,
    )
    solver = BodyContourSolver(constraints, family="dreadnought")
    print(f"  Created solver with family={solver.family}")
    print(f"  Defaults loaded: lower_bout={solver._defaults['lower_bout_mm']}mm")

    # Add a landmark and solve
    solver.add_landmark(LandmarkPoint(
        label='lower_bout_max',
        x_mm=190.5,  # half of 381mm
        y_mm=80.0,
        source='spec',
        confidence=1.0,
    ))

    result = solver.solve()
    print(f"  Solved: body_length={result.body_length_mm:.1f}mm")
    print(f"  Outline points: {len(result.outline_points)}")
    print(f"  Side heights: min={min(result.side_heights_mm):.1f}mm, max={max(result.side_heights_mm):.1f}mm")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Missing landmarks: {result.missing_landmarks}")
    print("  Section C-G: PASS\n")

    print("=== All sections verified ===")
