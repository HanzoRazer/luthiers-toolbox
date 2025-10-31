"""
CAM Module - CNC toolpath generation and G-code export.

This module converts CAD designs into CNC-ready toolpaths, generates G-code,
and provides utilities for optimizing cutting operations.
"""

from .toolpath import Toolpath, ToolpathGenerator, ToolpathType
from .gcode import GCodeGenerator, GCodeExporter
from .operations import PocketOperation, ProfileOperation, DrillOperation

__all__ = [
    "Toolpath",
    "ToolpathGenerator",
    "ToolpathType",
    "GCodeGenerator",
    "GCodeExporter",
    "PocketOperation",
    "ProfileOperation",
    "DrillOperation",
]
