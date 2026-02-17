"""
Parametric Guitar Body Outline Generator using Cubic Bézier Curves.

Implements the standard lutherie approach:
- Two cubic Bézier segments per side (neck→waist, waist→tail)
- C¹ continuity at waist for smooth toolpaths
- Parametric control via lutherie dimensions (upper bout, waist, lower bout, body length)

Coordinate System:
    x: along body length (0 = neck end, L = tail end)
    y: half-width (right side positive, left side is mirror)

Usage:
    from app.generators.bezier_body import BezierBodyParams, BezierBodyGenerator

    params = BezierBodyParams.dreadnought()
    generator = BezierBodyGenerator(params)
    outline = generator.generate_outline(resolution=200)
    generator.to_dxf("body_outline.dxf")
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal

import numpy as np

# Optional DXF export
try:
    import ezdxf
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False


@dataclass
class BezierBodyParams:
    """
    Parametric guitar body dimensions.

    All dimensions in inches (standard lutherie units).
    Angles in degrees.
    """
    # Core dimensions
    body_length: float          # L: total body length (neck block to tail)
    upper_bout_width: float     # W_u: width at upper bout
    waist_width: float          # W_w: width at waist (narrowest)
    lower_bout_width: float     # W_ℓ: width at lower bout

    # Station positions (as fraction of body_length, 0-1)
    waist_position: float = 0.48   # x_w/L: where waist occurs (0.45-0.55 typical)
    upper_bout_position: float = 0.20  # x_u/L: where upper bout is measured
    lower_bout_position: float = 0.75  # x_ℓ/L: where lower bout is measured

    # End widths (often close to adjacent bout widths)
    neck_end_width: float | None = None   # W_0: width at neck block (defaults to upper_bout * 0.85)
    tail_end_width: float | None = None   # W_t: width at tail (defaults to lower_bout * 0.92)

    # Tangent angles at key points (degrees, 0 = horizontal)
    waist_tangent_angle: float = 0.0      # θ_w: tangent at waist (typically ~0)
    neck_tangent_angle: float = -15.0     # θ_0: tangent at neck end (negative = rolls into upper bout)
    tail_tangent_angle: float = 12.0      # θ_2: tangent at tail end (positive = rounds into lower bout)

    # Handle lengths (as fraction of body_length)
    waist_handle: float = 0.15     # α/L: controls waist tightness
    neck_handle: float = 0.18      # β_0/L: controls neck-to-upper-bout flare
    tail_handle: float = 0.16      # β_2/L: controls lower-bout-to-tail rounding

    # Model metadata
    model_name: str = "custom"

    def __post_init__(self):
        """Apply defaults for optional fields."""
        if self.neck_end_width is None:
            self.neck_end_width = self.upper_bout_width * 0.85
        if self.tail_end_width is None:
            self.tail_end_width = self.lower_bout_width * 0.92

    @classmethod
    def dreadnought(cls) -> BezierBodyParams:
        """Martin Dreadnought-style dimensions."""
        return cls(
            body_length=20.0,
            upper_bout_width=11.5,
            waist_width=11.0,
            lower_bout_width=15.625,
            waist_position=0.48,
            upper_bout_position=0.18,
            lower_bout_position=0.72,
            waist_tangent_angle=0.0,
            neck_tangent_angle=-12.0,
            tail_tangent_angle=10.0,
            waist_handle=0.14,
            neck_handle=0.20,
            tail_handle=0.15,
            model_name="dreadnought",
        )

    @classmethod
    def orchestra_model(cls) -> BezierBodyParams:
        """OM (Orchestra Model) dimensions."""
        return cls(
            body_length=19.375,
            upper_bout_width=10.0,
            waist_width=9.5,
            lower_bout_width=15.0,
            waist_position=0.50,
            upper_bout_position=0.20,
            lower_bout_position=0.75,
            waist_tangent_angle=0.0,
            neck_tangent_angle=-10.0,
            tail_tangent_angle=8.0,
            waist_handle=0.15,
            neck_handle=0.18,
            tail_handle=0.14,
            model_name="orchestra_model",
        )

    @classmethod
    def parlor(cls) -> BezierBodyParams:
        """Parlor guitar dimensions."""
        return cls(
            body_length=18.0,
            upper_bout_width=9.25,
            waist_width=8.0,
            lower_bout_width=13.5,
            waist_position=0.52,
            upper_bout_position=0.22,
            lower_bout_position=0.78,
            waist_tangent_angle=0.0,
            neck_tangent_angle=-8.0,
            tail_tangent_angle=6.0,
            waist_handle=0.16,
            neck_handle=0.16,
            tail_handle=0.12,
            model_name="parlor",
        )

    @classmethod
    def jumbo(cls) -> BezierBodyParams:
        """Jumbo (Gibson J-200 style) dimensions."""
        return cls(
            body_length=21.0,
            upper_bout_width=12.75,
            waist_width=11.25,
            lower_bout_width=16.75,
            waist_position=0.46,
            upper_bout_position=0.17,
            lower_bout_position=0.70,
            waist_tangent_angle=0.0,
            neck_tangent_angle=-15.0,
            tail_tangent_angle=12.0,
            waist_handle=0.13,
            neck_handle=0.22,
            tail_handle=0.18,
            model_name="jumbo",
        )

    @classmethod
    def classical(cls) -> BezierBodyParams:
        """Classical guitar dimensions."""
        return cls(
            body_length=19.0,
            upper_bout_width=11.0,
            waist_width=9.5,
            lower_bout_width=14.375,
            waist_position=0.50,
            upper_bout_position=0.20,
            lower_bout_position=0.76,
            waist_tangent_angle=0.0,
            neck_tangent_angle=-10.0,
            tail_tangent_angle=8.0,
            waist_handle=0.15,
            neck_handle=0.17,
            tail_handle=0.14,
            model_name="classical",
        )

    @classmethod
    def concert(cls) -> BezierBodyParams:
        """Concert (0/00) size dimensions."""
        return cls(
            body_length=18.875,
            upper_bout_width=9.5,
            waist_width=8.5,
            lower_bout_width=13.5,
            waist_position=0.51,
            upper_bout_position=0.21,
            lower_bout_position=0.77,
            waist_tangent_angle=0.0,
            neck_tangent_angle=-9.0,
            tail_tangent_angle=7.0,
            waist_handle=0.15,
            neck_handle=0.17,
            tail_handle=0.13,
            model_name="concert",
        )

    def to_dict(self) -> dict:
        """Export parameters to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> BezierBodyParams:
        """Create from dictionary."""
        return cls(**d)


