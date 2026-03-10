"""
Production V-Carve CAM Module

Upgraded V-carve toolpath generation with proper CAM calculations.
Resolves: VINE-03 (V-carve G-code is demo quality)

Improvements over naive implementation:
- Cutter compensation (tool radius offset for V-bit geometry)
- Chipload calculation (feed rate based on material + tool)
- Multi-pass stepdown (depth per pass based on bit angle)
- V-bit geometry (automatic depth from line width)
- Feed rate optimization (corner slowdown, plunge rate limits)

Usage:
    from app.cam.vcarve import VCarveToolpath, VCarveConfig

    vcarve = VCarveToolpath(
        paths=mlpaths,
        config=VCarveConfig(
            bit_angle_deg=60.0,
            target_line_width_mm=2.0,
            material="hardwood",
        )
    )
    result = vcarve.generate()
    gcode = result.gcode
"""

from .toolpath import VCarveToolpath, VCarveConfig, VCarveResult
from .chipload import calculate_chipload, ChiploadParams, MATERIAL_CHIPLOAD
from .geometry import vbit_depth_for_width, vbit_width_at_depth

__all__ = [
    "VCarveToolpath",
    "VCarveConfig",
    "VCarveResult",
    "calculate_chipload",
    "ChiploadParams",
    "MATERIAL_CHIPLOAD",
    "vbit_depth_for_width",
    "vbit_width_at_depth",
]
