"""
Rosette Geometry — Core geometric primitives and constants.

All geometry in SVG units (1 unit = 0.01 inch). Inch conversions at boundaries.
"""
from __future__ import annotations

import math
from typing import Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Manufacturing Thresholds
# ─────────────────────────────────────────────────────────────────────────────

MFG_THRESHOLDS = {
    "FRAGILE_ARC": 0.060,
    "FRAGILE_DEPTH": 0.060,
    "NARROW_ARC": 0.100,
    "NARROW_DEPTH": 0.080,
    "MAX_SEGS_OUTER": 24,
    "THIN_TAB_ARC": 0.050,
}


# ─────────────────────────────────────────────────────────────────────────────
# Feasibility Specs
# ─────────────────────────────────────────────────────────────────────────────

class MaterialSpec:
    """Minimal material specification for feasibility checks."""
    def __init__(self, material_id: str, name: str, material_class: str):
        self.material_id = material_id
        self.name = name
        self.material_class = material_class


class ToolSpec:
    """Minimal tool specification for feasibility checks."""
    def __init__(
        self,
        tool_id: str,
        diameter_mm: float,
        flutes: int,
        tool_material: str,
        stickout_mm: float,
    ):
        self.tool_id = tool_id
        self.diameter_mm = diameter_mm
        self.flutes = flutes
        self.tool_material = tool_material
        self.stickout_mm = stickout_mm


# ─────────────────────────────────────────────────────────────────────────────
# Geometry Primitives
# ─────────────────────────────────────────────────────────────────────────────

def _rad(deg: float) -> float:
    """Convert degrees to radians."""
    return deg * math.pi / 180.0


def _pt_on_circle(cx: float, cy: float, r: float, deg: float) -> Tuple[float, float]:
    """Get point on circle at given angle (0° = top, clockwise)."""
    a = _rad(deg - 90)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def _fmt(n: float) -> str:
    """Format number for SVG output."""
    return f"{n:.3f}"


def _arc_inches(r_svg: float, ang_deg: float) -> float:
    """Arc length in inches given radius in SVG units and angle in degrees."""
    return r_svg * ang_deg * math.pi / 180.0 / 100.0


def arc_cell_path(cx: float, cy: float, r1: float, r2: float,
                  a1: float, a2: float) -> str:
    """Build SVG arc cell path between two radii and two angles."""
    x1i, y1i = _pt_on_circle(cx, cy, r1, a1)
    x1o, y1o = _pt_on_circle(cx, cy, r2, a1)
    x2o, y2o = _pt_on_circle(cx, cy, r2, a2)
    x2i, y2i = _pt_on_circle(cx, cy, r1, a2)
    lg = 1 if (a2 - a1) > 180 else 0
    return (
        f"M {_fmt(x1i)} {_fmt(y1i)} L {_fmt(x1o)} {_fmt(y1o)} "
        f"A {r2} {r2} 0 {lg} 1 {_fmt(x2o)} {_fmt(y2o)} "
        f"L {_fmt(x2i)} {_fmt(y2i)} "
        f"A {r1} {r1} 0 {lg} 0 {_fmt(x1i)} {_fmt(y1i)} Z"
    )


def tab_path(cx: float, cy: float, r_inner: float, r_outer: float,
             mid_angle: float, half_width: float) -> str:
    """Build SVG path for an extension tab."""
    x1, y1 = _pt_on_circle(cx, cy, r_inner, mid_angle - half_width)
    x2, y2 = _pt_on_circle(cx, cy, r_outer, mid_angle - half_width)
    x3, y3 = _pt_on_circle(cx, cy, r_outer, mid_angle + half_width)
    x4, y4 = _pt_on_circle(cx, cy, r_inner, mid_angle + half_width)
    return (
        f"M {_fmt(x1)} {_fmt(y1)} L {_fmt(x2)} {_fmt(y2)} "
        f"L {_fmt(x3)} {_fmt(y3)} L {_fmt(x4)} {_fmt(y4)} Z"
    )
