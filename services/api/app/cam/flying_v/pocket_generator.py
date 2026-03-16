# services/api/app/cam/flying_v/pocket_generator.py
"""
Flying V Pocket Toolpath Generator

Resolves FV-GAP-05: No pocket toolpath generator for Flying V parametric cavity placement.

Uses spec JSON (gibson_flying_v_1958.json) for all dimensions:
- Neck pocket: tenon dimensions from neck_pocket section
- Control cavity: dimensions from control_cavity section
- Pickup cavities: dimensions from pickups section

All positions are derived from body outline and bridge position.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Flying V spec JSON location
SPEC_PATH = Path(__file__).parent.parent.parent / "instrument_geometry" / "specs" / "gibson_flying_v_1958.json"


@dataclass
class CavitySpec:
    """Specification for a single cavity."""
    width_mm: float
    length_mm: float
    depth_mm: float
    center_x: float  # Relative to body centerline
    center_y: float  # Relative to bridge position (Y=0)
    notes: str = ""


@dataclass
class ToolSpec:
    """Tool specification for pocket operation."""
    diameter_mm: float
    type: str  # "upcut_spiral", "downcut_spiral", "brad_point"
    flutes: int = 2
    rpm: int = 18000
    feed_rate_mm_min: float = 2500.0
    plunge_rate_mm_min: float = 600.0
    stepdown_mm: float = 5.0
    stepover_percent: float = 60.0


@dataclass
class FlyingVSpec:
    """Complete Flying V specification loaded from JSON."""
    model_id: str
    variant: str
    body_thickness_mm: float
    scale_length_mm: float
    neck_pocket: CavitySpec
    control_cavity: CavitySpec
    neck_pickup: CavitySpec
    bridge_pickup: CavitySpec
    raw_spec: Dict[str, Any] = field(default_factory=dict)

    @property
    def body_width_mm(self) -> float:
        return self.raw_spec.get("body", {}).get("width_mm", 486.0)

    @property
    def body_length_mm(self) -> float:
        return self.raw_spec.get("body", {}).get("length_mm", 607.0)


def load_flying_v_spec(variant: str = "original_1958") -> FlyingVSpec:
    """
    Load Flying V specification from JSON.

    Args:
        variant: Variant name ("original_1958" or "reissue_2023")

    Returns:
        FlyingVSpec with all cavity dimensions loaded.

    Raises:
        FileNotFoundError: If spec JSON not found
        KeyError: If variant not found in spec
    """
    if not SPEC_PATH.exists():
        raise FileNotFoundError(f"Flying V spec not found: {SPEC_PATH}")

    with open(SPEC_PATH, "r", encoding="utf-8") as f:
        spec = json.load(f)

    # Get variant-specific data
    variants = spec.get("variants", {})
    if variant not in variants:
        raise KeyError(f"Variant '{variant}' not found. Available: {list(variants.keys())}")

    var_data = variants[variant]

    # Body data
    body = spec.get("body", {})
    body_thickness = body.get("thickness_mm", 44.45)

    # Neck pocket from spec
    neck_pocket_spec = spec.get("neck_pocket", {})
    neck_pocket = CavitySpec(
        width_mm=neck_pocket_spec.get("tenon_width_mm", 38.0),
        length_mm=neck_pocket_spec.get("tenon_length_mm", 76.0),
        depth_mm=neck_pocket_spec.get("tenon_depth_mm", 19.0),
        center_x=0.0,  # Centered on body
        # Y position: body length minus some offset (neck joins at fret 22)
        center_y=body.get("length_mm", 607.0) - 70.0,  # ~70mm from V apex
        notes=neck_pocket_spec.get("note", "Set-neck long tenon")
    )

    # Control cavity from spec
    control_spec = spec.get("control_cavity", {})
    control_cavity = CavitySpec(
        width_mm=control_spec.get("width_mm", 60.0),
        length_mm=control_spec.get("length_mm", 95.0),
        depth_mm=control_spec.get("depth_mm", 35.0),
        center_x=30.0,  # Offset from centerline into lower wing
        center_y=-80.0,  # Behind bridge (negative Y)
        notes=control_spec.get("note", "")
    )

    # Pickup cavities from spec
    pickups = spec.get("pickups", {})

    neck_pickup_spec = pickups.get("neck", {})
    neck_pickup = CavitySpec(
        width_mm=neck_pickup_spec.get("route_width_mm", 40.0),
        length_mm=neck_pickup_spec.get("route_length_mm", 71.0),
        depth_mm=neck_pickup_spec.get("route_depth_mm", 19.0),
        center_x=0.0,  # Centered
        center_y=neck_pickup_spec.get("center_from_bridge_mm", 155.0),
        notes="PAF humbucker - neck position"
    )

    bridge_pickup_spec = pickups.get("bridge", {})
    bridge_pickup = CavitySpec(
        width_mm=bridge_pickup_spec.get("route_width_mm", 40.0),
        length_mm=bridge_pickup_spec.get("route_length_mm", 71.0),
        depth_mm=bridge_pickup_spec.get("route_depth_mm", 19.0),
        center_x=0.0,  # Centered
        center_y=bridge_pickup_spec.get("center_from_bridge_mm", 20.0),
        notes="PAF humbucker - bridge position"
    )

    return FlyingVSpec(
        model_id="flying_v",
        variant=variant,
        body_thickness_mm=body_thickness,
        scale_length_mm=var_data.get("scale_length_mm", 628.65),
        neck_pocket=neck_pocket,
        control_cavity=control_cavity,
        neck_pickup=neck_pickup,
        bridge_pickup=bridge_pickup,
        raw_spec=spec,
    )


def _generate_zigzag_pocket(
    width_mm: float,
    length_mm: float,
    center_x: float,
    center_y: float,
    tool: ToolSpec,
    target_depth_mm: float,
) -> List[str]:
    """
    Generate zigzag pocket clearing toolpath.

    Returns list of G-code lines (without header/footer).
    """
    lines = []

    # Calculate pocket bounds with tool offset
    tool_r = tool.diameter_mm / 2
    stepover_mm = tool.diameter_mm * tool.stepover_percent / 100

    # Inner bounds (tool center path)
    min_x = center_x - width_mm / 2 + tool_r
    max_x = center_x + width_mm / 2 - tool_r
    min_y = center_y - length_mm / 2 + tool_r
    max_y = center_y + length_mm / 2 - tool_r

    # Calculate depth passes
    num_passes = max(1, int(target_depth_mm / tool.stepdown_mm + 0.99))
    actual_stepdown = target_depth_mm / num_passes

    # Generate passes
    for pass_num in range(1, num_passes + 1):
        z_depth = -actual_stepdown * pass_num

        lines.append(f"(--- Pass {pass_num}: Z = {z_depth:.3f} ---)")

        # Initial position
        lines.append(f"G0 X{min_x:.3f} Y{min_y:.3f}")
        lines.append(f"G1 Z{z_depth:.3f} F{tool.plunge_rate_mm_min:.1f}")

        # Zigzag pattern
        y = min_y
        direction = 1  # 1 = left to right, -1 = right to left

        while y <= max_y:
            if direction == 1:
                lines.append(f"G1 X{max_x:.3f} Y{y:.3f} F{tool.feed_rate_mm_min:.1f}")
            else:
                lines.append(f"G1 X{min_x:.3f} Y{y:.3f} F{tool.feed_rate_mm_min:.1f}")

            y += stepover_mm
            if y <= max_y:
                lines.append(f"G1 Y{y:.3f}")

            direction *= -1

        # Perimeter cleanup
        lines.append("(--- Perimeter cleanup ---)")
        lines.append(f"G1 X{min_x:.3f} Y{min_y:.3f}")
        lines.append(f"G1 X{max_x:.3f} Y{min_y:.3f}")
        lines.append(f"G1 X{max_x:.3f} Y{max_y:.3f}")
        lines.append(f"G1 X{min_x:.3f} Y{max_y:.3f}")
        lines.append(f"G1 X{min_x:.3f} Y{min_y:.3f}")

        lines.append("G0 Z5.000")

    return lines


def generate_control_cavity_toolpath(
    spec: FlyingVSpec,
    tool: Optional[ToolSpec] = None,
) -> str:
    """
    Generate G-code for control cavity pocket.

    Args:
        spec: Flying V specification
        tool: Optional tool specification (defaults to 1/4" upcut spiral)

    Returns:
        Complete G-code program as string.
    """
    if tool is None:
        tool = ToolSpec(
            diameter_mm=6.35,  # 1/4"
            type="upcut_spiral",
            rpm=18000,
            feed_rate_mm_min=2500.0,
            plunge_rate_mm_min=600.0,
            stepdown_mm=5.0,
            stepover_percent=60.0,
        )

    cavity = spec.control_cavity

    lines = [
        "(Flying V 1958 - Control Cavity Pocket)",
        f"(Cavity: {cavity.length_mm:.1f}mm x {cavity.width_mm:.1f}mm x {cavity.depth_mm:.1f}mm deep)",
        f"(Center: X={cavity.center_x:.1f}, Y={cavity.center_y:.1f})",
        f"(Tool: {tool.diameter_mm:.2f}mm {tool.type})",
        "(NOTE: Route from BACK face - flip workpiece)",
        "(Generated parametrically from gibson_flying_v_1958.json)",
        "",
        "G90",
        "G17",
        "G21",
        f"M3 S{tool.rpm}",
        "G4 P2",
        "G0 Z25.000",
        "",
    ]

    # Generate pocket
    pocket_lines = _generate_zigzag_pocket(
        width_mm=cavity.width_mm,
        length_mm=cavity.length_mm,
        center_x=cavity.center_x,
        center_y=cavity.center_y,
        tool=tool,
        target_depth_mm=cavity.depth_mm,
    )
    lines.extend(pocket_lines)

    # Footer
    lines.extend([
        "",
        "G0 Z25.000",
        "M5",
        "M30",
        "(End of control cavity program)",
    ])

    return "\n".join(lines)


def generate_neck_pocket_toolpath(
    spec: FlyingVSpec,
    roughing_tool: Optional[ToolSpec] = None,
    finishing_tool: Optional[ToolSpec] = None,
) -> str:
    """
    Generate G-code for neck pocket mortise (roughing + finishing).

    Args:
        spec: Flying V specification
        roughing_tool: Optional roughing tool (defaults to 1/2" upcut)
        finishing_tool: Optional finishing tool (defaults to 1/4" downcut)

    Returns:
        Complete G-code program as string.
    """
    if roughing_tool is None:
        roughing_tool = ToolSpec(
            diameter_mm=12.7,  # 1/2"
            type="upcut_spiral",
            rpm=16000,
            feed_rate_mm_min=3000.0,
            plunge_rate_mm_min=800.0,
            stepdown_mm=6.0,
            stepover_percent=60.0,
        )

    if finishing_tool is None:
        finishing_tool = ToolSpec(
            diameter_mm=6.35,  # 1/4"
            type="downcut_spiral",  # Critical for clean top edge
            rpm=18000,
            feed_rate_mm_min=2000.0,
            plunge_rate_mm_min=600.0,
            stepdown_mm=4.0,
            stepover_percent=50.0,
        )

    pocket = spec.neck_pocket

    lines = [
        "(Flying V 1958 - Neck Pocket Mortise)",
        f"(Mortise: {pocket.width_mm:.1f}mm x {pocket.length_mm:.1f}mm x {pocket.depth_mm:.1f}mm deep)",
        f"(Center: X={pocket.center_x:.1f}, Y={pocket.center_y:.1f})",
        f"(Roughing tool: {roughing_tool.diameter_mm:.2f}mm {roughing_tool.type})",
        f"(Finishing tool: {finishing_tool.diameter_mm:.2f}mm {finishing_tool.type})",
        f"(CRITICAL: Mortise depth = {pocket.depth_mm:.1f}mm per spec)",
        "(Generated parametrically from gibson_flying_v_1958.json)",
        "",
        "G90",
        "G17",
        "G21",
        f"M3 S{roughing_tool.rpm}",
        "G4 P2",
        "G0 Z25.000",
        "",
        "(=== ROUGHING PASS ===)",
    ]

    # Roughing pass
    rough_lines = _generate_zigzag_pocket(
        width_mm=pocket.width_mm - finishing_tool.diameter_mm,  # Leave material for finish
        length_mm=pocket.length_mm - finishing_tool.diameter_mm,
        center_x=pocket.center_x,
        center_y=pocket.center_y,
        tool=roughing_tool,
        target_depth_mm=pocket.depth_mm,
    )
    lines.extend(rough_lines)

    # Tool change
    lines.extend([
        "",
        "M5",
        "G0 Z25.000",
        f"(MSG, Change to {finishing_tool.diameter_mm:.2f}mm DOWNCUT spiral)",
        "M0",
        f"M3 S{finishing_tool.rpm}",
        "G4 P2",
        "",
        "(=== FINISHING PASS ===)",
        "(Single perimeter pass at full depth for clean walls)",
    ])

    # Finishing perimeter pass
    tool_r = finishing_tool.diameter_mm / 2
    min_x = pocket.center_x - pocket.width_mm / 2 + tool_r
    max_x = pocket.center_x + pocket.width_mm / 2 - tool_r
    min_y = pocket.center_y - pocket.length_mm / 2 + tool_r
    max_y = pocket.center_y + pocket.length_mm / 2 - tool_r

    lines.extend([
        f"G0 X{min_x:.3f} Y{min_y:.3f}",
        "G0 Z5.000",
        f"G1 Z{-pocket.depth_mm:.3f} F{finishing_tool.plunge_rate_mm_min:.1f}",
        f"G1 X{max_x:.3f} Y{min_y:.3f} F{finishing_tool.feed_rate_mm_min:.1f}",
        f"G1 X{max_x:.3f} Y{max_y:.3f}",
        f"G1 X{min_x:.3f} Y{max_y:.3f}",
        f"G1 X{min_x:.3f} Y{min_y:.3f}",
        "(--- Spring pass for dimensional accuracy ---)",
        f"G1 X{max_x:.3f} Y{min_y:.3f}",
        f"G1 X{max_x:.3f} Y{max_y:.3f}",
        f"G1 X{min_x:.3f} Y{max_y:.3f}",
        f"G1 X{min_x:.3f} Y{min_y:.3f}",
        "",
        "G0 Z25.000",
        "M5",
        "M30",
        "(End of neck pocket program)",
    ])

    return "\n".join(lines)


def generate_pickup_cavity_toolpath(
    spec: FlyingVSpec,
    pickup: str = "both",  # "neck", "bridge", or "both"
    tool: Optional[ToolSpec] = None,
) -> str:
    """
    Generate G-code for pickup cavity pocket(s).

    Args:
        spec: Flying V specification
        pickup: Which pickup ("neck", "bridge", or "both")
        tool: Optional tool specification

    Returns:
        Complete G-code program as string.
    """
    if tool is None:
        tool = ToolSpec(
            diameter_mm=6.35,  # 1/4"
            type="upcut_spiral",
            rpm=18000,
            feed_rate_mm_min=2500.0,
            plunge_rate_mm_min=600.0,
            stepdown_mm=5.0,
            stepover_percent=60.0,
        )

    cavities = []
    if pickup in ("neck", "both"):
        cavities.append(("Neck", spec.neck_pickup))
    if pickup in ("bridge", "both"):
        cavities.append(("Bridge", spec.bridge_pickup))

    lines = [
        f"(Flying V 1958 - Pickup Cavities ({pickup}))",
        f"(Tool: {tool.diameter_mm:.2f}mm {tool.type})",
        "(Generated parametrically from gibson_flying_v_1958.json)",
        "",
        "G90",
        "G17",
        "G21",
        f"M3 S{tool.rpm}",
        "G4 P2",
        "G0 Z25.000",
        "",
    ]

    for name, cavity in cavities:
        lines.append(f"(=== {name.upper()} PICKUP CAVITY ===)")
        lines.append(f"(Cavity: {cavity.length_mm:.1f}mm x {cavity.width_mm:.1f}mm x {cavity.depth_mm:.1f}mm)")
        lines.append(f"(Center: X={cavity.center_x:.1f}, Y={cavity.center_y:.1f})")
        lines.append("")

        pocket_lines = _generate_zigzag_pocket(
            width_mm=cavity.width_mm,
            length_mm=cavity.length_mm,
            center_x=cavity.center_x,
            center_y=cavity.center_y,
            tool=tool,
            target_depth_mm=cavity.depth_mm,
        )
        lines.extend(pocket_lines)
        lines.append("")

    lines.extend([
        "G0 Z25.000",
        "M5",
        "M30",
        "(End of pickup cavities program)",
    ])

    return "\n".join(lines)
