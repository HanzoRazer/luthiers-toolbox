"""
Blade Deflection Adapter (Saw Blades)

Estimates blade deflection under cutting load.

MODEL NOTES:
- Thin-kerf blades deflect more than standard kerf
- Larger diameters deflect more than smaller
- Higher feed forces increase deflection
- Deflection causes:
  - Wandering cuts
  - Burn marks
  - Blade damage

This is a simplified beam model. Real implementation should consider:
- Blade body thickness profile
- Stiffener slots/patterns
- Arbor support width
- Blade material (spring steel vs carbide body)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from ...core.safety import safety_critical

RiskLevel = Literal["GREEN", "YELLOW", "RED"]


@dataclass
class BladeDeflectionResult:
    """Result from blade deflection calculation."""
    deflection_mm: float
    risk: RiskLevel
    max_acceptable_mm: float
    message: str


@safety_critical
def estimate_blade_deflection(
    blade_diameter_mm: float,
    kerf_mm: float,
    feed_force_n: float,
    *,
    blade_body_mm: float = 2.0,  # Blade body thickness
    max_deflection_mm: float = 0.5,
) -> BladeDeflectionResult:
    """
    Estimate blade deflection under cutting load.

    Args:
        blade_diameter_mm: Blade diameter in mm
        kerf_mm: Kerf width in mm
        feed_force_n: Lateral feed force in Newtons
        blade_body_mm: Blade body thickness (plate thickness)
        max_deflection_mm: Maximum acceptable deflection

    Returns:
        BladeDeflectionResult with deflection estimate and risk
    """
    if blade_diameter_mm <= 0 or kerf_mm <= 0:
        return BladeDeflectionResult(
            deflection_mm=0.0,
            risk="GREEN",
            max_acceptable_mm=max_deflection_mm,
            message="Invalid blade parameters",
        )

    # Simplified deflection model
    # Deflection increases with:
    # - Larger diameter (longer unsupported span)
    # - Thinner body
    # - Higher force

    # Normalize to a 250mm (10") blade baseline
    diameter_factor = (blade_diameter_mm / 250.0) ** 2

    # Thinner body = more deflection (inverse cube relationship)
    body_factor = (2.0 / max(blade_body_mm, 0.5)) ** 3

    # Kerf factor (thin kerf = less stiffness)
    kerf_factor = 3.0 / max(kerf_mm, 1.5)

    # Base deflection estimate (mm per Newton of force)
    base_deflection_per_n = 0.001  # 1 micron per Newton baseline

    deflection = (
        feed_force_n
        * base_deflection_per_n
        * diameter_factor
        * body_factor
        * kerf_factor
    )

    # Determine risk level
    if deflection > max_deflection_mm:
        risk: RiskLevel = "RED"
        message = f"Deflection {deflection:.3f}mm exceeds limit - reduce feed or use stiffer blade"
    elif deflection > max_deflection_mm * 0.6:
        risk = "YELLOW"
        message = f"Deflection {deflection:.3f}mm approaching limit - monitor cut quality"
    else:
        risk = "GREEN"
        message = f"Deflection {deflection:.3f}mm within limits"

    return BladeDeflectionResult(
        deflection_mm=deflection,
        risk=risk,
        max_acceptable_mm=max_deflection_mm,
        message=message,
    )


@safety_critical
def estimate_feed_force_n(
    bite_mm: float,
    depth_mm: float,
    material_hardness: float = 1.0,
) -> float:
    """
    Estimate feed force based on cutting parameters.

    Args:
        bite_mm: Bite per tooth
        depth_mm: Depth of cut
        material_hardness: Relative hardness factor (1.0 = maple)

    Returns:
        Estimated feed force in Newtons
    """
    # Simplified force model
    # Force increases with bite, depth, and hardness
    base_force_per_mm2 = 50.0  # N per mm² of chip cross-section

    chip_area = bite_mm * depth_mm
    force = chip_area * base_force_per_mm2 * material_hardness

    return max(0.0, force)
