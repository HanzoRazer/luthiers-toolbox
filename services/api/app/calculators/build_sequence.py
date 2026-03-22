"""
Build Sequence Composition — CONSTRUCTION-010.

Shared state that flows through the entire guitar build sequence,
connecting individual calculators so outputs from one stage become
inputs to the next.

Pattern follows NeckPipelineConfig from app.cam.neck — a central
config object with staged result accumulation.

This module defines:
- BuildSpec: The shared state envelope with instrument parameters
- BuildResult: Accumulated outputs from all stages
- BuildStage: Protocol for individual calculation stages
- BuildSequence: Orchestrator that runs stages in order
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .string_tension import SetTensionResult
    from .bridge_calc import BridgeSpec
    from .headstock_break_angle import HeadstockBreakAngleResult
    from .setup_cascade import SetupCascadeResult
    from .finish_calc import FinishSchedule
    from .wood_movement_calc import WoodMovementSpec
    from .voicing_history_calc import VoicingReport
    from .plate_design.thickness_calculator import PlateThicknessResult, CoupledSystemResult
    from .plate_design.calibration import BodyCalibration
    from .saddle_force_calc import SaddleForceResult
    from .top_deflection_calc import DeflectionResult
    from .bracing_calc import RequiredBraceSpec


# ─── Enums ────────────────────────────────────────────────────────────────────

class InstrumentType(str, Enum):
    """Supported instrument types."""
    ACOUSTIC_STEEL = "acoustic_steel"
    ACOUSTIC_NYLON = "acoustic_nylon"
    ELECTRIC_SOLID = "electric_solid"
    ELECTRIC_HOLLOW = "electric_hollow"
    ARCHTOP = "archtop"


class BodyStyle(str, Enum):
    """Body style for dimensioning."""
    DREADNOUGHT = "dreadnought"
    OM_000 = "om_000"
    PARLOR = "parlor"
    JUMBO = "jumbo"
    CLASSICAL = "classical"
    STRATOCASTER = "stratocaster"
    TELECASTER = "telecaster"
    LES_PAUL = "les_paul"
    ES_335 = "es_335"
    ARCHTOP_17 = "archtop_17"


class NeckJointType(str, Enum):
    """Neck joint construction method."""
    DOVETAIL = "dovetail"
    BOLT_ON = "bolt_on"
    SET_NECK = "set_neck"
    NECK_THROUGH = "neck_through"


class StageStatus(str, Enum):
    """Status of a build stage."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


# ─── Build Spec ───────────────────────────────────────────────────────────────

@dataclass
class BuildSpec:
    """
    Shared state that flows through the entire build sequence.

    This is the central configuration envelope that all calculators
    can read from and contribute to.
    """
    # ─── Core Identity ───────────────────────────────────────────────────
    build_id: str = ""
    instrument_type: InstrumentType = InstrumentType.ACOUSTIC_STEEL
    body_style: BodyStyle = BodyStyle.DREADNOUGHT

    # ─── Dimensional Parameters ──────────────────────────────────────────
    scale_length_mm: float = 647.7  # 25.5"
    nut_width_mm: float = 43.0
    string_spacing_mm: float = 10.5
    string_count: int = 6
    fret_count: int = 20

    # ─── Materials ───────────────────────────────────────────────────────
    top_species: str = "sitka_spruce"
    back_species: str = "indian_rosewood"
    side_species: str = "indian_rosewood"
    neck_species: str = "mahogany"
    fretboard_species: str = "ebony"
    bridge_species: str = "ebony"

    # ─── Construction Choices ────────────────────────────────────────────
    neck_joint: NeckJointType = NeckJointType.DOVETAIL
    bracing_pattern: str = "x_brace"
    binding_style: str = "none"

    # ─── String Set ──────────────────────────────────────────────────────
    string_gauges_inches: List[float] = field(
        default_factory=lambda: [0.012, 0.016, 0.024, 0.032, 0.042, 0.054]
    )
    tuning_hz: List[float] = field(
        default_factory=lambda: [329.63, 246.94, 196.00, 146.83, 110.00, 82.41]
    )  # Standard E tuning

    # ─── Target Goals ────────────────────────────────────────────────────
    target_air_resonance_hz: float = 98.0  # G2 for dreadnought
    target_top_mode_hz: float = 185.0  # Approximate main monopole
    target_action_mm_12th: float = 2.5  # Action at 12th fret

    # ─── Environment ─────────────────────────────────────────────────────
    build_rh_pct: float = 45.0  # Relative humidity during build
    target_rh_pct: float = 45.0  # Expected usage humidity

    # ─── Finish ──────────────────────────────────────────────────────────
    finish_type: str = "nitro"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "build_id": self.build_id,
            "instrument_type": self.instrument_type.value,
            "body_style": self.body_style.value,
            "scale_length_mm": self.scale_length_mm,
            "nut_width_mm": self.nut_width_mm,
            "string_spacing_mm": self.string_spacing_mm,
            "string_count": self.string_count,
            "fret_count": self.fret_count,
            "top_species": self.top_species,
            "back_species": self.back_species,
            "side_species": self.side_species,
            "neck_species": self.neck_species,
            "fretboard_species": self.fretboard_species,
            "bridge_species": self.bridge_species,
            "neck_joint": self.neck_joint.value,
            "bracing_pattern": self.bracing_pattern,
            "binding_style": self.binding_style,
            "string_gauges_inches": self.string_gauges_inches,
            "tuning_hz": self.tuning_hz,
            "target_air_resonance_hz": self.target_air_resonance_hz,
            "target_top_mode_hz": self.target_top_mode_hz,
            "target_action_mm_12th": self.target_action_mm_12th,
            "build_rh_pct": self.build_rh_pct,
            "target_rh_pct": self.target_rh_pct,
            "finish_type": self.finish_type,
        }


