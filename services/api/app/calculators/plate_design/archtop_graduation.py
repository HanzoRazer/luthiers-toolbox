"""
Archtop graduation physics connection — ARCH-003.

Connects the normalized graduation template (archtop_graduation_template.json)
to the plate_design thickness calculator. The template provides the shape,
this module provides the scale (edge_mm, apex_mm) derived from wood properties
and target frequency.

Key insight: Archtop graduation proportions are consistent across instruments.
Shape = normalized template (edge=0.0 → apex=1.0).
Scale = set by plate_design thickness calculator from wood properties and target frequency.
arch_height is a separate parameter (approx 1:15 to 1:18 body width ratio).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal, Optional, Dict, Any

from app.calculators.plate_design import (
    analyze_plate,
    get_material_preset,
    get_body_calibration,
    BodyStyle,
)


@dataclass
class GraduationResult:
    """Result of archtop graduation calculation."""
    edge_mm: float
    apex_mm: float
    arch_height_mm: float
    body_style: str
    material: str
    target_hz: float

    def thickness_at_zone(self, normalized: float) -> float:
        """
        Apply normalized template value to get absolute thickness.

        Args:
            normalized: Value from 0.0 (edge) to 1.0 (apex)

        Returns:
            Absolute thickness in mm
        """
        return self.edge_mm + (self.apex_mm - self.edge_mm) * normalized

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def graduation_from_wood_and_target(
    material: str,
    body_style: str,
    target_hz: float,
    lower_bout_width_mm: float = 255.0,
    arch_height_ratio: float = 0.062,
    plate: Literal["top", "back"] = "top",
) -> GraduationResult:
    """
    Compute archtop graduation endpoints from wood properties and target frequency.

    The normalized graduation template shape is universal.
    This function provides the absolute endpoints (edge, apex)
    derived from physics, not empirical lookup.

    Args:
        material: Material preset name (e.g., "maple", "sitka_spruce")
        body_style: Body style (e.g., "archtop", "om")
        target_hz: Target frequency in Hz (e.g., 120.0 for archtop top)
        lower_bout_width_mm: Lower bout width for arch height calculation
        arch_height_ratio: Arch height as ratio of bout width
                          Typical: 0.055-0.070 for top, 0.067-0.083 for back
        plate: "top" or "back"

    Returns:
        GraduationResult with edge_mm, apex_mm, arch_height_mm

    Raises:
        ValueError: If material or body style is unknown
    """
    # Get material properties
    mat = get_material_preset(material)
    if mat is None:
        raise ValueError(f"Unknown material: {material}")

    # Get body calibration
    try:
        body_enum = BodyStyle(body_style.lower())
    except ValueError:
        raise ValueError(f"Unknown body style: {body_style}")

    calibration = get_body_calibration(body_enum)
    if calibration is None:
        raise ValueError(f"No calibration for body style: {body_style}")

    # Get plate dimensions from calibration
    if plate == "top":
        length_mm = calibration.top_a_m * 1000.0
        width_mm = calibration.top_b_m * 1000.0
    else:
        length_mm = calibration.back_a_m * 1000.0
        width_mm = calibration.back_b_m * 1000.0

    # Compute recommended thickness using physics model
    result = analyze_plate(
        E_L_GPa=mat.E_L_GPa,
        E_C_GPa=mat.E_C_GPa,
        density_kg_m3=mat.density_kg_m3,
        length_mm=length_mm,
        width_mm=width_mm,
        target_f_Hz=target_hz,
        material_name=material,
    )

    # apex = recommended thickness from physics
    apex_mm = result.recommended_h_mm

    # edge = typically 65% of apex for archtops (D'Aquisto/Benedetto pattern)
    edge_mm = round(apex_mm * 0.65, 2)

    # arch height from bout width ratio
    arch_height_mm = round(lower_bout_width_mm * arch_height_ratio, 1)

    return GraduationResult(
        edge_mm=edge_mm,
        apex_mm=apex_mm,
        arch_height_mm=arch_height_mm,
        body_style=body_style,
        material=material,
        target_hz=target_hz,
    )
