"""
Wiring Calculators Package

Electronics calculators for guitar wiring:

- treble_bleed: Treble bleed resistor/capacitor values
- switch_validator: Validate pickup switching configurations
- impedance_math: Pot/tone network impedance calculations

Usage:
    from app.calculators.wiring import (
        suggest_treble_bleed,
        validate_switch_config,
        calculate_tone_rolloff,
    )
"""

from .treble_bleed import suggest_treble_bleed, TrebleBleedResult
from .switch_validator import validate_switch_config, SwitchValidationResult
from .impedance_math import (
    calculate_parallel_resistance,
    calculate_tone_rolloff,
    calculate_pickup_load,
)

__all__ = [
    "suggest_treble_bleed",
    "TrebleBleedResult",
    "validate_switch_config",
    "SwitchValidationResult",
    "calculate_parallel_resistance",
    "calculate_tone_rolloff",
    "calculate_pickup_load",
]
