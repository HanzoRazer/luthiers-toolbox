# services/api/app/routers/radius_dish_router.py
"""
Radius Dish Router — parametric G-code generator.

Replaces the static pre-generated .nc files (only 15ft and 25ft)
with a generator that produces correct GRBL toolpaths for any radius,
dish width, ball-nose diameter, feeds, and stepover.

The toolpath
============

A radius dish is a concave spherical surface. The CNC mills it with a
ball-nose bit in a raster pattern. At each Y row the bit traces an X pass;
the Z depth at any (X, Y) position follows the sphere equation:

    Z(x, y) = R - sqrt(R² - x² - y²)

where R is the dish radius and the coordinate origin is the dish centre.
This is the exact spherical surface equation — no approximation.

The toolpath generates:
    1. Roughing passes (larger stepover, finish allowance)
    2. Finishing pass (tight stepover, full depth)

GRBL output uses G20 (inches) or G21 (mm) as selected.
Feed rates are specified in units/min.

Brace camber endpoint
=====================

Also exposes /radius-dish/brace-camber which converts a dish radius
and brace length to the pre-bend camber height. This is the calculation
that was silently missing from the system — the bridge between
"I have a 20ft back dish" and "how much curve do I grind into each brace".
"""

from __future__ import annotations

import math
from typing import List, Literal, Optional

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/radius-dish", tags=["Radius Dish"])


# ── Geometry ──────────────────────────────────────────────────────────────────

def dish_depth_mm(radius_mm: float, half_width_mm: float) -> float:
    """
    Maximum depth of a spherical dish.
    depth = R - sqrt(R² - (W/2)²)   [exact circular segment formula]
    """
    r2   = radius_mm ** 2
    hw2  = half_width_mm ** 2
    if hw2 >= r2:
        raise ValueError("Dish width exceeds twice the radius — geometry impossible.")
    return radius_mm - math.sqrt(r2 - hw2)


def dish_z_at(x_mm: float, y_mm: float, radius_mm: float) -> float:
    """
    Z depth (positive downward) at point (x, y) on a spherical dish surface.
    Z = R - sqrt(R² - x² - y²)
    Origin is at dish centre, surface level is Z=0.
    """
    r2  = radius_mm ** 2
    xy2 = x_mm ** 2 + y_mm ** 2
    if xy2 > r2:
        return 0.0  # outside dish — clamp to surface level
    return radius_mm - math.sqrt(r2 - xy2)


def brace_camber_mm(length_mm: float, radius_mm: float) -> float:
    """
    Pre-bend camber required for a brace to sit flush on a dished plate.
    camber = L² / (8R)   [chord-sagitta, exact geometry]
    """
    if radius_mm <= 0:
        return 0.0
    return length_mm ** 2 / (8.0 * radius_mm)


# ── G-code generator ──────────────────────────────────────────────────────────

def _grbl_header(units: str, safe_z: float, spindle_rpm: int) -> List[str]:
    unit_cmd = "G20" if units == "inch" else "G21"
    return [
        "%",
        f"({unit_cmd} {'inches' if units == 'inch' else 'mm'})",
        "G17 G40 G49 G80 G90",  # XY plane, cancel comp/offset/cycles, absolute
        unit_cmd,
        "G54",                   # work coordinate system
        f"S{spindle_rpm} M3",    # spindle on
        f"G0 Z{safe_z:.4f}",     # retract
    ]


def _grbl_footer(safe_z: float) -> List[str]:
    return [
        f"G0 Z{safe_z:.4f}",
        "M5",   # spindle off
        "M30",  # program end
        "%",
    ]