# ─── Stage Results ────────────────────────────────────────────────────────────

@dataclass
class StageResult:
    """Result from a single build stage."""
    stage_name: str
    status: StageStatus
    data: Any = None  # The actual calculator result
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    gate: str = "GREEN"  # GREEN, YELLOW, RED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "status": self.status.value,
            "data": self.data.to_dict() if hasattr(self.data, 'to_dict') else self.data,
            "warnings": self.warnings,
            "errors": self.errors,
            "gate": self.gate,
        }


@dataclass
class BuildResult:
    """Accumulated results from all build stages."""
    spec: BuildSpec
    stages: Dict[str, StageResult] = field(default_factory=dict)
    overall_gate: str = "GREEN"
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # ─── Typed stage outputs (Optional until stage runs) ─────────────────
    string_tension: Optional["SetTensionResult"] = None
    bridge_geometry: Optional["BridgeSpec"] = None
    headstock_break: Optional["HeadstockBreakAngleResult"] = None
    setup_cascade: Optional["SetupCascadeResult"] = None
    finish_schedule: Optional["FinishSchedule"] = None
    wood_movement: Optional["WoodMovementSpec"] = None
    voicing: Optional["VoicingReport"] = None
    top_plate: Optional["PlateThicknessResult"] = None
    back_plate: Optional["PlateThicknessResult"] = None
    coupled_system: Optional["CoupledSystemResult"] = None
    body_calibration: Optional["BodyCalibration"] = None

    # ─── Acoustic chain outputs (ACOUSTIC-005) ────────────────────────────
    neck_angle: Optional[dict] = None
    saddle_height: Optional[dict] = None
    break_angle: Optional[dict] = None
    saddle_force: Optional["SaddleForceResult"] = None
    top_deflection: Optional["DeflectionResult"] = None
    brace_sizing: Optional["RequiredBraceSpec"] = None

    def add_stage(self, result: StageResult) -> None:
        """Add a stage result and update overall gate."""
        self.stages[result.stage_name] = result

        # Propagate warnings/errors
        self.warnings.extend(result.warnings)
        self.errors.extend(result.errors)

        # Degrade overall gate if needed
        if result.gate == "RED":
            self.overall_gate = "RED"
        elif result.gate == "YELLOW" and self.overall_gate == "GREEN":
            self.overall_gate = "YELLOW"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec": self.spec.to_dict(),
            "stages": {k: v.to_dict() for k, v in self.stages.items()},
            "overall_gate": self.overall_gate,
            "warnings": self.warnings,
            "errors": self.errors,
        }


