"""Smart Guitar G-code Generator"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

# Local imports
from .schemas import (
    SmartGuitarSpec,
    SmartCamPlan,
    BodyDims,
    Handedness,
    ModelVariant,
    ElectronicsComponent,
    BBox3D,
    DEFAULT_TOOLPATHS,
)
from .planner import generate_plan
from .geometry_resolver import resolve_geometry, ResolvedGeometry
from .templates import SMART_GUITAR_TEMPLATES


# =============================================================================
# TOOL LIBRARY
# =============================================================================

TOOL_LIBRARY = {
    "T2_1_4_UPCUT": {
        "tool_number": 2,
        "diameter_mm": 6.35,
        "diameter_in": 0.25,
        "type": "endmill",
        "flutes": 2,
        "material": "carbide",
        "spindle_rpm": 12000,
        "feed_mmpm": 1200,  # mm/min
        "plunge_mmpm": 400,
    },
    "T2_1_4_DOWNCUT": {
        "tool_number": 2,
        "diameter_mm": 6.35,
        "diameter_in": 0.25,
        "type": "endmill",
        "flutes": 2,
        "material": "carbide",
        "spindle_rpm": 12000,
        "feed_mmpm": 1200,
        "plunge_mmpm": 400,
    },
    "T3_1_8_UPCUT": {
        "tool_number": 3,
        "diameter_mm": 3.175,
        "diameter_in": 0.125,
        "type": "endmill",
        "flutes": 2,
        "material": "carbide",
        "spindle_rpm": 18000,
        "feed_mmpm": 800,
        "plunge_mmpm": 200,
    },
}


# =============================================================================
# G-CODE EMITTER
# =============================================================================

@dataclass
class GCodeConfig:
    """G-code generation configuration."""
    safe_z: float = 10.0  # mm
    rapid_z: float = 5.0  # mm
    spindle_warmup_sec: float = 3.0
    units: str = "mm"  # mm or inch
    post_processor: str = "GRBL"  # GRBL, Mach4, LinuxCNC


class GCodeEmitter:
    """G-code emitter for Smart Guitar toolpaths."""

    def __init__(self, config: GCodeConfig = None):
        self.config = config or GCodeConfig()
        self.lines: List[str] = []
        self.current_tool: Optional[str] = None
        self.current_z: float = self.config.safe_z

    def header(self, program_name: str = "SMART_GUITAR"):
        """Emit program header."""
        now = datetime.now(timezone.utc).isoformat()
        self.lines.extend([
            f"( Program: {program_name} )",
            f"( Generated: {now} )",
            f"( Post: {self.config.post_processor} )",
            f"( Smart Guitar CAM Pipeline v1.0 )",
            "",
            "( --- SAFETY PREAMBLE --- )",
            "G90 G21" if self.config.units == "mm" else "G90 G20",  # Absolute, units
            "G17",  # XY plane
            f"G0 Z{self.config.safe_z:.3f}",  # Safe Z
            "",
        ])

    def tool_change(self, tool_id: str):
        """Emit tool change sequence."""
        if tool_id not in TOOL_LIBRARY:
            raise ValueError(f"Unknown tool: {tool_id}")

        tool = TOOL_LIBRARY[tool_id]
        self.current_tool = tool_id

        self.lines.extend([
            f"( --- TOOL CHANGE: {tool_id} --- )",
            f"G0 Z{self.config.safe_z:.3f}",
            f"M5",  # Spindle off
            f"T{tool['tool_number']} M6",  # Tool change
            f"( Tool: {tool['diameter_mm']:.2f}mm {tool['type']} )",
            f"S{tool['spindle_rpm']} M3",  # Spindle on CW
            f"G4 P{self.config.spindle_warmup_sec:.1f}",  # Dwell for spindle
            "",
        ])

    def rapid_to(self, x: float, y: float):
        """Rapid move to XY position."""
        self.lines.append(f"G0 X{x:.4f} Y{y:.4f}")

    def plunge_to(self, z: float):
        """Plunge to Z depth at plunge rate."""
        if self.current_tool:
            feed = TOOL_LIBRARY[self.current_tool]["plunge_mmpm"]
        else:
            feed = 200
        self.lines.append(f"G1 Z{z:.4f} F{feed:.0f}")
        self.current_z = z

    def cut_to(self, x: float, y: float, z: Optional[float] = None):
        """Linear cut move."""
        if self.current_tool:
            feed = TOOL_LIBRARY[self.current_tool]["feed_mmpm"]
        else:
            feed = 600

        if z is not None:
            self.lines.append(f"G1 X{x:.4f} Y{y:.4f} Z{z:.4f} F{feed:.0f}")
            self.current_z = z
        else:
            self.lines.append(f"G1 X{x:.4f} Y{y:.4f} F{feed:.0f}")

    def retract(self):
        """Retract to safe Z."""
        self.lines.append(f"G0 Z{self.config.safe_z:.3f}")
        self.current_z = self.config.safe_z

    def comment(self, text: str):
        """Add comment."""
        self.lines.append(f"( {text} )")

    def blank_line(self):
        """Add blank line."""
        self.lines.append("")

    def footer(self):
        """Emit program footer."""
        self.lines.extend([
            "",
            "( --- PROGRAM END --- )",
            f"G0 Z{self.config.safe_z:.3f}",
            "M5",  # Spindle off
            "G0 X0 Y0",  # Return to origin
            "M30",  # Program end
            "",
            "( END )",
        ])

    def get_program(self) -> str:
        """Get complete G-code program."""
        return "\n".join(self.lines)


# =============================================================================
# WP-3: Toolpath strategies extracted to toolpath_strategies.py
# =============================================================================
from .toolpath_strategies import (  # noqa: E402
    generate_pocket_spiral,
    generate_contour_path,
    generate_drill_path,
)


# =============================================================================
# MAIN G-CODE GENERATOR
# =============================================================================

def generate_smart_guitar_gcode(
    cavity_map_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    handedness: str = "RH",
) -> str:
    """Generate complete G-code from Smart Guitar cavity map."""
    # Default paths
    if cavity_map_path is None:
        # Try multiple locations
        possible_paths = [
            Path(__file__).parent.parent.parent.parent.parent.parent / "sg-spec" / "smart_guitar_cavity_map.json",
            Path("C:/Users/thepr/Downloads/sg-spec/smart_guitar_cavity_map.json"),
        ]
        for p in possible_paths:
            if p.exists():
                cavity_map_path = p
                break

    if output_path is None:
        exports_dir = Path(__file__).parent.parent.parent.parent / "exports"
        exports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = exports_dir / f"smart_guitar_{timestamp}.nc"

    # Load cavity map
    print(f"Loading cavity map: {cavity_map_path}")
    with open(cavity_map_path, "r") as f:
        cavity_map = json.load(f)

    # Create SmartGuitarSpec from cavity map
    body_dims = cavity_map.get("body_geometry", {})
    constraints = cavity_map.get("body_constraints", {})

    spec = SmartGuitarSpec(
        model_id="smart_guitar",
        model_variant=ModelVariant.headed,
        handedness=Handedness.RH if handedness == "RH" else Handedness.LH,
        body=BodyDims(
            thickness_in=body_dims.get("thickness_in", 1.75),
            rim_in=constraints.get("rim_min_in", 0.50),
            spine_w_in=constraints.get("spine_width_min_in", 1.50),
        ),
        target_hollow_depth_in=constraints.get("max_hollow_depth_in", 1.20),
        pod_depth_in=1.20,
        pickup_depth_in=0.75,
    )

    # Add electronics from cavity map
    electronics_map = cavity_map.get("electronics_components", {})
    for comp_id, comp_data in electronics_map.items():
        dims = comp_data.get("dimensions_mm", {})
        spec.electronics.append(
            ElectronicsComponent(
                id=comp_id,
                name=comp_data.get("display_name", comp_id),
                bbox=BBox3D(
                    w_mm=dims.get("width", 50),
                    d_mm=dims.get("depth", 50),
                    h_mm=dims.get("height", 20),
                ),
            )
        )

    print(f"Created spec: {spec.model_id}, handedness={spec.handedness.value}")

    # Generate CAM plan
    print("Generating CAM plan...")
    plan = generate_plan(spec)
    print(f"  Cavities: {len(plan.cavities)}")
    print(f"  Brackets: {len(plan.brackets)}")
    print(f"  Channels: {len(plan.channels)}")
    print(f"  Operations: {len(plan.ops)}")

    # Resolve geometry
    print("Resolving geometry...")
    geometry = resolve_geometry(plan)
    print(f"  Body: {geometry.body_width_mm:.1f} x {geometry.body_height_mm:.1f} mm")
    print(f"  Resolved cavities: {len(geometry.cavities)}")

    # Generate G-code
    print("Generating G-code...")
    config = GCodeConfig(
        safe_z=10.0,
        rapid_z=5.0,
        units="mm",
        post_processor="GRBL",
    )
    emitter = GCodeEmitter(config)

    # Header
    emitter.header("SMART_GUITAR_CAM")
    emitter.comment(f"Cavity Map: {cavity_map_path.name if cavity_map_path else 'default'}")
    emitter.comment(f"Handedness: {handedness}")
    emitter.comment(f"Body: {geometry.body_width_mm:.1f} x {geometry.body_height_mm:.1f} mm")
    emitter.blank_line()

    # Process each operation from the CAM plan
    for op in plan.ops:
        emitter.comment(f"=== {op.op_id}: {op.title} ===")
        emitter.comment(f"Strategy: {op.strategy}, Tool: {op.tool}")
        emitter.comment(f"Depth: {op.depth_in:.3f}in ({op.depth_in * 25.4:.2f}mm)")
        emitter.blank_line()

        # Tool change
        emitter.tool_change(op.tool)

        tool = TOOL_LIBRARY[op.tool]
        tool_dia = tool["diameter_mm"]
        stepover = op.stepover_in * 25.4  # Convert to mm
        stepdown = op.max_stepdown_in * 25.4  # Convert to mm
        depth = op.depth_in * 25.4  # Convert to mm

        # Find matching cavities/channels for this operation
        if op.op_id in ["OP10", "OP20"]:
            # Hollow chambers and pod - use pocket strategy
            for cavity in plan.cavities:
                template_id = cavity.template_id
                if template_id in geometry.cavities:
                    cavity_data = geometry.cavities[template_id]
                    if cavity_data.get("status") != "resolved":
                        emitter.comment(f"SKIP: {template_id} (not resolved)")
                        continue

                    emitter.comment(f"Cavity: {template_id} ({cavity.kind.value})")

                    points = cavity_data.get("geometry", {}).get("points", [])
                    if not points:
                        emitter.comment("WARN: No geometry points")
                        continue

                    # Generate pocket spiral toolpath
                    passes = generate_pocket_spiral(
                        points=points,
                        tool_dia=tool_dia,
                        stepover=stepover,
                        depth=depth,
                        stepdown=stepdown,
                    )

                    for pass_idx, pass_points in enumerate(passes):
                        if not pass_points:
                            continue
                        emitter.comment(f"Pass {pass_idx + 1}/{len(passes)}")

                        # Rapid to first point
                        emitter.rapid_to(pass_points[0][0], pass_points[0][1])
                        emitter.plunge_to(pass_points[0][2])

                        # Cut the pass
                        for pt in pass_points[1:]:
                            emitter.cut_to(pt[0], pt[1], pt[2])

                        emitter.retract()

        elif op.op_id == "OP30":
            # Wire channels - use contour strategy
            for channel in plan.channels:
                template_id = channel.template_id
                if template_id in geometry.cavities:
                    channel_data = geometry.cavities[template_id]
                    if channel_data.get("status") != "resolved":
                        continue

                    emitter.comment(f"Channel: {template_id} ({channel.kind.value})")

                    points = channel_data.get("geometry", {}).get("points", [])
                    if not points:
                        continue

                    passes = generate_contour_path(
                        points=points,
                        depth=depth,
                        stepdown=stepdown,
                    )

                    for pass_idx, pass_points in enumerate(passes):
                        if not pass_points:
                            continue
                        emitter.comment(f"Contour pass {pass_idx + 1}")
                        emitter.rapid_to(pass_points[0][0], pass_points[0][1])
                        emitter.plunge_to(pass_points[0][2])

                        for pt in pass_points[1:]:
                            emitter.cut_to(pt[0], pt[1], pt[2])

                        emitter.retract()

        elif op.op_id == "OP40":
            # Drill passages
            drill_data = cavity_map.get("drill_passages", {})
            passages = drill_data.get("passages", [])

            for passage in passages:
                emitter.comment(f"Drill: {passage.get('id', 'unknown')}")
                dia = passage.get("diameter_mm", 6.35)
                drill_depth = passage.get("depth_mm", depth)

                # Placeholder position - would need proper positioning logic
                x = geometry.body_width_mm / 2
                y = geometry.body_height_mm * 0.8

                drill_points = generate_drill_path(x, y, drill_depth)

                emitter.rapid_to(x, y)
                for pt in drill_points:
                    emitter.cut_to(pt[0], pt[1], pt[2])
                emitter.retract()

        elif op.op_id == "OP50":
            # Pickup cavities - pocket strategy
            emitter.comment("Pickup cavities")

            # Generate placeholder pickup positions
            center_x = geometry.body_width_mm / 2

            for pickup_name, y_offset in [("neck", -40), ("bridge", 80)]:
                emitter.comment(f"Pickup: {pickup_name}")

                # Standard humbucker dimensions
                pickup_w = 82.0
                pickup_h = 38.0

                # Create pickup rectangle points
                y = geometry.body_height_mm / 2 + y_offset
                points = [
                    (center_x - pickup_w/2, y - pickup_h/2),
                    (center_x + pickup_w/2, y - pickup_h/2),
                    (center_x + pickup_w/2, y + pickup_h/2),
                    (center_x - pickup_w/2, y + pickup_h/2),
                    (center_x - pickup_w/2, y - pickup_h/2),
                ]

                passes = generate_pocket_spiral(
                    points=points,
                    tool_dia=tool_dia,
                    stepover=stepover,
                    depth=depth,
                    stepdown=stepdown,
                )

                for pass_idx, pass_points in enumerate(passes):
                    if not pass_points:
                        continue
                    emitter.rapid_to(pass_points[0][0], pass_points[0][1])
                    emitter.plunge_to(pass_points[0][2])

                    for pt in pass_points[1:]:
                        emitter.cut_to(pt[0], pt[1], pt[2])

                    emitter.retract()

        emitter.blank_line()

    # Footer
    emitter.footer()

    # Get program
    program = emitter.get_program()

    # Write output
    print(f"Writing G-code to: {output_path}")
    with open(output_path, "w") as f:
        f.write(program)

    # Stats
    line_count = len(program.split("\n"))
    print(f"Generated {line_count} lines of G-code")

    return program


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

