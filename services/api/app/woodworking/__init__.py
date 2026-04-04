"""Woodworking calculators: joinery, frame-and-panel, board feet."""

# NOTE: FloatingBridgeResult, compute_break_angle_deg, compute_saddle_height_from_twelfth_action
# were removed — the file wooden_floating_bridge.py was deleted as redundant (commit 1b61f219).
# Floating bridge geometry is handled by archtop_floating_bridge.py in instrument_geometry/bridge/.

from .joinery import (
    BoxJointResult,
    BiscuitLayoutResult,
    MortiseTenonResult,
    DovetailAngleResult,
    compute_box_joint,
    compute_biscuit_layout,
    compute_mortise_tenon,
    compute_dovetail_angle_from_slope,
)
from .panels import (
    FloatingPanelGapResult,
    PanelBlankResult,
    compute_floating_panel_gaps,
    compute_panel_blank_oversize,
)
from .board_feet import (
    board_feet,
    wood_weight,
    seasonal_movement,
    movement_budget_for_species,
)

__all__ = [
    "BoxJointResult",
    "BiscuitLayoutResult",
    "MortiseTenonResult",
    "DovetailAngleResult",
    "compute_dovetail_angle_from_slope",
    "compute_box_joint",
    "compute_biscuit_layout",
    "compute_mortise_tenon",
    "FloatingPanelGapResult",
    "PanelBlankResult",
    "compute_floating_panel_gaps",
    "compute_panel_blank_oversize",
    "board_feet",
    "wood_weight",
    "seasonal_movement",
    "movement_budget_for_species",
]
