"""
Neck & Headstock Geometry — Outline and profile generation functions.

Split from neck_headstock_config.py during decomposition.
"""

from __future__ import annotations

import math
from typing import List, Tuple

from .neck_headstock_enums import HeadstockStyle, NeckProfile
from .neck_headstock_presets import NeckDimensions


def generate_headstock_outline(
    style: HeadstockStyle, dims: NeckDimensions
) -> List[Tuple[float, float]]:
    """Generate headstock outline points."""
    points = []

    if style == HeadstockStyle.GIBSON_OPEN:
        # Gibson open-book headstock
        # Symmetric about centerline
        half_width = dims.nut_width_in / 2

        points = [
            # Start at nut, right side
            (0.0, half_width),
            # Transition to headstock width
            (-0.5, half_width + 0.125),
            (-1.0, 1.5),
            # Upper bout
            (-2.0, 1.75),
            (-3.5, 1.85),
            # Top curve
            (-5.0, 1.8),
            (-6.0, 1.6),
            (-6.5, 1.3),
            (-7.0, 0.9),
            # Center notch (open book)
            (-7.2, 0.3),
            (-7.5, 0.0),  # Center point
            # Mirror for left side
            (-7.2, -0.3),
            (-7.0, -0.9),
            (-6.5, -1.3),
            (-6.0, -1.6),
            (-5.0, -1.8),
            (-3.5, -1.85),
            (-2.0, -1.75),
            (-1.0, -1.5),
            (-0.5, -half_width - 0.125),
            (0.0, -half_width),
        ]

    elif style == HeadstockStyle.FENDER_STRAT:
        # Fender 6-in-line Stratocaster headstock
        # Reference: All-Fender-Headstocks.pdf, Fender-Stratocaster-62.pdf
        # Dimensions: ~178mm (7.0") long × ~89mm (3.5") wide, asymmetric
        # Tuner side (bass) is wider than treble side
        # Flat headstock (0° angle), no scarf joint
        half_nut = dims.nut_width_in / 2

        points = [
            # Start at nut, treble side
            (0.0, -half_nut),
            # Treble edge - slight flare then narrow taper
            (-0.3, -half_nut - 0.05),
            (-0.8, -half_nut - 0.10),
            (-1.5, -0.60),
            (-3.0, -0.55),
            (-5.0, -0.50),
            (-6.5, -0.42),
            # Tip - rounded asymmetric
            (-7.0, -0.30),
            (-7.15, -0.10),
            (-7.20, 0.10),
            (-7.15, 0.35),
            (-7.0, 0.60),
            # Bass/tuner edge - wider, gentle curve back
            (-6.5, 1.05),
            (-5.5, 1.30),
            (-4.0, 1.45),
            (-2.5, 1.55),
            (-1.5, 1.55),
            (-1.0, 1.50),
            (-0.5, half_nut + 0.35),
            (-0.2, half_nut + 0.10),
            # Back to nut, bass side
            (0.0, half_nut),
        ]

    elif style == HeadstockStyle.PADDLE:
        # Simple paddle shape
        half_width = dims.blank_width_in / 2
        length = dims.headstock_length_in

        points = [
            (0.0, half_width),
            (-length, half_width),
            (-length, -half_width),
            (0.0, -half_width),
        ]

    elif style == HeadstockStyle.GIBSON_SOLID:
        # Gibson solid headstock (acoustic J-45, Hummingbird, etc.)
        # Resolves VINE-06: Gibson acoustic solid headstock outline missing
        # Similar to open-book but without center notch, slightly narrower
        # Reference: Gibson acoustic headstock ~170mm long × ~95mm wide
        half_width = dims.nut_width_in / 2

        points = [
            # Start at nut, right side
            (0.0, half_width),
            # Transition to headstock width
            (-0.5, half_width + 0.10),
            (-1.0, 1.40),
            # Upper bout - slightly narrower than electric
            (-2.0, 1.60),
            (-3.5, 1.70),
            # Top curve - rounded, no center notch
            (-5.0, 1.65),
            (-6.0, 1.50),
            (-6.5, 1.20),
            (-6.8, 0.80),
            (-7.0, 0.40),
            (-7.1, 0.0),   # Center point (smooth, no notch)
            # Mirror for left side
            (-7.0, -0.40),
            (-6.8, -0.80),
            (-6.5, -1.20),
            (-6.0, -1.50),
            (-5.0, -1.65),
            (-3.5, -1.70),
            (-2.0, -1.60),
            (-1.0, -1.40),
            (-0.5, -half_width - 0.10),
            (0.0, -half_width),
        ]

    elif style == HeadstockStyle.FENDER_TELE:
        # Fender Telecaster 6-in-line headstock
        # Similar to Strat but with squared-off tip
        # Reference: Fender-Telecaster.pdf, ~178mm long × ~89mm wide
        half_nut = dims.nut_width_in / 2

        points = [
            # Start at nut, treble side
            (0.0, -half_nut),
            # Treble edge
            (-0.3, -half_nut - 0.05),
            (-1.0, -0.65),
            (-3.0, -0.55),
            (-5.0, -0.48),
            (-6.5, -0.40),
            # Tip - more squared than Strat
            (-7.0, -0.35),
            (-7.1, -0.20),
            (-7.1, 0.20),
            (-7.0, 0.50),
            # Bass/tuner edge
            (-6.5, 1.00),
            (-5.0, 1.30),
            (-3.0, 1.48),
            (-1.5, 1.52),
            (-1.0, 1.48),
            (-0.5, half_nut + 0.30),
            # Back to nut
            (0.0, half_nut),
        ]

    elif style == HeadstockStyle.PRS:
        # PRS headstock - 3+3 configuration, distinctive curved shape
        # Reference: PRS Custom 24, ~165mm long × ~95mm wide
        half_width = dims.nut_width_in / 2

        points = [
            # Start at nut, right side
            (0.0, half_width),
            # Transition - gentle S-curve
            (-0.5, half_width + 0.15),
            (-1.0, 1.30),
            (-2.0, 1.55),
            # Upper section - characteristic PRS curve
            (-3.0, 1.65),
            (-4.0, 1.68),
            (-5.0, 1.60),
            # Tip - rounded
            (-5.8, 1.35),
            (-6.3, 0.95),
            (-6.5, 0.50),
            (-6.5, 0.0),   # Center
            # Mirror for left side
            (-6.5, -0.50),
            (-6.3, -0.95),
            (-5.8, -1.35),
            (-5.0, -1.60),
            (-4.0, -1.68),
            (-3.0, -1.65),
            (-2.0, -1.55),
            (-1.0, -1.30),
            (-0.5, -half_width - 0.15),
            (0.0, -half_width),
        ]

    elif style == HeadstockStyle.CLASSICAL:
        # Classical guitar slotted headstock
        # Resolves: classical guitar support
        # Reference: ~190mm long × ~80mm wide, with tuner slots
        half_width = dims.nut_width_in / 2  # Classical is wider (2.0")

        points = [
            # Start at nut, right side
            (0.0, half_width),
            # Transition
            (-0.3, half_width + 0.05),
            (-0.8, 1.20),
            # Straight-ish sides typical of classical
            (-2.0, 1.35),
            (-4.0, 1.40),
            (-6.0, 1.35),
            # Rounded top
            (-7.0, 1.15),
            (-7.4, 0.80),
            (-7.5, 0.40),
            (-7.5, 0.0),   # Center
            # Mirror
            (-7.5, -0.40),
            (-7.4, -0.80),
            (-7.0, -1.15),
            (-6.0, -1.35),
            (-4.0, -1.40),
            (-2.0, -1.35),
            (-0.8, -1.20),
            (-0.3, -half_width - 0.05),
            (0.0, -half_width),
        ]


    elif style == HeadstockStyle.MARTIN:
        # Martin acoustic slotted headstock (OM-GAP-06)
        # Reference: Martin D-28, OM-28 headstock
        # Dimensions: ~190mm (7.5") long × ~85mm (3.35") wide
        # 3+3 slotted configuration, distinctive squared shoulders
        half_width = dims.nut_width_in / 2

        points = [
            # Start at nut, right side
            (0.0, half_width),
            # Transition - Martin has subtle flare
            (-0.3, half_width + 0.08),
            (-0.8, 1.15),
            # Squared shoulders - distinctive Martin shape
            (-1.5, 1.35),
            (-2.5, 1.42),
            (-4.0, 1.45),
            (-5.5, 1.42),
            # Top - rounded but less than Gibson
            (-6.5, 1.30),
            (-7.0, 1.05),
            (-7.3, 0.70),
            (-7.5, 0.35),
            (-7.5, 0.0),   # Center point
            # Mirror for left side
            (-7.5, -0.35),
            (-7.3, -0.70),
            (-7.0, -1.05),
            (-6.5, -1.30),
            (-5.5, -1.42),
            (-4.0, -1.45),
            (-2.5, -1.42),
            (-1.5, -1.35),
            (-0.8, -1.15),
            (-0.3, -half_width - 0.08),
            (0.0, -half_width),
        ]

    elif style == HeadstockStyle.BENEDETTO:
        # Benedetto archtop headstock (BEN-GAP-06)
        # Reference: Benedetto 17", Bravo, La Venezia
        # Dimensions: ~175mm (6.9") long × ~90mm (3.55") wide
        # 3+3 configuration, elegant curved shape, slightly swept back
        # Distinguished by graceful curves and pointed tip
        half_width = dims.nut_width_in / 2

        points = [
            # Start at nut, right side
            (0.0, half_width),
            # Transition - elegant S-curve
            (-0.4, half_width + 0.12),
            (-1.0, 1.25),
            (-1.8, 1.50),
            # Upper bout - flowing curves
            (-2.8, 1.62),
            (-3.8, 1.68),
            (-4.8, 1.65),
            # Tip - pointed and elegant (Benedetto signature)
            (-5.5, 1.50),
            (-6.0, 1.20),
            (-6.3, 0.85),
            (-6.5, 0.45),
            (-6.6, 0.0),   # Pointed center
            # Mirror for left side
            (-6.5, -0.45),
            (-6.3, -0.85),
            (-6.0, -1.20),
            (-5.5, -1.50),
            (-4.8, -1.65),
            (-3.8, -1.68),
            (-2.8, -1.62),
            (-1.8, -1.50),
            (-1.0, -1.25),
            (-0.4, -half_width - 0.12),
            (0.0, -half_width),
        ]

    else:
        # Default to paddle if not implemented
        return generate_headstock_outline(HeadstockStyle.PADDLE, dims)

    return points


