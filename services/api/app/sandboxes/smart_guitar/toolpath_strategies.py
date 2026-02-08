"""Smart Guitar toolpath strategy generators.

Extracted from generate_gcode.py (WP-3) for god-object decomposition.
"""

from __future__ import annotations

import math
from typing import List, Tuple


def generate_pocket_spiral(
    points: List[Tuple[float, float]],
    tool_dia: float,
    stepover: float,
    depth: float,
    stepdown: float,
) -> List[List[Tuple[float, float, float]]]:
    """
    Generate pocket clearing spiral toolpath.

    Returns list of passes, each pass is list of (x, y, z) points.
    """
    passes = []

    # Calculate number of Z passes
    num_z_passes = max(1, math.ceil(depth / stepdown))
    z_increment = depth / num_z_passes

    # Calculate bounding box
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    # Generate spiral from center outward for each Z level
    for z_pass in range(num_z_passes):
        z = -z_increment * (z_pass + 1)
        pass_points = []

        # Simplified spiral: concentric offsets from center
        max_radius = max(max_x - center_x, max_y - center_y)
        current_radius = tool_dia / 2

        while current_radius < max_radius:
            # Generate points around this radius
            num_points = max(8, int(2 * math.pi * current_radius / stepover))
            for i in range(num_points + 1):
                angle = 2 * math.pi * i / num_points
                x = center_x + current_radius * math.cos(angle)
                y = center_y + current_radius * math.sin(angle)

                # Check if point is inside polygon (simplified - use bbox)
                if min_x <= x <= max_x and min_y <= y <= max_y:
                    pass_points.append((x, y, z))

            current_radius += stepover

        if pass_points:
            passes.append(pass_points)

    return passes


def generate_contour_path(
    points: List[Tuple[float, float]],
    depth: float,
    stepdown: float,
    offset: float = 0,
) -> List[List[Tuple[float, float, float]]]:
    """
    Generate contour following toolpath.

    Returns list of passes at different Z depths.
    """
    passes = []

    num_z_passes = max(1, math.ceil(depth / stepdown))
    z_increment = depth / num_z_passes

    for z_pass in range(num_z_passes):
        z = -z_increment * (z_pass + 1)
        pass_points = [(p[0], p[1], z) for p in points]
        # Close the contour
        if pass_points and pass_points[0] != pass_points[-1]:
            pass_points.append(pass_points[0])
        passes.append(pass_points)

    return passes


def generate_drill_path(
    x: float,
    y: float,
    depth: float,
    peck_depth: float = 3.0,
) -> List[Tuple[float, float, float]]:
    """
    Generate peck drilling toolpath.
    """
    points = []
    current_z = 0

    while current_z > -depth:
        next_z = max(-depth, current_z - peck_depth)
        points.append((x, y, next_z))
        # Retract for chip clearing
        points.append((x, y, current_z + 1.0))
        current_z = next_z

    # Final depth
    points.append((x, y, -depth))
    return points
