#!/usr/bin/env python3
"""Les Paul Body CNC Generator - The Production Shop

WP-3: Config moved to lespaul_config.py, generator to lespaul_gcode/ package.
This module retains the LesPaulBodyGenerator facade and re-exports for
backward compatibility.

B-1: Added from_project() classmethod for project-driven CAM generation.
"""

from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from ..schemas.instrument_project import InstrumentProjectData

from .lespaul_dxf_reader import ExtractedPath, LesPaulDXFReader
from .lespaul_config import ToolConfig as ToolConfig, MachineConfig as MachineConfig
from .lespaul_config import TOOLS as TOOLS, MACHINES as MACHINES
from .lespaul_gcode import LesPaulGCodeGenerator as LesPaulGCodeGenerator
from .cam_utils import _require_cam_ready, _require_spec


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

class LesPaulBodyGenerator:
    """Main interface for Les Paul body G-code generation."""

    def __init__(self, dxf_path: str, machine: str = "txrx_router"):
        self.dxf_path = Path(dxf_path)
        self.machine = MACHINES.get(machine, MACHINES["txrx_router"])

        # Load DXF
        self.reader = LesPaulDXFReader(str(self.dxf_path))
        self.reader.load()

        self.generator = None
        self.stats = {}

    @classmethod
    def from_project(
        cls,
        project: "InstrumentProjectData",
        machine: str = "txrx_router",
    ) -> "LesPaulBodyGenerator":
        """
        Create a LesPaulBodyGenerator from InstrumentProjectData (GEN-3/B-1).

        Uses the canonical LesPaul_CAM_Closed.dxf template with project dimensions.
        Requires project to be CAM-ready (not DRAFT status).

        Args:
            project: InstrumentProjectData with spec and manufacturing_state
            machine: Machine profile name (default: txrx_router)

        Returns:
            Configured LesPaulBodyGenerator instance

        Raises:
            ValueError: If project is not CAM-ready or DXF template not found

        Example:
            >>> gen = LesPaulBodyGenerator.from_project(project)
            >>> gen.generate("output/lespaul.nc")
        """
        _require_cam_ready(project)
        _require_spec(project)

        # Resolve canonical DXF path
        dxf_path = (
            Path(__file__).parent.parent
            / "instrument_geometry"
            / "body"
            / "dxf"
            / "electric"
            / "LesPaul_CAM_Closed.dxf"
        )

        if not dxf_path.exists():
            # Fallback to LesPaul_body.dxf
            alt_path = dxf_path.parent / "LesPaul_body.dxf"
            if alt_path.exists():
                dxf_path = alt_path
            else:
                raise ValueError(
                    f"Les Paul DXF template not found. "
                    f"Checked: {dxf_path} and {alt_path}"
                )

        return cls(str(dxf_path), machine=machine)

    def generate(self,
                 output_path: str,
                 stock_thickness: float = 1.75,
                 program_name: str = None) -> str:
        """Generate G-code and save to file."""
        if program_name is None:
            program_name = self.dxf_path.stem

        self.generator = LesPaulGCodeGenerator(
            reader=self.reader,
            machine=self.machine,
            stock_thickness_in=stock_thickness,
        )

        gcode = self.generator.generate_full_program(program_name)

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w") as f:
            f.write(gcode)

        self.stats = self.generator.get_stats()
        self.stats["output_path"] = str(output)
        self.stats["body_size"] = {
            "width": self.reader.body_outline.width if self.reader.body_outline else 0,
            "height": self.reader.body_outline.height if self.reader.body_outline else 0,
        }

        return str(output)

    def get_summary(self) -> Dict[str, Any]:
        """Get DXF and generation summary."""
        summary = self.reader.get_summary()
        summary["stats"] = self.stats
        return summary
