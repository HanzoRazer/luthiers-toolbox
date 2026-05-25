"""
CAM Profiling Module

Outside-contour toolpath generation for body perimeter routing.
Resolves: OM-GAP-02, BEN-GAP-03, VINE-07, FV-GAP-03

Usage:
    from app.cam.profiling import ProfileToolpath, ProfileConfig

    profile = ProfileToolpath(
        outline=body_polygon,
        config=ProfileConfig(
            tool_diameter_mm=6.35,
            cut_depth_mm=25.0,
            tab_count=4,
        )
    )
    gcode = profile.generate_gcode()
"""

from .profile_toolpath import ProfileToolpath, ProfileConfig, ProfileResult, MillingDirection
from .tabs import TabGenerator, Tab
from .intent_schema import ProfileDesignV1, ProfilePointV1, validate_profile_design
from .intent_adapter import profile_params_from_intent
from .feasibility import compute_profile_feasibility, ProfileFeasibilityResult

__all__ = [
    "ProfileToolpath",
    "ProfileConfig",
    "ProfileResult",
    "MillingDirection",
    "TabGenerator",
    "Tab",
    # Intent migration (CamIntentV1 support)
    "ProfileDesignV1",
    "ProfilePointV1",
    "validate_profile_design",
    "profile_params_from_intent",
    "compute_profile_feasibility",
    "ProfileFeasibilityResult",
]
