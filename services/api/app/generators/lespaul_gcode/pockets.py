"""Pocket operations mixin for Les Paul generator."""
from __future__ import annotations

import math
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..lespaul_config import MachineConfig, ToolConfig
    from ..lespaul_dxf_reader import LesPaulDXFReader


class PocketOperationsMixin:
    """Mixin providing pocket clearing operations."""

    # These attributes are expected to be set by the main class
    gcode: List[str]
    reader: "LesPaulDXFReader"
    machine: "MachineConfig"
    tools: Dict[int, "ToolConfig"]

    # These methods are expected from other mixins
    def _emit(self, line: str): ...
    def _tool_change(self, tool_num: int, operation: str = ""): ...
    def _rapid(self, x: float = None, y: float = None, z: float = None): ...
    def _feed(self, x: float = None, y: float = None, z: float = None, f: float = None): ...

    def generate_pocket(self,
                        layer: str,
                        tool_num: int,
                        depth_in: float,
                        operation_name: str) -> str:
        """Generate pocket clearing operation for a layer."""
        if layer not in self.reader.paths:
            return ""

        tool = self.tools[tool_num]
        paths = [p for p in self.reader.paths[layer] if p.is_closed]

        if not paths:
            return ""

        self._emit("")
        self._emit(f"( ============================================ )")
        self._emit(f"( {operation_name} )")
        self._emit(f"( ============================================ )")
        self._emit(f"( Layer: {layer} )")
        self._emit(f"( Paths: {len(paths)} )")
        self._emit(f"( Depth: {depth_in}\" )")

        self._tool_change(tool_num, operation_name)

        doc = tool.stepdown_in
        num_passes = max(1, math.ceil(depth_in / doc))
        stepover = tool.stepover_in

        for path in paths:
            translated = self.reader.translate_path(path)
            cx, cy = path.center
            cx -= self.reader.origin_offset[0]
            cy -= self.reader.origin_offset[1]

            self._emit(f"( Pocket at ({cx:.2f}, {cy:.2f}), {path.width:.2f}\" × {path.height:.2f}\" )")

            for pass_num in range(num_passes):
                current_depth = -doc * (pass_num + 1)
                if current_depth < -depth_in:
                    current_depth = -depth_in

                # Move to center
                self._rapid(z=self.machine.safe_z_in)
                self._rapid(cx, cy)
                self._rapid(z=self.machine.retract_z_in)

                # Helical entry
                helix_radius = tool.diameter_in / 4
                self._emit(f"( Pass {pass_num + 1}: helical entry to Z{current_depth:.4f} )")
                self._emit(f"G2 X{cx:.4f} Y{cy:.4f} I{helix_radius:.4f} J0 Z{current_depth:.4f} F{tool.plunge_ipm:.1f}")

                # Spiral outward
                self._emit(f"F{tool.feed_ipm:.1f}")

                max_offset = min(path.width, path.height) / 2 - tool.diameter_in / 2
                current_offset = stepover

                while current_offset < max_offset:
                    # Simple rectangular spiral
                    x1 = cx - current_offset
                    x2 = cx + current_offset
                    y1 = cy - current_offset
                    y2 = cy + current_offset

                    self._feed(x1, y1)
                    self._feed(x2, y1)
                    self._feed(x2, y2)
                    self._feed(x1, y2)
                    self._feed(x1, y1)

                    current_offset += stepover

                # Perimeter cleanup
                for px, py in translated:
                    self._feed(px, py)

            self._rapid(z=self.machine.retract_z_in)

        return "\n".join(self.gcode)

    def generate_cover_recess(self,
                              tool_num: int = 2,
                              depth_in: float = 0.125) -> str:
        """Generate back cover recess pocket."""
        if 'Cover Recess' not in self.reader.paths:
            return ""

        tool = self.tools[tool_num]
        # Get closed paths with reasonable dimensions (filter out arc artifacts)
        paths = [p for p in self.reader.paths['Cover Recess']
                 if p.is_closed and p.width > 1.0 and p.height > 1.0]

        if not paths:
            return ""

        # Use the largest path
        paths = sorted(paths, key=lambda p: p.perimeter, reverse=True)[:1]

        self._emit("")
        self._emit(f"( ============================================ )")
        self._emit(f"( OP25: BACK COVER RECESS )")
        self._emit(f"( ============================================ )")
        self._emit(f"( Rabbet for back cover plate )")
        self._emit(f"( Depth: {depth_in}\" )")

        self._tool_change(tool_num, "Back cover recess")

        for path in paths:
            translated = self.reader.translate_path(path)
            cx, cy = path.center
            cx -= self.reader.origin_offset[0]
            cy -= self.reader.origin_offset[1]

            self._emit(f"( Cover recess at ({cx:.2f}, {cy:.2f}), {path.width:.2f}\" × {path.height:.2f}\" )")

            # Single depth pass for shallow rabbet
            self._rapid(z=self.machine.safe_z_in)
            self._rapid(cx, cy)
            self._rapid(z=self.machine.retract_z_in)

            # Helical entry
            helix_radius = tool.diameter_in / 4
            self._emit(f"G2 X{cx:.4f} Y{cy:.4f} I{helix_radius:.4f} J0 Z{-depth_in:.4f} F{tool.plunge_ipm:.1f}")

            # Spiral out to clear pocket
            self._emit(f"F{tool.feed_ipm:.1f}")
            stepover = tool.stepover_in
            max_offset = min(path.width, path.height) / 2 - tool.diameter_in / 2
            current_offset = stepover

            while current_offset < max_offset:
                x1 = cx - current_offset
                x2 = cx + current_offset
                y1 = cy - current_offset
                y2 = cy + current_offset

                self._feed(x1, y1)
                self._feed(x2, y1)
                self._feed(x2, y2)
                self._feed(x1, y2)
                self._feed(x1, y1)

                current_offset += stepover

            # Perimeter cleanup
            for px, py in translated:
                self._feed(px, py)

            self._rapid(z=self.machine.retract_z_in)

        return "\n".join(self.gcode)
