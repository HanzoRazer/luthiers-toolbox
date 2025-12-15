# services/api/app/pipelines/rosette/__init__.py
"""
Rosette Pipeline Module
Complete rosette design and manufacturing toolkit.

Submodules:
- rosette_calc: Channel dimension computation
- rosette_make_gcode: Spiral G-code generation
- rosette_post_fill: G-code template filling
- rosette_to_dxf: Minimal DXF circle generation
"""

from .rosette_calc import compute
from .rosette_make_gcode import generate_spiral_gcode
from .rosette_post_fill import fill_template, list_placeholders, DEFAULT_PARAMS
from .rosette_to_dxf import generate_rosette_dxf, save_rosette_dxf

__all__ = [
    # Calculations
    "compute",
    # G-code generation
    "generate_spiral_gcode",
    # Template filling
    "fill_template",
    "list_placeholders",
    "DEFAULT_PARAMS",
    # DXF generation
    "generate_rosette_dxf",
    "save_rosette_dxf",
]
