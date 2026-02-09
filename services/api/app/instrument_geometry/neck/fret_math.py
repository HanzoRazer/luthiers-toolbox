"""Instrument Geometry: Scale Length & Fret Positions"""

from __future__ import annotations

from dataclasses import dataclass
from math import pow as math_pow, atan2, pi, fabs, atan, degrees
from typing import List, Tuple, Optional, Dict, Any

# Constants
SEMITONE_RATIO = 2.0 ** (1.0 / 12.0)  # ≈ 1.05946309435929

# Fan-fret perpendicular tolerance (radians)
# Used to determine if a fret is "perpendicular enough" to treat as straight
PERP_ANGLE_EPS = 1e-4  # ~0.006 degrees


@dataclass
class FanFretPoint:
    """A single point on a fan-fret (multiscale) fretboard."""
    fret_number: int
    string_index: int
    x_mm: float
    y_mm: float
    angle_rad: float = 0.0
    is_perpendicular: bool = True
    bass_scale_mm: Optional[float] = None
    treble_scale_mm: Optional[float] = None
    
    @property
    def position_mm(self) -> Tuple[float, float]:
        """Return (x, y) position tuple."""
        return (self.x_mm, self.y_mm)
    
    @property
    def angle_deg(self) -> float:
        """Return fret angle in degrees."""
        return self.angle_rad * 180.0 / pi
    
    def distance_to(self, other: "FanFretPoint") -> float:
        """Calculate distance to another FanFretPoint."""
        dx = self.x_mm - other.x_mm
        dy = self.y_mm - other.y_mm
        return (dx * dx + dy * dy) ** 0.5


def _compute_fret_angle(
    bass_x: float,
    treble_x: float,
    fretboard_width_mm: float,
) -> Tuple[float, bool]:
    """Compute the angle of a fan fret relative to perpendicular."""
    if fretboard_width_mm <= 0:
        return (0.0, True)
    
    dx = treble_x - bass_x
    dy = fretboard_width_mm
    
    # Angle from perpendicular (perpendicular would have dx=0)
    angle_rad = atan2(dx, dy)
    
    # Check if effectively perpendicular
    is_perp = fabs(angle_rad) < PERP_ANGLE_EPS
    
    return (angle_rad, is_perp)


def compute_fret_positions_mm(scale_length_mm: float, fret_count: int) -> List[float]:
    """Compute distance from the nut to each fret (in mm) for an equal-tempered"""
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
    """Compute the spacing between consecutive frets (in mm)."""
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
    """Compute the effective scale length after saddle (and optional nut) compensation."""
    return scale_length_mm + saddle_comp_mm - nut_comp_mm


def compute_fret_to_bridge_mm(
    scale_length_mm: float,
    fret_number: int,
) -> float:
    """Compute the distance from a specific fret to the bridge."""
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
    fretboard_width_mm: float = 50.0,
) -> List[List[FanFretPoint]]:
    """Compute fret positions for a multiscale (fanned fret) instrument."""
    if bass_scale_mm <= 0 or treble_scale_mm <= 0:
        raise ValueError("Scale lengths must be > 0")
    if fret_count <= 0 or string_count <= 1:
        raise ValueError("fret_count must be > 0, string_count must be > 1")

    bass_positions = compute_fret_positions_mm(bass_scale_mm, fret_count)
    treble_positions = compute_fret_positions_mm(treble_scale_mm, fret_count)

    frets: List[List[FanFretPoint]] = []
    half_width = fretboard_width_mm / 2.0

    for fret_idx in range(fret_count):
        fret_line: List[FanFretPoint] = []
        bass_pos = bass_positions[fret_idx]
        treble_pos = treble_positions[fret_idx]
        
        # Compute fret angle
        angle_rad, is_perp = _compute_fret_angle(
            bass_pos, treble_pos, fretboard_width_mm
        )
        
        # Override: if this is the designated perpendicular fret, force perpendicular
        if fret_idx + 1 == perpendicular_fret:
            is_perp = True
            angle_rad = 0.0

        for string_idx in range(string_count):
            # Linear interpolation from bass to treble
            t = string_idx / (string_count - 1)
            x_pos = bass_pos + (treble_pos - bass_pos) * t
            y_pos = -half_width + (fretboard_width_mm * t)  # -half to +half
            
            point = FanFretPoint(
                fret_number=fret_idx + 1,
                string_index=string_idx,
                x_mm=x_pos,
                y_mm=y_pos,
                angle_rad=angle_rad,
                is_perpendicular=is_perp,
                bass_scale_mm=bass_scale_mm,
                treble_scale_mm=treble_scale_mm,
            )
            fret_line.append(point)

        frets.append(fret_line)

    return frets