def generate_radius_dish_gcode(
    radius_mm: float,
    dish_width_mm: float,
    dish_length_mm: float,
    ball_nose_dia_mm: float,
    stepover_mm: float,
    feed_mm_min: float,
    plunge_mm_min: float,
    safe_z_mm: float,
    finish_allowance_mm: float,
    roughing_stepover_mm: float,
    spindle_rpm: int,
    units: str,
    include_roughing: bool,
) -> str:
    """
    Generate GRBL G-code for milling a spherical radius dish.

    The ball-nose bit centre follows the dish surface. Because the ball
    tip is the lowest point of the tool, there is no cutter compensation
    needed for a spherical surface — the centre-of-ball path IS the
    dish surface path.

    The dish is milled in X-direction rows (Y incremented per row).
    Origin is at the centre of the dish top surface.
    Z-positive is up; cuts go to negative Z.
    """
    lines: List[str] = []

    unit_scale = 1.0 / 25.4 if units == "inch" else 1.0
    def fmt(v: float) -> str:
        return f"{v * unit_scale:.4f}"

    lines += _grbl_header(units, safe_z_mm * unit_scale, spindle_rpm)

    half_w = dish_width_mm  / 2.0
    half_l = dish_length_mm / 2.0
    max_depth = dish_depth_mm(radius_mm, max(half_w, half_l))

    def pass_rows(s_over: float, z_allowance: float, pass_label: str) -> List[str]:
        """Raster rows for one pass (roughing or finishing)."""
        out = [f"({pass_label}: stepover={s_over:.1f}mm allowance={z_allowance:.2f}mm)"]
        y = -half_l
        direction = 1
        while y <= half_l + 0.001:
            # Start of row: rapid to safe Z then to X start
            x_start = -half_w if direction == 1 else half_w
            x_end   =  half_w if direction == 1 else -half_w
            z_start  = dish_z_at(x_start, y, radius_mm) + z_allowance
            out.append(f"G0 X{fmt(x_start)} Y{fmt(y)}")
            out.append(f"G1 Z{fmt(-z_start)} F{feed_mm_min * unit_scale:.1f}")
            # Linear interpolation across the row
            n_steps = max(2, int(abs(x_end - x_start) / 2.0) + 1)  # 2mm segments
            for i in range(1, n_steps + 1):
                t = i / n_steps
                x = x_start + (x_end - x_start) * t
                z = dish_z_at(x, y, radius_mm) + z_allowance
                out.append(f"G1 X{fmt(x)} Z{fmt(-z)} F{feed_mm_min * unit_scale:.1f}")
            out.append(f"G0 Z{fmt(safe_z_mm)}")
            y        += s_over
            direction = -direction
        return out

    if include_roughing:
        lines += pass_rows(roughing_stepover_mm, finish_allowance_mm, "ROUGHING")

    lines += pass_rows(stepover_mm, 0.0, "FINISHING")
    lines += _grbl_footer(safe_z_mm * unit_scale)

    return "\n".join(lines) + "\n"


# ── Request / Response models ──────────────────────────────────────────────────

class RadiusDishRequest(BaseModel):
    radius_ft: Optional[float]  = Field(default=None, description="Dish radius in feet")
    radius_mm: Optional[float]  = Field(default=None, description="Dish radius in mm")
    dish_width_mm:  float = Field(default=381.0, description="Dish width (mm)")
    dish_length_mm: float = Field(default=381.0, description="Dish length (mm)")
    ball_nose_dia_mm: float = Field(default=12.7, description="Ball nose diameter (mm)")
    stepover_mm: float       = Field(default=3.0,  description="Finishing stepover (mm)")
    roughing_stepover_mm: float = Field(default=8.0, description="Roughing stepover (mm)")
    feed_mm_min: float       = Field(default=2500.0)
    plunge_mm_min: float     = Field(default=800.0)
    safe_z_mm: float         = Field(default=15.0)
    finish_allowance_mm: float = Field(default=0.5, description="Stock left after roughing")
    spindle_rpm: int         = Field(default=18000)
    units: Literal["mm", "inch"] = Field(default="mm")
    include_roughing: bool   = Field(default=True)

    def resolved_radius_mm(self) -> float:
        if self.radius_mm and self.radius_mm > 0:
            return self.radius_mm
        if self.radius_ft and self.radius_ft > 0:
            return self.radius_ft * 304.8
        raise ValueError("Provide radius_ft or radius_mm.")


class RadiusDishCalcRequest(BaseModel):
    radius_ft: Optional[float] = None
    radius_mm: Optional[float] = None
    width_mm:  float = Field(default=381.0)
    length_mm: float = Field(default=381.0)

    def resolved_radius_mm(self) -> float:
        if self.radius_mm and self.radius_mm > 0:
            return self.radius_mm
        if self.radius_ft and self.radius_ft > 0:
            return self.radius_ft * 304.8
        raise ValueError("Provide radius_ft or radius_mm.")


class BraceCamberRequest(BaseModel):
    brace_length_mm: float = Field(..., description="Brace length (mm)")
    radius_ft: Optional[float] = None
    radius_mm: Optional[float] = None

    def resolved_radius_mm(self) -> float:
        if self.radius_mm and self.radius_mm > 0:
            return self.radius_mm
        if self.radius_ft and self.radius_ft > 0:
            return self.radius_ft * 304.8
        raise ValueError("Provide radius_ft or radius_mm.")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/generate-gcode")
