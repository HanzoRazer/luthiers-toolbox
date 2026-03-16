# app/cam/neck/orchestrator.py

"""
Neck CNC Pipeline Orchestrator (LP-GAP-03)

Coordinates all neck machining operations into a single unified pipeline.
Chains: truss rod → profile rough → profile finish → fret slots.

Coordinate convention (VINE-05):
- Y=0 at nut centerline
- +Y toward bridge
- X=0 centerline
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from .config import NeckPipelineConfig, NeckToolSpec
from .truss_rod_channel import TrussRodChannelGenerator, TrussRodResult
from .profile_carving import ProfileCarvingGenerator, ProfileCarvingResult
from .fret_slots import FretSlotGenerator, FretSlotResult


@dataclass
class NeckPipelineResult:
    """Complete result of neck CNC pipeline."""
    gcode_lines: List[str] = field(default_factory=list)
    config: Optional[NeckPipelineConfig] = None

    # Sub-operation results
    truss_rod: Optional[TrussRodResult] = None
    profile_rough: Optional[ProfileCarvingResult] = None
    profile_finish: Optional[ProfileCarvingResult] = None
    fret_slots: Optional[FretSlotResult] = None

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
            "config": self.config.to_dict() if self.config else None,
            "operations": {
                "truss_rod": self.truss_rod.to_dict() if self.truss_rod else None,
                "profile_rough": self.profile_rough.to_dict() if self.profile_rough else None,
                "profile_finish": self.profile_finish.to_dict() if self.profile_finish else None,
                "fret_slots": self.fret_slots.to_dict() if self.fret_slots else None,
            },
        }

    def get_gcode(self) -> str:
        """Return complete G-code as string."""
        return "\n".join(self.gcode_lines)


class NeckPipeline:
    """
    Neck CNC pipeline orchestrator.

    Generates complete G-code program for neck machining by chaining
    individual operations in the correct sequence:

    1. OP10: Truss rod channel (clears channel before profile carving)
    2. OP40: Profile roughing (removes bulk material)
    3. OP45: Profile finishing (final surface)
    4. OP50: Fret slots (cut after fretboard surface is finished)

    Each operation can be enabled/disabled independently.
    """

    def __init__(self, config: NeckPipelineConfig):
        self.config = config

        # Initialize generators
        self.truss_rod_gen = TrussRodChannelGenerator(config)
        self.profile_gen = ProfileCarvingGenerator(config)
        self.fret_slot_gen = FretSlotGenerator(config)

        # Operation flags
        self.include_truss_rod = True
        self.include_profile_rough = True
        self.include_profile_finish = True
        self.include_fret_slots = config.include_fret_slots

    def generate(
        self,
        include_truss_rod: Optional[bool] = None,
        include_profile_rough: Optional[bool] = None,
        include_profile_finish: Optional[bool] = None,
        include_fret_slots: Optional[bool] = None,
    ) -> NeckPipelineResult:
        """
        Generate complete neck CNC program.

        Args:
            include_truss_rod: Override truss rod operation flag
            include_profile_rough: Override profile roughing flag
            include_profile_finish: Override profile finishing flag
            include_fret_slots: Override fret slots flag

        Returns:
            NeckPipelineResult with complete G-code and operation details
        """
        # Apply overrides
        if include_truss_rod is not None:
            self.include_truss_rod = include_truss_rod
        if include_profile_rough is not None:
            self.include_profile_rough = include_profile_rough
        if include_profile_finish is not None:
            self.include_profile_finish = include_profile_finish
        if include_fret_slots is not None:
            self.include_fret_slots = include_fret_slots

        result = NeckPipelineResult(config=self.config)
        lines = result.gcode_lines

        # Program header
        lines.extend(self._program_header())

        # OP10: Truss rod channel
        if self.include_truss_rod:
            tr_result = self.truss_rod_gen.generate()
            result.truss_rod = tr_result
            lines.extend(tr_result.gcode_lines)
            result.total_cut_time_seconds += tr_result.cut_time_seconds
            result.total_operations += 1

            # Add access pocket if configured
            access_lines = self.truss_rod_gen.generate_access_pocket()
            if access_lines:
                lines.extend(access_lines)

        # OP40: Profile roughing
        if self.include_profile_rough:
            pr_result = self.profile_gen.generate_roughing()
            result.profile_rough = pr_result
            lines.extend(pr_result.gcode_lines)
            result.total_cut_time_seconds += pr_result.cut_time_seconds
            result.total_operations += 1

        # OP45: Profile finishing
        if self.include_profile_finish:
            pf_result = self.profile_gen.generate_finishing()
            result.profile_finish = pf_result
            lines.extend(pf_result.gcode_lines)
            result.total_cut_time_seconds += pf_result.cut_time_seconds
            result.total_operations += 1

        # OP50: Fret slots
        if self.include_fret_slots:
            fs_result = self.fret_slot_gen.generate()
            result.fret_slots = fs_result
            lines.extend(fs_result.gcode_lines)
            result.total_cut_time_seconds += fs_result.cut_time_seconds
            result.total_operations += 1

        # Program footer
        lines.extend(self._program_footer())

        return result

    def _program_header(self) -> List[str]:
        """Generate program header with setup commands."""
        profile_name = self.config.profile_type.value.replace("_", " ").title()

        return [
            "( ============================================ )",
            "( NECK CNC PIPELINE )",
            "( ============================================ )",
            f"( Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC )",
            f"( Scale length: {self.config.scale_length_mm:.2f}mm ({self.config.scale_length_mm / 25.4:.3f}in) )",
            f"( Fret count: {self.config.fret_count} )",
            f"( Profile: {profile_name} )",
            f"( Material: {self.config.material.value} )",
            "( )",
            "( Coordinate system (VINE-05): )",
            "( Y=0 at nut centerline )",
            "( +Y toward bridge )",
            "( X=0 centerline )",
            "( ============================================ )",
            "",
            "G90 G94 G17",  # Absolute, feed/min, XY plane
            f"G21" if self.config.output_units == "mm" else "G20",  # Units
            "G40 G49 G80",  # Cancel cutter comp, tool length, canned cycles
            "",
        ]

    def _program_footer(self) -> List[str]:
        """Generate program footer with cleanup commands."""
        return [
            "",
            "( ============================================ )",
            "( END OF PROGRAM )",
            "( ============================================ )",
            "M5",  # Spindle off
            "G0 Z50.000",  # Safe retract
            "G0 X0.000 Y0.000",  # Return to origin
            "M30",  # Program end
            "%",
        ]

    def generate_operation(
        self,
        operation: str,
        tool: Optional[NeckToolSpec] = None,
    ) -> NeckPipelineResult:
        """
        Generate a single operation.

        Args:
            operation: One of "truss_rod", "profile_rough", "profile_finish", "fret_slots"
            tool: Optional tool override

        Returns:
            NeckPipelineResult with single operation G-code
        """
        result = NeckPipelineResult(config=self.config)
        lines = result.gcode_lines

        lines.extend(self._program_header())

        if operation == "truss_rod":
            tr_result = self.truss_rod_gen.generate(tool=tool)
            result.truss_rod = tr_result
            lines.extend(tr_result.gcode_lines)
            result.total_cut_time_seconds = tr_result.cut_time_seconds
            result.total_operations = 1

        elif operation == "profile_rough":
            pr_result = self.profile_gen.generate_roughing(tool=tool)
            result.profile_rough = pr_result
            lines.extend(pr_result.gcode_lines)
            result.total_cut_time_seconds = pr_result.cut_time_seconds
            result.total_operations = 1

        elif operation == "profile_finish":
            pf_result = self.profile_gen.generate_finishing(tool=tool)
            result.profile_finish = pf_result
            lines.extend(pf_result.gcode_lines)
            result.total_cut_time_seconds = pf_result.cut_time_seconds
            result.total_operations = 1

        elif operation == "fret_slots":
            fs_result = self.fret_slot_gen.generate(tool=tool)
            result.fret_slots = fs_result
            lines.extend(fs_result.gcode_lines)
            result.total_cut_time_seconds = fs_result.cut_time_seconds
            result.total_operations = 1

        else:
            raise ValueError(f"Unknown operation: {operation}. "
                           f"Valid: truss_rod, profile_rough, profile_finish, fret_slots")

        lines.extend(self._program_footer())

        return result

    def preview_stations(self) -> List[dict]:
        """Preview profile carving stations without generating G-code."""
        stations = self.profile_gen.generate_stations()
        return [s.to_dict() for s in stations]

    def preview_fret_positions(self) -> List[dict]:
        """Preview fret slot positions without generating G-code."""
        slots = self.fret_slot_gen.calculate_slot_positions()
        return [s.to_dict() for s in slots]
