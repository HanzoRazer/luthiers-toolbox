"""
Logarithmic Concha Spiral Soundhole Generator.

Generates a nautilus-inspired spiral soundhole that conforms to the
upper bout curve of an acoustic guitar. The spiral follows a logarithmic
growth pattern, creating an organic aesthetic while maintaining proper
acoustic properties.

Mathematical basis:
  r(θ) = r_start × e^(k × θ)

Where:
  - r_start is the inner radius at spiral start
  - k is the growth rate per radian
  - θ is the angle in radians

The spiral slot has parallel walls offset ±(slot_width/2) perpendicular
to the spiral tangent at each point.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import ezdxf
from ezdxf.enums import TextEntityAlignment


@dataclass
class SpiralSoundholeSpec:
    """Specification for a logarithmic spiral soundhole."""

    bout_radius_mm: float  # Upper bout radius (e.g., 195mm for dreadnought)
    slot_width_mm: float  # Width of the spiral slot (e.g., 8mm)
    spiral_start_r_mm: float  # Inner radius at spiral start (e.g., 20mm)
    spiral_turns: float  # Number of turns (e.g., 0.85)
    growth_rate: float  # Logarithmic growth per radian (e.g., 15mm)
    center_x_mm: float = 0.0  # Center X position on top
    center_y_mm: float = 0.0  # Center Y position on top

    @property
    def growth_rate_per_radian(self) -> float:
        """Convert growth rate to the k constant in r = r0 * e^(k*θ)."""
        # The growth_rate parameter represents how much the radius grows
        # over one full turn (2π radians)
        if self.spiral_start_r_mm <= 0:
            return 0.0
        # r_end = r_start * e^(k * 2π * turns)
        # growth_rate ≈ r_end - r_start for small growth
        # Solve for k: k = ln(1 + growth_rate/r_start) / (2π * turns)
        total_angle = 2 * math.pi * self.spiral_turns
        if total_angle <= 0:
            return 0.0
        return math.log(1 + self.growth_rate / self.spiral_start_r_mm) / total_angle


@dataclass
class SpiralGeometry:
    """Computed geometry for a spiral soundhole."""

    centerline_points: List[Tuple[float, float]] = field(default_factory=list)
    outer_wall: List[Tuple[float, float]] = field(default_factory=list)
    inner_wall: List[Tuple[float, float]] = field(default_factory=list)
    area_mm2: float = 0.0
    perimeter_mm: float = 0.0
    pa_ratio_mm_inv: float = 0.0  # Perimeter to area ratio (1/mm)
    total_length_mm: float = 0.0  # Total centerline length


def _compute_spiral_point(
    r_start: float, k: float, theta: float, center_x: float, center_y: float
) -> Tuple[float, float]:
    """Compute a point on the logarithmic spiral."""
    r = r_start * math.exp(k * theta)
    x = center_x + r * math.cos(theta)
    y = center_y + r * math.sin(theta)
    return (x, y)


def _compute_tangent_normal(
    r_start: float, k: float, theta: float
) -> Tuple[float, float]:
    """
    Compute the unit normal vector perpendicular to the spiral at angle θ.

    For r = r0 * e^(k*θ):
      dr/dθ = k * r
      dx/dθ = dr/dθ * cos(θ) - r * sin(θ) = r * (k*cos(θ) - sin(θ))
      dy/dθ = dr/dθ * sin(θ) + r * cos(θ) = r * (k*sin(θ) + cos(θ))

    Normal is perpendicular to tangent: (-dy/dθ, dx/dθ) normalized
    """
    r = r_start * math.exp(k * theta)

    # Tangent components (not normalized by r since it cancels)
    tx = k * math.cos(theta) - math.sin(theta)
    ty = k * math.sin(theta) + math.cos(theta)

    # Normal is perpendicular to tangent (rotate 90°)
    nx = -ty
    ny = tx

    # Normalize
    length = math.sqrt(nx * nx + ny * ny)
    if length < 1e-10:
        return (0.0, 1.0)

    return (nx / length, ny / length)


def _polyline_length(points: List[Tuple[float, float]]) -> float:
    """Compute the total length of a polyline."""
    if len(points) < 2:
        return 0.0

    total = 0.0
    for i in range(1, len(points)):
        dx = points[i][0] - points[i - 1][0]
        dy = points[i][1] - points[i - 1][1]
        total += math.sqrt(dx * dx + dy * dy)

    return total


def _shoelace_area(points: List[Tuple[float, float]]) -> float:
    """Compute the area of a polygon using the shoelace formula."""
    if len(points) < 3:
        return 0.0

    n = len(points)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]

    return abs(area) / 2.0


def compute_spiral_geometry(
    spec: SpiralSoundholeSpec, num_points: int = 100
) -> SpiralGeometry:
    """
    Compute the full geometry of a spiral soundhole.

    Args:
        spec: The spiral specification
        num_points: Number of points to sample along the spiral

    Returns:
        SpiralGeometry with centerline, walls, and metrics
    """
    k = spec.growth_rate_per_radian
    total_angle = 2 * math.pi * spec.spiral_turns

    centerline: List[Tuple[float, float]] = []
    outer_wall: List[Tuple[float, float]] = []
    inner_wall: List[Tuple[float, float]] = []

    half_width = spec.slot_width_mm / 2.0

    for i in range(num_points):
        theta = (i / (num_points - 1)) * total_angle if num_points > 1 else 0

        # Centerline point
        cx, cy = _compute_spiral_point(
            spec.spiral_start_r_mm, k, theta, spec.center_x_mm, spec.center_y_mm
        )
        centerline.append((cx, cy))

        # Normal vector at this point
        nx, ny = _compute_tangent_normal(spec.spiral_start_r_mm, k, theta)

        # Offset for outer and inner walls
        outer_wall.append((cx + nx * half_width, cy + ny * half_width))
        inner_wall.append((cx - nx * half_width, cy - ny * half_width))

    # Compute metrics
    centerline_length = _polyline_length(centerline)
    outer_length = _polyline_length(outer_wall)
    inner_length = _polyline_length(inner_wall)

    # The slot forms a ribbon - approximate area as centerline_length × slot_width
    # More accurate: use the actual closed polygon formed by outer + reversed inner
    slot_polygon = outer_wall + list(reversed(inner_wall))
    area = _shoelace_area(slot_polygon)

    # Perimeter is outer + inner wall lengths plus the two end caps
    # End caps are approximately slot_width each
    perimeter = outer_length + inner_length + 2 * spec.slot_width_mm

    pa_ratio = perimeter / area if area > 0 else 0.0

    return SpiralGeometry(
        centerline_points=centerline,
        outer_wall=outer_wall,
        inner_wall=inner_wall,
        area_mm2=area,
        perimeter_mm=perimeter,
        pa_ratio_mm_inv=pa_ratio,
        total_length_mm=centerline_length,
    )


def generate_dxf(spec: SpiralSoundholeSpec, output_path: Path | str) -> Path:
    """
    Generate an R2000 DXF file with the spiral soundhole geometry.

    Layers:
        SPIRAL_CENTERLINE  - Reference line (not cut)
        SPIRAL_OUTER_WALL  - Cut path
        SPIRAL_INNER_WALL  - Cut path
        BOUT_REFERENCE     - Upper bout arc (reference only)

    Args:
        spec: The spiral specification
        output_path: Path for the output DXF file

    Returns:
        Path to the generated DXF file
    """
    output_path = Path(output_path)
    geometry = compute_spiral_geometry(spec)

    doc = ezdxf.new(dxfversion="R2000")
    msp = doc.modelspace()

    # Create layers
    doc.layers.add("SPIRAL_CENTERLINE", color=7)  # White - reference
    doc.layers.add("SPIRAL_OUTER_WALL", color=1)  # Red - cut
    doc.layers.add("SPIRAL_INNER_WALL", color=1)  # Red - cut
    doc.layers.add("BOUT_REFERENCE", color=5)  # Blue - reference

    # Draw centerline as polyline
    if geometry.centerline_points:
        msp.add_lwpolyline(
            geometry.centerline_points, dxfattribs={"layer": "SPIRAL_CENTERLINE"}
        )

    # Draw outer wall as polyline
    if geometry.outer_wall:
        msp.add_lwpolyline(
            geometry.outer_wall, dxfattribs={"layer": "SPIRAL_OUTER_WALL"}
        )

    # Draw inner wall as polyline
    if geometry.inner_wall:
        msp.add_lwpolyline(
            geometry.inner_wall, dxfattribs={"layer": "SPIRAL_INNER_WALL"}
        )

    # Draw bout reference arc
    # The bout arc is centered at the spiral center, with radius = bout_radius_mm
    # We draw an arc that spans the spiral extent
    total_angle = 2 * math.pi * spec.spiral_turns
    start_angle_deg = 0
    end_angle_deg = math.degrees(total_angle)

    msp.add_arc(
        center=(spec.center_x_mm, spec.center_y_mm),
        radius=spec.bout_radius_mm,
        start_angle=start_angle_deg,
        end_angle=end_angle_deg,
        dxfattribs={"layer": "BOUT_REFERENCE"},
    )

    # Add dimension text
    doc.layers.add("DIMENSIONS", color=3)  # Green
    text_y = spec.center_y_mm - spec.bout_radius_mm - 20

    msp.add_text(
        f"Spiral: {spec.spiral_turns:.2f} turns, "
        f"Start R={spec.spiral_start_r_mm:.1f}mm, "
        f"Slot W={spec.slot_width_mm:.1f}mm",
        height=3,
        dxfattribs={
            "layer": "DIMENSIONS",
            "insert": (spec.center_x_mm - 50, text_y),
        },
    )

    msp.add_text(
        f"Area={geometry.area_mm2:.1f}mm², "
        f"P:A={geometry.pa_ratio_mm_inv:.4f}/mm",
        height=3,
        dxfattribs={
            "layer": "DIMENSIONS",
            "insert": (spec.center_x_mm - 50, text_y - 5),
        },
    )

    doc.saveas(str(output_path))
    return output_path


def spec_to_dict(spec: SpiralSoundholeSpec) -> dict:
    """Convert spec to dictionary for JSON serialization."""
    return {
        "bout_radius_mm": spec.bout_radius_mm,
        "slot_width_mm": spec.slot_width_mm,
        "spiral_start_r_mm": spec.spiral_start_r_mm,
        "spiral_turns": spec.spiral_turns,
        "growth_rate": spec.growth_rate,
        "center_x_mm": spec.center_x_mm,
        "center_y_mm": spec.center_y_mm,
    }


def geometry_to_dict(geom: SpiralGeometry) -> dict:
    """Convert geometry to dictionary for JSON serialization."""
    return {
        "centerline_points": geom.centerline_points,
        "outer_wall": geom.outer_wall,
        "inner_wall": geom.inner_wall,
        "area_mm2": geom.area_mm2,
        "perimeter_mm": geom.perimeter_mm,
        "pa_ratio_mm_inv": geom.pa_ratio_mm_inv,
        "total_length_mm": geom.total_length_mm,
    }
