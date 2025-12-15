"""
Neck Taper Suite: Core Mathematical Engine

Wave 17 - Instrument Geometry Integration

This module implements the distance-based neck taper formulas derived from:
- CNC Layout Guide for tapered guitar neck blank
- Shop Notes Formula Guide  
- Mathematical Derivation (similar triangles)

Core Formula:
    W_f = W_nut + (x_f / L_N) × (W_end - W_nut)
    
Where:
    W_f = width at fret f
    x_f = physical distance from nut to fret f
    L_N = reference length (nut to end fret)
    W_nut = nut width
    W_end = width at reference end fret
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class TaperInputs:
    """
    Input parameters for neck taper calculations.
    
    Attributes:
        scale_length: Scale length (L) in mm or inches (must be consistent)
        nut_width: Width at nut (W_nut)
        end_fret: Reference end fret number (N)
        end_width: Width at end fret (W_end)
    """
    scale_length: float
    nut_width: float
    end_fret: int
    end_width: float


@dataclass
class FretWidth:
    """
    Calculated width information for a specific fret.
    
    Attributes:
        fret: Fret number
        distance_from_nut: Physical distance from nut (x_f)
        width: Full fretboard width at this fret (W_f)
        half_width: Half-width for edge layout (H_f = W_f / 2)
    """
    fret: int
    distance_from_nut: float
    width: float
    half_width: float


# ---------------------------------------------------------------------------
# Core formulas from the derivation + CNC guide
# ---------------------------------------------------------------------------

def fret_distance(scale_length: float, f: int) -> float:
    """
    Calculate physical distance from nut to fret f.
    
    Formula: x_f = L - L / 2^(f/12)
    
    This is the standard equal temperament fret spacing formula.
    
    Args:
        scale_length: Scale length (L)
        f: Fret number (0 = nut, 1 = first fret, etc.)
        
    Returns:
        Distance from nut to fret f in same units as scale_length
    """
    return scale_length - scale_length / (2 ** (f / 12))


def reference_length(scale_length: float, N: int) -> float:
    """
    Calculate distance from nut to the reference end fret.
    
    Formula: L_N = L - L / 2^(N/12)
    
    Args:
        scale_length: Scale length (L)
        N: Reference end fret number
        
    Returns:
        Distance from nut to fret N
    """
    return fret_distance(scale_length, N)


def width_at_fret(inputs: TaperInputs, f: int) -> FretWidth:
    """
    Calculate fretboard width at a specific fret using distance-based taper.
    
    Formula: W_f = W_nut + (x_f / L_N) × (W_end - W_nut)
    
    This uses similar triangles to interpolate width based on actual
    physical distance rather than fret index, which is more geometrically
    accurate for CNC layout.
    
    Args:
        inputs: Taper input parameters
        f: Fret number
        
    Returns:
        FretWidth with calculated dimensions
    """
    x_f = fret_distance(inputs.scale_length, f)
    L_N = reference_length(inputs.scale_length, inputs.end_fret)

    W_f = inputs.nut_width + (x_f / L_N) * (inputs.end_width - inputs.nut_width)
    H_f = W_f / 2

    return FretWidth(
        fret=f,
        distance_from_nut=x_f,
        width=W_f,
        half_width=H_f
    )


def compute_taper_table(
    inputs: TaperInputs,
    frets: List[int]
) -> List[FretWidth]:
    """
    Generate taper table for multiple frets.
    
    Args:
        inputs: Taper input parameters
        frets: List of fret numbers to calculate
        
    Returns:
        List of FretWidth objects, one per fret
        
    Example:
        >>> inputs = TaperInputs(647.7, 42.0, 12, 57.0)
        >>> table = compute_taper_table(inputs, range(0, 13))
        >>> table[0].width  # Nut width
        42.0
        >>> table[12].width  # 12th fret width
        57.0
    """
    return [width_at_fret(inputs, f) for f in frets]
