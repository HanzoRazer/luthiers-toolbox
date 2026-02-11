"""Drilling operations mixin for Les Paul generator."""
from __future__ import annotations

import math
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..lespaul_config import MachineConfig, ToolConfig
    from ..lespaul_dxf_reader import LesPaulDXFReader


class DrillingOperationsMixin:
    """Mixin providing drilling and boring operations."""

    # These attributes are expected to be set by the main class
    gcode: List[str]
    reader: "LesPaulDXFReader"
    machine: "MachineConfig"
    tools: Dict[int, "ToolConfig"]
    stock_thickness: float

    # These methods are expected from other mixins
    def _emit(self, line: str): ...
    def _tool_change(self, tool_num: int, operation: str = ""): ...
    def _rapid(self, x: float = None, y: float = None, z: float = None): ...

    def generate_drilling_operation(self,
                                    holes: List[Dict[str, float]],
                                    tool_num: int,
                                    depth_in: float,
                                    operation_name: str,
                                    peck_depth_in: float = 0.125) -> str:
        """Generate drilling operations using G83 peck cycle."""
        if not holes:
            return ""

        tool = self.tools[tool_num]

        self._emit("")
        self._emit(f"( ============================================ )")
        self._emit(f"( {operation_name} )")
        self._emit(f"( ============================================ )")
        self._emit(f"( Holes: {len(holes)} )")
        self._emit(f"( Depth: {depth_in}\" )")
        self._emit(f"( Peck: {peck_depth_in}\" )")

        self._tool_change(tool_num, operation_name)

        for i, hole in enumerate(holes):
            x, y = hole['x'], hole['y']
            diameter = hole.get('diameter', 0.25)

            self._emit(f"( Hole {i+1}: ({x:.3f}, {y:.3f}) Ø{diameter:.3f}\" )")

            # Move to position
            self._rapid(z=self.machine.safe_z_in)
            self._rapid(x, y)

            # Determine if we need to bore (hole > tool) or just drill
            if diameter > tool.diameter_in * 1.1:
                # Helical bore for larger holes
                bore_radius = (diameter - tool.diameter_in) / 2
                self._emit(f"( Helical bore - radius {bore_radius:.3f}\" )")
                self._rapid(z=self.machine.retract_z_in)

                # Helical descent
                z_current = 0
                while z_current > -depth_in:
                    z_current -= tool.stepdown_in
                    if z_current < -depth_in:
                        z_current = -depth_in
                    self._emit(f"G2 X{x:.4f} Y{y:.4f} I{bore_radius:.4f} J0 Z{z_current:.4f} F{tool.plunge_ipm:.1f}")

                # Final cleanup circle
                self._emit(f"G2 X{x:.4f} Y{y:.4f} I{bore_radius:.4f} J0 F{tool.feed_ipm:.1f}")
            else:
                # Standard peck drill cycle
                self._emit(f"G83 Z{-depth_in:.4f} R{self.machine.retract_z_in:.4f} Q{peck_depth_in:.4f} F{tool.plunge_ipm:.1f}")

        self._emit("G80  ; Cancel canned cycle")
        self._rapid(z=self.machine.safe_z_in)

        return "\n".join(self.gcode)

    def _extract_holes_from_layer(self, layer_name: str) -> List[Dict[str, float]]:
        """Extract hole data from arc-based polylines in a layer."""
        holes = []

        if not self.reader.doc:
            return holes

        msp = self.reader.doc.modelspace()

        for e in msp:
            if e.dxf.layer == layer_name and e.dxftype() == 'LWPOLYLINE':
                pts = list(e.get_points())
                # Arc-based circles have 2 points with bulge
                if len(pts) == 2 and pts[0][4] != 0:
                    x1, y1 = pts[0][0], pts[0][1]
                    x2, y2 = pts[1][0], pts[1][1]

                    chord = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                    diameter = chord

                    # Center and translate to work coords
                    cx = (x1 + x2) / 2 - self.reader.origin_offset[0]
                    cy = (y1 + y2) / 2 - self.reader.origin_offset[1]

                    # Only include holes within body bounds
                    if self.reader.body_outline:
                        body_w = self.reader.body_outline.width
                        body_h = self.reader.body_outline.height
                        if 0 <= cx <= body_w and 0 <= cy <= body_h:
                            holes.append({
                                'x': cx,
                                'y': cy,
                                'diameter': diameter,
                            })

        # Remove duplicates
        unique = []
        for h in holes:
            is_dup = any(
                abs(h['x'] - u['x']) < 0.01 and abs(h['y'] - u['y']) < 0.01
                for u in unique
            )
            if not is_dup:
                unique.append(h)

        return unique
