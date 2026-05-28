"""
Compatibility shim — tests and legacy imports use `app.calculators.saw.*`.

Canonical implementations live in `app.calculators.saw_adapters`.
"""

from app.calculators.saw_adapters.bite_per_tooth_adapter import (
    BitePerToothResult,
    compute_bite_per_tooth,
)
from app.calculators.saw_adapters.deflection_adapter import (
    BladeDeflectionResult,
    estimate_blade_deflection,
    estimate_feed_force_n,
)
from app.calculators.saw_adapters.heat_adapter import SawHeatResult, estimate_saw_heat_risk
from app.calculators.saw_adapters.kickback_adapter import KickbackRiskResult, assess_kickback_risk
from app.calculators.saw_adapters.machine_class import MachineClass
from app.calculators.saw_adapters.rim_speed_adapter import SawRimSpeedResult, compute_saw_rim_speed

__all__ = [
    "BitePerToothResult",
    "BladeDeflectionResult",
    "KickbackRiskResult",
    "MachineClass",
    "SawHeatResult",
    "SawRimSpeedResult",
    "assess_kickback_risk",
    "compute_bite_per_tooth",
    "compute_saw_rim_speed",
    "estimate_blade_deflection",
    "estimate_feed_force_n",
    "estimate_saw_heat_risk",
]
