# app/cam/neck/orchestrator.py

"""
Neck CNC Pipeline Orchestrator (LP-GAP-03)

Coordinates all neck machining operations into a single unified pipeline.
Chains: truss rod → profile rough → profile finish → fret slots.

Coordinate convention (VINE-05):
- Y=0 at nut centerline
- +Y toward bridge
- X=0 centerline

Machine context (BCamMachineSpec) flows through the pipeline:
  - safe_z_mm used in footer and all retract moves
  - tool_change_pause (M1 on BCAM 2030A) inserted between every operation
  - post_dialect controls G-code dialect via PostProcessor

Tool change sequence between operations (NEW — was missing, SAFETY FIX):
  M5 → retract to safe_z → T_ M6 → G43 H_ → S_ M3 → M1 → G4 dwell → G0 safe_z
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from .config import NeckPipelineConfig, NeckToolSpec
from .truss_rod_channel import TrussRodChannelGenerator, TrussRodResult
from .profile_carving import ProfileCarvingGenerator, ProfileCarvingResult
from .fret_slots import FretSlotGenerator, FretSlotResult

from app.cam.machines import BCamMachineSpec, BCAM_2030A
from app.cam.post_processor import (
    PostProcessor, PostConfig, ToolChangeMode, ToolSpec,
)


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

    1. OP10: Truss rod channel (T2 — 1/8" flat end mill)
    2. OP40: Profile roughing   (T1 — 1/4" ball end)
    3. OP45: Profile finishing  (T3 — larger ball end)
    4. OP50: Fret slots         (T4 — thin kerf saw)

    A PostProcessor tool change block (M5 → M6 → G43 → M3 → M1 pause → dwell)
    is emitted between every operation.  On the BCAM 2030A the pause mode is
    M1 (optional stop) — the operator changes the tool and presses cycle start.

    Each operation can be enabled/disabled independently.
    """

    def __init__(
        self,
        config: NeckPipelineConfig,
        machine: BCamMachineSpec = BCAM_2030A,
    ):
        self.config = config
        self.machine = machine

        # PostProcessor carries machine context into every tool change block.
        # ToolChangeMode.M1 = optional stop (operator changes tool, presses cycle start).
        # emit_tool_length_comp=True adds G43 H_ after each M6 so Z reference is
        # correct for every tool — critical when stickout differs between tools.
        self.post = PostProcessor(PostConfig(
            tool_change_pause=ToolChangeMode.M1,
            emit_tool_length_comp=True,
            safe_z_mm=machine.safe_z_mm,
            dwell_after_spindle_ms=machine.dwell_after_spindle_ms,
            controller=machine.post_dialect.upper(),
        ))

        # Initialize generators — propagate machine safe_z so their local
        # retract moves agree with the machine spec.
        self.truss_rod_gen = TrussRodChannelGenerator(config)
        self.profile_gen   = ProfileCarvingGenerator(config)
        self.fret_slot_gen = FretSlotGenerator(config)

        # Push machine safe_z into each generator (overrides their hardcoded 25.0mm)
        self.truss_rod_gen.safe_z_mm = machine.safe_z_mm
        self.truss_rod_gen.retract_z_mm = machine.retract_z_mm
        self.profile_gen.safe_z_mm   = machine.safe_z_mm
        self.profile_gen.retract_z_mm = machine.retract_z_mm
        self.fret_slot_gen.safe_z_mm  = machine.safe_z_mm
        self.fret_slot_gen.retract_z_mm = machine.retract_z_mm

        # Operation flags
        self.include_truss_rod    = True
        self.include_profile_rough = True
        self.include_profile_finish = True
        self.include_fret_slots   = config.include_fret_slots

    # ── Tool change helper ────────────────────────────────────────────────────

    def _tool_change_block(self, tool: NeckToolSpec) -> List[str]:
        """
        Emit a full tool change sequence via PostProcessor.

        Produces:
          ( Tool Change: T_ - name )
          M5                         spindle off
          T_ M6                      tool change
          G43 H_                     tool length compensation
          S_ M3                      spindle on at tool RPM
          M1  ( Change to name )     operator pause — BCAM has no ATC
          G4 P2000                   2s dwell for spindle ramp-up
          G0 Z10.000                 retract to machine safe Z
        """
        post_tool = ToolSpec(
            tool_number=tool.tool_number,
            name=tool.name,
            rpm=tool.rpm,
        )
        return self.post.tool_change(tool=post_tool)

    # ── Full pipeline ─────────────────────────────────────────────────────────

    def generate(
        self,
        include_truss_rod:    Optional[bool] = None,
        include_profile_rough: Optional[bool] = None,
        include_profile_finish: Optional[bool] = None,
        include_fret_slots:   Optional[bool] = None,
    ) -> NeckPipelineResult:
        """
        Generate complete neck CNC program.

        Tool change blocks with M1 operator pause are inserted between
        every enabled operation.  The footer uses machine.safe_z_mm
        (not a hardcoded value).

        Args:
            include_truss_rod: Override truss rod operation flag
            include_profile_rough: Override profile roughing flag
            include_profile_finish: Override profile finishing flag
            include_fret_slots: Override fret slots flag

        Returns:
            NeckPipelineResult with complete G-code and operation details
        """
        if include_truss_rod is not None:
            self.include_truss_rod = include_truss_rod
        if include_profile_rough is not None:
            self.include_profile_rough = include_profile_rough
        if include_profile_finish is not None:
            self.include_profile_finish = include_profile_finish
        if include_fret_slots is not None:
            self.include_fret_slots = include_fret_slots

        result = NeckPipelineResult(config=self.config)
        lines  = result.gcode_lines
        completed_ops: List[str] = []   # track which ops ran, for tool change logic

        lines.extend(self._program_header())

        # ── OP10: Truss rod channel (T2 — 1/8" flat end mill) ────────────────
        if self.include_truss_rod:
            tool = self.config.tools.get(2)
            if tool:
                lines.extend(self._tool_change_block(tool))
            tr_result = self.truss_rod_gen.generate()
            result.truss_rod = tr_result
            lines.extend(tr_result.gcode_lines)
            result.total_cut_time_seconds += tr_result.cut_time_seconds
            result.total_operations += 1
            completed_ops.append("truss_rod")

            access_lines = self.truss_rod_gen.generate_access_pocket()
            if access_lines:
                lines.extend(access_lines)

        # ── OP40: Profile roughing (T1 — 1/4" ball end) ───────────────────────
        if self.include_profile_rough:
            tool = self.config.tools.get(1)
            if tool:
                lines.extend(self._tool_change_block(tool))
            pr_result = self.profile_gen.generate_roughing()
            result.profile_rough = pr_result
            lines.extend(pr_result.gcode_lines)
            result.total_cut_time_seconds += pr_result.cut_time_seconds
            result.total_operations += 1
            completed_ops.append("profile_rough")

        # ── OP45: Profile finishing (T3 — larger ball end) ────────────────────
        if self.include_profile_finish:
            tool = self.config.tools.get(3)
            if tool:
                lines.extend(self._tool_change_block(tool))
            pf_result = self.profile_gen.generate_finishing()
            result.profile_finish = pf_result
            lines.extend(pf_result.gcode_lines)
            result.total_cut_time_seconds += pf_result.cut_time_seconds
            result.total_operations += 1
            completed_ops.append("profile_finish")

        # ── OP50: Fret slots (T4 — thin kerf saw) ─────────────────────────────
        if self.include_fret_slots:
            tool = self.config.tools.get(4)
            if tool:
                lines.extend(self._tool_change_block(tool))
            fs_result = self.fret_slot_gen.generate()
            result.fret_slots = fs_result
            lines.extend(fs_result.gcode_lines)
            result.total_cut_time_seconds += fs_result.cut_time_seconds
            result.total_operations += 1
            completed_ops.append("fret_slots")

        lines.extend(self._program_footer())
        return result

    # ── Program structure ─────────────────────────────────────────────────────

    def _program_header(self) -> List[str]:
        """Generate program header with safety block and machine annotation."""
        profile_name = self.config.profile_type.value.replace("_", " ").title()
        unit_code = "G21" if self.config.output_units == "mm" else "G20"

        return [
            "( ============================================ )",
            "( NECK CNC PIPELINE )",
            "( ============================================ )",
            f"( Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC )",
            f"( Machine: {self.machine.label} )",
            f"( Post dialect: {self.machine.post_dialect.upper()} )",
            f"( Safe Z: {self.machine.safe_z_mm:.1f}mm  Max Z: {self.machine.max_z_mm:.1f}mm )",
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
            "G90 G94 G17",   # Absolute, feed/min, XY plane
            unit_code,       # Units (G21 mm or G20 inch)
            "G40 G49 G80",   # Cancel cutter comp, tool length, canned cycles
            "",
        ]

    def _program_footer(self) -> List[str]:
        """Generate program footer.  Safe Z from machine spec — no hardcoded values."""
        return [
            "",
            "( ============================================ )",
            "( END OF PROGRAM )",
            "( ============================================ )",
            "M5",                                              # Spindle off
            f"G0 Z{self.machine.safe_z_mm:.3f}",              # Safe retract (machine spec)
            "G0 X0.000 Y0.000",                               # Return to origin
            "M30",                                            # Program end + rewind
            "%",
        ]

    # ── Single-operation generation ───────────────────────────────────────────

    def generate_operation(
        self,
        operation: str,
        tool: Optional[NeckToolSpec] = None,
    ) -> NeckPipelineResult:
        """
        Generate a single operation with its own header/footer.

        Used by the CAM workspace wizard to preview each op independently
        before assembling the full program.

        Args:
            operation: "truss_rod" | "profile_rough" | "profile_finish" | "fret_slots"
            tool: Optional tool override

        Returns:
            NeckPipelineResult with single operation G-code
        """
        result = NeckPipelineResult(config=self.config)
        lines  = result.gcode_lines

        lines.extend(self._program_header())

        if operation == "truss_rod":
            eff_tool = tool or self.config.tools.get(2)
            if eff_tool:
                lines.extend(self._tool_change_block(eff_tool))
            tr_result = self.truss_rod_gen.generate(tool=tool)
            result.truss_rod = tr_result
            lines.extend(tr_result.gcode_lines)
            result.total_cut_time_seconds = tr_result.cut_time_seconds
            result.total_operations = 1

        elif operation == "profile_rough":
            eff_tool = tool or self.config.tools.get(1)
            if eff_tool:
                lines.extend(self._tool_change_block(eff_tool))
            pr_result = self.profile_gen.generate_roughing(tool=tool)
            result.profile_rough = pr_result
            lines.extend(pr_result.gcode_lines)
            result.total_cut_time_seconds = pr_result.cut_time_seconds
            result.total_operations = 1

        elif operation == "profile_finish":
            eff_tool = tool or self.config.tools.get(3)
            if eff_tool:
                lines.extend(self._tool_change_block(eff_tool))
            pf_result = self.profile_gen.generate_finishing(tool=tool)
            result.profile_finish = pf_result
            lines.extend(pf_result.gcode_lines)
            result.total_cut_time_seconds = pf_result.cut_time_seconds
            result.total_operations = 1

        elif operation == "fret_slots":
            eff_tool = tool or self.config.tools.get(4)
            if eff_tool:
                lines.extend(self._tool_change_block(eff_tool))
            fs_result = self.fret_slot_gen.generate(tool=tool)
            result.fret_slots = fs_result
            lines.extend(fs_result.gcode_lines)
            result.total_cut_time_seconds = fs_result.cut_time_seconds
            result.total_operations = 1

        else:
            raise ValueError(
                f"Unknown operation: {operation!r}. "
                "Valid: truss_rod, profile_rough, profile_finish, fret_slots"
            )

        lines.extend(self._program_footer())
        return result

    # ── Preview helpers ───────────────────────────────────────────────────────

    def preview_stations(self) -> List[dict]:
        """Preview profile carving stations without generating G-code."""
        stations = self.profile_gen.generate_stations()
        return [s.to_dict() for s in stations]

    def preview_fret_positions(self) -> List[dict]:
        """Preview fret slot positions without generating G-code."""
        slots = self.fret_slot_gen.calculate_slot_positions()
        return [s.to_dict() for s in slots]
