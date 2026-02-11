"""Main Les Paul G-code generator class."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .primitives import GCodePrimitivesMixin
from .perimeter import PerimeterOperationMixin
from .pockets import PocketOperationsMixin
from .drilling import DrillingOperationsMixin

from ..lespaul_dxf_reader import LesPaulDXFReader
from ..lespaul_config import ToolConfig, MachineConfig


class LesPaulGCodeGenerator(
    GCodePrimitivesMixin,
    PerimeterOperationMixin,
    PocketOperationsMixin,
    DrillingOperationsMixin,
):
    """Generate production G-code for Les Paul body cutting."""

    def __init__(self,
                 reader: LesPaulDXFReader,
                 machine: MachineConfig = None,
                 tools: Dict[int, ToolConfig] = None,
                 stock_thickness_in: float = 1.75):
        from ..lespaul_config import MACHINES, TOOLS

        self.reader = reader
        self.machine = machine or MACHINES['txrx_router']
        self.tools = tools or TOOLS
        self.stock_thickness = stock_thickness_in

        self.gcode: List[str] = []
        self.current_tool: Optional[int] = None
        self.current_z: float = self.machine.safe_z_in
        self.stats = {
            'rapid_distance': 0.0,
            'cut_distance': 0.0,
            'cut_time_min': 0.0,
        }

    def generate_full_program(self, program_name: str = "LesPaul_Body") -> str:
        """Generate complete CNC program for Les Paul body."""
        self.gcode = []

        self._header(program_name)

        # OP20: Pocket rough - T1 (10mm)
        self.generate_pocket("Neck Mortise", 1, 0.75, "OP20: Neck Pocket Rough")
        self.generate_pocket("Pickup Cavity", 1, 0.75, "OP21: Pickup Cavity Rough")
        self.generate_pocket("Electronic Cavities", 1, 1.25, "OP22: Electronics Cavity Rough")

        # OP25: Cover recess (back) - T2 (6mm)
        self.generate_cover_recess(tool_num=2, depth_in=0.125)

        # OP30: Pocket finish - T2 (6mm)
        self.generate_pocket("Neck Mortise", 2, 0.75, "OP30: Neck Pocket Finish")
        self.generate_pocket("Pickup Cavity", 2, 0.75, "OP31: Pickup Cavity Finish")

        # OP40: Channels - T3 (3mm)
        self.generate_pocket("Wiring Channel", 3, 0.5, "OP40: Wiring Channel")

        # OP50: Perimeter
        self.generate_body_perimeter(tool_num=2, tab_count=6)

        # OP60: Drilling operations - T3 (3mm drill)
        # Extract holes from DXF layers
        pot_holes = self._extract_holes_from_layer('Pot Holes')
        if pot_holes:
            self.generate_drilling_operation(
                pot_holes, 3, self.stock_thickness,
                "OP60: Pot Shaft Holes (3/8\" through)"
            )

        studs = self._extract_holes_from_layer('Studs')
        if studs:
            # Bridge studs are deeper, tailpiece studs shallower
            bridge_studs = [h for h in studs if h['diameter'] > 0.4]
            tailpiece_studs = [h for h in studs if h['diameter'] <= 0.4]

            if bridge_studs:
                self.generate_drilling_operation(
                    bridge_studs, 3, 0.75,
                    "OP61: Bridge Post Holes (7/16\")"
                )
            if tailpiece_studs:
                self.generate_drilling_operation(
                    tailpiece_studs, 3, 0.625,
                    "OP62: Tailpiece Stud Holes (9/32\")"
                )

        screw_holes = self._extract_holes_from_layer('Screws')
        if screw_holes:
            self.generate_drilling_operation(
                screw_holes, 3, 0.5,
                "OP63: Screw Pilot Holes (#8)"
            )

        self._footer()

        return "\n".join(self.gcode)

    def save(self, filepath: str):
        """Save G-code to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.gcode))
        return filepath

    def get_stats(self) -> Dict[str, Any]:
        """Get cutting statistics."""
        return {
            'cut_distance_in': round(self.stats['cut_distance'], 2),
            'estimated_time_min': round(self.stats['cut_time_min'], 1),
            'gcode_lines': len(self.gcode),
        }
