"""
Neck & Headstock configuration: dataclasses, enums, tool configs, presets,
and geometry helpers (headstock outline, tuner positions, profile cross-sections).

Extracted from neck_headstock_generator.py during WP-3 decomposition.
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# =============================================================================
# TOOL CONFIGURATION
# =============================================================================

@dataclass
class NeckToolConfig:
    """Tool configuration for neck operations."""
    number: int
    name: str
    diameter_in: float
    rpm: int
    feed_ipm: float
    plunge_ipm: float
    stepdown_in: float

    @property
    def diameter_mm(self) -> float:
        return self.diameter_in * 25.4


# Neck-specific tool library (smaller tools for precision work)
NECK_TOOLS: Dict[int, NeckToolConfig] = {
    1: NeckToolConfig(1, "1/4\" Ball End", 0.250, 18000, 100, 20, 0.10),
    2: NeckToolConfig(2, "1/8\" Flat End", 0.125, 20000, 60, 15, 0.05),
    3: NeckToolConfig(3, "1/4\" Flat End", 0.250, 18000, 80, 18, 0.08),
    4: NeckToolConfig(4, "3/8\" Ball End", 0.375, 16000, 120, 25, 0.12),
    5: NeckToolConfig(5, "1/16\" Flat End", 0.0625, 24000, 30, 10, 0.02),
    10: NeckToolConfig(10, "11/32\" Drill", 0.344, 2000, 10, 5, 0.05),  # Tuner holes
}


# =============================================================================
# ENUMS
# =============================================================================

class HeadstockStyle(str, Enum):
    GIBSON_OPEN = "gibson_open"
    GIBSON_SOLID = "gibson_solid"
    FENDER_STRAT = "fender_strat"
    FENDER_TELE = "fender_tele"
    PRS = "prs"
    CLASSICAL = "classical"
    PADDLE = "paddle"


class NeckProfile(str, Enum):
    C_SHAPE = "c"
    D_SHAPE = "d"
    V_SHAPE = "v"
    U_SHAPE = "u"
    ASYMMETRIC = "asymmetric"
    COMPOUND = "compound"


# =============================================================================
# DIMENSIONS
# =============================================================================

@dataclass
class NeckDimensions:
    """Neck blank and finished dimensions."""
    # Blank dimensions
    blank_length_in: float = 26.0      # Includes headstock + heel
    blank_width_in: float = 3.5        # Wide enough for headstock
    blank_thickness_in: float = 1.0    # Before carving

    # Finished dimensions
    nut_width_in: float = 1.6875       # 1-11/16" standard
    heel_width_in: float = 2.25        # At body joint
    depth_at_1st_in: float = 0.82      # Neck depth at 1st fret
    depth_at_12th_in: float = 0.92     # Neck depth at 12th fret

    # Scale
    scale_length_in: float = 25.5

    # Headstock
    headstock_angle_deg: float = 14.0  # Gibson style
    headstock_thickness_in: float = 0.55
    headstock_length_in: float = 7.5

    # Truss rod
    truss_rod_width_in: float = 0.25
    truss_rod_depth_in: float = 0.375
    truss_rod_length_in: float = 18.0  # From nut


# =============================================================================
# PRESETS
# =============================================================================

NECK_PRESETS: Dict[str, NeckDimensions] = {
    "gibson_50s": NeckDimensions(
        nut_width_in=1.6875,
        depth_at_1st_in=0.86,
        depth_at_12th_in=0.96,
        scale_length_in=24.75,
        headstock_angle_deg=17.0,
    ),
    "gibson_60s": NeckDimensions(
        nut_width_in=1.6875,
        depth_at_1st_in=0.80,
        depth_at_12th_in=0.90,
        scale_length_in=24.75,
        headstock_angle_deg=17.0,
    ),
    "fender_vintage": NeckDimensions(
        nut_width_in=1.625,
        depth_at_1st_in=0.82,
        depth_at_12th_in=0.92,
        scale_length_in=25.5,
        headstock_angle_deg=0.0,  # Flat headstock
    ),
    "fender_modern": NeckDimensions(
        nut_width_in=1.6875,
        depth_at_1st_in=0.78,
        depth_at_12th_in=0.88,
        scale_length_in=25.5,
        headstock_angle_deg=0.0,
    ),
    "prs": NeckDimensions(
        nut_width_in=1.6875,
        depth_at_1st_in=0.83,
        depth_at_12th_in=0.90,
        scale_length_in=25.0,
        headstock_angle_deg=10.0,
    ),
    "classical": NeckDimensions(
        nut_width_in=2.0,
        depth_at_1st_in=0.85,
        depth_at_12th_in=0.95,
        scale_length_in=25.6,  # 650mm
        headstock_angle_deg=15.0,
        blank_width_in=4.0,  # Wider for slotted
    ),
}


# =============================================================================
# HEADSTOCK GEOMETRY
# =============================================================================

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
        # Fender 6-in-line
        half_width = dims.nut_width_in / 2

        points = [
            (0.0, half_width),
            (-0.25, half_width),
            (-0.5, half_width + 0.25),
            (-1.0, half_width + 0.5),
            # Upper edge (tuner side)
            (-2.0, 1.5),
            (-4.0, 1.45),
            (-6.0, 1.35),
            (-7.0, 1.2),
            # Tip
            (-7.5, 0.8),
            (-7.5, -0.4),  # Asymmetric
            # Lower edge
            (-7.0, -0.7),
            (-5.0, -0.65),
            (-3.0, -0.6),
            (-1.0, -half_width),
            (0.0, -half_width),
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
        # 6-in-line
        spacing = 0.9
        y_offset = 0.9
        for i in range(6):
            x = -1.5 - (i * spacing)
            positions.append((x, y_offset))

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
