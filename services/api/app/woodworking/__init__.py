"""Woodworking calculators: floating bridge setup, joinery, frame-and-panel."""

from .wooden_floating_bridge import (
    FloatingBridgeResult,
    compute_break_angle_deg,
    compute_saddle_height_from_twelfth_action,
)
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
from .archtop_floating_bridge import (
    BENEDETTO_17,
    ArchtopFloatingBridgeReport,
    Benedetto17Defaults,
    build_archtop_bridge_report,
    compute_foot_arch_geometry,
    compute_post_hole_positions,
    compute_saddle_slot,
    generate_dxf,
    resolve_arch_radius_from_sagitta,
)

__all__ = [
    "FloatingBridgeResult",
    "compute_break_angle_deg",
    "compute_saddle_height_from_twelfth_action",
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
    "BENEDETTO_17",
    "Benedetto17Defaults",
    "ArchtopFloatingBridgeReport",
    "resolve_arch_radius_from_sagitta",
    "compute_foot_arch_geometry",
    "compute_post_hole_positions",
    "compute_saddle_slot",
    "generate_dxf",
    "build_archtop_bridge_report",
]
