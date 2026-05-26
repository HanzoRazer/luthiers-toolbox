"""
CAM Drilling Module

Parametric drilling operations for guitar manufacturing.
Resolves: FV-GAP-06 (String-through drilling has no backend API)

Operations:
- G83 peck drilling cycle for deep holes
- String-through ferrule patterns
- Bolt/screw patterns (neck, pickguard, etc.)
- Pilot holes for hardware

Usage:
    from app.cam.drilling import (
        PeckDrill,
        DrillConfig,
        StringThroughPattern,
        BoltPattern,
    )

    # String-through drilling
    pattern = StringThroughPattern(
        string_count=6,
        spacing_mm=10.5,
        start_x=0,
        start_y=0,
    )
    drill = PeckDrill(
        holes=pattern.get_holes(),
        config=DrillConfig(
            hole_depth_mm=45.0,
            peck_depth_mm=5.0,
            drill_diameter_mm=3.0,
        )
    )
    gcode = drill.generate_gcode()
"""

from .peck_cycle import PeckDrill, DrillConfig, DrillResult, DrillHole
from .patterns import (
    StringThroughPattern,
    BoltPattern,
    GridPattern,
    CircularPattern,
)
from .intent_schema import DrillingDesignV1, DrillPointV1, validate_drilling_design
from .intent_adapter import drilling_params_from_intent
from .feasibility import (
    DrillingFeasibilityResult,
    compute_drilling_feasibility,
    hash_feasibility_result,
)

__all__ = [
    # Core drilling
    "PeckDrill",
    "DrillConfig",
    "DrillResult",
    "DrillHole",
    # Patterns
    "StringThroughPattern",
    "BoltPattern",
    "GridPattern",
    "CircularPattern",
    # Intent (8I)
    "DrillingDesignV1",
    "DrillPointV1",
    "validate_drilling_design",
    "drilling_params_from_intent",
    "DrillingFeasibilityResult",
    "compute_drilling_feasibility",
    "hash_feasibility_result",
]
