"""
CAM Pocketing Module

Area-clearing pocketing operations using the L.1 adaptive core.

Operations:
- Area clearing with zigzag/spiral patterns
- Island (no-cut region) handling
- Roughing and finishing passes

Usage:
    from app.cam.pocketing import (
        PocketDesignV1,
        validate_pocket_design,
        pocket_params_from_intent,
        compute_pocket_feasibility,
        PocketFeasibilityResult,
    )

    # From CamIntentV1
    adaptation = pocket_params_from_intent(intent)

    # Check feasibility
    feasibility = compute_pocket_feasibility(
        boundary=adaptation.loops[0],
        islands=adaptation.loops[1:],
        ...
    )

    # Generate toolpath via L.1
    from app.cam.adaptive_core_l1 import plan_adaptive_l1, to_toolpath
    path_pts = plan_adaptive_l1(
        loops=adaptation.loops,
        tool_d=adaptation.tool_d,
        stepover=adaptation.stepover,
        ...
    )
"""

# Schema imports (no heavy dependencies)
from .intent_schema import (
    PocketDesignV1,
    PocketIslandV1,
    PocketPointV1,
    validate_pocket_design,
)

# Adapter imports (no heavy dependencies)
from .intent_adapter import (
    PocketIntentAdaptation,
    pocket_params_from_intent,
)

# Feasibility imports (requires shapely - lazy import for environments without it)
def __getattr__(name):
    """Lazy import for feasibility module (requires shapely)."""
    if name in (
        "PocketFeasibilityResult",
        "compute_pocket_feasibility",
        "compute_pocket_area",
        "hash_feasibility_result",
    ):
        from . import feasibility
        return getattr(feasibility, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Schema
    "PocketDesignV1",
    "PocketIslandV1",
    "PocketPointV1",
    "validate_pocket_design",
    # Adapter
    "PocketIntentAdaptation",
    "pocket_params_from_intent",
    # Feasibility (lazy)
    "PocketFeasibilityResult",
    "compute_pocket_feasibility",
    "compute_pocket_area",
    "hash_feasibility_result",
]
