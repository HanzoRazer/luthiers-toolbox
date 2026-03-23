"""
Bridge Geometry Subpackage

Provides bridge placement, saddle positioning, and intonation compensation.

Modules:
- geometry: Core bridge geometry calculations (moved from bridge_geometry.py)
- placement: Bridge placement helpers (Wave 14)
- compensation: Intonation compensation calculations (Wave 14)
"""

from .geometry import (
    compute_bridge_location_mm,
    compute_saddle_positions_mm,
    compute_bridge_height_profile,
    compute_archtop_bridge_placement,
    compute_compensation_estimate,
    STANDARD_6_STRING_COMPENSATION,
    STANDARD_4_STRING_BASS_COMPENSATION,
)
from .placement import compute_bridge_placement
from .compensation import compute_compensated_bridge

__all__ = [
    # geometry (legacy)
    "compute_bridge_location_mm",
    "compute_saddle_positions_mm",
    "compute_bridge_height_profile",
    "compute_archtop_bridge_placement",
    "compute_compensation_estimate",
    "STANDARD_6_STRING_COMPENSATION",
    "STANDARD_4_STRING_BASS_COMPENSATION",
    # placement (Wave 14)
    "compute_bridge_placement",
    # compensation (Wave 14)
    "compute_compensated_bridge",
    # electric bridges
    "ELECTRIC_BRIDGES",
    "ElectricBridgeSpec",
    "list_electric_bridges",
    "get_bridge_spec",
    "get_bridge_preset_dict",
    "post_hole_positions",
    "saddle_string_positions",
    "compatibility_check",
    "thread_compatibility",
    # floyd rose
    "FR_ORIGINAL",
    "FloydRoseOriginalDimensions",
    "FloydRoseRoutingSpec",
    "FloydRoseSaddleSpec",
    "compute_routing_spec",
    "compute_saddle_positions",
    "floyd_rose_bridge_preset",
    "floyd_rose_routing_gcode",
    "radius_match_note",
]

from .electric_bridges import (
    ELECTRIC_BRIDGES,
    ElectricBridgeSpec,
    list_electric_bridges,
    get_bridge_spec,
    get_bridge_preset_dict,
    post_hole_positions,
    saddle_string_positions,
    compatibility_check,
    thread_compatibility,
    bridge_summary,
)

from .floyd_rose_tremolo import (
    FR_ORIGINAL,
    FloydRoseOriginalDimensions,
    FloydRoseRoutingSpec,
    FloydRoseSaddleSpec,
    compute_routing_spec,
    compute_saddle_positions,
    floyd_rose_bridge_preset,
    floyd_rose_routing_gcode,
    radius_match_note,
)
