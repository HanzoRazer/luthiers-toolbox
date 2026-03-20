# services/api/app/calculators/binding_math.py
"""
Pure geometry math functions for binding calculations.

No domain dependencies - only math and typing imports.
Extracted from binding_geometry.py for reuse and testability.
"""

from __future__ import annotations

import math
from typing import List, Tuple

# Type aliases
Pt2D = Tuple[float, float]
Pt3D = Tuple[float, float, float]


def distance_2d(p1: Pt2D, p2: Pt2D) -> float:
    """Calculate 2D Euclidean distance."""
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def distance_3d(p1: Pt3D, p2: Pt3D) -> float:
    """Calculate 3D Euclidean distance."""
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2)


def normalize_2d(v: Tuple[float, float]) -> Tuple[float, float]:
    """Normalize a 2D vector to unit length."""
    mag = math.sqrt(v[0] ** 2 + v[1] ** 2)
    if mag < 1e-10:
        return (0.0, 0.0)
    return (v[0] / mag, v[1] / mag)


def angle_between_vectors(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
    """Calculate angle between two 2D vectors in degrees."""
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    # Clamp to avoid numerical issues with acos
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))


def calculate_curvature_radius(p1: Pt2D, p2: Pt2D, p3: Pt2D) -> float:
    """
    Calculate the radius of curvature through three points.

    Uses the circumradius formula for a triangle.
    Returns infinity for collinear points.
    """
    # Side lengths
    a = distance_2d(p2, p3)
    b = distance_2d(p1, p3)
    c = distance_2d(p1, p2)

    # Semi-perimeter
    s = (a + b + c) / 2

    # Area via Heron's formula
    area_sq = s * (s - a) * (s - b) * (s - c)
    if area_sq <= 0:
        return float("inf")  # Collinear points

    area = math.sqrt(area_sq)

    # Circumradius R = (a * b * c) / (4 * area)
    if area < 1e-10:
        return float("inf")
    return (a * b * c) / (4 * area)


def polyline_length(points: List[Pt2D]) -> float:
    """Calculate total length of a polyline."""
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(len(points) - 1):
        total += distance_2d(points[i], points[i + 1])
    return total


def polyline_length_3d(points: List[Pt3D]) -> float:
    """Calculate total length of a 3D polyline."""
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(len(points) - 1):
        total += distance_3d(points[i], points[i + 1])
    return total
