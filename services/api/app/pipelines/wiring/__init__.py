"""
Wiring Pipeline Module
Guitar electronics validation and calculation tools.
"""
from .switch_validate import validate, suggest_hardware, HARDWARE_LIMITS
from .treble_bleed import recommend, format_circuit

__all__ = [
    'validate',
    'suggest_hardware', 
    'HARDWARE_LIMITS',
    'recommend',
    'format_circuit',
]