# ─── Build Stage Protocol ─────────────────────────────────────────────────────

class BuildStage(ABC):
    """
    Abstract base for a build calculation stage.

    Each stage:
    1. Reads parameters from BuildSpec
    2. Optionally reads outputs from previous stages in BuildResult
    3. Runs its calculator
    4. Writes output to BuildResult
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stage identifier."""
        ...

    @property
    def dependencies(self) -> List[str]:
        """Names of stages that must complete before this one."""
        return []

    @abstractmethod
    def run(self, spec: BuildSpec, result: BuildResult) -> StageResult:
        """Execute this stage's calculation."""
        ...


# ─── Concrete Stages ──────────────────────────────────────────────────────────

class StringTensionStage(BuildStage):
    """Calculate string tension for the string set."""

    @property
    def name(self) -> str:
        return "string_tension"

    def run(self, spec: BuildSpec, result: BuildResult) -> StageResult:
        from .string_tension import compute_set_tension, StringSpec

        try:
            # Build StringSpec list from spec
            note_names = ["E4", "B3", "G3", "D3", "A2", "E2"][:spec.string_count]
            strings = []
            for i in range(spec.string_count):
                gauge = spec.string_gauges_inches[i]
                strings.append(StringSpec(
                    name=str(i + 1),
                    gauge_inch=gauge,
                    is_wound=(gauge >= 0.020),
                    note=note_names[i] if i < len(note_names) else f"S{i+1}",
                    frequency_hz=spec.tuning_hz[i],
                ))

            tension_result = compute_set_tension(
                strings=strings,
                scale_length_mm=spec.scale_length_mm,
            )
            result.string_tension = tension_result

            gate = "GREEN"
            warnings = []

            # Check total tension (convert N to kg: 1 kg = 9.81 N)
            total_kg = tension_result.total_tension_n / 9.81
            if total_kg > 85:
                warnings.append(f"High total tension: {total_kg:.1f}kg")
                gate = "YELLOW"

            return StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                data=tension_result,
                warnings=warnings,
                gate=gate,
            )
        except Exception as e:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                errors=[str(e)],
                gate="RED",
            )


class BridgeGeometryStage(BuildStage):
    """Calculate bridge dimensions."""

    @property
    def name(self) -> str:
        return "bridge_geometry"

    def run(self, spec: BuildSpec, result: BuildResult) -> StageResult:
        from .bridge_calc import compute_bridge_spec

        try:
            # Map body style to bridge style
            body_to_bridge = {
                BodyStyle.DREADNOUGHT: "dreadnought",
                BodyStyle.OM_000: "om_000",
                BodyStyle.PARLOR: "parlor",
                BodyStyle.JUMBO: "dreadnought",  # Similar bridge
                BodyStyle.CLASSICAL: "classical",
            }
            bridge_style = body_to_bridge.get(spec.body_style, "dreadnought")

            bridge = compute_bridge_spec(
                body_style=bridge_style,
                scale_length_mm=spec.scale_length_mm,
                string_count=spec.string_count,
                custom_spacing_mm=spec.string_spacing_mm,
            )
            result.bridge_geometry = bridge

            return StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                data=bridge,
                gate=bridge.gate if hasattr(bridge, 'gate') else "GREEN",
            )
        except Exception as e:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                errors=[str(e)],
                gate="RED",
            )


class WoodMovementStage(BuildStage):
    """Calculate expected wood movement for humidity changes."""

    @property
    def name(self) -> str:
        return "wood_movement"

    def run(self, spec: BuildSpec, result: BuildResult) -> StageResult:
        from .wood_movement_calc import compute_wood_movement

        try:
            # Calculate movement for the top plate
            # Using a typical top width of 400mm
            movement = compute_wood_movement(
                species=spec.top_species,
                dimension_mm=400.0,
                rh_from=spec.build_rh_pct,
                rh_to=spec.target_rh_pct,
            )
            result.wood_movement = movement

            warnings = []
            gate = "GREEN"

            # Check if movement is significant
            if abs(movement.movement_mm) > 2.0:
                warnings.append(
                    f"Significant wood movement: {movement.movement_mm:.2f}mm "
                    f"({movement.direction})"
                )
                gate = "YELLOW"

            return StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                data=movement,
                warnings=warnings,
                gate=gate,
            )
        except Exception as e:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                errors=[str(e)],
                gate="RED",
            )


