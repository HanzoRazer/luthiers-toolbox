# app/cam/carving/orchestrator.py

"""
3D Surface Carving Pipeline Orchestrator (BEN-GAP-08)

Coordinates roughing and finishing passes into a complete carving program.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .config import CarvingConfig, CarvingToolSpec
from .graduation_map import GraduationMap
from .surface_carving import SurfaceCarvingGenerator, CarvingResult

from app.core.safety import safety_critical


@dataclass
class CarvingPipelineResult:
    """Complete result of carving pipeline."""
    gcode_lines: List[str] = field(default_factory=list)
    config: Optional[CarvingConfig] = None
    graduation_map: Optional[GraduationMap] = None

    # Sub-operation results
    roughing: Optional[CarvingResult] = None
    semi_finish: Optional[CarvingResult] = None
    finishing: Optional[CarvingResult] = None

    # Summary
    total_cut_time_seconds: float = 0.0
    total_operations: int = 0
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "total_cut_time_seconds": round(self.total_cut_time_seconds, 1),
            "total_cut_time_minutes": round(self.total_cut_time_seconds / 60, 1),
            "total_operations": self.total_operations,
            "gcode_line_count": len(self.gcode_lines),
            "graduation_map": self.graduation_map.to_dict() if self.graduation_map else None,
            "operations": {
                "roughing": self.roughing.to_dict() if self.roughing else None,
                "semi_finish": self.semi_finish.to_dict() if self.semi_finish else None,
                "finishing": self.finishing.to_dict() if self.finishing else None,
            },
        }

    def get_gcode(self) -> str:
        """Return complete G-code as string."""
        return "\n".join(self.gcode_lines)


class CarvingPipeline:
    """
    3D Surface Carving Pipeline Orchestrator.

    Generates complete G-code program for graduated thickness carving:

    1. Roughing: Remove bulk material with large tool, leave finish allowance
    2. Semi-Finish (optional): Intermediate pass for deep surfaces
    3. Finishing: Final surface with small tool, tight stepover

    Supports:
    - Archtop guitar tops/backs (Benedetto, Gibson)
    - Les Paul carved maple tops
    - General 3D surfaces from graduation maps
    """

    def __init__(
        self,
        config: CarvingConfig,
        graduation_map: GraduationMap,
    ):
        self.config = config
        self.graduation_map = graduation_map
        self.generator = SurfaceCarvingGenerator(config, graduation_map)

        # Operation flags
        self.include_roughing = True
        self.include_semi_finish = False  # Optional intermediate pass
        self.include_finishing = True

    @safety_critical
    def generate(
        self,
        include_roughing: Optional[bool] = None,
        include_semi_finish: Optional[bool] = None,
        include_finishing: Optional[bool] = None,
    ) -> CarvingPipelineResult:
        """
        Generate complete carving program.

        Args:
            include_roughing: Override roughing flag
            include_semi_finish: Override semi-finish flag
            include_finishing: Override finishing flag

        Returns:
            CarvingPipelineResult with complete G-code
        """
        # Apply overrides
        if include_roughing is not None:
            self.include_roughing = include_roughing
        if include_semi_finish is not None:
            self.include_semi_finish = include_semi_finish
        if include_finishing is not None:
            self.include_finishing = include_finishing

        result = CarvingPipelineResult(
            config=self.config,
            graduation_map=self.graduation_map,
        )
        lines = result.gcode_lines

        # Program header
        lines.extend(self._program_header())

        # Roughing
        if self.include_roughing:
            rough_result = self.generator.generate_roughing()
            result.roughing = rough_result
            lines.extend(rough_result.gcode_lines)
            result.total_cut_time_seconds += rough_result.cut_time_seconds
            result.total_operations += 1

        # Semi-finish (optional intermediate pass)
        if self.include_semi_finish:
            # Use medium tool with medium stepover
            semi_tool = self.config.tools.get(2)  # Semi-finish tool
            if semi_tool:
                semi_result = self.generator.generate_finishing(tool=semi_tool)
                semi_result.operation_name = "OP15: Carving Semi-Finish"
                result.semi_finish = semi_result
                lines.extend(semi_result.gcode_lines)
                result.total_cut_time_seconds += semi_result.cut_time_seconds
                result.total_operations += 1

        # Finishing
        if self.include_finishing:
            finish_result = self.generator.generate_finishing()
            result.finishing = finish_result
            lines.extend(finish_result.gcode_lines)
            result.total_cut_time_seconds += finish_result.cut_time_seconds
            result.total_operations += 1

        # Program footer
        lines.extend(self._program_footer())

        return result

    def _program_header(self) -> List[str]:
        """Generate program header."""
        surface_type = self.graduation_map.config.surface_type.value.replace("_", " ").title()

        return [
            "( ============================================ )",
            "( 3D SURFACE CARVING PIPELINE )",
            "( ============================================ )",
            f"( Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC )",
            f"( Surface type: {surface_type} )",
            f"( Bounds X: {self.graduation_map.config.bounds_x_mm[0]:.1f} to {self.graduation_map.config.bounds_x_mm[1]:.1f}mm )",
            f"( Bounds Y: {self.graduation_map.config.bounds_y_mm[0]:.1f} to {self.graduation_map.config.bounds_y_mm[1]:.1f}mm )",
            f"( Apex thickness: {self.graduation_map.config.apex_thickness_mm:.2f}mm )",
            f"( Edge thickness: {self.graduation_map.config.edge_thickness_mm:.2f}mm )",
            f"( Stock thickness: {self.config.stock_thickness_mm:.2f}mm )",
            f"( Material: {self.config.material.value} )",
            "( ============================================ )",
            "",
            "G90 G94 G17",  # Absolute, feed/min, XY plane
            "G21" if self.config.output_units == "mm" else "G20",  # Units
            "G40 G49 G80",  # Cancel cutter comp, tool length, canned cycles
            "",
        ]

    def _program_footer(self) -> List[str]:
        """Generate program footer."""
        return [
            "",
            "( ============================================ )",
            "( END OF CARVING PROGRAM )",
            "( ============================================ )",
            "M5",  # Spindle off
            f"G0 Z{self.config.safe_z_mm:.3f}",  # Safe retract
            "G0 X0.000 Y0.000",  # Return to origin
            "M30",  # Program end
            "%",
        ]

    @safety_critical
    def generate_roughing_only(
        self,
        tool: Optional[CarvingToolSpec] = None,
    ) -> CarvingPipelineResult:
        """Generate only roughing passes."""
        result = CarvingPipelineResult(
            config=self.config,
            graduation_map=self.graduation_map,
        )
        lines = result.gcode_lines

        lines.extend(self._program_header())

        rough_result = self.generator.generate_roughing(tool=tool)
        result.roughing = rough_result
        lines.extend(rough_result.gcode_lines)
        result.total_cut_time_seconds = rough_result.cut_time_seconds
        result.total_operations = 1

        lines.extend(self._program_footer())

        return result

    @safety_critical
    def generate_finishing_only(
        self,
        tool: Optional[CarvingToolSpec] = None,
    ) -> CarvingPipelineResult:
        """Generate only finishing passes."""
        result = CarvingPipelineResult(
            config=self.config,
            graduation_map=self.graduation_map,
        )
        lines = result.gcode_lines

        lines.extend(self._program_header())

        finish_result = self.generator.generate_finishing(tool=tool)
        result.finishing = finish_result
        lines.extend(finish_result.gcode_lines)
        result.total_cut_time_seconds = finish_result.cut_time_seconds
        result.total_operations = 1

        lines.extend(self._program_footer())

        return result

    def preview_graduation(self) -> dict:
        """Preview graduation map properties without generating G-code."""
        return {
            "surface_type": self.graduation_map.config.surface_type.value,
            "grid_size": (
                self.graduation_map.config.grid_size_x,
                self.graduation_map.config.grid_size_y,
            ),
            "bounds_x_mm": self.graduation_map.config.bounds_x_mm,
            "bounds_y_mm": self.graduation_map.config.bounds_y_mm,
            "apex_thickness_mm": self.graduation_map.config.apex_thickness_mm,
            "edge_thickness_mm": self.graduation_map.config.edge_thickness_mm,
            "recurve_depth_mm": self.graduation_map.config.recurve_depth_mm,
            "sample_thicknesses": {
                "center": self.graduation_map.get_thickness_at(0, 0),
                "top": self.graduation_map.get_thickness_at(0, self.graduation_map.config.bounds_y_mm[1] * 0.8),
                "bottom": self.graduation_map.get_thickness_at(0, self.graduation_map.config.bounds_y_mm[0] * 0.8),
                "left": self.graduation_map.get_thickness_at(self.graduation_map.config.bounds_x_mm[0] * 0.8, 0),
                "right": self.graduation_map.get_thickness_at(self.graduation_map.config.bounds_x_mm[1] * 0.8, 0),
            },
        }

    def preview_z_levels(self) -> List[float]:
        """Preview Z levels that will be used for roughing."""
        return self.graduation_map.generate_z_levels(
            stock_thickness_mm=self.config.stock_thickness_mm,
            stepdown_mm=self.config.roughing.stepdown_mm,
            finish_allowance_mm=self.config.roughing.finish_allowance_mm,
        )
