"""G-code primitives mixin for Les Paul generator."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..lespaul_config import MachineConfig, ToolConfig
    from ..lespaul_dxf_reader import LesPaulDXFReader


class GCodePrimitivesMixin:
    """Mixin providing core G-code generation primitives."""

    # These attributes are expected to be set by the main class
    gcode: List[str]
    reader: "LesPaulDXFReader"
    machine: "MachineConfig"
    tools: Dict[int, "ToolConfig"]
    stock_thickness: float
    current_tool: Optional[int]
    current_z: float

    def _emit(self, line: str):
        """Add line to G-code output."""
        self.gcode.append(line)

    def _header(self, program_name: str):
        """Generate program header."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        self._emit(f"; {program_name}")
        self._emit(f"; Generated: {now}")
        self._emit(f"; Generator: Luthier's ToolBox - Les Paul Body Generator")
        self._emit(f"; Machine: {self.machine.name}")
        self._emit(f"; Stock: {self.stock_thickness}\" thick")
        self._emit(";")

        if self.reader.body_outline:
            self._emit(f"; Body size: {self.reader.body_outline.width:.2f}\" × {self.reader.body_outline.height:.2f}\"")
            self._emit(f"; Perimeter: {self.reader.body_outline.perimeter:.1f}\"")

        self._emit(";")
        self._emit("")
        self._emit("( SAFE START )")
        self._emit("G20         ; Inches")
        self._emit("G17         ; XY plane")
        self._emit("G90         ; Absolute")
        self._emit("G94         ; Feed per minute")
        self._emit("G54         ; Work offset")
        self._emit(f"G0 Z{self.machine.safe_z_in:.4f}")
        self._emit("")

    def _footer(self):
        """Generate program footer."""
        self._emit("")
        self._emit("( PROGRAM END )")
        self._emit("M5          ; Spindle off")
        self._emit(f"G0 Z{self.machine.safe_z_in:.4f}")
        self._emit("G0 X0 Y0    ; Return home")
        self._emit("M30         ; End program")

    def _tool_change(self, tool_num: int, operation: str = ""):
        """Generate tool change sequence."""
        if self.current_tool == tool_num:
            return

        tool = self.tools[tool_num]

        if self.current_tool is not None:
            self._emit("M5")

        self._emit("")
        self._emit(f"( TOOL CHANGE: T{tool_num} - {tool.name} )")
        if operation:
            self._emit(f"( {operation} )")
        self._emit(f"T{tool_num} M6")
        self._emit(f"S{tool.rpm} M3")
        self._emit("G4 P2       ; Dwell for spindle")
        self._emit(f"G0 Z{self.machine.safe_z_in:.4f}")

        self.current_tool = tool_num

    def _rapid(self, x: float = None, y: float = None, z: float = None):
        """Rapid move."""
        parts = ["G0"]
        if x is not None:
            parts.append(f"X{x:.4f}")
        if y is not None:
            parts.append(f"Y{y:.4f}")
        if z is not None:
            parts.append(f"Z{z:.4f}")
            self.current_z = z
        self._emit(" ".join(parts))

    def _feed(self, x: float = None, y: float = None, z: float = None, f: float = None):
        """Feed move."""
        parts = ["G1"]
        if x is not None:
            parts.append(f"X{x:.4f}")
        if y is not None:
            parts.append(f"Y{y:.4f}")
        if z is not None:
            parts.append(f"Z{z:.4f}")
            self.current_z = z
        if f is not None:
            parts.append(f"F{f:.1f}")
        self._emit(" ".join(parts))