class FinishScheduleStage(BuildStage):
    """Calculate finish schedule."""

    @property
    def name(self) -> str:
        return "finish_schedule"

    def run(self, spec: BuildSpec, result: BuildResult) -> StageResult:
        from .finish_calc import compute_finish_schedule

        try:
            schedule = compute_finish_schedule(
                finish_type=spec.finish_type,
                wood_species=spec.back_species,  # Back typically has largest pores
            )
            result.finish_schedule = schedule

            return StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                data=schedule,
                gate=schedule.gate,
                warnings=schedule.notes if schedule.notes else [],
            )
        except Exception as e:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                errors=[str(e)],
                gate="RED",
            )


# ─── Acoustic Chain Stages (ACOUSTIC-005) ────────────────────────────────────


class NeckAngleStage(BuildStage):
    """
    Calculate neck angle from spec geometry.

    Reads: spec.scale_length_mm, spec.target_action_mm_12th, geometry params
    Writes: result.neck_angle
    """

    @property
    def name(self) -> str:
        return "neck_angle"

    def run(self, spec: BuildSpec, result: BuildResult) -> StageResult:
        try:
            from app.instrument_geometry.neck.neck_angle import (
                NeckAngleInput,
                compute_neck_angle,
            )
        except ImportError:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.SKIPPED,
                warnings=["neck_angle module not available"],
                gate="YELLOW",
            )

        try:
            # Build input from spec (using typical acoustic defaults)
            inp = NeckAngleInput(
                bridge_height_mm=12.0,  # Typical bridge height
                saddle_projection_mm=3.0,  # Typical saddle projection
                fretboard_height_at_joint_mm=5.0,
                nut_to_bridge_mm=spec.scale_length_mm,
                neck_joint_fret=14,
                action_12th_mm=spec.target_action_mm_12th,
            )
            angle_result = compute_neck_angle(inp)

            result.neck_angle = {
                "angle_deg": angle_result.angle_deg,
                "gate": angle_result.gate,
                "message": angle_result.message,
            }

            return StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                data=result.neck_angle,
                gate=angle_result.gate,
                warnings=[angle_result.message] if angle_result.gate != "GREEN" else [],
            )
        except Exception as e:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                errors=[str(e)],
                gate="RED",
            )


class SaddleHeightStage(BuildStage):
    """
    Compute saddle height from neck angle and target action.

    Depends on: NeckAngleStage
    Reads: result.neck_angle, spec.target_action_mm_12th
    Writes: result.saddle_height
    """

    @property
    def name(self) -> str:
        return "saddle_height"

    @property
    def dependencies(self) -> List[str]:
        return ["neck_angle"]

    def run(self, spec: BuildSpec, result: BuildResult) -> StageResult:
        # Short-circuit if upstream is missing
        if result.neck_angle is None:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.SKIPPED,
                warnings=["Missing upstream: neck_angle"],
                gate="YELLOW",
            )

        try:
            # Derive saddle height from neck angle and action
            # Formula: saddle_height ≈ action + projection
            neck_angle_deg = result.neck_angle.get("angle_deg", 1.5)
            target_action = spec.target_action_mm_12th

            # Simple model: saddle height = target action + 0.5mm (for projection above bridge)
            saddle_height_mm = target_action + 0.5

            # Gate: 3-12mm is manufacturable
            if saddle_height_mm < 3.0:
                gate = "RED"
                warnings = [f"Saddle height {saddle_height_mm:.1f}mm too low (<3mm)"]
            elif saddle_height_mm > 12.0:
                gate = "RED"
                warnings = [f"Saddle height {saddle_height_mm:.1f}mm too high (>12mm)"]
            elif saddle_height_mm < 4.0 or saddle_height_mm > 10.0:
                gate = "YELLOW"
                warnings = [f"Saddle height {saddle_height_mm:.1f}mm marginal (ideal: 4-10mm)"]
            else:
                gate = "GREEN"
                warnings = []

            result.saddle_height = {
                "saddle_height_mm": round(saddle_height_mm, 2),
                "neck_angle_deg": neck_angle_deg,
                "gate": gate,
            }

            return StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                data=result.saddle_height,
                gate=gate,
                warnings=warnings,
            )
        except Exception as e:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                errors=[str(e)],
                gate="RED",
            )


