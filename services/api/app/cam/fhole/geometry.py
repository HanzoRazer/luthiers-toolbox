# app/cam/fhole/geometry.py

"""
F-Hole Geometry Generator (BEN-GAP-09)

Generates parametric F-hole contours for archtop guitars.

F-holes are modeled as elongated shapes with:
- Pointed or rounded tips at top and bottom
- Curved upper and lower bouts
- Narrow waist connecting the bouts
- Traditional violin/archtop aesthetic
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional

from .config import FHoleGeometryConfig, FHolePositionConfig, FHoleStyle

Pt = Tuple[float, float]


@dataclass
class FHoleContour:
    """
    Generated F-hole contour with metadata.
    """

    points: List[Pt]  # Closed contour points (clockwise)
    center: Pt  # Center point of F-hole
    bounding_box: Tuple[float, float, float, float]  # min_x, min_y, max_x, max_y
    length_mm: float
    width_mm: float

    def to_dict(self) -> dict:
        return {
            "point_count": len(self.points),
            "center": self.center,
            "bounding_box": self.bounding_box,
            "length_mm": self.length_mm,
            "width_mm": self.width_mm,
        }


class FHoleGenerator:
    """
    Parametric F-hole contour generator.

    Generates smooth F-hole shapes using cubic Bezier curves
    that can be sampled at any resolution.
    """

    def __init__(self, config: FHoleGeometryConfig):
        self.config = config

    def generate(self) -> FHoleContour:
        """
        Generate F-hole contour centered at origin.

        Returns closed contour with clockwise winding.
        """
        if self.config.style == FHoleStyle.TRADITIONAL_ARCHTOP:
            points = self._generate_traditional()
        elif self.config.style == FHoleStyle.CONTEMPORARY:
            points = self._generate_contemporary()
        elif self.config.style == FHoleStyle.VENETIAN:
            points = self._generate_venetian()
        else:
            points = self._generate_traditional()

        # Calculate metadata
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

        return FHoleContour(
            points=points,
            center=center,
            bounding_box=bbox,
            length_mm=self.config.length_mm,
            width_mm=self.config.width_mm,
        )

    def _generate_traditional(self) -> List[Pt]:
        """
        Generate traditional archtop F-hole shape.

        The shape resembles a stylized 'f' with:
        - Pointed tips at top and bottom
        - Bulging upper and lower bouts
        - Narrow waist in the middle
        """
        cfg = self.config
        length = cfg.length_mm
        width = cfg.width_mm
        n_pts = cfg.points_per_curve

        # Key Y positions (from top = 0 to bottom = length)
        y_top = 0.0
        y_upper_bout = length * cfg.upper_bout_position
        y_waist = length * 0.5
        y_lower_bout = length * cfg.lower_bout_position
        y_bottom = length

        # Key X widths (half-widths from centerline)
        hw_tip_top = width * 0.05 * (1 - cfg.tip_sharpness)  # Pointed or round tip
        hw_upper = width * cfg.upper_bout_width_ratio * 0.5
        hw_waist = width * cfg.waist_width_ratio * 0.5
        hw_lower = width * cfg.lower_bout_width_ratio * 0.5
        hw_tip_bottom = width * 0.05 * (1 - cfg.tip_sharpness)

        points = []

        # Generate right side (positive X), top to bottom
        # Top tip
        points.append((hw_tip_top, y_top))

        # Top tip to upper bout (outward curve)
        for i in range(1, n_pts):
            t = i / n_pts
            y = y_top + t * (y_upper_bout - y_top)
            # Bezier-like curve bulging outward
            x = self._bezier_bulge(t, hw_tip_top, hw_upper, 0.4)
            points.append((x, y))

        # Upper bout point
        points.append((hw_upper, y_upper_bout))

        # Upper bout to waist (inward curve)
        for i in range(1, n_pts):
            t = i / n_pts
            y = y_upper_bout + t * (y_waist - y_upper_bout)
            x = self._bezier_bulge(t, hw_upper, hw_waist, -0.3)
            points.append((x, y))

        # Waist point
        points.append((hw_waist, y_waist))

        # Waist to lower bout (outward curve)
        for i in range(1, n_pts):
            t = i / n_pts
            y = y_waist + t * (y_lower_bout - y_waist)
            x = self._bezier_bulge(t, hw_waist, hw_lower, 0.3)
            points.append((x, y))

        # Lower bout point
        points.append((hw_lower, y_lower_bout))

        # Lower bout to bottom tip (inward curve)
        for i in range(1, n_pts):
            t = i / n_pts
            y = y_lower_bout + t * (y_bottom - y_lower_bout)
            x = self._bezier_bulge(t, hw_lower, hw_tip_bottom, -0.4)
            points.append((x, y))

        # Bottom tip
        points.append((hw_tip_bottom, y_bottom))

        # Generate left side (negative X), bottom to top (mirror)
        # Bottom tip to lower bout
        for i in range(1, n_pts):
            t = i / n_pts
            y = y_bottom - t * (y_bottom - y_lower_bout)
            x = -self._bezier_bulge(t, hw_tip_bottom, hw_lower, 0.4)
            points.append((x, y))

        # Lower bout
        points.append((-hw_lower, y_lower_bout))

        # Lower bout to waist
        for i in range(1, n_pts):
            t = i / n_pts
            y = y_lower_bout - t * (y_lower_bout - y_waist)
            x = -self._bezier_bulge(t, hw_lower, hw_waist, -0.3)
            points.append((x, y))

        # Waist
        points.append((-hw_waist, y_waist))

        # Waist to upper bout
        for i in range(1, n_pts):
            t = i / n_pts
            y = y_waist - t * (y_waist - y_upper_bout)
            x = -self._bezier_bulge(t, hw_waist, hw_upper, 0.3)
            points.append((x, y))

        # Upper bout
        points.append((-hw_upper, y_upper_bout))

        # Upper bout to top tip
        for i in range(1, n_pts):
            t = i / n_pts
            y = y_upper_bout - t * (y_upper_bout - y_top)
            x = -self._bezier_bulge(t, hw_upper, hw_tip_top, -0.4)
            points.append((x, y))

        # Close at top tip
        points.append((-hw_tip_top, y_top))

        # Center the F-hole vertically (Y=0 at center)
        y_center = length / 2
        points = [(x, y - y_center) for x, y in points]

        return points

    def _generate_contemporary(self) -> List[Pt]:
        """Generate simpler contemporary F-hole shape."""
        # Simplified version with less pronounced bouts
        cfg = self.config
        length = cfg.length_mm
        width = cfg.width_mm
        n_pts = cfg.points_per_curve

        points = []
        half_length = length / 2
        half_width = width / 2

        # Ellipse-like shape with pinched waist
        for i in range(n_pts * 4):
            t = 2 * math.pi * i / (n_pts * 4)
            # Base ellipse
            x = half_width * math.sin(t)
            y = half_length * math.cos(t)

            # Pinch the waist
            waist_factor = 1 - 0.3 * (1 - abs(math.cos(t)))
            x *= waist_factor

            points.append((x, y))

        return points

    def _generate_venetian(self) -> List[Pt]:
        """Generate elongated Venetian-style F-hole."""
        # More pointed tips, narrower overall
        cfg = self.config
        cfg_copy = FHoleGeometryConfig(
            length_mm=cfg.length_mm * 1.1,  # Longer
            width_mm=cfg.width_mm * 0.85,  # Narrower
            style=FHoleStyle.TRADITIONAL_ARCHTOP,
            tip_sharpness=0.85,  # More pointed
            waist_width_ratio=0.25,  # Narrower waist
            points_per_curve=cfg.points_per_curve,
        )
        gen = FHoleGenerator(cfg_copy)
        return gen._generate_traditional()

    def _bezier_bulge(
        self,
        t: float,
        start_x: float,
        end_x: float,
        bulge: float,
    ) -> float:
        """
        Calculate X position along a bulging curve.

        Args:
            t: Parameter 0..1 along curve
            start_x: Starting X position
            end_x: Ending X position
            bulge: Bulge amount (-1..1), positive = outward
        """
        # Quadratic Bezier with control point offset
        mid_x = (start_x + end_x) / 2 + bulge * max(start_x, end_x)

        # Quadratic Bezier: B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
        x = (
            (1 - t) ** 2 * start_x +
            2 * (1 - t) * t * mid_x +
            t ** 2 * end_x
        )
        return x


def transform_contour(
    contour: FHoleContour,
    position: FHolePositionConfig,
    mirror: bool = False,
) -> FHoleContour:
    """
    Transform F-hole contour to body position.

    Args:
        contour: Original centered contour
        position: Position configuration
        mirror: If True, mirror across X axis (for bass-side F-hole)

    Returns:
        Transformed contour
    """
    points = []
    angle_rad = math.radians(position.rotation_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    for x, y in contour.points:
        # Mirror if bass side
        if mirror:
            x = -x
            angle_rad_m = -angle_rad  # Opposite rotation for mirror
            cos_a = math.cos(angle_rad_m)
            sin_a = math.sin(angle_rad_m)

        # Rotate
        x_rot = x * cos_a - y * sin_a
        y_rot = x * sin_a + y * cos_a

        # Translate
        x_final = x_rot + (position.x_offset_mm if not mirror else -position.x_offset_mm)
        y_final = y_rot + position.y_offset_mm

        points.append((x_final, y_final))

    # Recalculate metadata
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

    return FHoleContour(
        points=points,
        center=center,
        bounding_box=bbox,
        length_mm=contour.length_mm,
        width_mm=contour.width_mm,
    )


def generate_fhole_pair(
    geometry: FHoleGeometryConfig,
    position: FHolePositionConfig,
) -> Tuple[FHoleContour, FHoleContour]:
    """
    Generate a pair of F-holes (treble and bass side).

    Returns:
        (treble_fhole, bass_fhole) tuple
    """
    generator = FHoleGenerator(geometry)
    base_contour = generator.generate()

    # Treble side (right, positive X)
    treble = transform_contour(base_contour, position, mirror=False)

    # Bass side (left, negative X)
    bass = transform_contour(base_contour, position, mirror=True)

    return treble, bass
