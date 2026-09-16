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

from ..instrument_geometry.dxf_authority import require_manufacturing_authority
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
        """Prepare G-code generation from a DXF template.

        This is the manufacturing choke point for every entry path (the
        BodyGenerator factory, from_project(), and direct construction): a
        governed catalog asset must hold positive manufacturing authority
        before its geometry is read. Raises ManufacturingAuthorityBlocked
        (a ValueError, so the CAM routers' 422 mapping covers it) when it does
        not. DXFs outside the catalog keep their existing contract - the export
        gate's preflight and topology checks - and are not judged here.
        """
        self.dxf_path = Path(dxf_path)
        self.authority = require_manufacturing_authority(self.dxf_path)
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
            ValueError: If project is not CAM-ready, the DXF template is missing,
                or the template lacks manufacturing authority

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

        # No fallback: substituting a different asset for a missing manufacturing
        # template hides the real failure and would machine geometry nobody asked
        # for (owner ruling 2026-09-16).
        if not dxf_path.exists():
            raise ValueError(
                f"Les Paul manufacturing template is unavailable: {dxf_path.name} is not in the catalog"
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