def compute_multiscale_fret_positions_tuples(
    bass_scale_mm: float,
    treble_scale_mm: float,
    fret_count: int,
    string_count: int,
    perpendicular_fret: int = 0,
) -> List[List[Tuple[float, float]]]:
    """
    Legacy wrapper: Returns simple (x, y) tuples instead of FanFretPoint objects.
    
    Provided for backwards compatibility with code expecting tuple format.
    For new code, use compute_multiscale_fret_positions_mm() instead.
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


# ============================================================================
# BACKWARD COMPATIBILITY IMPLEMENTATION
# ============================================================================
# Added during Architecture Drift Patch (Wave E1)
# This implementation maintains compatibility with routers expecting the old
# compute_fan_fret_positions() signature from fret_math.py.bak (lines 274-434)
#
# Used by:
#   - app.routers.instrument_geometry_router (line 529)
#   - app.cam.cam_preview_router (if used)
#   - app.routers.cam_fret_slots_router (if used)
#
# NOTE: The old FanFretPoint had different fields than the new one:
#   Old: fret_number, treble_pos_mm, bass_pos_mm, angle_rad, center_x, center_y, is_perpendicular
#   New: fret_number, string_index, x_mm, y_mm, angle_rad, is_perpendicular, bass_scale_mm, treble_scale_mm
#
# To maintain compatibility, we create a compatibility class that matches the old structure.

@dataclass
class FanFretPointLegacy:
    """DEPRECATED: Legacy FanFretPoint structure from Wave 19 (fret_math.py.bak line 274)."""
    fret_number: int
    treble_pos_mm: float
    bass_pos_mm: float
    angle_rad: float
    center_x: float
    center_y: float
    is_perpendicular: bool = False
    
    @property
    def angle_deg(self) -> float:
        """Return fret angle in degrees."""
        return self.angle_rad * 180.0 / pi


def _compute_fret_position_standard(scale_length_mm: float, fret_number: int) -> float:
    """
    Helper: Calculate fret position for standard (non-fan) fretting using Rule of 18.
    
    Args:
        scale_length_mm: Scale length in millimeters
        fret_number: Fret number (1-24, 0 = nut)
    
    Returns:
        Distance from nut to fret in millimeters
    """
    if fret_number == 0:
        return 0.0
    return scale_length_mm * (1.0 - math_pow(2.0, -fret_number / 12.0))


def _calculate_perpendicular_fret_intersection(
    treble_scale_mm: float,
    bass_scale_mm: float,
    target_fret: int = 7
) -> Tuple[float, float]:
    """Helper: Calculate the intersection point where the specified fret should be perpendicular."""
    treble_pos = _compute_fret_position_standard(treble_scale_mm, target_fret)
    bass_pos = _compute_fret_position_standard(bass_scale_mm, target_fret)
    avg_pos = (treble_pos + bass_pos) / 2.0
    return (avg_pos, avg_pos)


def compute_fan_fret_positions(
    treble_scale_mm: float,
    bass_scale_mm: float,
    fret_count: int,
    nut_width_mm: float,
    heel_width_mm: float,
    perpendicular_fret: int = 7,
    scale_length_reference_mm: float = None,
) -> List[FanFretPointLegacy]:
    """DEPRECATED: Backward compatibility implementation for old compute_fan_fret_positions API."""
    fret_points: List[FanFretPointLegacy] = []
    
    # Calculate perpendicular fret position (both sides equal)
    perp_treble, perp_bass = _calculate_perpendicular_fret_intersection(
        treble_scale_mm, bass_scale_mm, perpendicular_fret
    )
    
    # Calculate Y positions (half-widths, since centerline is at Y=0)
    nut_half = nut_width_mm / 2.0
    heel_half = heel_width_mm / 2.0
    
    for fret_num in range(fret_count + 1):  # Include fret 0 (nut)
        # Calculate X positions (distance from nut)
        if fret_num == perpendicular_fret:
            # Perpendicular fret: both sides at same position
            treble_x = perp_treble
            bass_x = perp_bass
        else:
            # Regular fret: use respective scale lengths
            treble_x = _compute_fret_position_standard(treble_scale_mm, fret_num)
            bass_x = _compute_fret_position_standard(bass_scale_mm, fret_num)
        
        # Calculate average X for taper interpolation
        avg_x = (treble_x + bass_x) / 2.0
        
        # Estimate scale length position (0 at nut, 1 at bridge)
        scale_ratio = avg_x / treble_scale_mm if treble_scale_mm > 0 else 0.0
        scale_ratio = min(1.0, scale_ratio)  # Clamp to [0, 1]
        
        # Interpolate Y positions based on fretboard taper
        # Treble side is negative Y, bass side is positive Y
        treble_y = -1.0 * (nut_half + (heel_half - nut_half) * scale_ratio)
        bass_y = nut_half + (heel_half - nut_half) * scale_ratio
        
        # Calculate fret angle (deviation from perpendicular to centerline)
        dx = treble_x - bass_x  # Positive when treble is ahead of bass
        dy = bass_y - treble_y  # Full width from treble side to bass side
        
        if abs(dx) < 0.001:  # Perpendicular fret (or very close)
            angle_rad = 0.0
            is_perp = True
        else:
            angle_rad = atan(dx / dy) if abs(dy) > 0.001 else 0.0
            is_perp = (fret_num == perpendicular_fret) or (abs(angle_rad) < PERP_ANGLE_EPS)
        
        # Create FanFretPointLegacy with old structure
        fret_point = FanFretPointLegacy(
            fret_number=fret_num,
            treble_pos_mm=treble_x,
            bass_pos_mm=bass_x,
            angle_rad=angle_rad,
            center_x=avg_x,
            center_y=0.0,  # Centerline
            is_perpendicular=is_perp
        )
        fret_points.append(fret_point)
    
    return fret_points


def validate_fan_fret_geometry(
    treble_scale_mm: float,
    bass_scale_mm: float,
    fret_count: int,
    perpendicular_fret: int,
) -> Dict[str, Any]:
    """DEPRECATED: Validate fan-fret parameters before calculation."""
    warnings = []
    
    if treble_scale_mm <= 0:
        return {"valid": False, "message": "Treble scale length must be positive"}
    
    if bass_scale_mm <= 0:
        return {"valid": False, "message": "Bass scale length must be positive"}
    
    if bass_scale_mm < treble_scale_mm:
        return {"valid": False, "message": "Bass scale should be >= treble scale (standard convention)"}
    
    if perpendicular_fret < 0 or perpendicular_fret > fret_count:
        return {"valid": False, "message": f"Perpendicular fret must be between 0 and {fret_count}"}
    
    # Scale range check
    if treble_scale_mm < 500 or treble_scale_mm > 900:
        warnings.append(f"Treble scale ({treble_scale_mm:.1f}mm) is outside typical range (500-900mm)")
    
    if bass_scale_mm < 500 or bass_scale_mm > 900:
        warnings.append(f"Bass scale ({bass_scale_mm:.1f}mm) is outside typical range (500-900mm)")
    
    scale_diff = bass_scale_mm - treble_scale_mm
    if scale_diff > 100.0:
        warnings.append(f"Scale difference ({scale_diff:.1f}mm) is unusually large (>100mm)")
    
    result = {"valid": True, "message": "Fan-fret geometry is valid"}
    if warnings:
        result["warnings"] = warnings
    
    return result


# Common fan-fret configurations (DEPRECATED: for backward compatibility only)
FAN_FRET_PRESETS = {
    "7_string_standard": {
        "treble_scale_mm": 648.0,  # 25.5"
        "bass_scale_mm": 686.0,    # 27"
        "perpendicular_fret": 7,
        "description": "Standard 7-string multi-scale (25.5\"-27\")"
    },
    "8_string_standard": {
        "treble_scale_mm": 648.0,  # 25.5"
        "bass_scale_mm": 711.2,    # 28"
        "perpendicular_fret": 8,
        "description": "Standard 8-string multi-scale (25.5\"-28\")"
    },
    "baritone_6_string": {
        "treble_scale_mm": 660.0,  # 26"
        "bass_scale_mm": 685.8,    # 27"
        "perpendicular_fret": 7,
        "description": "Baritone 6-string multi-scale (26\"-27\")"
    }
}
