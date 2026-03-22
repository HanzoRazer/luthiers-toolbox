# services/api/app/calculators/bracing_calc.py

"""
Bracing calculator for The Production Shop.

Cross-section area, second moment (I), EI stiffness, and camber use
`._bracing_physics` (Session A — real geometry). Mass estimation uses
the same volume model as the pipeline CLI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from . import _bracing_physics as physics


class BracingCalcInput(BaseModel):
    """
    Input for bracing calculations.
    
    Supports both explicit fields (recommended) and generic params dict
    for backward compatibility with legacy code.
    """
    # Explicit fields for the common use case
    profile_type: str = Field(
        default="parabolic",
        description="Brace profile type: rectangular, triangular, parabolic, scalloped"
    )
    width_mm: float = Field(default=12.0, description="Brace width in mm")
    height_mm: float = Field(default=8.0, description="Brace height/peak in mm")
    length_mm: float = Field(default=300.0, description="Brace length in mm")
    density_kg_m3: float = Field(
        default=420.0,
        description="Wood density in kg/m³ (Sitka spruce ~420, Red spruce ~380)"
    )
    
    # Generic params for backward compatibility
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters passed through to legacy functions"
    )

    def to_profile_dict(self) -> Dict[str, Any]:
        """Convert to profile dict expected by legacy brace_section_area_mm2."""
        return {
            "type": self.profile_type,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
        }

    def to_legacy_kwargs(self) -> Dict[str, Any]:
        """Convert to kwargs for generic legacy calls."""
        base = {
            "profile_type": self.profile_type,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "length_mm": self.length_mm,
            "density_kg_m3": self.density_kg_m3,
        }
        base.update(self.params)
        return base


class BraceSectionResult(BaseModel):
    """Result of bracing section calculation."""
    
    profile_type: str
    width_mm: float
    height_mm: float
    area_mm2: float
    description: str = ""
    
    # Raw dict for any additional data
    raw: Dict[str, Any] = Field(default_factory=dict)


def calculate_brace_section(data: BracingCalcInput) -> BraceSectionResult:
    """
    Calculate bracing section properties.
    
    This is the canonical entrypoint for RMOS/Art Studio
    when they need bracing section properties.
    
    Args:
        data: Bracing input parameters
        
    Returns:
        BraceSectionResult with area and profile info
    """
    profile = data.to_profile_dict()
    area = physics.brace_section_area_mm2(profile)

    # Generate description
    descriptions = {
        "rectangular": "Full rectangular cross-section",
        "triangular": "Triangular (peaked) cross-section",
        "parabolic": "Parabolic (scalloped peak) cross-section",
        "scalloped": "Scalloped (reduced mass) cross-section",
    }
    desc = descriptions.get(data.profile_type, f"{data.profile_type} profile")
    
    return BraceSectionResult(
        profile_type=data.profile_type,
        width_mm=data.width_mm,
        height_mm=data.height_mm,
        area_mm2=area,
        description=desc,
        raw={"profile": profile, "area_mm2": area}
    )


def estimate_mass_grams(data: BracingCalcInput) -> float:
    """
    Estimate bracing mass in grams.
    
    Uses the legacy estimate_mass_grams function with:
    - length_mm from input
    - area_mm2 calculated from profile
    - density_kg_m3 from input
    
    Returns:
        Estimated mass in grams
    """
    profile = data.to_profile_dict()
    area = physics.brace_section_area_mm2(profile)

    mass = physics.estimate_mass_grams(
        data.length_mm,
        area,
        data.density_kg_m3
    )
    return float(mass)


def calculate_brace_set(braces: list[BracingCalcInput]) -> Dict[str, Any]:
    """
    Calculate properties for a set of braces.
    
    Args:
        braces: List of brace inputs
        
    Returns:
        Dict with individual results and totals
    """
    results = []
    total_mass = 0.0
    total_area = 0.0
    
    for i, brace in enumerate(braces):
        section = calculate_brace_section(brace)
        mass = estimate_mass_grams(brace)
        
        results.append({
            "index": i,
            "profile_type": section.profile_type,
            "width_mm": section.width_mm,
            "height_mm": section.height_mm,
            "length_mm": brace.length_mm,
            "area_mm2": section.area_mm2,
            "mass_grams": mass,
        })
        total_mass += mass
        total_area += section.area_mm2
    
    return {
        "braces": results,
        "totals": {
            "count": len(braces),
            "total_mass_grams": total_mass,
            "total_section_area_mm2": total_area,
        }
    }

# =============================================================================
# ACOUSTIC-004 - Inverse Brace Sizing (from deflection target)
# =============================================================================


@dataclass
class BraceSizingTarget:
    """Target deflection parameters for inverse brace sizing."""

    max_deflection_mm: float  # Maximum allowable total deflection (with creep)
    applied_load_n: float  # String tension load at bridge
    plate_length_mm: float  # Body length (bridge to tail direction)
    bridge_position_fraction: float = 0.63  # Bridge position (0=tail, 1=neck)
    existing_plate_EI_Nm2: float = 0.0  # From compute_plate_EI in top_deflection_calc


@dataclass
class RequiredBraceSpec:
    """Result of inverse brace sizing calculation."""

    required_EI_Nm2: float  # Total EI needed to meet deflection target
    required_brace_EI_Nm2: float  # Brace contribution (total - plate)
    suggested_width_mm: float
    suggested_height_mm: float
    wood_species: str
    profile_type: str
    gate: Literal["ACHIEVABLE", "MARGINAL", "NOT_ACHIEVABLE"]
    notes: List[str] = field(default_factory=list)


# Creep factor must match top_deflection_calc.py
_CREEP_FACTOR = 0.35


def compute_required_EI(target: BraceSizingTarget) -> float:
    """
    Inverse of deflection formula: compute EI needed to limit deflection.

    From simply-supported beam: delta = F * a^2 * b^2 / (3 * EI * L)
    Solving for EI: EI = F * a^2 * b^2 / (3 * delta_max * L)

    Args:
        target: Deflection target parameters.

    Returns:
        Required composite EI in N*m^2.
    """
    if target.max_deflection_mm <= 0:
        raise ValueError("max_deflection_mm must be positive")
    if target.applied_load_n <= 0:
        raise ValueError("applied_load_n must be positive")

    # Account for creep in target (delta_static = delta_total / 1.35)
    static_limit_mm = target.max_deflection_mm / (1.0 + _CREEP_FACTOR)
    static_limit_m = static_limit_mm / 1000.0

    # Convert length to meters
    L_m = target.plate_length_mm / 1000.0

    # Bridge position distances
    a = target.bridge_position_fraction * L_m
    b = (1.0 - target.bridge_position_fraction) * L_m

    # Inverse formula: EI = F * a^2 * b^2 / (3 * delta * L)
    required_EI = (target.applied_load_n * (a ** 2) * (b ** 2)) / (3.0 * static_limit_m * L_m)

    return required_EI


def compute_brace_dimensions_for_EI(
    required_brace_EI_Nm2: float,
    wood_species: str = "sitka_spruce",
    brace_width_mm: float = 5.5,
    profile_type: str = "parabolic",
) -> RequiredBraceSpec:
    """
    Compute brace height needed to achieve target EI.

    For rectangular: I = w * h^3 / 12, so h = cbrt(12 * I / w)
    Since EI = E * I: I = EI / E, then h = cbrt(12 * EI / (E * w))

    For parabolic: effective I is approximately 8/175 of rectangular.
    So h = cbrt(175 * EI / (8 * E * w))

    Args:
        required_brace_EI_Nm2: Required brace EI contribution.
        wood_species: Wood species for E lookup.
        brace_width_mm: Brace width (default 5.5mm for X-brace).
        profile_type: Brace profile (rectangular, parabolic, triangular).

    Returns:
        RequiredBraceSpec with dimensions and gate.
    """
    notes: List[str] = []

    # Get MOE for species
    E_MPa = physics.MATERIAL_MOE_MPA.get(wood_species, physics.DEFAULT_MOE_MPA)

    # Convert EI from N*m^2 to N*mm^2 for mm calculations
    # 1 N*m^2 = 1e6 N*mm^2
    required_EI_Nmm2 = required_brace_EI_Nm2 * 1e6

    # E in N/mm^2 (MPa)
    E_Nmm2 = E_MPa

    # Width in mm
    w = brace_width_mm

    # Compute I required: I = EI / E
    I_required_mm4 = required_EI_Nmm2 / E_Nmm2

    # Solve for height based on profile
    if profile_type == "rectangular":
        # I = w * h^3 / 12  =>  h = cbrt(12 * I / w)
        h_cubed = 12.0 * I_required_mm4 / w
        height_mm = h_cubed ** (1.0 / 3.0) if h_cubed > 0 else 0.0
    elif profile_type == "parabolic":
        # Parabolic I is approximately 8/175 of rectangular
        # For parabolic with peak height h: I_parabolic = (8/175) * w * h^3
        # So: h^3 = 175 * I / (8 * w)
        h_cubed = 175.0 * I_required_mm4 / (8.0 * w)
        height_mm = h_cubed ** (1.0 / 3.0) if h_cubed > 0 else 0.0
    elif profile_type == "triangular":
        # I = w * h^3 / 36  =>  h = cbrt(36 * I / w)
        h_cubed = 36.0 * I_required_mm4 / w
        height_mm = h_cubed ** (1.0 / 3.0) if h_cubed > 0 else 0.0
    else:
        # Default to rectangular
        h_cubed = 12.0 * I_required_mm4 / w
        height_mm = h_cubed ** (1.0 / 3.0) if h_cubed > 0 else 0.0
        notes.append(f"Unknown profile '{profile_type}', used rectangular formula.")

    # Determine gate based on height
    if height_mm <= 10.0:
        gate: Literal["ACHIEVABLE", "MARGINAL", "NOT_ACHIEVABLE"] = "ACHIEVABLE"
        notes.append(f"Height {height_mm:.1f}mm is within typical range (<=10mm).")
    elif height_mm <= 14.0:
        gate = "MARGINAL"
        notes.append(
            f"Height {height_mm:.1f}mm is tall but achievable (10-14mm). "
            "Consider wider brace or additional bracing."
        )
    else:
        gate = "NOT_ACHIEVABLE"
        notes.append(
            f"Height {height_mm:.1f}mm exceeds practical limits (>14mm). "
            "Use multiple braces or stiffer wood species."
        )

    notes.append(f"Wood species: {wood_species} (E={E_MPa:.0f} MPa)")
    notes.append(f"Profile: {profile_type}")

    return RequiredBraceSpec(
        required_EI_Nm2=required_brace_EI_Nm2,
        required_brace_EI_Nm2=required_brace_EI_Nm2,
        suggested_width_mm=brace_width_mm,
        suggested_height_mm=round(height_mm, 2),
        wood_species=wood_species,
        profile_type=profile_type,
        gate=gate,
        notes=notes,
    )


def solve_brace_sizing(
    target: BraceSizingTarget,
    wood_species: str = "sitka_spruce",
    brace_width_mm: float = 5.5,
    profile_type: str = "parabolic",
    brace_count: int = 2,
) -> RequiredBraceSpec:
    """
    Full inverse solver: from deflection target to brace dimensions.

    Combines compute_required_EI and compute_brace_dimensions_for_EI.

    Args:
        target: Deflection target parameters.
        wood_species: Wood species for braces.
        brace_width_mm: Individual brace width.
        profile_type: Brace profile type.
        brace_count: Number of braces to distribute EI across.

    Returns:
        RequiredBraceSpec with dimensions for a single brace.
    """
    # Compute total required EI
    total_required_EI = compute_required_EI(target)

    # Subtract existing plate EI to get brace contribution needed
    required_brace_EI_total = max(0.0, total_required_EI - target.existing_plate_EI_Nm2)

    # Divide by brace count to get per-brace EI
    per_brace_EI = required_brace_EI_total / brace_count if brace_count > 0 else required_brace_EI_total

    # Compute dimensions for single brace
    result = compute_brace_dimensions_for_EI(
        required_brace_EI_Nm2=per_brace_EI,
        wood_species=wood_species,
        brace_width_mm=brace_width_mm,
        profile_type=profile_type,
    )

    # Update result with total EI info
    result.required_EI_Nm2 = total_required_EI
    result.notes.insert(0, f"Total EI required: {total_required_EI:.2f} N*m^2")
    result.notes.insert(1, f"Plate EI: {target.existing_plate_EI_Nm2:.2f} N*m^2")
    result.notes.insert(2, f"Brace EI needed: {required_brace_EI_total:.2f} N*m^2 ({brace_count} braces)")

    return result