class BreakAngleStage(BuildStage):
    """
    Compute bridge break angle from saddle height.

    Depends on: SaddleHeightStage
    Reads: result.saddle_height
    Writes: result.break_angle
    """

    @property
    def name(self) -> str:
        return "break_angle"

    @property
    def dependencies(self) -> List[str]:
        return ["saddle_height"]

    def run(self, spec: BuildSpec, result: BuildResult) -> StageResult:
        # Short-circuit if upstream is missing
        if result.saddle_height is None:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.SKIPPED,
                warnings=["Missing upstream: saddle_height"],
                gate="YELLOW",
            )

        try:
            from .bridge_break_angle import BreakAngleInput, calculate_break_angle

            saddle_height = result.saddle_height.get("saddle_height_mm", 3.0)

            inp = BreakAngleInput(
                saddle_projection_mm=saddle_height - 1.5,  # Projection above bridge
                pin_to_saddle_mm=6.0,  # Typical acoustic
            )
            break_result = calculate_break_angle(inp)

            result.break_angle = {
                "break_angle_deg": break_result.break_angle_deg,
                "gate": break_result.gate,
                "rating": break_result.rating,
            }

            return StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                data=result.break_angle,
                gate=break_result.gate,
            )
        except Exception as e:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                errors=[str(e)],
                gate="RED",
            )


class SaddleForceStage(BuildStage):
    """
    Compute saddle force from string tensions and break angles.

    Depends on: BreakAngleStage, StringTensionStage
    Reads: result.break_angle, result.string_tension
    Writes: result.saddle_force
    """

    @property
    def name(self) -> str:
        return "saddle_force"

    @property
    def dependencies(self) -> List[str]:
        return ["break_angle", "string_tension"]

    def run(self, spec: BuildSpec, result: BuildResult) -> StageResult:
        # Short-circuit if upstream is missing
        if result.break_angle is None:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.SKIPPED,
                warnings=["Missing upstream: break_angle"],
                gate="YELLOW",
            )
        if result.string_tension is None:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.SKIPPED,
                warnings=["Missing upstream: string_tension"],
                gate="YELLOW",
            )

        try:
            from .saddle_force_calc import compute_saddle_force

            # Get per-string tensions
            tensions = [s.tension_n for s in result.string_tension.strings]

            # Use same break angle for all strings (simplified)
            break_angle = result.break_angle.get("break_angle_deg", 12.0)
            break_angles = [break_angle] * len(tensions)

            force_result = compute_saddle_force(
                string_tensions_n=tensions,
                break_angles_deg=break_angles,
            )
            result.saddle_force = force_result

            return StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                data={
                    "total_vertical_force_n": force_result.total_vertical_force_n,
                    "gate": force_result.gate,
                },
                gate=force_result.gate,
                warnings=force_result.notes,
            )
        except Exception as e:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                errors=[str(e)],
                gate="RED",
            )


class TopDeflectionStage(BuildStage):
    """
    Compute top plate deflection under saddle force.

    Depends on: SaddleForceStage
    Reads: result.saddle_force, spec.top_species
    Writes: result.top_deflection
    """

    @property
    def name(self) -> str:
        return "top_deflection"

    @property
    def dependencies(self) -> List[str]:
        return ["saddle_force"]

    def run(self, spec: BuildSpec, result: BuildResult) -> StageResult:
        # Short-circuit if upstream is missing
        if result.saddle_force is None:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.SKIPPED,
                warnings=["Missing upstream: saddle_force"],
                gate="YELLOW",
            )

        try:
            from .top_deflection_calc import (
                PlateProperties,
                BraceContribution,
                compute_top_deflection,
            )

            # Default plate properties for typical spruce top
            plate = PlateProperties(
                E_L_GPa=12.0,  # Sitka spruce longitudinal
                E_C_GPa=0.8,   # Sitka spruce cross-grain
                thickness_mm=2.8,  # Typical graduated thickness
                length_mm=500.0,  # Body length
                width_mm=400.0,  # Lower bout
            )

            # Typical bracing contribution
            braces = BraceContribution(
                brace_EI_Nm2=50.0,  # Approximate for X-brace
                brace_count=2,
            )

            load = result.saddle_force.total_vertical_force_n
            deflection_result = compute_top_deflection(
                load_n=load,
                plate=plate,
                braces=braces,
            )
            result.top_deflection = deflection_result

            return StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                data={
                    "static_mm": deflection_result.static_deflection_mm,
                    "total_projected_mm": deflection_result.total_projected_mm,
                    "gate": deflection_result.gate,
                },
                gate=deflection_result.gate,
                warnings=deflection_result.notes,
            )
        except Exception as e:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                errors=[str(e)],
                gate="RED",
            )


