"""
Instrument Geometry: Scale Length & Fret Positions

Implements canonical equal-tempered fret spacing for a given scale length.

See docs/KnowledgeBase/Instrument_Geometry/Fret_Scale_Theory.md
for derivations, references, and assumptions.

Core Formula (12th Root of 2):
    The distance from the nut to the nth fret is:
        d_n = scale_length - scale_length / (2^(n/12))

    Or equivalently:
        d_n = scale_length * (1 - 1/(2^(n/12)))

    This is derived from equal temperament, where each semitone
    has a frequency ratio of 2^(1/12) ≈ 1.05946.

References:
    - https://www.liutaiomottola.com/formulae/fret.htm
    - Stewart-MacDonald fret scale calculator
    - "Guitar Making: Tradition and Technology" by Cumpiano & Natelson

Moved from: instrument_geometry/scale_length.py (Wave 14 reorg)
"""

from __future__ import annotations

from math import pow as math_pow
from typing import List, Tuple

# Constants
SEMITONE_RATIO = 2.0 ** (1.0 / 12.0)  # ≈ 1.05946309435929


def compute_fret_positions_mm(scale_length_mm: float, fret_count: int) -> List[float]:
    """
    Compute distance from the nut to each fret (in mm) for an equal-tempered
    instrument using the 12th-root-of-2 rule.

    Formula (distance from nut to nth fret):
        d_n = scale_length - scale_length / (2 ** (n / 12))
        d_n = scale_length * (1 - 2 ** (-n / 12))

    Args:
        scale_length_mm: Full scale length in millimeters (nut to bridge reference).
        fret_count: Number of frets to compute (e.g. 20, 21, 22, 24).

    Returns:
        List of length `fret_count`, where index 0 is the 1st fret, etc.
        Each value is the distance from the nut to that fret in mm.

    Raises:
        ValueError: If scale_length_mm <= 0 or fret_count <= 0.

    Example:
        >>> positions = compute_fret_positions_mm(648.0, 22)  # 25.5" Fender scale
        >>> round(positions[11], 2)  # 12th fret should be at half scale length
        324.0

    Common Scale Lengths:
        - Fender: 648.0 mm (25.5")
        - Gibson: 628.65 mm (24.75")
        - PRS: 635.0 mm (25")
        - Classical: 650.0 mm (25.6")
    """
    if scale_length_mm <= 0:
        raise ValueError("scale_length_mm must be > 0")
    if fret_count <= 0:
        raise ValueError("fret_count must be > 0")

    fret_positions: List[float] = []
    for n in range(1, fret_count + 1):
        # Distance from nut to nth fret
        ratio = math_pow(2.0, n / 12.0)
        position = scale_length_mm - (scale_length_mm / ratio)
        # Equivalent: position = scale_length_mm * (1 - 1/ratio)
        fret_positions.append(position)

    return fret_positions


def compute_fret_spacing_mm(scale_length_mm: float, fret_count: int) -> List[float]:
    """
    Compute the spacing between consecutive frets (in mm).

    This gives the distance from one fret to the next, useful for
    CNC slot cutting where you need incremental moves.

    Args:
        scale_length_mm: Full scale length in millimeters.
        fret_count: Number of frets to compute.

    Returns:
        List of length `fret_count`, where:
        - Index 0 is the distance from nut to 1st fret
        - Index 1 is the distance from 1st fret to 2nd fret
        - etc.

    Example:
        >>> spacings = compute_fret_spacing_mm(648.0, 22)
        >>> round(spacings[0], 2)  # First fret spacing (nut to 1st)
        36.4
        >>> round(spacings[11], 2)  # 12th fret spacing (11th to 12th)
        17.17
    """
    if scale_length_mm <= 0:
        raise ValueError("scale_length_mm must be > 0")
    if fret_count <= 0:
        raise ValueError("fret_count must be > 0")

    positions = compute_fret_positions_mm(scale_length_mm, fret_count)
    spacings: List[float] = []

    for i, pos in enumerate(positions):
        if i == 0:
            # Distance from nut (0) to first fret
            spacings.append(pos)
        else:
            # Distance from previous fret to current fret
            spacings.append(pos - positions[i - 1])

    return spacings


