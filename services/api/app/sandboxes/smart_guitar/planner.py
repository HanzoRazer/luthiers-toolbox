"""
Smart Guitar Planner (SG-SBX-0.1)
=================================

Generates CAM plans from Smart Guitar specs.
Outputs cavities, brackets, channels, and toolpath operations.
"""

from __future__ import annotations

from typing import List

from .schemas import (
    BracketPlan,
    CavityKind,
    CavityPlan,
    ChannelKind,
    ChannelPlan,
    DEFAULT_TOOLPATHS,
    SmartCamPlan,
    SmartGuitarSpec,
    ToolpathOp,
)
from .validators import validate_spec


def generate_plan(spec: SmartGuitarSpec) -> SmartCamPlan:
    """
    Generate a CAM plan from a Smart Guitar spec.
    
    The plan includes:
    - Cavity definitions (hollow chambers, pod, etc.)
    - Bracket mounting templates for electronics
    - Wire channel routes
    - Toolpath operations with conservative defaults
    
    Args:
        spec: The Smart Guitar design specification
        
    Returns:
        SmartCamPlan with all manufacturing data
    """
    errors, warnings, spec = validate_spec(spec)

    # Generate cavity plans
    cavities: List[CavityPlan] = [
        CavityPlan(
            kind=CavityKind.bass,
            depth_in=spec.target_hollow_depth_in,
            template_id="cavity_bass_main_v1",
            notes=["Keep rim + spine constraints"],
        ),
        CavityPlan(
            kind=CavityKind.treble,
            depth_in=spec.target_hollow_depth_in,
            template_id="cavity_treble_main_v1",
            notes=["Must not overlap pod keep-out"],
        ),
        CavityPlan(
            kind=CavityKind.tail,
            depth_in=spec.target_hollow_depth_in,
            template_id="cavity_tail_wing_v1",
            notes=["Stability risk during perimeter cut; consider web bridges"],
        ),
        CavityPlan(
            kind=CavityKind.pod,
            depth_in=spec.pod_depth_in,
            template_id=f"pod_{spec.handedness.value.lower()}_v1",
            notes=["Electronics bay; service cover required"],
        ),
    ]

    # Generate bracket plans from electronics inventory
    brackets: List[BracketPlan] = []
    for c in spec.electronics:
        brackets.append(
            BracketPlan(
                component_id=c.id,
                template_id=f"bracket_{c.id}_v1",
                notes=c.notes,
            )
        )

    # Generate channel plans
    channels: List[ChannelPlan] = [
        ChannelPlan(
            kind=ChannelKind.route,
            template_id=f"wire_routes_{spec.handedness.value.lower()}_v1",
            notes=["Route audio away from power; maintain bend radius"],
        ),
        ChannelPlan(
            kind=ChannelKind.drill,
            template_id=f"drill_passages_{spec.handedness.value.lower()}_v1",
            notes=["Use brad-point; verify breakout risk"],
        ),
    ]

    # Get conservative toolpath defaults
    t2 = DEFAULT_TOOLPATHS["T2_1_4_UPCUT"]
    t3 = DEFAULT_TOOLPATHS["T3_1_8_UPCUT"]

    # Generate toolpath operations
    ops: List[ToolpathOp] = [
        ToolpathOp(
            op_id="OP10",
            title="Back: Hollow chambers rough (2D Adaptive)",
            strategy="2d_adaptive",
            tool="T2_1_4_UPCUT",
            max_stepdown_in=t2["max_stepdown_in"],
            stepover_in=t2["stepover_in"],
            depth_in=spec.target_hollow_depth_in,
            dxf_layer_ref="05_HOLLOW_MAIN_BASS / 06_HOLLOW_MAIN_TREBLE / 07_HOLLOW_TAIL",
            notes=["Verify top skin remains intact; probe Z before cut."],
        ),
        ToolpathOp(
            op_id="OP20",
            title="Back: Pod cavity rough (2D Adaptive)",
            strategy="2d_adaptive",
            tool="T2_1_4_UPCUT",
            max_stepdown_in=min(0.10, t2["max_stepdown_in"]),
            stepover_in=t2["stepover_in"],
            depth_in=spec.pod_depth_in,
            dxf_layer_ref="09_POD_CAVITY_*",
            notes=["Deep pocket: evacuate chips; check wall thickness."],
        ),
        ToolpathOp(
            op_id="OP30",
            title="Back: Wire channels (route)",
            strategy="2d_contour",
            tool="T3_1_8_UPCUT",
            max_stepdown_in=t3["max_stepdown_in"],
            stepover_in=t3["stepover_in"],
            depth_in=min(0.50, spec.target_hollow_depth_in),
            dxf_layer_ref="14_WIRE_CHANNELS_*",
            notes=["Keep away from pickup cavities; honor bend radius."],
        ),
        ToolpathOp(
            op_id="OP40",
            title="Back: Drill passages",
            strategy="drill",
            tool="T3_1_8_UPCUT",
            max_stepdown_in=t3["max_stepdown_in"],
            stepover_in=0.0,
            depth_in=min(0.75, spec.target_hollow_depth_in),
            dxf_layer_ref="15_DRILL_CHANNELS_*",
            notes=["Pilot first; confirm no breakout through top skin."],
        ),
        ToolpathOp(
            op_id="OP50",
            title="Top: Pickup cavities",
            strategy="2d_pocket",
            tool="T2_1_4_UPCUT",
            max_stepdown_in=min(0.10, t2["max_stepdown_in"]),
            stepover_in=t2["stepover_in"],
            depth_in=spec.pickup_depth_in,
            dxf_layer_ref="12_PICKUP_CAVITY_NECK / 13_PICKUP_CAVITY_BRIDGE",
            notes=["Verify hardware stack; adjust depth to pickup rings."],
        ),
    ]

    return SmartCamPlan(
        model_id=spec.model_id,
        model_variant=spec.model_variant,
        handedness=spec.handedness,
        cavities=cavities,
        brackets=brackets,
        channels=channels,
        ops=ops,
        warnings=warnings,
        errors=errors,
    )