def generate_tuner_positions(
    style: HeadstockStyle, dims: NeckDimensions
) -> List[Tuple[float, float]]:
    """
    Generate tuner hole positions.

    Returns list of (x, y) coordinates for drilling.
    """
    positions: List[Tuple[float, float]] = []

    if style == HeadstockStyle.GIBSON_OPEN:
        # 3+3 configuration
        positions.extend([
            (-1.8, 1.25),
            (-3.5, 1.45),
            (-5.2, 1.35),
        ])
        positions.extend([
            (-1.8, -1.25),
            (-3.5, -1.45),
            (-5.2, -1.35),
        ])

    elif style == HeadstockStyle.FENDER_STRAT:
        # 6-in-line Strat
        spacing = 0.9
        y_offset = 0.9
        for i in range(6):
            x = -1.5 - (i * spacing)
            positions.append((x, y_offset))

    elif style == HeadstockStyle.GIBSON_SOLID:
        # 3+3 configuration (same as open, slightly different positions)
        positions.extend([
            (-1.7, 1.15),
            (-3.4, 1.35),
            (-5.1, 1.25),
        ])
        positions.extend([
            (-1.7, -1.15),
            (-3.4, -1.35),
            (-5.1, -1.25),
        ])

    elif style == HeadstockStyle.FENDER_TELE:
        # 6-in-line Tele (same pattern as Strat)
        spacing = 0.9
        y_offset = 0.9
        for i in range(6):
            x = -1.5 - (i * spacing)
            positions.append((x, y_offset))

    elif style == HeadstockStyle.PRS:
        # 3+3 configuration with PRS spacing
        positions.extend([
            (-1.6, 1.20),
            (-3.2, 1.40),
            (-4.8, 1.30),
        ])
        positions.extend([
            (-1.6, -1.20),
            (-3.2, -1.40),
            (-4.8, -1.30),
        ])

    elif style == HeadstockStyle.CLASSICAL:
        # 3+3 slotted configuration
        # Tuner holes are in the slots, not on face
        positions.extend([
            (-2.0, 1.05),
            (-4.0, 1.10),
            (-6.0, 1.05),
        ])
        positions.extend([
            (-2.0, -1.05),
            (-4.0, -1.10),
            (-6.0, -1.05),
        ])


    elif style == HeadstockStyle.MARTIN:
        # 3+3 slotted configuration (Martin acoustic)
        # Tuner holes are in the slots, positioned for Grover/Waverly style tuners
        positions.extend([
            (-2.0, 1.10),
            (-4.0, 1.15),
            (-6.0, 1.10),
        ])
        positions.extend([
            (-2.0, -1.10),
            (-4.0, -1.15),
            (-6.0, -1.10),
        ])

    elif style == HeadstockStyle.BENEDETTO:
        # 3+3 configuration (Benedetto archtop)
        # Tuner positions for Gotoh/Schaller style tuners
        positions.extend([
            (-1.8, 1.22),
            (-3.5, 1.40),
            (-5.2, 1.35),
        ])
        positions.extend([
            (-1.8, -1.22),
            (-3.5, -1.40),
            (-5.2, -1.35),
        ])

    return positions