def compute_compensated_scale_length_mm(
    scale_length_mm: float,
    saddle_comp_mm: float,
    nut_comp_mm: float = 0.0,
) -> float:
    """
    Compute the effective scale length after saddle (and optional nut) compensation.

    Intonation compensation is needed because:
    1. Fretting a string increases its tension (sharpens pitch)
    2. String stiffness affects vibration (wound strings need more compensation)
    3. Action height affects stretch when fretting

    Args:
        scale_length_mm: Nominal scale length (nut to saddle reference).
        saddle_comp_mm: Saddle setback compensation (positive = longer).
        nut_comp_mm: Nut compensation (positive = shorter effective length).

    Returns:
        Compensated scale length in mm.

    Example:
        >>> compute_compensated_scale_length_mm(648.0, 2.5, 0.5)
        650.0
    """
    return scale_length_mm + saddle_comp_mm - nut_comp_mm


def compute_fret_to_bridge_mm(
    scale_length_mm: float,
    fret_number: int,
) -> float:
    """
    Compute the distance from a specific fret to the bridge.

    Useful for intonation calculations and pickup placement.

    Args:
        scale_length_mm: Full scale length in mm.
        fret_number: Fret number (1 = first fret, 12 = octave, etc.)

    Returns:
        Distance from the specified fret to the bridge in mm.

    Example:
        >>> round(compute_fret_to_bridge_mm(648.0, 12), 2)
        324.0  # 12th fret is exactly half scale length
    """
    if fret_number <= 0:
        return scale_length_mm  # From nut to bridge

    positions = compute_fret_positions_mm(scale_length_mm, fret_number)
    fret_position = positions[fret_number - 1]
    return scale_length_mm - fret_position


def compute_multiscale_fret_positions_mm(
    bass_scale_mm: float,
    treble_scale_mm: float,
    fret_count: int,
    string_count: int,
    perpendicular_fret: int = 0,
) -> List[List[Tuple[float, float]]]:
    """
    Compute fret positions for a multiscale (fanned fret) instrument.

    Each fret becomes a line segment connecting different positions
    on the bass and treble sides.

    Args:
        bass_scale_mm: Scale length on bass side.
        treble_scale_mm: Scale length on treble side.
        fret_count: Number of frets.
        string_count: Number of strings.
        perpendicular_fret: Which fret is perpendicular to strings (0 = nut).

    Returns:
        List of frets, where each fret is a list of (x, y) positions
        for each string position (bass to treble).

    Note:
        This is a simplified linear interpolation. Real multiscale
        instruments may use more complex fan patterns.
    """
    if bass_scale_mm <= 0 or treble_scale_mm <= 0:
        raise ValueError("Scale lengths must be > 0")
    if fret_count <= 0 or string_count <= 1:
        raise ValueError("fret_count must be > 0, string_count must be > 1")

    bass_positions = compute_fret_positions_mm(bass_scale_mm, fret_count)
    treble_positions = compute_fret_positions_mm(treble_scale_mm, fret_count)

    frets: List[List[Tuple[float, float]]] = []

    for fret_idx in range(fret_count):
        fret_line: List[Tuple[float, float]] = []
        bass_pos = bass_positions[fret_idx]
        treble_pos = treble_positions[fret_idx]

        for string_idx in range(string_count):
            # Linear interpolation from bass to treble
            t = string_idx / (string_count - 1)
            x_pos = bass_pos + (treble_pos - bass_pos) * t
            y_pos = t  # Normalized y-position (0 = bass, 1 = treble)
            fret_line.append((x_pos, y_pos))

        frets.append(fret_line)

    return frets


# Convenience: Common scale lengths in mm
SCALE_LENGTHS_MM = {
    "fender_standard": 648.0,      # 25.5"
    "gibson_standard": 628.65,     # 24.75"
    "prs_standard": 635.0,         # 25"
    "classical": 650.0,            # 25.6"
    "parlor": 609.6,               # 24"
    "baritone": 685.8,             # 27"
    "bass_standard": 863.6,        # 34"
    "bass_short": 762.0,           # 30"
    "mandolin": 349.25,            # 13.75"
    "banjo": 660.4,                # 26"
}

# Convenience: Common radius values in mm
RADIUS_VALUES_MM = {
    "vintage_fender": 184.15,      # 7.25"
    "modern_fender": 241.3,        # 9.5"
    "gibson": 304.8,               # 12"
    "prs": 254.0,                  # 10"
    "ibanez": 400.05,              # 15.75"
    "martin": 406.4,               # 16"
    "flat": float("inf"),          # Flat radius
}
