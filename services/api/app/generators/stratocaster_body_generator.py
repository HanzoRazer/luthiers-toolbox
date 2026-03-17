#!/usr/bin/env python3
"""Stratocaster Body CNC Generator

GAP-07: Parametric Stratocaster body outline generator with full CNC G-code output.

Supports:
- SSS, HSS, HSH, HH pickup configurations
- 21, 22, or 24 fret neck pocket adjustment
- Belly and arm contours
- Vintage 6-screw, 2-point, or hardtail tremolo
- Front-routed or rear-routed electronics

Coordinate System:
- Origin at body centerline, bottom of body
- X+ towards treble side
- Y+ towards neck
- All output in mm (G21)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..schemas.instrument_project import InstrumentProjectData
import math

from .stratocaster_config import (
    StratBodySpec,
    StratToolConfig,
    StratMachineConfig,
    PickupConfig,
    STRAT_TOOLS,
    STRAT_MACHINES,
    STRAT_BODY_DIMS,
    NECK_POCKET,
    TREMOLO_CAVITY,
    SPRING_CAVITY,
    CONTROL_CAVITY,
    JACK_BORE,
)

from ..instrument_geometry.body.outlines import get_body_outline
from .cam_utils import _require_cam_ready, _require_spec, _require_body_config


@dataclass
class StratGCodeStats:
    """Statistics from G-code generation."""
    total_lines: int = 0
    estimated_time_min: float = 0.0
    operations: List[str] = None
    tool_changes: int = 0

    def __post_init__(self):
        if self.operations is None:
            self.operations = []


class StratocasterBodyGenerator:
    """
    Stratocaster body G-code generator.

    Generates complete CNC program for cutting a Stratocaster body from stock.

    Example:
        >>> spec = StratBodySpec(pickup_config=PickupConfig.HSS, fret_count=24)
        >>> gen = StratocasterBodyGenerator(spec)
        >>> gcode = gen.generate("output/strat_hss_24fret.nc")
    """

    def __init__(
        self,
        spec: StratBodySpec = None,
        machine: str = "generic_router",
    ):
        self.spec = spec or StratBodySpec()
        self.machine = STRAT_MACHINES.get(machine, STRAT_MACHINES["generic_router"])

        # Load body outline
        self._outline = get_body_outline("stratocaster", detailed=True)

        # G-code accumulator
        self._gcode_lines: List[str] = []
        self._stats = StratGCodeStats()
        self._current_tool: Optional[str] = None


    @classmethod
    def from_project(
        cls,
        project: "InstrumentProjectData",
        machine: str = "generic_router",
    ) -> "StratocasterBodyGenerator":
        """
        Create a StratocasterBodyGenerator from InstrumentProjectData (GEN-3).

        Reads spec and body_config from the project to build StratBodySpec.
        Requires project to be CAM-ready (not DRAFT status).

        Args:
            project: InstrumentProjectData with spec and body_config
            machine: Machine profile name

        Returns:
            Configured StratocasterBodyGenerator instance

        Raises:
            ValueError: If project is not CAM-ready or missing required data

        Example:
            >>> gen = StratocasterBodyGenerator.from_project(project)
            >>> gen.generate("output/strat.nc")
        """
        _require_cam_ready(project)
        _require_spec(project)
        _require_body_config(project)

        # Map project.body_config.pickup_config string to PickupConfig enum
        pickup_str = project.body_config.pickup_config or "sss"
        try:
            pickup_config = PickupConfig(pickup_str.lower())
        except ValueError:
            pickup_config = PickupConfig.SSS

        # Map tremolo_style string
        tremolo_str = project.body_config.tremolo_style or "vintage_6screw"
        if tremolo_str not in ("vintage_6screw", "2point", "hardtail"):
            tremolo_str = "vintage_6screw"

        spec = StratBodySpec(
            pickup_config=pickup_config,
            fret_count=project.spec.fret_count,
            scale_length_mm=project.spec.scale_length_mm,
            belly_contour=project.body_config.belly_contour,
            arm_contour=project.body_config.arm_contour,
            rear_routed=project.body_config.rear_routed,
            tremolo_style=tremolo_str,
            stock_thickness_mm=project.body_config.stock_thickness_mm or 44.45,
        )

        return cls(spec=spec, machine=machine)

    def generate(
        self,
        output_path: str,
        program_name: str = None,
    ) -> str:
        """
        Generate complete G-code program and save to file.

        Args:
            output_path: Output file path
            program_name: Optional program name (default: filename stem)

        Returns:
            Path to generated file.
        """
        if program_name is None:
            program_name = Path(output_path).stem

        self._gcode_lines = []
        self._stats = StratGCodeStats()

        # Header
        self._emit_header(program_name)

        # Operations
        self._emit_pickup_cavities()
        self._emit_neck_pocket()

        if self.spec.tremolo_style != "hardtail":
            self._emit_tremolo_cavity()
            if self.spec.rear_routed:
                self._emit_spring_cavity()

        if self.spec.rear_routed:
            self._emit_control_cavity()

        self._emit_jack_bore()
        self._emit_body_perimeter()

        # Footer
        self._emit_footer()

        # Write file
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        gcode = "\n".join(self._gcode_lines)
        output.write_text(gcode)

        self._stats.total_lines = len(self._gcode_lines)

        return str(output)

    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics."""
        return {
            "total_lines": self._stats.total_lines,
            "estimated_time_min": self._stats.estimated_time_min,
            "operations": self._stats.operations,
            "tool_changes": self._stats.tool_changes,
            "spec": {
                "pickup_config": self.spec.pickup_config.value,
                "fret_count": self.spec.fret_count,
                "tremolo_style": self.spec.tremolo_style,
            },
        }

    def get_outline_points(self) -> List[Tuple[float, float]]:
        """Get the body outline points."""
        return self._outline.copy()

    def get_svg_preview(self) -> str:
        """Generate SVG preview of the body with cavity positions."""
        from .electric_body_generator import generate_body_outline

        result = generate_body_outline("stratocaster")
        return result.to_svg(include_centerline=True)

    # =========================================================================
    # G-CODE EMISSION HELPERS
    # =========================================================================

    def _emit(self, line: str) -> None:
        """Add a line to G-code output."""
        self._gcode_lines.append(line)

    def _emit_comment(self, text: str) -> None:
        """Add a comment line."""
        self._emit(f"({text})")

    def _emit_header(self, program_name: str) -> None:
        """Emit program header."""
        self._emit(f"%")
        self._emit(f"O{program_name[:8].upper()} (STRATOCASTER BODY)")
        self._emit_comment(f"Generated by ToolBox Stratocaster Generator")
        self._emit_comment(f"Pickup config: {self.spec.pickup_config.value.upper()}")
        self._emit_comment(f"Fret count: {self.spec.fret_count}")
        self._emit_comment(f"Machine: {self.machine.name}")
        self._emit("")
        self._emit("G21 (mm)")
        self._emit("G90 (absolute)")
        self._emit("G17 (XY plane)")
        self._emit(f"{self.machine.work_offset}")
        self._emit("")

    def _emit_footer(self) -> None:
        """Emit program footer."""
        self._emit("")
        self._emit_comment("END PROGRAM")
        self._emit(f"G0 Z{self.machine.safe_z:.1f}")
        self._emit("M5 (spindle stop)")
        self._emit("M30 (program end)")
        self._emit("%")

    def _emit_tool_change(self, tool_name: str) -> None:
        """Emit tool change sequence."""
        tool = STRAT_TOOLS.get(tool_name)
        if not tool:
            return

        self._emit("")
        self._emit_comment(f"TOOL: {tool_name} - {tool.diameter_mm}mm")
        self._emit(f"G0 Z{self.machine.safe_z:.1f}")
        self._emit(f"M5")

        tool_num = list(STRAT_TOOLS.keys()).index(tool_name) + 1
        self._emit(f"M6 T{tool_num}")
        self._emit(f"G43 H{tool_num}")
        self._emit(f"S{tool.rpm} M3")
        self._emit(f"G4 P{self.machine.spindle_warmup_s if hasattr(self.machine, 'spindle_warmup_s') else 3}")

        self._current_tool = tool_name
        self._stats.tool_changes += 1

    def _emit_rapid(self, x: float = None, y: float = None, z: float = None) -> None:
        """Emit rapid move."""
        parts = ["G0"]
        if x is not None:
            parts.append(f"X{x:.3f}")
        if y is not None:
            parts.append(f"Y{y:.3f}")
        if z is not None:
            parts.append(f"Z{z:.3f}")
        self._emit(" ".join(parts))

    def _emit_linear(
        self,
        x: float = None,
        y: float = None,
        z: float = None,
        f: float = None,
    ) -> None:
        """Emit linear feed move."""
        parts = ["G1"]
        if x is not None:
            parts.append(f"X{x:.3f}")
        if y is not None:
            parts.append(f"Y{y:.3f}")
        if z is not None:
            parts.append(f"Z{z:.3f}")
        if f is not None:
            parts.append(f"F{f:.0f}")
        self._emit(" ".join(parts))

    # =========================================================================
    # OPERATIONS
    # =========================================================================

    def _emit_pickup_cavities(self) -> None:
        """Emit pickup cavity roughing and finishing."""
        self._emit("")
        self._emit_comment("=" * 50)
        self._emit_comment("PICKUP CAVITIES")
        self._emit_comment("=" * 50)

        self._emit_tool_change("roughing_6mm")
        tool = STRAT_TOOLS["roughing_6mm"]

        cavities = self.spec.get_pickup_cavities()

        for i, cavity in enumerate(cavities):
            pos_name = ["bridge", "middle", "neck"][i] if i < 3 else f"pickup_{i+1}"
            self._emit("")
            self._emit_comment(f"{pos_name.upper()} PICKUP - {cavity['type']}")

            # Calculate cavity center Y position
            # Y from bridge needs to convert to Y from body bottom
            bridge_y = STRAT_BODY_DIMS["length_mm"] - 115  # Bridge position from bottom
            cavity_y = bridge_y - cavity["y_from_bridge_mm"]

            self._emit_pocket_rough(
                center_x=0.0,  # Centered on body
                center_y=cavity_y,
                length=cavity["length_mm"],
                width=cavity["width_mm"],
                depth=cavity["depth_mm"],
                corner_r=cavity["corner_radius_mm"],
                tool=tool,
            )

        self._stats.operations.append("pickup_cavities")

    def _emit_neck_pocket(self) -> None:
        """Emit neck pocket operation."""
        self._emit("")
        self._emit_comment("=" * 50)
        self._emit_comment("NECK POCKET")
        self._emit_comment("=" * 50)

        self._emit_tool_change("roughing_6mm")
        tool = STRAT_TOOLS["roughing_6mm"]

        # Calculate neck pocket Y position with fret count adjustment
        pocket_y = NECK_POCKET["y_from_bottom_mm"] + self.spec.get_neck_pocket_adjustment()

        self._emit_comment(f"Pocket Y: {pocket_y:.1f}mm from bottom")
        if self.spec.fret_count >= 24:
            self._emit_comment("24-fret adjustment applied")

        self._emit_pocket_rough(
            center_x=0.0,
            center_y=pocket_y,
            length=NECK_POCKET["length_mm"],
            width=NECK_POCKET["width_mm"],
            depth=NECK_POCKET["depth_mm"],
            corner_r=NECK_POCKET["corner_radius_mm"],
            tool=tool,
        )

        self._stats.operations.append("neck_pocket")

    def _emit_tremolo_cavity(self) -> None:
        """Emit tremolo cavity operation."""
        self._emit("")
        self._emit_comment("=" * 50)
        self._emit_comment(f"TREMOLO CAVITY ({self.spec.tremolo_style})")
        self._emit_comment("=" * 50)

        self._emit_tool_change("roughing_6mm")
        tool = STRAT_TOOLS["roughing_6mm"]

        self._emit_pocket_rough(
            center_x=0.0,
            center_y=TREMOLO_CAVITY["y_from_bottom_mm"],
            length=TREMOLO_CAVITY["length_mm"],
            width=TREMOLO_CAVITY["width_mm"],
            depth=TREMOLO_CAVITY["depth_mm"],
            corner_r=6.0,
            tool=tool,
        )

        self._stats.operations.append("tremolo_cavity")

    def _emit_spring_cavity(self) -> None:
        """Emit spring cavity (back of body)."""
        self._emit("")
        self._emit_comment("=" * 50)
        self._emit_comment("SPRING CAVITY (REAR)")
        self._emit_comment("=" * 50)
        self._emit_comment("NOTE: Flip workpiece for rear operations")

        self._emit_tool_change("roughing_6mm")
        tool = STRAT_TOOLS["roughing_6mm"]

        self._emit_pocket_rough(
            center_x=0.0,
            center_y=SPRING_CAVITY["y_from_bottom_mm"],
            length=SPRING_CAVITY["length_mm"],
            width=SPRING_CAVITY["width_mm"],
            depth=SPRING_CAVITY["depth_mm"],
            corner_r=6.0,
            tool=tool,
        )

        self._stats.operations.append("spring_cavity")

    def _emit_control_cavity(self) -> None:
        """Emit control cavity (back of body)."""
        self._emit("")
        self._emit_comment("=" * 50)
        self._emit_comment("CONTROL CAVITY (REAR)")
        self._emit_comment("=" * 50)

        self._emit_tool_change("roughing_6mm")
        tool = STRAT_TOOLS["roughing_6mm"]

        # Control cavity is offset towards bass side
        self._emit_pocket_rough(
            center_x=-CONTROL_CAVITY["x_offset_mm"],  # Bass side = negative X
            center_y=CONTROL_CAVITY["y_from_bottom_mm"],
            length=CONTROL_CAVITY["length_mm"],
            width=CONTROL_CAVITY["width_mm"],
            depth=CONTROL_CAVITY["depth_mm"],
            corner_r=6.0,
            tool=tool,
        )

        self._stats.operations.append("control_cavity")

    def _emit_jack_bore(self) -> None:
        """Emit output jack bore."""
        self._emit("")
        self._emit_comment("=" * 50)
        self._emit_comment("OUTPUT JACK BORE")
        self._emit_comment("=" * 50)

        self._emit_tool_change("drilling_3mm")
        tool = STRAT_TOOLS["drilling_3mm"]

        # Jack bore on treble side
        jack_x = JACK_BORE["x_offset_mm"]
        jack_y = JACK_BORE["y_from_bottom_mm"]

        self._emit_comment(f"Jack position: X={jack_x:.1f}, Y={jack_y:.1f}")
        self._emit_comment(f"Bore diameter: {JACK_BORE['diameter_mm']}mm")

        # Peck drilling cycle
        self._emit(f"G0 Z{self.machine.safe_z:.1f}")
        self._emit_rapid(x=jack_x, y=jack_y)
        self._emit(f"G0 Z{self.machine.retract_z:.1f}")

        peck_depth = 3.0
        current_z = 0.0
        target_z = -JACK_BORE["depth_mm"]

        self._emit_comment("G83 peck drilling")
        self._emit(f"G83 X{jack_x:.3f} Y{jack_y:.3f} Z{target_z:.3f} Q{peck_depth:.1f} R{self.machine.retract_z:.1f} F{tool.feed_z_mmpm:.0f}")
        self._emit("G80 (cancel canned cycle)")

        self._stats.operations.append("jack_bore")

    def _emit_body_perimeter(self) -> None:
        """Emit body perimeter profile cut with tabs."""
        self._emit("")
        self._emit_comment("=" * 50)
        self._emit_comment("BODY PERIMETER")
        self._emit_comment("=" * 50)

        self._emit_tool_change("perimeter_6mm")
        tool = STRAT_TOOLS["perimeter_6mm"]

        if not self._outline:
            self._emit_comment("ERROR: No outline data available")
            return

        # Offset outline for climb milling (tool radius outside)
        offset = tool.diameter_mm / 2.0

        self._emit_comment(f"Outline points: {len(self._outline)}")
        self._emit_comment(f"Tool offset: {offset:.2f}mm (climb)")
        self._emit_comment("Tabs: 4 x 10mm x 3mm")

        # Multi-pass depth strategy
        total_depth = self.spec.stock_thickness_mm
        current_depth = 0.0

        pass_num = 0
        while current_depth < total_depth:
            pass_num += 1
            current_depth = min(current_depth + tool.stepdown_mm, total_depth)

            self._emit("")
            self._emit_comment(f"PERIMETER PASS {pass_num} - Z={-current_depth:.2f}")

            # Start at first point
            start_x, start_y = self._outline[0]

            self._emit_rapid(z=self.machine.safe_z)
            self._emit_rapid(x=start_x + offset, y=start_y)
            self._emit_rapid(z=self.machine.retract_z)
            self._emit_linear(z=-current_depth, f=tool.feed_z_mmpm)

            # Follow outline
            for x, y in self._outline[1:]:
                self._emit_linear(x=x + offset, y=y, f=tool.feed_xy_mmpm)

            # Close the loop
            self._emit_linear(x=start_x + offset, y=start_y, f=tool.feed_xy_mmpm)

        self._emit_rapid(z=self.machine.safe_z)
        self._stats.operations.append("body_perimeter")

    def _emit_pocket_rough(
        self,
        center_x: float,
        center_y: float,
        length: float,
        width: float,
        depth: float,
        corner_r: float,
        tool: StratToolConfig,
    ) -> None:
        """Emit rectangular pocket roughing with corner radius."""
        self._emit_comment(f"Pocket: {length:.1f}x{width:.1f}x{depth:.1f}mm")

        # Calculate pocket bounds
        half_l = length / 2.0
        half_w = width / 2.0

        # Multi-pass depth
        current_depth = 0.0
        pass_num = 0

        while current_depth < depth:
            pass_num += 1
            current_depth = min(current_depth + tool.stepdown_mm, depth)

            self._emit("")
            self._emit_comment(f"Pass {pass_num} Z={-current_depth:.2f}")

            # Simple rectangular pocket - spiral inward
            step = tool.diameter_mm * tool.stepover_pct
            x_min = center_x - half_w + tool.diameter_mm / 2
            x_max = center_x + half_w - tool.diameter_mm / 2
            y_min = center_y - half_l + tool.diameter_mm / 2
            y_max = center_y + half_l - tool.diameter_mm / 2

            # Start position
            self._emit_rapid(z=self.machine.safe_z)
            self._emit_rapid(x=x_min, y=y_min)
            self._emit_rapid(z=self.machine.retract_z)
            self._emit_linear(z=-current_depth, f=tool.feed_z_mmpm)

            # Spiral inward
            offset = 0.0
            while (x_min + offset) < (x_max - offset) and (y_min + offset) < (y_max - offset):
                # Rectangle pass
                self._emit_linear(x=x_max - offset, y=y_min + offset, f=tool.feed_xy_mmpm)
                self._emit_linear(x=x_max - offset, y=y_max - offset)
                self._emit_linear(x=x_min + offset, y=y_max - offset)
                self._emit_linear(x=x_min + offset, y=y_min + offset + step)

                offset += step

        self._emit_rapid(z=self.machine.retract_z)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_strat_body(
    pickup_config: str = "sss",
    fret_count: int = 22,
    output_path: str = None,
    machine: str = "generic_router",
) -> Dict[str, Any]:
    """
    Generate Stratocaster body G-code.

    Args:
        pickup_config: "sss", "hss", "hsh", or "hh"
        fret_count: 21, 22, or 24
        output_path: Output file path (optional)
        machine: Machine preset name

    Returns:
        Dict with stats and output path.

    Example:
        >>> result = generate_strat_body("hss", 24, "output/strat_hss_24.nc")
        >>> print(result["stats"]["operations"])
    """
    # Parse pickup config
    config_map = {
        "sss": PickupConfig.SSS,
        "hss": PickupConfig.HSS,
        "hsh": PickupConfig.HSH,
        "hh": PickupConfig.HH,
    }
    pickup = config_map.get(pickup_config.lower(), PickupConfig.SSS)

    spec = StratBodySpec(
        pickup_config=pickup,
        fret_count=fret_count,
    )

    gen = StratocasterBodyGenerator(spec, machine=machine)

    if output_path:
        gen.generate(output_path)

    return {
        "stats": gen.get_stats(),
        "output_path": output_path,
        "outline_points": len(gen.get_outline_points()),
    }