class BraceSizingStage(BuildStage):
    """
    Check if current bracing meets deflection target.

    Depends on: TopDeflectionStage
    Reads: result.top_deflection
    Writes: result.brace_sizing
    """

    @property
    def name(self) -> str:
        return "brace_sizing"

    @property
    def dependencies(self) -> List[str]:
        return ["top_deflection"]

    def run(self, spec: BuildSpec, result: BuildResult) -> StageResult:
        # Short-circuit if upstream is missing
        if result.top_deflection is None:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.SKIPPED,
                warnings=["Missing upstream: top_deflection"],
                gate="YELLOW",
            )

        try:
            from .bracing_calc import BraceSizingTarget, solve_brace_sizing

            # Target: keep deflection under 2.0mm (GREEN threshold)
            target = BraceSizingTarget(
                max_deflection_mm=2.0,
                applied_load_n=result.saddle_force.total_vertical_force_n if result.saddle_force else 300.0,
                plate_length_mm=500.0,
                existing_plate_EI_Nm2=result.top_deflection.composite_EI_Nm2,
            )

            sizing_result = solve_brace_sizing(
                target=target,
                wood_species=spec.top_species,
                brace_width_mm=5.5,
                profile_type="parabolic",
                brace_count=2,
            )
            result.brace_sizing = sizing_result

            return StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                data={
                    "required_EI_Nm2": sizing_result.required_EI_Nm2,
                    "suggested_height_mm": sizing_result.suggested_height_mm,
                    "gate": sizing_result.gate,
                },
                gate=sizing_result.gate,
                warnings=sizing_result.notes[:2] if len(sizing_result.notes) > 2 else sizing_result.notes,
            )
        except Exception as e:
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                errors=[str(e)],
                gate="RED",
            )


# ─── Build Sequence Orchestrator ──────────────────────────────────────────────

class BuildSequence:
    """
    Orchestrator that runs build stages in order.

    Handles dependencies and propagates results between stages.
    """

    def __init__(self, stages: Optional[List[BuildStage]] = None):
        """
        Initialize with stages.

        If no stages provided, uses default acoustic guitar sequence.
        """
        if stages is None:
            stages = self.default_acoustic_stages()

        self.stages = stages

    @staticmethod
    def default_acoustic_stages() -> List[BuildStage]:
        """Default stage sequence for acoustic guitar builds (10 stages)."""
        return [
            # Original 4 stages
            StringTensionStage(),
            BridgeGeometryStage(),
            WoodMovementStage(),
            FinishScheduleStage(),
            # Acoustic chain stages (ACOUSTIC-005)
            NeckAngleStage(),
            SaddleHeightStage(),
            BreakAngleStage(),
            SaddleForceStage(),
            TopDeflectionStage(),
            BraceSizingStage(),
        ]

    def run(self, spec: BuildSpec) -> BuildResult:
        """
        Execute all stages in order.

        Args:
            spec: The build specification

        Returns:
            BuildResult with accumulated stage outputs
        """
        result = BuildResult(spec=spec)
        completed = set()

        for stage in self.stages:
            # Check dependencies
            missing = set(stage.dependencies) - completed
            if missing:
                stage_result = StageResult(
                    stage_name=stage.name,
                    status=StageStatus.SKIPPED,
                    warnings=[f"Missing dependencies: {missing}"],
                    gate="YELLOW",
                )
            else:
                stage_result = stage.run(spec, result)
                if stage_result.status == StageStatus.COMPLETED:
                    completed.add(stage.name)

            result.add_stage(stage_result)

        return result

    def validate_spec(self, spec: BuildSpec) -> List[str]:
        """
        Validate a build spec before running.

        Returns list of validation errors (empty if valid).
        """
        errors = []

        if spec.scale_length_mm <= 0:
            errors.append("Scale length must be positive")

        if spec.string_count != len(spec.string_gauges_inches):
            errors.append(
                f"String count ({spec.string_count}) doesn't match "
                f"gauge count ({len(spec.string_gauges_inches)})"
            )

        if spec.string_count != len(spec.tuning_hz):
            errors.append(
                f"String count ({spec.string_count}) doesn't match "
                f"tuning count ({len(spec.tuning_hz)})"
            )

        return errors