# =============================================================================
# NECK PROFILE GEOMETRY
# =============================================================================

def generate_neck_profile_points(
    profile: NeckProfile,
    dims: NeckDimensions,
    position_from_nut: float,
) -> List[Tuple[float, float]]:
    """Generate cross-section profile points at a given position."""
    t = position_from_nut / dims.scale_length_in
    t = max(0, min(1, t))

    width = dims.nut_width_in + (dims.heel_width_in - dims.nut_width_in) * t
    depth = dims.depth_at_1st_in + (dims.depth_at_12th_in - dims.depth_at_1st_in) * t
    half_width = width / 2

    if profile == NeckProfile.C_SHAPE:
        points = []
        for i in range(21):
            angle = math.pi * i / 20
            y = half_width * math.cos(angle)
            z = -depth * (0.2 + 0.8 * math.sin(angle))
            points.append((y, z))
        return points

    elif profile == NeckProfile.D_SHAPE:
        points = []
        for i in range(21):
            angle = math.pi * i / 20
            y = half_width * math.cos(angle)
            z = -depth * (0.4 + 0.6 * math.sin(angle))
            points.append((y, z))
        return points

    elif profile == NeckProfile.V_SHAPE:
        points = []
        for i in range(21):
            t_local = i / 20
            y = half_width * (1 - 2 * t_local)
            z = -depth * (1 - abs(1 - 2 * t_local) * 0.3)
            points.append((y, z))
        return points

    # Default to C
    return generate_neck_profile_points(NeckProfile.C_SHAPE, dims, position_from_nut)
