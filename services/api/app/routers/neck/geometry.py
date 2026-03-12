"""
Neck geometry functions - pure geometry calculations.

Extracted from neck_router.py. Contains no FastAPI dependencies.
"""
from typing import List

from .schemas import Point2D, NeckParameters

# Import canonical fret math - NO inline math in routers (Fortran Rule)
from ...instrument_geometry.neck.fret_math import compute_fret_positions_mm


def calculate_fret_positions(scale_length_in: float, num_frets: int = 22) -> List[float]:
    """
    Calculate fret positions using equal temperament formula.
    Returns distance from nut to each fret in inches.

    Delegates to canonical compute_fret_positions_mm() from fret_math.py.
    """
    scale_length_mm = scale_length_in * 25.4
    positions_mm = compute_fret_positions_mm(scale_length_mm, num_frets)
    return [pos / 25.4 for pos in positions_mm]


def generate_neck_profile(params: NeckParameters) -> List[Point2D]:
    """
    Generate neck profile outline (side view).

    Simplified C-profile with linear taper from nut to heel.
    """
    profile = []

    # Nut end (0, 0)
    profile.append(Point2D(x=0.0, y=0.0))

    # Neck length at bottom
    profile.append(Point2D(x=params.neck_length, y=0.0))

    # Heel width
    profile.append(Point2D(x=params.neck_length, y=params.heel_width / 2))

    # Nut width
    profile.append(Point2D(x=0.0, y=params.nut_width / 2))

    # Close path
    profile.append(Point2D(x=0.0, y=0.0))

    return profile


def generate_fretboard_outline(params: NeckParameters) -> List[Point2D]:
    """
    Generate fretboard outline (top view).

    Rectangle with width taper from nut to neck join.
    """
    fretboard = []

    # Fretboard typically extends ~2" past neck join on Les Paul
    fretboard_length = params.neck_length + 2.0

    # Width at nut
    nut_w = params.nut_width
    # Width at body (slightly wider)
    body_w = params.heel_width * 0.95

    # Rectangle outline
    fretboard.append(Point2D(x=0.0, y=-nut_w / 2))
    fretboard.append(Point2D(x=fretboard_length, y=-body_w / 2))
    fretboard.append(Point2D(x=fretboard_length, y=body_w / 2))
    fretboard.append(Point2D(x=0.0, y=nut_w / 2))
    fretboard.append(Point2D(x=0.0, y=-nut_w / 2))

    return fretboard


def generate_headstock_outline(params: NeckParameters) -> List[Point2D]:
    """
    Generate headstock outline (Gibson-style angled).
    """
    headstock = []

    # Simplified Les Paul headstock shape
    width = params.blank_width
    length = params.headstock_length

    # Starting at nut (0, 0), extends backward
    headstock.append(Point2D(x=0.0, y=-width / 2))
    headstock.append(Point2D(x=-length, y=-width / 2))
    headstock.append(Point2D(x=-length, y=width / 2))
    headstock.append(Point2D(x=0.0, y=width / 2))
    headstock.append(Point2D(x=0.0, y=-width / 2))

    return headstock


def generate_tuner_holes(params: NeckParameters) -> List[Point2D]:
    """
    Generate tuner hole positions (3+3 layout).
    """
    holes = []

    # 3+3 layout: 3 on treble side, 3 on bass side
    spacing = params.tuner_layout
    x_start = -params.headstock_length + 1.5  # 1.5" from headstock end

    # Treble side (top 3)
    for i in range(3):
        holes.append(Point2D(
            x=x_start,
            y=(params.blank_width / 4) + (i * spacing / 3)
        ))

    # Bass side (bottom 3)
    for i in range(3):
        holes.append(Point2D(
            x=x_start,
            y=-(params.blank_width / 4) - (i * spacing / 3)
        ))

    return holes


def generate_centerline(params: NeckParameters) -> List[Point2D]:
    """Generate centerline reference."""
    return [
        Point2D(x=-params.headstock_length, y=0.0),
        Point2D(x=params.neck_length + 3.0, y=0.0)
    ]


# ============================================================================
# UNIT CONVERSION
# ============================================================================

def convert_point(point: Point2D, from_units: str, to_units: str) -> Point2D:
    """Convert point between inches and millimeters."""
    if from_units == to_units:
        return point

    if from_units == "in" and to_units == "mm":
        factor = 25.4
    elif from_units == "mm" and to_units == "in":
        factor = 1.0 / 25.4
    else:
        return point

    return Point2D(x=point.x * factor, y=point.y * factor)


def convert_points(points: List[Point2D], from_units: str, to_units: str) -> List[Point2D]:
    """Convert list of points."""
    return [convert_point(p, from_units, to_units) for p in points]


def convert_value(value: float, from_units: str, to_units: str) -> float:
    """Convert scalar value."""
    if from_units == to_units:
        return value

    if from_units == "in" and to_units == "mm":
        return value * 25.4
    elif from_units == "mm" and to_units == "in":
        return value / 25.4
    else:
        return value
