"""
Neck & Headstock configuration — Re-export shim.

Original module decomposed into:
- neck_headstock_enums.py     — HeadstockStyle, NeckProfile enums
- neck_headstock_presets.py   — NeckToolConfig, NECK_TOOLS, NeckDimensions, NECK_PRESETS
- neck_headstock_geometry.py  — generate_headstock_outline, generate_tuner_positions,
                                generate_neck_profile_points

This shim preserves all existing imports.
"""

from .neck_headstock_enums import *
from .neck_headstock_presets import *
from .neck_headstock_geometry import *

__all__ = [
    # Enums
    "HeadstockStyle",
    "NeckProfile",
    # Tool config
    "NeckToolConfig",
    "NECK_TOOLS",
    # Dimensions
    "NeckDimensions",
    # Presets
    "NECK_PRESETS",
    # Geometry functions
    "generate_headstock_outline",
    "generate_tuner_positions",
    "generate_neck_profile_points",
]