# ─── Factory Functions ────────────────────────────────────────────────────────

def create_dreadnought_spec(build_id: str = "") -> BuildSpec:
    """Create spec for a standard dreadnought guitar."""
    return BuildSpec(
        build_id=build_id,
        instrument_type=InstrumentType.ACOUSTIC_STEEL,
        body_style=BodyStyle.DREADNOUGHT,
        scale_length_mm=647.7,  # 25.5"
        target_air_resonance_hz=98.0,  # G2
    )


def create_om_spec(build_id: str = "") -> BuildSpec:
    """Create spec for an OM/000 guitar."""
    return BuildSpec(
        build_id=build_id,
        instrument_type=InstrumentType.ACOUSTIC_STEEL,
        body_style=BodyStyle.OM_000,
        scale_length_mm=632.46,  # 24.9"
        target_air_resonance_hz=108.0,  # Slightly higher for smaller body
        string_gauges_inches=[0.011, 0.015, 0.023, 0.030, 0.039, 0.050],
    )


def create_classical_spec(build_id: str = "") -> BuildSpec:
    """Create spec for a classical guitar."""
    return BuildSpec(
        build_id=build_id,
        instrument_type=InstrumentType.ACOUSTIC_NYLON,
        body_style=BodyStyle.CLASSICAL,
        scale_length_mm=650.0,  # 25.6"
        nut_width_mm=52.0,
        string_count=6,
        fret_count=19,
        top_species="cedar",
        back_species="indian_rosewood",
        string_gauges_inches=[0.028, 0.032, 0.040, 0.030, 0.036, 0.044],  # Nylon
        tuning_hz=[329.63, 246.94, 196.00, 146.83, 110.00, 82.41],
        target_air_resonance_hz=95.0,
        bracing_pattern="fan",
        finish_type="french_polish",
    )


def run_build_sequence(spec: BuildSpec) -> BuildResult:
    """
    Convenience function to run the default build sequence.

    Args:
        spec: The build specification

    Returns:
        BuildResult with all stage outputs
    """
    sequence = BuildSequence()
    errors = sequence.validate_spec(spec)

    if errors:
        result = BuildResult(spec=spec)
        result.errors = errors
        result.overall_gate = "RED"
        return result

    return sequence.run(spec)

def default_acoustic_stages() -> List[BuildStage]:
    """
    Returns all 10 stages for the acoustic guitar build pipeline.
    
    Stages in dependency order:
    1. StringTensionStage - Calculate string tensions
    2. BridgeGeometryStage - Calculate bridge dimensions  
    3. WoodMovementStage - Calculate expected wood movement
    4. FinishScheduleStage - Calculate finish schedule
    5. NeckAngleStage - Calculate neck angle from geometry
    6. SaddleHeightStage - Compute saddle height from neck angle
    7. BreakAngleStage - Compute break angle from saddle height
    8. SaddleForceStage - Compute saddle force from tensions and angles
    9. TopDeflectionStage - Compute top deflection under saddle force
    10. BraceSizingStage - Check if bracing meets deflection target
    """
    return [
        StringTensionStage(),
        BridgeGeometryStage(),
        WoodMovementStage(),
        FinishScheduleStage(),
        NeckAngleStage(),
        SaddleHeightStage(),
        BreakAngleStage(),
        SaddleForceStage(),
        TopDeflectionStage(),
        BraceSizingStage(),
    ]
