"""
cam_core.gcode
==============

G-code generation and data models for CAM core operations.

Modules:
    gcode_models         — Pydantic schemas (SawGCodeRequest, SawToolpath, etc.)
    saw_gcode_generator  — Multi-pass saw G-code generator (CP-S57)
"""

from .gcode_models import (
    Point2D,
    SawToolpath,
    DepthPass,
    SawGCodeRequest,
    SawGCodeResult,
)

__all__ = [
    "Point2D",
    "SawToolpath",
    "DepthPass",
    "SawGCodeRequest",
    "SawGCodeResult",
]