@dataclass
class ControlPoints:
    """The 7 control points defining the body outline Bézier curves."""
    P0: tuple[float, float]   # Neck end point
    P1: tuple[float, float]   # Waist point (join)
    P2: tuple[float, float]   # Tail end point
    C_A1: tuple[float, float] # Segment A handle at neck
    C_A2: tuple[float, float] # Segment A handle at waist
    C_B1: tuple[float, float] # Segment B handle at waist
    C_B2: tuple[float, float] # Segment B handle at tail


def _deg_to_rad(deg: float) -> float:
    """Convert degrees to radians."""
    return deg * math.pi / 180.0


def _unit_vector(angle_deg: float) -> tuple[float, float]:
    """Unit vector from angle in degrees."""
    rad = _deg_to_rad(angle_deg)
    return (math.cos(rad), math.sin(rad))


def cubic_bezier(
    P0: tuple[float, float],
    C1: tuple[float, float],
    C2: tuple[float, float],
    P1: tuple[float, float],
    t: float | np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """
    Evaluate cubic Bézier curve at parameter t.

    B(t) = (1-t)³P₀ + 3(1-t)²t·C₁ + 3(1-t)t²·C₂ + t³P₁

    Args:
        P0: Start point
        C1: First control point
        C2: Second control point
        P1: End point
        t: Parameter value(s) in [0, 1]

    Returns:
        (x, y) arrays of curve points
    """
    t = np.atleast_1d(t)
    mt = 1 - t  # (1-t)

    # Bernstein basis polynomials
    b0 = mt ** 3
    b1 = 3 * (mt ** 2) * t
    b2 = 3 * mt * (t ** 2)
    b3 = t ** 3

    x = b0 * P0[0] + b1 * C1[0] + b2 * C2[0] + b3 * P1[0]
    y = b0 * P0[1] + b1 * C1[1] + b2 * C2[1] + b3 * P1[1]

    return x, y


class BezierBodyGenerator:
    """
    Generate guitar body outline from parametric Bézier curves.

    The outline consists of two cubic Bézier segments per side:
    - Segment A: neck end → waist
    - Segment B: waist → tail end

    The left side is the mirror image (y → -y).
    """

    def __init__(self, params: BezierBodyParams):
        self.params = params
        self._control_points: ControlPoints | None = None
        self._outline: list[tuple[float, float]] | None = None

    def compute_control_points(self) -> ControlPoints:
        """
        Compute the 7 control points from parameters.

        Uses the C¹ continuity constraint at the waist.
        """
        p = self.params
        L = p.body_length

        # Anchor points (on-curve)
        P0 = (0.0, p.neck_end_width / 2)
        P1 = (p.waist_position * L, p.waist_width / 2)
        P2 = (L, p.tail_end_width / 2)

        # Tangent unit vectors
        u0 = _unit_vector(p.neck_tangent_angle)
        v = _unit_vector(p.waist_tangent_angle)
        u2 = _unit_vector(p.tail_tangent_angle)

        # Handle lengths (absolute)
        alpha = p.waist_handle * L
        beta0 = p.neck_handle * L
        beta2 = p.tail_handle * L

        # Segment A control points (neck → waist)
        C_A1 = (P0[0] + beta0 * u0[0], P0[1] + beta0 * u0[1])
        C_A2 = (P1[0] - alpha * v[0], P1[1] - alpha * v[1])

        # Segment B control points (waist → tail)
        # C¹ continuity: C_B1 = P1 + α·v (mirror of C_A2 about P1)
        C_B1 = (P1[0] + alpha * v[0], P1[1] + alpha * v[1])
        C_B2 = (P2[0] - beta2 * u2[0], P2[1] - beta2 * u2[1])

        self._control_points = ControlPoints(
            P0=P0, P1=P1, P2=P2,
            C_A1=C_A1, C_A2=C_A2,
            C_B1=C_B1, C_B2=C_B2
        )
        return self._control_points

    @property
    def control_points(self) -> ControlPoints:
        """Get control points, computing if necessary."""
        if self._control_points is None:
            self.compute_control_points()
        return self._control_points

    def generate_segment_a(self, resolution: int = 50) -> list[tuple[float, float]]:
        """Generate points for Segment A (neck → waist)."""
        cp = self.control_points
        t = np.linspace(0, 1, resolution)
        x, y = cubic_bezier(cp.P0, cp.C_A1, cp.C_A2, cp.P1, t)
        return list(zip(x.tolist(), y.tolist()))

    def generate_segment_b(self, resolution: int = 50) -> list[tuple[float, float]]:
        """Generate points for Segment B (waist → tail)."""
        cp = self.control_points
        t = np.linspace(0, 1, resolution)
        x, y = cubic_bezier(cp.P1, cp.C_B1, cp.C_B2, cp.P2, t)
        return list(zip(x.tolist(), y.tolist()))

    def generate_right_side(self, resolution: int = 100) -> list[tuple[float, float]]:
        """Generate right side outline (positive y)."""
        seg_res = resolution // 2
        seg_a = self.generate_segment_a(seg_res)
        seg_b = self.generate_segment_b(seg_res)
        # Remove duplicate point at waist join
        return seg_a + seg_b[1:]

    def generate_left_side(self, resolution: int = 100) -> list[tuple[float, float]]:
        """Generate left side outline (negative y, mirrored)."""
        right = self.generate_right_side(resolution)
        # Mirror y, reverse order for continuous path
        return [(x, -y) for x, y in reversed(right)]

    def generate_outline(
        self,
        resolution: int = 200,
        closed: bool = True
    ) -> list[tuple[float, float]]:
        """
        Generate complete body outline.

        Args:
            resolution: Total number of points (split between sides)
            closed: If True, close the path by connecting back to start

        Returns:
            List of (x, y) points defining the outline
        """
        side_res = resolution // 2

        right = self.generate_right_side(side_res)
        left = self.generate_left_side(side_res)

        # Connect: right side (neck→tail) + left side (tail→neck)
        outline = right + left[1:]  # Remove duplicate tail point

        if closed and outline:
            # Close path
            outline.append(outline[0])

        self._outline = outline
        return outline

    def get_bounding_box(self) -> tuple[float, float, float, float]:
        """
        Get bounding box of the outline.

        Returns:
            (min_x, min_y, max_x, max_y)
        """
        if self._outline is None:
            self.generate_outline()

        xs = [p[0] for p in self._outline]
        ys = [p[1] for p in self._outline]
        return (min(xs), min(ys), max(xs), max(ys))

    def get_dimensions(self) -> dict[str, float]:
        """Get computed outline dimensions."""
        min_x, min_y, max_x, max_y = self.get_bounding_box()
        return {
            "length": max_x - min_x,
            "width": max_y - min_y,
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
        }

    def measure_width_at(self, x: float) -> float:
        """
        Measure total width at a given x position.

        Args:
            x: Position along body length

        Returns:
            Total width (both sides) at that x position
        """
        if self._outline is None:
            self.generate_outline()

        # Find points closest to x
        tolerance = self.params.body_length / 100
        nearby = [p for p in self._outline if abs(p[0] - x) < tolerance]

        if not nearby:
            return 0.0

        ys = [p[1] for p in nearby]
        return max(ys) - min(ys)

    def to_dxf(
        self,
        output_path: str | Path,
        layer_name: str = "BODY_OUTLINE",
        use_spline: bool = False
    ) -> Path:
        """
        Export outline to DXF file.

        Args:
            output_path: Output file path
            layer_name: DXF layer name
            use_spline: If True, export as spline; else as polyline

        Returns:
            Path to created file
        """
        if not HAS_EZDXF:
            raise ImportError("ezdxf required for DXF export: pip install ezdxf")

        if self._outline is None:
            self.generate_outline()

        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Create layer
        doc.layers.add(layer_name)

        if use_spline:
            # Export as B-spline
            points = [(x, y, 0) for x, y in self._outline]
            msp.add_spline(points, dxfattribs={"layer": layer_name})
        else:
            # Export as polyline
            points = [(x, y) for x, y in self._outline]
            msp.add_lwpolyline(points, close=True, dxfattribs={"layer": layer_name})

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        doc.saveas(str(output))

        return output

    def to_svg(
        self,
        output_path: str | Path,
        stroke_width: float = 0.02,
        padding: float = 0.5
    ) -> Path:
        """
        Export outline to SVG file.

        Args:
            output_path: Output file path
            stroke_width: Line width in inches
            padding: Padding around outline in inches

        Returns:
            Path to created file
        """
        if self._outline is None:
            self.generate_outline()

        min_x, min_y, max_x, max_y = self.get_bounding_box()

        width = (max_x - min_x) + 2 * padding
        height = (max_y - min_y) + 2 * padding

        # Offset to center in viewbox
        ox = padding - min_x
        oy = padding - min_y

        # Build path data
        points = [(x + ox, height - (y + oy)) for x, y in self._outline]  # Flip Y
        path_d = f"M {points[0][0]:.4f},{points[0][1]:.4f} "
        path_d += " ".join(f"L {x:.4f},{y:.4f}" for x, y in points[1:])
        path_d += " Z"

        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{width}in" height="{height}in"
     viewBox="0 0 {width} {height}">
  <title>{self.params.model_name} Body Outline</title>
  <path d="{path_d}"
        fill="none"
        stroke="black"
        stroke-width="{stroke_width}"/>
</svg>'''

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(svg)

        return output

    def to_json(self, output_path: str | Path | None = None) -> dict:
        """
        Export outline data to JSON.

        Args:
            output_path: If provided, save to file

        Returns:
            Dictionary with parameters, control points, and outline
        """
        cp = self.control_points

        data = {
            "params": self.params.to_dict(),
            "control_points": {
                "P0": cp.P0,
                "P1": cp.P1,
                "P2": cp.P2,
                "C_A1": cp.C_A1,
                "C_A2": cp.C_A2,
                "C_B1": cp.C_B1,
                "C_B2": cp.C_B2,
            },
            "dimensions": self.get_dimensions(),
        }

        if output_path:
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(data, indent=2))

        return data


# Preset registry
BODY_PRESETS: dict[str, BezierBodyParams] = {
    "dreadnought": BezierBodyParams.dreadnought(),
    "orchestra_model": BezierBodyParams.orchestra_model(),
    "om": BezierBodyParams.orchestra_model(),
    "parlor": BezierBodyParams.parlor(),
    "jumbo": BezierBodyParams.jumbo(),
    "classical": BezierBodyParams.classical(),
    "concert": BezierBodyParams.concert(),
}


def get_preset(name: str) -> BezierBodyParams:
    """Get preset parameters by name."""
    name_lower = name.lower().replace("-", "_").replace(" ", "_")
    if name_lower not in BODY_PRESETS:
        available = ", ".join(BODY_PRESETS.keys())
        raise ValueError(f"Unknown preset '{name}'. Available: {available}")
    return BODY_PRESETS[name_lower]


def list_presets() -> list[str]:
    """List available preset names."""
    return list(BODY_PRESETS.keys())
