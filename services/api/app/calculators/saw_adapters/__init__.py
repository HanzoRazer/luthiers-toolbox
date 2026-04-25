"""
Saw Lab Calculator Adapters — Compatibility Shim

This module re-exports saw calculators from ltb-woodworking-studio when available,
falling back to local implementations if the package is not installed.

Migration Status: IN PROGRESS (Phase 3, 2026-04-25)
Canonical location: ltb-woodworking-studio/woodworking_v2/services/api/app/calculators/saw/

Usage (unchanged):
    from app.calculators.saw_adapters import compute_bite_per_tooth
"""

try:
    # Try importing from ltb-woodworking-studio (canonical location)
    from woodworking_v2.services.api.app.calculators.saw import (
        compute_bite_per_tooth,
        compute_saw_rim_speed,
        estimate_saw_heat_risk,
        estimate_blade_deflection,
        assess_kickback_risk,
        MachineClass,
    )
    _USING_WOODWORKING_STUDIO = True
except ImportError:
    # Fall back to local implementations
    from .bite_per_tooth_adapter import compute_bite_per_tooth
    from .rim_speed_adapter import compute_saw_rim_speed
    from .heat_adapter import estimate_saw_heat_risk
    from .deflection_adapter import estimate_blade_deflection
    from .kickback_adapter import assess_kickback_risk
    from .machine_class import MachineClass
    _USING_WOODWORKING_STUDIO = False

__all__ = [
    "compute_bite_per_tooth",
    "compute_saw_rim_speed",
    "estimate_saw_heat_risk",
    "estimate_blade_deflection",
    "assess_kickback_risk",
    "MachineClass",
]
