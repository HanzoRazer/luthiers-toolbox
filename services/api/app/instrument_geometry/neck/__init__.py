"""
Neck Geometry Subpackage

Provides fret spacing, neck profiles, and compound radius calculations.

Modules:
- fret_math: Equal-tempered fret position calculations
- neck_profiles: InstrumentSpec, FretboardSpec dataclasses
- radius_profiles: Compound radius arc calculations
"""

from .fret_math import (
    compute_fret_positions_mm,
    compute_fret_spacing_mm,
    compute_compensated_scale_length_mm,
    compute_fret_to_bridge_mm,
    compute_multiscale_fret_positions_mm,
    SCALE_LENGTHS_MM,
    RADIUS_VALUES_MM,
    SEMITONE_RATIO,
)
from .neck_profiles import (
    InstrumentSpec,
    FretboardSpec,
    BridgeSpec,
    RadiusProfile,
)
from .radius_profiles import (
    compute_compound_radius_at_fret,
    compute_radius_arc_points,
    compute_radius_drop_mm,
    compute_fret_crown_height_mm,
    compute_string_height_at_fret,
    generate_compound_radius_profile,
    inches_to_mm,
    mm_to_inches,
)

__all__ = [
    # fret_math
    "compute_fret_positions_mm",
    "compute_fret_spacing_mm",
    "compute_compensated_scale_length_mm",
    "compute_fret_to_bridge_mm",
    "compute_multiscale_fret_positions_mm",
    "SCALE_LENGTHS_MM",
    "RADIUS_VALUES_MM",
    "SEMITONE_RATIO",
    # neck_profiles
    "InstrumentSpec",
    "FretboardSpec",
    "BridgeSpec",
    "RadiusProfile",
    # radius_profiles
    "compute_compound_radius_at_fret",
    "compute_radius_arc_points",
    "compute_radius_drop_mm",
    "compute_fret_crown_height_mm",
    "compute_string_height_at_fret",
    "generate_compound_radius_profile",
    "inches_to_mm",
    "mm_to_inches",
]
