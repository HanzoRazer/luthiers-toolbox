# services/api/app/calculators/overhang_channel_calc.py

"""
Fretboard Overhang Channel Calculator — GAP-05

Generates the geometry for a shallow recess in the guitar body
to clear the extended fretboard on 24-fret (or higher) guitars.

Context:
- Standard Strat: fretboard ends at fret 22, body surface is flush
- 24-fret Strat: fretboard extends ~20mm past fret 22, overhanging the body
- This overhang requires a shallow channel routed into the body top

The channel is typically:
- 1.5-3mm deep (just enough to clear fret tang + fretboard binding)
- ~5mm wider than fretboard at each side (clearance for finish/binding)
- Starts at the body/neck joint and extends to accommodate the overhang

Coordinate system:
- Origin (X=0) at nut
- X+ toward bridge
- Y=0 centerline
- Nut width at X=0, heel width at neck/body junction
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Literal
from enum import Enum


class ChannelShape(str, Enum):
    """Overhang channel end shape options."""
    SQUARED = "squared"        # Straight end (easier to rout)
    ROUNDED = "rounded"        # Radiused end matching fretboard
    CONTOURED = "contoured"    # Follows fretboard taper


@dataclass
class OverhangChannelParams:
    """Input parameters for overhang channel calculation."""

    # Scale and fret parameters
    scale_length_mm: float = 647.7  # 25.5" Fender default
    fret_count: int = 24            # Must be > 22 for overhang
    standard_fret_count: int = 22   # Reference for "standard" guitar

    # Fretboard dimensions
    nut_width_mm: float = 42.86     # 1.6875" Fender spec
    heel_width_mm: float = 56.36    # 2.22" at heel

    # Neck pocket / body junction
    body_junction_fret: float = 17.0  # Where neck meets body

    # Channel specifications
    channel_depth_mm: float = 2.0   # Shallow recess depth
    side_clearance_mm: float = 3.0  # Extra width on each side
    end_clearance_mm: float = 2.0   # Extra length past last fret

    # Shape options
    end_shape: ChannelShape = ChannelShape.ROUNDED
    corner_radius_mm: float = 3.0   # For rounded corners


@dataclass
class OverhangChannelResult:
    """Calculated overhang channel geometry."""

    # Reference points (from nut)
    fret_22_position_mm: float
    fret_24_position_mm: float
    body_junction_mm: float

    # Overhang dimensions
    overhang_length_mm: float       # How far fretboard extends past fret 22
    channel_start_mm: float         # Where channel begins (X from nut)
    channel_end_mm: float           # Where channel ends (X from nut)
    channel_length_mm: float        # Total channel length

    # Width at key positions
    fretboard_width_at_22_mm: float
    fretboard_width_at_24_mm: float
    channel_width_at_start_mm: float
    channel_width_at_end_mm: float

    # Pocket parameters
    channel_depth_mm: float
    corner_radius_mm: float
    end_shape: ChannelShape

    # Outline points (closed polyline, CW from body junction)
    outline_points_mm: List[Tuple[float, float]] = field(default_factory=list)

    # Notes for the builder
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fret_22_position_mm": round(self.fret_22_position_mm, 2),
            "fret_24_position_mm": round(self.fret_24_position_mm, 2),
            "body_junction_mm": round(self.body_junction_mm, 2),
            "overhang_length_mm": round(self.overhang_length_mm, 2),
            "channel_start_mm": round(self.channel_start_mm, 2),
            "channel_end_mm": round(self.channel_end_mm, 2),
            "channel_length_mm": round(self.channel_length_mm, 2),
            "fretboard_width_at_22_mm": round(self.fretboard_width_at_22_mm, 2),
            "fretboard_width_at_24_mm": round(self.fretboard_width_at_24_mm, 2),
            "channel_width_at_start_mm": round(self.channel_width_at_start_mm, 2),
            "channel_width_at_end_mm": round(self.channel_width_at_end_mm, 2),
            "channel_depth_mm": round(self.channel_depth_mm, 2),
            "corner_radius_mm": round(self.corner_radius_mm, 2),
            "end_shape": self.end_shape.value,
            "outline_points_mm": [(round(x, 3), round(y, 3)) for x, y in self.outline_points_mm],
            "notes": self.notes,
        }


# =============================================================================
# CORE CALCULATIONS
# =============================================================================

def fret_position_from_nut_mm(scale_length_mm: float, fret_number: int) -> float:
    """
    Calculate fret position from nut using 12-TET formula.

    Formula: position = scale_length * (1 - 1/2^(fret/12))
    """
    if fret_number <= 0:
        return 0.0
    return scale_length_mm * (1 - 1 / (2 ** (fret_number / 12)))


def interpolate_fretboard_width(
    nut_width_mm: float,
    heel_width_mm: float,
    nut_to_heel_mm: float,
    position_from_nut_mm: float,
) -> float:
    """
    Calculate fretboard width at any position using linear interpolation.

    Standard fretboards taper linearly from nut to heel.
    """
    if nut_to_heel_mm <= 0:
        return nut_width_mm

    ratio = min(1.0, max(0.0, position_from_nut_mm / nut_to_heel_mm))
    return nut_width_mm + ratio * (heel_width_mm - nut_width_mm)


def calculate_overhang_channel(
    params: Optional[OverhangChannelParams] = None,
    **kwargs,
) -> OverhangChannelResult:
    """
    Calculate the overhang channel geometry for extended-fret guitars.

    Args:
        params: OverhangChannelParams object, or pass kwargs
        **kwargs: Override any OverhangChannelParams fields

    Returns:
        OverhangChannelResult with full channel geometry

    Example:
        >>> result = calculate_overhang_channel(
        ...     scale_length_mm=647.7,
        ...     fret_count=24,
        ...     nut_width_mm=42.86,
        ...     heel_width_mm=56.36,
        ... )
        >>> print(f"Overhang: {result.overhang_length_mm}mm")
    """
    # Build params from kwargs or defaults
    if params is None:
        params = OverhangChannelParams(**kwargs)

    notes = []

    # Validate: overhang only needed for > standard frets
    if params.fret_count <= params.standard_fret_count:
        notes.append(f"No overhang needed: {params.fret_count} frets ≤ standard {params.standard_fret_count}")
        return OverhangChannelResult(
            fret_22_position_mm=fret_position_from_nut_mm(params.scale_length_mm, 22),
            fret_24_position_mm=fret_position_from_nut_mm(params.scale_length_mm, 24),
            body_junction_mm=fret_position_from_nut_mm(params.scale_length_mm, params.body_junction_fret),
            overhang_length_mm=0.0,
            channel_start_mm=0.0,
            channel_end_mm=0.0,
            channel_length_mm=0.0,
            fretboard_width_at_22_mm=0.0,
            fretboard_width_at_24_mm=0.0,
            channel_width_at_start_mm=0.0,
            channel_width_at_end_mm=0.0,
            channel_depth_mm=0.0,
            corner_radius_mm=0.0,
            end_shape=params.end_shape,
            outline_points_mm=[],
            notes=notes,
        )

    # Calculate reference positions
    fret_22_pos = fret_position_from_nut_mm(params.scale_length_mm, 22)
    fret_last_pos = fret_position_from_nut_mm(params.scale_length_mm, params.fret_count)
    body_junction = fret_position_from_nut_mm(params.scale_length_mm, params.body_junction_fret)

    # Overhang = distance from fret 22 to last fret
    overhang_length = fret_last_pos - fret_22_pos

    # Channel extents
    # Start: where fretboard begins to overhang (typically fret 22 area)
    # We actually start the channel slightly before fret 22 for clean transition
    channel_start = fret_22_pos - 5.0  # 5mm before fret 22

    # End: past the last fret with clearance
    channel_end = fret_last_pos + params.end_clearance_mm

    channel_length = channel_end - channel_start

    # Calculate fretboard widths
    # Use body junction as the heel reference for width interpolation
    nut_to_heel = body_junction  # Simplified: treat body junction as heel

    width_at_22 = interpolate_fretboard_width(
        params.nut_width_mm, params.heel_width_mm, nut_to_heel, fret_22_pos
    )
    width_at_last = interpolate_fretboard_width(
        params.nut_width_mm, params.heel_width_mm, nut_to_heel, fret_last_pos
    )

    # Channel widths (fretboard + clearance on each side)
    channel_width_start = width_at_22 + 2 * params.side_clearance_mm
    channel_width_end = width_at_last + 2 * params.side_clearance_mm

    # Generate outline points
    outline = _generate_channel_outline(
        channel_start=channel_start,
        channel_end=channel_end,
        width_start=channel_width_start,
        width_end=channel_width_end,
        end_shape=params.end_shape,
        corner_radius=params.corner_radius_mm,
    )

    # Build notes
    notes.append(f"24-fret overhang: {overhang_length:.1f}mm past fret 22")
    notes.append(f"Channel depth: {params.channel_depth_mm}mm (clears fret tang + binding)")

    if params.fret_count > 24:
        notes.append(f"Extended range: {params.fret_count} frets (beyond standard 24)")

    return OverhangChannelResult(
        fret_22_position_mm=fret_22_pos,
        fret_24_position_mm=fret_position_from_nut_mm(params.scale_length_mm, 24),
        body_junction_mm=body_junction,
        overhang_length_mm=overhang_length,
        channel_start_mm=channel_start,
        channel_end_mm=channel_end,
        channel_length_mm=channel_length,
        fretboard_width_at_22_mm=width_at_22,
        fretboard_width_at_24_mm=width_at_last if params.fret_count == 24 else fret_position_from_nut_mm(params.scale_length_mm, 24),
        channel_width_at_start_mm=channel_width_start,
        channel_width_at_end_mm=channel_width_end,
        channel_depth_mm=params.channel_depth_mm,
        corner_radius_mm=params.corner_radius_mm,
        end_shape=params.end_shape,
        outline_points_mm=outline,
        notes=notes,
    )


def _generate_channel_outline(
    channel_start: float,
    channel_end: float,
    width_start: float,
    width_end: float,
    end_shape: ChannelShape,
    corner_radius: float,
    arc_segments: int = 8,
) -> List[Tuple[float, float]]:
    """
    Generate closed outline points for the overhang channel.

    Returns points in clockwise order starting from the body junction
    side (channel_start), treble side.

    Coordinate system:
    - X = position along neck (from nut)
    - Y = 0 at centerline, +Y = treble side, -Y = bass side
    """
    points: List[Tuple[float, float]] = []

    half_width_start = width_start / 2
    half_width_end = width_end / 2

    if end_shape == ChannelShape.SQUARED:
        # Simple rectangle with tapered sides
        points = [
            (channel_start, half_width_start),   # Start, treble
            (channel_end, half_width_end),       # End, treble
            (channel_end, -half_width_end),      # End, bass
            (channel_start, -half_width_start),  # Start, bass
            (channel_start, half_width_start),   # Close
        ]

    elif end_shape == ChannelShape.ROUNDED:
        # Tapered rectangle with rounded end
        # Start side (body junction) is straight
        points.append((channel_start, half_width_start))  # Start, treble

        # Treble edge to end
        points.append((channel_end - corner_radius, half_width_end))

        # Rounded end (arc from treble to bass)
        center_y = 0
        for i in range(arc_segments + 1):
            angle = math.pi / 2 - (math.pi * i / arc_segments)
            x = channel_end - corner_radius + corner_radius * math.cos(angle)
            # Scale Y by half_width_end to make elliptical if needed
            y = half_width_end * math.sin(angle)
            points.append((x, y))

        # Bass edge back to start
        points.append((channel_end - corner_radius, -half_width_end))
        points.append((channel_start, -half_width_start))

        # Close
        points.append((channel_start, half_width_start))

    elif end_shape == ChannelShape.CONTOURED:
        # Follow fretboard taper with smooth end
        # Linear interpolation along the channel
        num_segments = 10

        # Treble side (start to end)
        for i in range(num_segments + 1):
            t = i / num_segments
            x = channel_start + t * (channel_end - channel_start)
            y = half_width_start + t * (half_width_end - half_width_start)
            points.append((x, y))

        # Rounded end cap
        for i in range(1, arc_segments):
            angle = math.pi / 2 - (math.pi * i / arc_segments)
            x = channel_end + corner_radius * (math.cos(angle) - 1)
            y = half_width_end * math.sin(angle)
            points.append((x, y))

        # Bass side (end to start)
        for i in range(num_segments, -1, -1):
            t = i / num_segments
            x = channel_start + t * (channel_end - channel_start)
            y = -(half_width_start + t * (half_width_end - half_width_start))
            points.append((x, y))

        # Close
        points.append(points[0])

    return points


# =============================================================================
# PUBLIC API
# =============================================================================

def calculate_24fret_strat_overhang() -> OverhangChannelResult:
    """
    Convenience function for standard 24-fret Stratocaster overhang channel.

    Uses:
    - 25.5" (647.7mm) scale length
    - 24 frets
    - Standard Fender neck dimensions
    """
    return calculate_overhang_channel(
        scale_length_mm=647.7,
        fret_count=24,
        nut_width_mm=42.86,
        heel_width_mm=56.36,
        body_junction_fret=17.0,
        channel_depth_mm=2.0,
        side_clearance_mm=3.0,
        end_clearance_mm=2.0,
        end_shape=ChannelShape.ROUNDED,
    )


def calculate_24fret_lespaul_overhang() -> OverhangChannelResult:
    """
    Convenience function for 24-fret Les Paul overhang channel.

    Uses:
    - 24.75" (628.65mm) scale length
    - 24 frets
    - Gibson neck dimensions
    """
    return calculate_overhang_channel(
        scale_length_mm=628.65,
        fret_count=24,
        nut_width_mm=43.0,
        heel_width_mm=55.0,
        body_junction_fret=16.0,  # Gibson joins earlier
        channel_depth_mm=2.0,
        side_clearance_mm=3.0,
        end_clearance_mm=2.0,
        end_shape=ChannelShape.ROUNDED,
    )
