"""
Bracing Geometry Subpackage

Provides bracing pattern calculations for acoustic instruments.

Modules:
- x_brace: X-bracing patterns (dreadnought, jumbo, etc.)
- fan_brace: Fan bracing patterns (classical, flamenco)
"""

from .x_brace import get_x_brace_pattern
from .fan_brace import get_fan_brace_pattern

__all__ = [
    "get_x_brace_pattern",
    "get_fan_brace_pattern",
]
