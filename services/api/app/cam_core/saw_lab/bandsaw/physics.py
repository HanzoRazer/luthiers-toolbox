"""
Bandsaw physics: blade tension, drift (Duginske-style empirical), gullet feed, validation, planning.

References: Duginske, *The New Complete Guide to the Bandsaw*; gullet capacity vs chip load.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .blade_spec import BandsawBladeSpec
from .machine import Bandsaw

# Tension stress bands (Pa): T = sigma * A
_CARBON_STEEL_SIGMA_PA = (55e6, 70e6)
_BI_METAL_SIGMA_PA = (70e6, 90e6)


def _sigma_nominal(blade_family: str) -> float:
    if blade_family.lower() in ("bi_metal", "bimetal", "bi-metal"):
        lo, hi = _BI_METAL_SIGMA_PA
    else:
        lo, hi = _CARBON_STEEL_SIGMA_PA
    return (lo + hi) / 2.0


def compute_blade_tension(
    blade: BandsawBladeSpec,
    *,
    stress_fraction: float = 0.5,
) -> Dict[str, Any]:
    """
    Blade tension force: T = σ × A (cross-section of strip behind teeth).

    Uses mid-band σ for carbon steel (55–70 MPa) or bi-metal (70–90 MPa).
    ``stress_fraction`` scales σ within the family (0–1).
    """
    a_m2 = blade.cross_section_mm2() * 1e-6
    lo, hi = (
        _BI_METAL_SIGMA_PA
        if blade.blade_family.lower() in ("bi_metal", "bimetal", "bi-metal")
        else _CARBON_STEEL_SIGMA_PA
    )
    sigma = lo + (hi - lo) * max(0.0, min(1.0, stress_fraction))
    tension_n = sigma * a_m2
    return {
        "tension_n": round(tension_n, 2),
        "sigma_pa": sigma,
        "sigma_mpa": sigma / 1e6,
        "cross_section_m2": a_m2,
        "blade_family": blade.blade_family,
        "notes": "σ × blade_back cross-section; set tension gauge per manufacturer deflection.",
    }


def compute_drift_angle(
    blade_width_mm: float,
    wheel_diameter_mm: float,
    rpm: float,
    tpi: float,
) -> Dict[str, Any]:
    """
    Empirical drift angle (degrees) — blade lead, wheel crown, and speed.

    Duginske: drift is not a single constant; this is a conservative shop estimate
    for layout (follow fence / mark line). Increases with relative blade width
    and lower RPM; decreases with finer pitch.
    """
    rpm = max(rpm, 1.0)
    wd = max(wheel_diameter_mm, 1.0)
    bw = max(blade_width_mm, 0.1)
    pitch_mm = 25.4 / max(tpi, 0.1)
    drift_rad = 0.012 * (bw / wd) * (1500.0 / rpm) * (6.35 / pitch_mm)
    drift_deg = max(0.05, min(4.0, math.degrees(drift_rad)))
    return {
        "drift_angle_deg": round(drift_deg, 3),
        "reference": "Duginske — empirical; verify with test cut on your machine.",
        "blade_width_mm": blade_width_mm,
        "wheel_diameter_mm": wheel_diameter_mm,
        "rpm": rpm,
        "tpi": tpi,
    }


def compute_feed_rate(
    blade: BandsawBladeSpec,
    sfpm: float,
    stock_thickness_mm: float,
    *,
    gullet_fill_efficiency: float = 0.35,
) -> Dict[str, Any]:
    """
    Gullet-capacity limited feed (mm/s) from tooth pitch and gullet area proxy.

    Models gullet area ~ ½ × pitch × gullet_depth with depth ~ 0.55 × blade width.
    """
    if stock_thickness_mm <= 0 or sfpm <= 0:
        return {"feed_mm_s": 0.0, "notes": "Invalid stock or SFPM."}

    pitch_mm = 25.4 / max(blade.tpi, 0.1)
    gullet_depth_mm = 0.55 * blade.width_mm
    gullet_area_mm2 = 0.5 * pitch_mm * gullet_depth_mm
    eff = max(0.1, min(0.9, gullet_fill_efficiency))

    # Chip volume rate ~ gullet_area * sfpm * eff / (stock engagement factor)
    engagement = max(stock_thickness_mm, blade.kerf_mm)
    ipm = (gullet_area_mm2 * sfpm * eff) / (engagement * 25.4 * 12.0)
    ipm = max(0.2, min(ipm, 150.0))
    mm_s = ipm * 25.4 / 60.0
    return {
        "feed_mm_s": round(mm_s, 4),
        "feed_ipm": round(ipm, 3),
        "gullet_area_mm2": round(gullet_area_mm2, 3),
        "tooth_pitch_mm": round(pitch_mm, 4),
        "notes": "Gullet model — reduce feed if sawdust packs or blade wanders.",
    }


def validate_resaw_setup(
    machine: Bandsaw,
    blade: BandsawBladeSpec,
    stock_thickness_mm: float,
    rpm: float,
) -> Dict[str, Any]:
    """Feasibility and warnings for resaw."""
    warnings: List[str] = []
    sfpm = machine.surface_speed_sfpm(rpm)

    if sfpm < 2200:
        warnings.append("Low SFPM; may wander or burn — increase RPM or wheel speed.")
    if sfpm > 6500:
        warnings.append("High SFPM for wood; heat and wear increase.")

    if stock_thickness_mm > blade.width_mm * 8.0:
        warnings.append("Cut depth large vs blade width; use wider blade or reduce depth.")

    if machine.max_resaw_height_mm and stock_thickness_mm > machine.max_resaw_height_mm:
        warnings.append("Stock thicker than stated saw resaw capacity.")

    if blade.width_mm < stock_thickness_mm * 0.12:
        warnings.append("Blade may be narrow for this resaw depth.")

    return {
        "ok": len(warnings) == 0,
        "sfpm": round(sfpm, 2),
        "warnings": warnings,
    }


def plan_curve_cut(
    blade: BandsawBladeSpec,
    planned_curve_radius_mm: float,
    *,
    width_to_radius_factor: float = 6.0,
) -> Dict[str, Any]:
    """
    Minimum radius vs blade width (rule-of-thumb ~6× width, Duginske class texts).

    Override ``min_curve_radius_mm`` on the blade when known from manufacturer.
    """
    min_r = blade.min_curve_radius_mm
    if min_r is None or min_r <= 0:
        min_r = width_to_radius_factor * blade.width_mm
    feasible = planned_curve_radius_mm >= min_r * 0.98
    return {
        "min_curve_radius_mm": round(min_r, 2),
        "planned_curve_radius_mm": planned_curve_radius_mm,
        "feasible": feasible,
        "notes": "Verify with blade sticker; wide blades need larger radii.",
    }


@dataclass
class ResawBookmatchPlan:
    """Bookmatched plate resaw / thinning."""

    plate_width_mm: float
    plate_thickness_mm: float
    kerf_mm: float
    target_thickness_mm: float
    half_width_mm: float
    halves_per_plate: int
    thickness_passes_estimate: int
    notes: List[str] = field(default_factory=list)


def plan_resaw_cut(
    plate_width_mm: float,
    plate_thickness_mm: float,
    kerf_mm: float,
    target_thickness_mm: float,
    *,
    bookmatch: bool = True,
) -> Dict[str, Any]:
    """
    Bookmatching: split width; estimate thinning passes after opening cut.

    ``thickness_passes_estimate`` uses coarse removal per pass = max(kerf, 1.5mm).
    """
    notes: List[str] = []
    half_w = plate_width_mm / 2.0 if bookmatch else plate_width_mm
    if bookmatch:
        notes.append("Center rip for bookmatch; joint opened faces after bandsaw.")

    removal = max(plate_thickness_mm - target_thickness_mm, 0.0)
    per_pass = max(kerf_mm, 1.5)
    passes = int(math.ceil(removal / per_pass)) if removal > 0 else 0

    plan = ResawBookmatchPlan(
        plate_width_mm=plate_width_mm,
        plate_thickness_mm=plate_thickness_mm,
        kerf_mm=kerf_mm,
        target_thickness_mm=target_thickness_mm,
        half_width_mm=half_w,
        halves_per_plate=2 if bookmatch else 1,
        thickness_passes_estimate=passes,
        notes=notes,
    )
    return {
        "half_width_mm": plan.half_width_mm,
        "halves_per_plate": plan.halves_per_plate,
        "thickness_passes_estimate": plan.thickness_passes_estimate,
        "remaining_thickness_to_remove_mm": round(removal, 3),
        "notes": plan.notes,
    }


__all__ = [
    "compute_blade_tension",
    "compute_drift_angle",
    "compute_feed_rate",
    "validate_resaw_setup",
    "plan_curve_cut",
    "plan_resaw_cut",
]
