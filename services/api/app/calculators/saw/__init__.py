"""
Saw Lab Calculator Adapters

This package adapts Saw Lab 2.0 physics calculators into the Calculator Spine's
common data models and API surface.

Adapters:
- bite_per_tooth_adapter: Chip thickness per tooth calculations
- heat_adapter: Thermal risk from friction
- deflection_adapter: Blade deflection under load
- rim_speed_adapter: Surface velocity at blade edge
- kickback_adapter: Kickback risk assessment

Usage:
    from app.calculators.saw import evaluate_saw_operation

    result = evaluate_saw_operation(
        blade_id="SB-24T-10",
        material_id="maple",
        feed_mm_min=3000,
        rpm=3450,
        depth_mm=25,
    )
"""

from .bite_per_tooth_adapter import compute_bite_per_tooth
from .rim_speed_adapter import compute_saw_rim_speed
from .heat_adapter import estimate_saw_heat_risk
from .deflection_adapter import estimate_blade_deflection
from .kickback_adapter import assess_kickback_risk

__all__ = [
    "compute_bite_per_tooth",
    "compute_saw_rim_speed",
    "estimate_saw_heat_risk",
    "estimate_blade_deflection",
    "assess_kickback_risk",
]
