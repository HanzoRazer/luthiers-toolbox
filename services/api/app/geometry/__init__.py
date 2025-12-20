"""
Geometry Utilities Package

Pure math functions for common geometric operations.
Follows the Fortran Rule: all math operations in their own subroutines.

Modules:
    arc_utils: Arc tessellation, circle generation, arc length calculations
"""

from .arc_utils import (
    generate_circle_points,
    tessellate_arc,
    tessellate_arc_radians,
    arc_center_from_endpoints,
    arc_signed_sweep,
    arc_length,
    arc_length_from_angle,
    circle_circumference,
    nearest_point_distance,
    trapezoidal_motion_time,
)

__all__ = [
    "generate_circle_points",
    "tessellate_arc",
    "tessellate_arc_radians",
    "arc_center_from_endpoints",
    "arc_signed_sweep",
    "arc_length",
    "arc_length_from_angle",
    "circle_circumference",
    "nearest_point_distance",
    "trapezoidal_motion_time",
]
