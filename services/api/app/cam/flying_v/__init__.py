# services/api/app/cam/flying_v/__init__.py
"""
Flying V CAM Module

Resolves:
- FV-GAP-05: Pocket toolpath generator for parametric cavity placement
- FV-GAP-10: Neck pocket depth validation

Uses spec JSON (gibson_flying_v_1958.json) for all dimensions.
"""

from .pocket_generator import (
    FlyingVSpec,
    load_flying_v_spec,
    generate_control_cavity_toolpath,
    generate_neck_pocket_toolpath,
    generate_pickup_cavity_toolpath,
)

from .depth_validator import (
    validate_neck_pocket_depth,
    validate_control_cavity_depth,
    validate_all_depths,
    validate_flying_v_gcode_file,
)

__all__ = [
    # Spec loading
    "FlyingVSpec",
    "load_flying_v_spec",
    # Toolpath generation
    "generate_control_cavity_toolpath",
    "generate_neck_pocket_toolpath",
    "generate_pickup_cavity_toolpath",
    # Depth validation
    "validate_neck_pocket_depth",
    "validate_control_cavity_depth",
    "validate_all_depths",
    "validate_flying_v_gcode_file",
]
