# services/api/app/calculators/bracing_calc.py

"""
Bracing calculator façade for the Luthier's ToolBox.

This module centralizes access to bracing physics that currently
lives in `pipelines.bracing.bracing_calc`.

Legacy math is preserved in that module; this layer provides a
stable, RMOS/Art Studio-friendly interface so we can evolve the
call signatures over time without losing the underlying formulas.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

# Import the migrated bracing functions
try:
    from ..pipelines.bracing import bracing_calc as legacy
except ImportError as exc:
    raise ImportError(
        "Bracing calculator module `pipelines.bracing.bracing_calc` "
        "was not found. Ensure the migration placed it correctly."
    ) from exc


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
    area = legacy.brace_section_area_mm2(profile)
    
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
    area = legacy.brace_section_area_mm2(profile)
    
    mass = legacy.estimate_mass_grams(
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
