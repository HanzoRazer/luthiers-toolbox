"""
Bracing Geometry Subpackage

Provides bracing pattern calculations for acoustic instruments.

Modules:
- x_brace: X-bracing patterns (dreadnought, jumbo, etc.)
- fan_brace: Fan bracing patterns (classical, flamenco)
- martin_d28_1937_65260: source-constrained #65260 reconstruction candidate
"""

from .x_brace import get_x_brace_pattern, get_j45_bracing
from .fan_brace import get_fan_brace_pattern
from .martin_d28_1937_65260 import (
    D28_65260_RECONSTRUCTION_V01,
    get_martin_d28_1937_65260_reconstruction,
)

__all__ = [
    "get_x_brace_pattern",
    "get_j45_bracing",
    "get_fan_brace_pattern",
    "D28_65260_RECONSTRUCTION_V01",
    "get_martin_d28_1937_65260_reconstruction",
]
