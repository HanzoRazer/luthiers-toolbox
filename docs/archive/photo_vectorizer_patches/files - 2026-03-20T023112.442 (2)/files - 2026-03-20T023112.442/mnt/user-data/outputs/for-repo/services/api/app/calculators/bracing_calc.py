# services/api/app/calculators/bracing_calc.py
"""
Bracing calculator — stable API facade over the physics engine.

The physics live in pipelines.bracing.bracing_calc.
This module exposes a typed Pydantic interface for RMOS / Art Studio.

All fields are now connected to real calculations:
    profile_type     → cross-section area and I formulas
    width_mm         → geometric inputs
    height_mm        → geometric inputs
    h_end_mm         → scallop tip height (used in mean area and mass)
    scallop_length_mm → scallop taper length
    length_mm        → mass and camber
    density_kg_m3    → mass
    back_radius_mm   → camber for back braces
    top_radius_mm    → camber for top braces
    material         → MOE lookup for EI
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ..pipelines.bracing import bracing_calc as physics


class BracingCalcInput(BaseModel):
    profile_type: str = Field(
        default="parabolic",
        description="rectangular | triangular | parabolic | scalloped",
    )
    width_mm: float = Field(default=12.0)
    height_mm: float = Field(default=8.0)
    h_end_mm: float = Field(
        default=3.5,
        description="Scallop tip height (scalloped profile only)",
    )
    scallop_length_mm: float = Field(
        default=40.0,
        description="Scallop taper length each end (scalloped profile only)",
    )
    length_mm: float = Field(default=300.0)
    density_kg_m3: float = Field(default=420.0)
    material: str = Field(default="sitka_spruce")
    back_radius_mm: float = Field(
        default=0.0,
        description="Back dish radius (mm). 0 = no camber. e.g. 6096 for 20ft.",
    )
    top_radius_mm: float = Field(
        default=0.0,
        description="Top dish radius (mm). 0 = no camber.",
    )
    plate: str = Field(
        default="top",
        description="'top' or 'back' — selects which radius for camber.",
    )
    params: Dict[str, Any] = Field(default_factory=dict)

    def to_profile_dict(self) -> Dict[str, Any]:
        return {
            "type": self.profile_type,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "h_end_mm": self.h_end_mm,
            "scallop_length": self.scallop_length_mm,
        }


class BraceSectionResult(BaseModel):
    profile_type: str
    width_mm: float
    height_mm: float
    center_area_mm2: float
    mean_area_mm2: float
    second_moment_mm4: float
    EI_N_mm2: float
    camber_mm: float
    description: str = ""
    raw: Dict[str, Any] = Field(default_factory=dict)


def calculate_brace_section(data: BracingCalcInput) -> BraceSectionResult:
    """Full section properties for one brace."""
    profile = data.to_profile_dict()
    center_area = physics.brace_section_area_mm2(profile)
    mean_area   = physics.brace_mean_area_mm2(
        profile, data.length_mm, data.h_end_mm, data.scallop_length_mm
    )
    I  = physics.brace_second_moment_mm4(profile)
    EI = physics.brace_bending_stiffness_EI(profile, data.material)

    radius_mm = data.back_radius_mm if data.plate == "back" else data.top_radius_mm
    camber = physics.brace_camber_mm(data.length_mm, radius_mm)

    descriptions = {
        "rectangular": "Full rectangular cross-section",
        "triangular":  "Triangular (peaked) cross-section",
        "parabolic":   "Parabolic cross-section (A = 2/3 × w × h)",
        "scalloped":   "Scalloped ends — parabolic center section",
    }

    return BraceSectionResult(
        profile_type=data.profile_type,
        width_mm=data.width_mm,
        height_mm=data.height_mm,
        center_area_mm2=round(center_area, 3),
        mean_area_mm2=round(mean_area, 3),
        second_moment_mm4=round(I, 3),
        EI_N_mm2=round(EI, 0),
        camber_mm=round(camber, 3),
        description=descriptions.get(data.profile_type, data.profile_type),
        raw={"profile": profile},
    )


def estimate_mass_grams(data: BracingCalcInput) -> float:
    """Brace mass using mean cross-section (accounts for scallop)."""
    profile  = data.to_profile_dict()
    mean_area = physics.brace_mean_area_mm2(
        profile, data.length_mm, data.h_end_mm, data.scallop_length_mm
    )
    return float(physics.estimate_mass_grams(data.length_mm, mean_area, data.density_kg_m3))


def calculate_brace_set(braces: List[BracingCalcInput]) -> Dict[str, Any]:
    """Properties for a complete brace set with totals."""
    results = []
    total_mass = 0.0

    for i, brace in enumerate(braces):
        section = calculate_brace_section(brace)
        mass    = estimate_mass_grams(brace)
        results.append({
            "index":              i,
            "profile_type":       section.profile_type,
            "width_mm":           section.width_mm,
            "height_mm":          section.height_mm,
            "length_mm":          brace.length_mm,
            "center_area_mm2":    section.center_area_mm2,
            "mean_area_mm2":      section.mean_area_mm2,
            "second_moment_mm4":  section.second_moment_mm4,
            "EI_N_mm2":           section.EI_N_mm2,
            "camber_mm":          section.camber_mm,
            "mass_grams":         round(mass, 2),
        })
        total_mass += mass

    return {
        "braces": results,
        "totals": {
            "count":            len(braces),
            "total_mass_grams": round(total_mass, 2),
        },
    }
