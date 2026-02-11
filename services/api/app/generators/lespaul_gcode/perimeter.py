"""Body perimeter operation mixin for Les Paul generator."""
from __future__ import annotations

import math
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..lespaul_config import MachineConfig, ToolConfig
    from ..lespaul_dxf_reader import LesPaulDXFReader


class PerimeterOperationMixin:
    """Mixin providing body perimeter cutting operation."""

    # These attributes are expected to be set by the main class
    gcode: List[str]
    reader: "LesPaulDXFReader"
    machine: "MachineConfig"
    tools: Dict[int, "ToolConfig"]
    stock_thickness: float
    stats: Dict[str, float]

    # These methods are expected from other mixins
    def _emit(self, line: str): ...
    def _tool_change(self, tool_num: int, operation: str = ""): ...
    def _rapid(self, x: float = None, y: float = None, z: float = None): ...
    def _feed(self, x: float = None, y: float = None, z: float = None, f: float = None): ...

    def generate_body_perimeter(self,
                                tool_num: int = 2,
                                tab_count: int = 6,
                                tab_width_in: float = 0.5,
                                tab_height_in: float = 0.125,
                                finish_allowance_in: float = 0.02) -> str:
        """
        Generate body perimeter cut with holding tabs.

        This is the main body outline cut (OP50 in your workflow).
        """
        if not self.reader.body_outline:
            raise ValueError("No body outline found in DXF")

        tool = self.tools[tool_num]
        path = self.reader.translate_path(self.reader.body_outline)

        # Calculate passes
        doc = tool.stepdown_in
        total_depth = self.stock_thickness
        num_passes = max(1, math.ceil(total_depth / doc))
        tab_z = -total_depth + tab_height_in

        self._emit("")
        self._emit("( ============================================ )")
        self._emit("( OP50: BODY PERIMETER CONTOUR )")
        self._emit("( ============================================ )")
        self._emit(f"( Tool: T{tool_num} {tool.name} )")
        self._emit(f"( Depth: {total_depth}\" in {num_passes} passes )")
        self._emit(f"( DOC: {doc}\" per pass )")
        self._emit(f"( Tabs: {tab_count} × {tab_width_in}\" wide × {tab_height_in}\" tall )")
        self._emit(f"( Feed: {tool.feed_ipm} IPM )")

        self._tool_change(tool_num, "Body perimeter contour")

        # Calculate tab positions along path
        perimeter = self.reader.body_outline.perimeter
        tab_spacing = perimeter / tab_count
        tab_positions = [(i + 0.5) * tab_spacing for i in range(tab_count)]

        # Start point
        start_x, start_y = path[0]

        for pass_num in range(num_passes):
            current_depth = -doc * (pass_num + 1)
            if current_depth < -total_depth:
                current_depth = -total_depth

            is_final_passes = pass_num >= num_passes - 2  # Last 2 passes get tabs

            self._emit("")
            self._emit(f"( Pass {pass_num + 1}/{num_passes}: Z = {current_depth:.4f} )")

            # Move to start
            self._rapid(z=self.machine.safe_z_in)
            self._rapid(start_x, start_y)
            self._rapid(z=self.machine.retract_z_in)

            # Ramp entry (3° ramp angle)
            ramp_distance = abs(current_depth - self.machine.retract_z_in) / math.tan(math.radians(3))
            ramp_distance = min(ramp_distance, 2.0)  # Max 2" ramp

            if len(path) > 1:
                # Ramp along first segment
                dx = path[1][0] - path[0][0]
                dy = path[1][1] - path[0][1]
                seg_len = math.sqrt(dx*dx + dy*dy)
                if seg_len > 0:
                    t = min(1.0, ramp_distance / seg_len)
                    ramp_x = start_x + dx * t
                    ramp_y = start_y + dy * t
                    self._feed(ramp_x, ramp_y, current_depth, tool.plunge_ipm)
            else:
                self._feed(z=current_depth, f=tool.plunge_ipm)

            # Cut perimeter
            self._emit(f"F{tool.feed_ipm:.1f}")

            accumulated_dist = 0.0
            tab_idx = 0
            in_tab = False

            for i in range(1, len(path)):
                px, py = path[i]
                prev_x, prev_y = path[i-1]

                seg_len = math.sqrt((px - prev_x)**2 + (py - prev_y)**2)

                # Handle tabs on final passes when below tab_z
                if is_final_passes and current_depth < tab_z and tab_idx < len(tab_positions):
                    # Check if we're entering or in a tab zone
                    while tab_idx < len(tab_positions):
                        tab_start = tab_positions[tab_idx] - tab_width_in / 2
                        tab_end = tab_positions[tab_idx] + tab_width_in / 2

                        if accumulated_dist < tab_start < accumulated_dist + seg_len:
                            # Entering tab - raise Z
                            if not in_tab:
                                self._feed(z=tab_z, f=tool.plunge_ipm)
                                in_tab = True

                        if accumulated_dist < tab_end < accumulated_dist + seg_len:
                            # Exiting tab - lower Z
                            if in_tab:
                                self._feed(z=current_depth, f=tool.plunge_ipm)
                                in_tab = False
                                tab_idx += 1
                                continue

                        break

                self._feed(px, py)
                accumulated_dist += seg_len

                # Track cutting distance
                self.stats['cut_distance'] += seg_len

            # Close the path if not already closed
            if path[0] != path[-1]:
                self._feed(path[0][0], path[0][1])

            self._rapid(z=self.machine.retract_z_in)

        # Calculate cut time
        self.stats['cut_time_min'] += self.stats['cut_distance'] / tool.feed_ipm

        return "\n".join(self.gcode)
