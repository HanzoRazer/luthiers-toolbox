"""
scale_intonation.py

Core scale length, fret spacing, and bridge compensation helpers
for the Instrument Geometry system.

This module is intentionally generic:
- No hard-wired instrument-specific values.
- No UI or framework dependencies.
- Pure math + simple data structures.

Higher-level code (model presets, DXF exporters, RMOS, Art Studio)
should call these helpers to generate fret tables and saddle positions.

Wave 19 Module - Fan-Fret CAM Foundation
Enhanced with comprehensive intonation system while maintaining
backward compatibility with existing code.

Usage:
    from instrument_geometry.scale_intonation import (
        compute_fret_positions_mm,
        generate_fret_table,
        compute_saddle_positions,
    )
    
    # Backward compatible
    positions = compute_fret_positions_mm(648.0, 22)
    
    # New comprehensive system
    fret_table = generate_fret_table(648.0, 24)
    saddle_positions = compute_saddle_positions(648.0, string_specs)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict

# Backward compatibility imports
from .neck.fret_math import (  # noqa: F401
    compute_fret_positions_mm,
    compute_fret_spacing_mm,
    SEMITONE_RATIO,
)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class FretRow:
    """
    Describes a single fret entry in a fret table.

    All distances are in millimeters (mm), unless otherwise noted.
    """
    fret: int
    from_nut_mm: float
    from_bridge_mm: float
    spacing_to_next_mm: Optional[float]  # None for last fret


@dataclass
class StringCompSpec:
    """
    Input parameters for estimating compensation for a single string.

    This is intentionally simplified and may be refined later.

    Fields:
        diameter_mm:
            String diameter (gauge) in mm.

        modulus_mpa:
            Effective Young's modulus (approximate) in MPa
            for the string construction (plain vs wound).

        tension_newton:
            Approximate string tension at pitch, in Newtons.

        action_height_mm:
            Action (string height above fret) at the 12th fret, in mm.

        k:
            Empirical tuning constant to account for setup style,
            playing attack, etc. Typically determined experimentally.
    """
    diameter_mm: float
    modulus_mpa: float
    tension_newton: float
    action_height_mm: float
    k: float


@dataclass
class SaddlePositionRow:
    """
    Output description for a single string's saddle position.
    
    Fields:
        string_index:
            1-based string number (1 = high E on a typical guitar).

        comp_mm:
            Compensation offset beyond the theoretical scale length, in mm.

        saddle_position_mm:
            Distance from nut to saddle contact point, in mm.
    """
    string_index: int
    comp_mm: float
    saddle_position_mm: float


# ---------------------------------------------------------------------------
# Core Equal-Temperament Fret Math
# ---------------------------------------------------------------------------


def fret_distance_from_nut(scale_length_mm: float, fret: int) -> float:
    """
    Distance from nut to fret `fret` for a 12-TET scale:

        from_nut(f) = L0 * (1 - 2^(-f/12))

    where L0 is the scale length in mm.
    """
    if fret < 0:
        raise ValueError("fret must be >= 0")
    return scale_length_mm * (1.0 - 2.0 ** (-fret / 12.0))


def fret_distance_from_bridge(scale_length_mm: float, fret: int) -> float:
    """
    Distance from bridge to fret `fret`:

        from_bridge(f) = L0 / 2^(f/12) = L0 * 2^(-f/12)
    """
    if fret < 0:
        raise ValueError("fret must be >= 0")
    return scale_length_mm * (2.0 ** (-fret / 12.0))


def fret_spacing(scale_length_mm: float, fret: int) -> float:
    """
    Spacing between fret (f-1) and fret f:

        ΔL_f = L0 * (2^(1/12) - 1) / 2^(f/12)

    For f = 0, spacing is undefined; this function expects fret >= 1.
    """
    if fret <= 0:
        raise ValueError("fret must be >= 1 to compute spacing_to_next")
    return scale_length_mm * (2.0 ** (1.0 / 12.0) - 1.0) / (2.0 ** (fret / 12.0))


def generate_fret_table(scale_length_mm: float, num_frets: int) -> List[FretRow]:
    """
    Generate a full fret table from fret 0 to `num_frets` inclusive.

    Fret 0 is treated as the nut position (0 mm from nut, L0 from bridge).

    Returns a list of FretRow entries.
    """
    if num_frets < 0:
        raise ValueError("num_frets must be >= 0")

    rows: List[FretRow] = []

    for f in range(0, num_frets + 1):
        from_nut = fret_distance_from_nut(scale_length_mm, f)
        from_bridge = fret_distance_from_bridge(scale_length_mm, f)

        if f < num_frets:
            spacing_next = fret_spacing(scale_length_mm, f + 1)
        else:
            spacing_next = None

        rows.append(
            FretRow(
                fret=f,
                from_nut_mm=from_nut,
                from_bridge_mm=from_bridge,
                spacing_to_next_mm=spacing_next,
            )
        )

    return rows


# ---------------------------------------------------------------------------
# Neck Joint / Bridge Layout
# ---------------------------------------------------------------------------


def joint_to_bridge_distance_mm(scale_length_mm: float, joint_fret: int) -> float:
    """
    Distance from the neck joint fret to the (theoretical) bridge line.

        joint_to_bridge = L0 / 2^(joint_fret/12)

    This is useful for validating body layouts and placing bridges
    for designs where the neck joins the body at a specific fret,
    e.g. 14th fret on many archtops.
    """
    if joint_fret <= 0:
        raise ValueError("joint_fret must be >= 1")
    return scale_length_mm / (2.0 ** (joint_fret / 12.0))


# ---------------------------------------------------------------------------
# Bridge Compensation (Simplified Model)
# ---------------------------------------------------------------------------


def estimate_compensation_mm(
    diameter_mm: float,
    modulus_mpa: float,
    tension_newton: float,
    action_height_mm: float,
    k: float,
) -> float:
    """
    Estimate compensation for a single string (very simplified).

    Conceptual form:

        C ≈ (d^2 * E) / (4 * T) + (Δh * k)

    where:
        d   = string diameter in mm
        E   = effective modulus in MPa
        T   = string tension in N
        Δh  = action height at 12th fret, mm
        k   = empirical constant for setup style and attack

    This is not meant to be a highly accurate physics model; it is a
    tunable approximation that can be calibrated against real setups.
    """
    if tension_newton <= 0:
        raise ValueError("tension_newton must be > 0")

    stiffness_term = (diameter_mm ** 2 * modulus_mpa) / (4.0 * tension_newton)
    action_term = action_height_mm * k
    return stiffness_term + action_term


def compute_saddle_positions(
    scale_length_mm: float,
    string_specs: List[StringCompSpec],
) -> List[SaddlePositionRow]:
    """
    Compute saddle positions for a set of strings.

    For each string:
        theoretical line = scale_length_mm
        compensated saddle = theoretical + C_string

    Returns a list of SaddlePositionRow entries.
    """
    rows: List[SaddlePositionRow] = []

    for idx, spec in enumerate(string_specs):
        comp = estimate_compensation_mm(
            diameter_mm=spec.diameter_mm,
            modulus_mpa=spec.modulus_mpa,
            tension_newton=spec.tension_newton,
            action_height_mm=spec.action_height_mm,
            k=spec.k,
        )
        saddle_pos = scale_length_mm + comp

        rows.append(
            SaddlePositionRow(
                string_index=idx + 1,
                comp_mm=comp,
                saddle_position_mm=saddle_pos,
            )
        )

    return rows


# ---------------------------------------------------------------------------
# Convenience: build default string sets for presets
# ---------------------------------------------------------------------------


def make_simple_compensation_profile(
    scale_length_mm: float,
    per_string_comp_mm: Dict[int, float],
) -> List[SaddlePositionRow]:
    """
    Utility for presets where you already know roughly how much
    compensation you want per string (in mm), e.g. from measurement.

    This allows you to bypass the full physics approximation for now,
    while still using the SaddlePositionRow structure.
    """
    rows: List[SaddlePositionRow] = []

    for string_index, comp_mm in sorted(per_string_comp_mm.items()):
        saddle_pos = scale_length_mm + comp_mm
        rows.append(
            SaddlePositionRow(
                string_index=string_index,
                comp_mm=comp_mm,
                saddle_position_mm=saddle_pos,
            )
        )

    return rows


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


__all__ = [
    # Backward compatibility
    "compute_fret_positions_mm",
    "compute_fret_spacing_mm",
    "SEMITONE_RATIO",
    
    # Data models
    "FretRow",
    "StringCompSpec",
    "SaddlePositionRow",
    
    # Fret math
    "fret_distance_from_nut",
    "fret_distance_from_bridge",
    "fret_spacing",
    "generate_fret_table",
    
    # Bridge/joint
    "joint_to_bridge_distance_mm",
    
    # Compensation
    "estimate_compensation_mm",
    "compute_saddle_positions",
    "make_simple_compensation_profile",
]