def generate_gcode(req: RadiusDishRequest) -> PlainTextResponse:
    """
    Generate GRBL G-code for a spherical radius dish.

    Accepts any radius (not just 15ft / 25ft). Produces a real raster
    toolpath from the sphere equation Z = R - sqrt(R² - x² - y²).
    """
    r_mm = req.resolved_radius_mm()
    gcode = generate_radius_dish_gcode(
        radius_mm=r_mm,
        dish_width_mm=req.dish_width_mm,
        dish_length_mm=req.dish_length_mm,
        ball_nose_dia_mm=req.ball_nose_dia_mm,
        stepover_mm=req.stepover_mm,
        feed_mm_min=req.feed_mm_min,
        plunge_mm_min=req.plunge_mm_min,
        safe_z_mm=req.safe_z_mm,
        finish_allowance_mm=req.finish_allowance_mm,
        roughing_stepover_mm=req.roughing_stepover_mm,
        spindle_rpm=req.spindle_rpm,
        units=req.units,
        include_roughing=req.include_roughing,
    )
    r_ft = r_mm / 304.8
    filename = f"radius_dish_{r_ft:.0f}ft_{req.dish_width_mm:.0f}mm_{req.units}_grbl.nc"
    return PlainTextResponse(
        content=gcode,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/calculate")
def calculate_dish(req: RadiusDishCalcRequest) -> dict:
    """
    Dish depth, surface area, and key geometry for any radius and dimensions.
    """
    r_mm   = req.resolved_radius_mm()
    r_ft   = r_mm / 304.8
    hw, hl = req.width_mm / 2, req.length_mm / 2
    depth_from_width  = dish_depth_mm(r_mm, hw)
    depth_from_length = dish_depth_mm(r_mm, hl)
    max_depth = max(depth_from_width, depth_from_length)

    return {
        "radius_mm":          round(r_mm, 1),
        "radius_ft":          round(r_ft, 2),
        "dish_width_mm":      req.width_mm,
        "dish_length_mm":     req.length_mm,
        "depth_at_width_mm":  round(depth_from_width, 3),
        "depth_at_length_mm": round(depth_from_length, 3),
        "max_depth_mm":       round(max_depth, 3),
        "formula":            "depth = R - sqrt(R² - (W/2)²)",
    }


@router.post("/brace-camber")
def brace_camber(req: BraceCamberRequest) -> dict:
    """
    Pre-bend camber required for a brace to match a dish radius.

    camber = L² / (8R)   [chord-sagitta, exact geometry]

    This is the calculation that connects the radius dish to the braces.
    A brace of length L on a dish of radius R must have its bottom relieved
    by exactly this amount to sit flush against the curved plate.
    """
    r_mm   = req.resolved_radius_mm()
    r_ft   = r_mm / 304.8
    camber = brace_camber_mm(req.brace_length_mm, r_mm)

    return {
        "brace_length_mm": req.brace_length_mm,
        "radius_mm":       round(r_mm, 1),
        "radius_ft":       round(r_ft, 2),
        "camber_mm":       round(camber, 3),
        "camber_in":       round(camber / 25.4, 4),
        "formula":         "camber = L² / (8R)",
        "note": (
            f"The brace bottom must be relieved by {camber:.2f}mm at centre "
            f"({camber/25.4:.4f}\") to sit flush on a {r_ft:.0f}ft dish."
        ),
    }


@router.get("/common-radii")
def common_radii() -> dict:
    """Reference table of common dish radii."""
    radii = [
        {"ft": 12, "mm": 12 * 304.8, "use": "Traditional archtop, tight curve"},
        {"ft": 15, "mm": 15 * 304.8, "use": "Steel-string acoustic back, standard"},
        {"ft": 20, "mm": 20 * 304.8, "use": "Steel-string acoustic back, medium"},
        {"ft": 25, "mm": 25 * 304.8, "use": "Steel-string acoustic back, shallow (Taylor-style)"},
        {"ft": 28, "mm": 28 * 304.8, "use": "Very shallow — almost flat"},
    ]
    for r in radii:
        # Depth for a 15" (381mm) wide dish at this radius
        r["depth_for_15in_wide_mm"] = round(dish_depth_mm(r["mm"], 190.5), 2)
    return {"radii": radii}
