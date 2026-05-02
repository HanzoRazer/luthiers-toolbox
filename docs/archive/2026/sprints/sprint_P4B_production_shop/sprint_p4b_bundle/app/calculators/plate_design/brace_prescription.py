"""
app/calculators/plate_design/brace_prescription.py

Translates InverseSolverResult into physical brace dimensions for the workshop.

Takes the inverse solver's output (a target thickness and achieved modal
frequencies) plus the plate's material properties and produces a BracePrescription:
a set of brace geometries with manufacturability constraints enforced.

INSTRUMENT CLASS: DECISION SUPPORT
This module produces advisory output (brace geometry recommendations).
It does not appear in viewer_pack_v1 and is not subject to provenance tracking.
See docs/ADR-0009-advisory-boundary.md

Usage:
    from app.calculators.plate_design.brace_prescription import (
        prescribe_bracing, BracePrescription, BraceSpec
    )
    from app.calculators.plate_design.inverse_solver import InverseSolverResult
    from app.analyzer.viewer_pack_bridge import PlateInputs

    prescription = prescribe_bracing(inputs, solver_result, style="x_brace")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Brace style definitions
# ---------------------------------------------------------------------------

class BraceStyle(str, Enum):
    X_BRACE    = "x_brace"      # Steel-string standard
    FAN_BRACE  = "fan_brace"    # Classical / flamenco
    LADDER     = "ladder"       # Archtop / some parlour
    MODIFIED_X = "modified_x"  # X + two tone bars


# Soundhole radius clearance — braces must not cross soundhole (mm from centre)
_SOUNDHOLE_RADIUS_MM = 52.0


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class BraceSpec:
    """
    Physical specification for a single brace.

    All dimensions in mm. Height is the peak (crown) dimension.
    Scallop depth applies to the scalloped area between bridge plate
    and upper bout — 0 = flat bottom (no scalloping).
    """
    label: str                   # e.g. "bass_X_leg", "treble_X_leg", "cross_brace_1"
    style: BraceStyle
    width_mm: float              # Brace cross-section width
    height_mm: float             # Brace crown height (at centre)
    length_mm: float             # Total brace length
    scallop_depth_mm: float = 0.0  # Scallop depth at ends
    position_from_centre_mm: float = 0.0  # Distance from plate centreline
    notes: str = ""

    @property
    def aspect_ratio(self) -> float:
        """Height / width — controls bending stiffness contribution."""
        return self.height_mm / self.width_mm if self.width_mm > 0 else 0.0

    @property
    def bending_stiffness_contribution(self) -> float:
        """
        EI proxy for the brace itself (ignoring glue surface).
        Proportional to width × height³ — the actual EI requires the
        brace material's E, which is not stored here.
        """
        return self.width_mm * (self.height_mm ** 3) / 12.0


@dataclass
class BracePrescription:
    """
    Full bracing prescription for a single plate.

    Produced by prescribe_bracing() from an InverseSolverResult and PlateInputs.
    """

    style: BraceStyle
    braces: List[BraceSpec] = field(default_factory=list)

    # Material context (from PlateInputs)
    plate_species: str = ""
    plate_E_L_GPa: float = 0.0
    plate_E_C_GPa: float = 0.0
    plate_thickness_mm: float = 0.0

    # Solver outcomes
    target_frequencies_Hz: List[float] = field(default_factory=list)
    achieved_frequencies_Hz: List[float] = field(default_factory=list)
    rms_error_Hz: float = 0.0
    converged: bool = False

    # Manufacturability
    manufacturability_warnings: List[str] = field(default_factory=list)
    manufacturability_score: int = 100  # 0–100; deductions for each warning

    # Provenance
    source_session: str = ""
    bending_measured: bool = False
    notes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Brace prescription — {self.style.value}",
            f"  Plate: {self.plate_species}, "
            f"E_L={self.plate_E_L_GPa:.1f} GPa, "
            f"h={self.plate_thickness_mm:.2f} mm",
            f"  Solver: {'converged' if self.converged else 'DID NOT CONVERGE'}, "
            f"RMS error={self.rms_error_Hz:.1f} Hz",
            f"  Manufacturability: {self.manufacturability_score}/100",
            "",
            "Braces:",
        ]
        for b in self.braces:
            lines.append(
                f"  {b.label}: {b.width_mm:.1f}W × {b.height_mm:.1f}H × "
                f"{b.length_mm:.0f}L mm"
                + (f"  (scallop {b.scallop_depth_mm:.1f}mm)" if b.scallop_depth_mm else "")
            )
        if self.manufacturability_warnings:
            lines.append("\nWarnings:")
            for w in self.manufacturability_warnings:
                lines.append(f"  ⚠ {w}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Manufacturability rules
# ---------------------------------------------------------------------------

# Router bit diameter constraint — brace width cannot be less than this
_MIN_BRACE_WIDTH_MM = 4.0        # 1/8" bit = 3.175 mm; use 4 mm for safety
_MAX_BRACE_HEIGHT_MM = 14.0      # Maximum practical brace height
_MIN_BRACE_HEIGHT_MM = 2.5       # Below this, brace has negligible stiffness


def _check_manufacturability(
    braces: List[BraceSpec],
    plate_length_mm: float,
    plate_width_mm: float,
) -> Tuple[List[str], int]:
    """Return (warnings, score). Score starts at 100, loses points per warning."""
    warnings: List[str] = []
    score = 100

    for b in braces:
        if b.width_mm < _MIN_BRACE_WIDTH_MM:
            warnings.append(
                f"{b.label}: width {b.width_mm:.1f} mm < minimum {_MIN_BRACE_WIDTH_MM} mm "
                f"(router bit constraint). Increase to {_MIN_BRACE_WIDTH_MM} mm."
            )
            score -= 15

        if b.height_mm > _MAX_BRACE_HEIGHT_MM:
            warnings.append(
                f"{b.label}: height {b.height_mm:.1f} mm exceeds maximum {_MAX_BRACE_HEIGHT_MM} mm. "
                f"Reduce or split into two braces."
            )
            score -= 10

        if b.height_mm < _MIN_BRACE_HEIGHT_MM:
            warnings.append(
                f"{b.label}: height {b.height_mm:.1f} mm is too low to contribute "
                f"meaningful stiffness. Increase to at least {_MIN_BRACE_HEIGHT_MM} mm."
            )
            score -= 10

        if b.length_mm > plate_length_mm:
            warnings.append(
                f"{b.label}: length {b.length_mm:.0f} mm exceeds plate length "
                f"{plate_length_mm:.0f} mm."
            )
            score -= 20

    return warnings, max(0, score)


# ---------------------------------------------------------------------------
# Brace geometry calculators
# ---------------------------------------------------------------------------

def _x_brace_specs(
    plate_length_mm: float,
    plate_width_mm: float,
    target_h_mm: float,
    E_L: float,
) -> List[BraceSpec]:
    """
    Generate X-brace geometry scaled to the plate's target stiffness.

    The height of the X-brace legs is scaled from the inverse solver's
    target plate thickness using a simple proportionality based on the
    plate's E_L. Heavier bracing compensates for softer wood.
    """
    # Base dimensions from Martin-style reference (dreadnought, Sitka at 10.5 GPa)
    _ref_E_L = 10.5
    _ref_height = 9.5
    _ref_width  = 5.5

    # Scale height inversely with E_L — softer wood needs taller braces
    scale = (_ref_E_L / E_L) ** 0.5
    height = round(max(_MIN_BRACE_HEIGHT_MM, min(_ref_height * scale, _MAX_BRACE_HEIGHT_MM)), 1)
    width  = round(max(_MIN_BRACE_WIDTH_MM, _ref_width * (scale ** 0.3)), 1)

    # Scallop depth: ~25% of height
    scallop = round(height * 0.25, 1)

    # X-brace leg length spans from near soundhole to waist area
    leg_length = round(plate_length_mm * 0.55, 0)

    return [
        BraceSpec("bass_X_leg",    BraceStyle.X_BRACE, width, height,
                  leg_length, scallop, -plate_width_mm * 0.05,
                  "Primary bass-side X leg"),
        BraceSpec("treble_X_leg",  BraceStyle.X_BRACE, width, height,
                  leg_length, scallop,  plate_width_mm * 0.05,
                  "Primary treble-side X leg"),
        BraceSpec("upper_cross",   BraceStyle.X_BRACE, round(max(_MIN_BRACE_WIDTH_MM, width * 0.7), 1),
                  round(height * 0.55, 1), round(plate_width_mm * 0.7, 0),
                  round(scallop * 0.5, 1), -plate_length_mm * 0.2,
                  "Upper transverse brace"),
        BraceSpec("lower_cross",   BraceStyle.X_BRACE, round(max(_MIN_BRACE_WIDTH_MM, width * 0.7), 1),
                  round(height * 0.45, 1), round(plate_width_mm * 0.65, 0),
                  round(scallop * 0.5, 1),  plate_length_mm * 0.2,
                  "Lower transverse brace"),
    ]


def _fan_brace_specs(
    plate_length_mm: float,
    plate_width_mm: float,
    target_h_mm: float,
    E_L: float,
) -> List[BraceSpec]:
    """
    Generate classical fan-brace geometry.

    5-fan pattern: 3 longitudinal fan struts + 2 harmonic bars.
    Heights scaled for typical cedar/spruce classical tops.
    """
    scale = (10.5 / E_L) ** 0.4
    h_centre = round(max(2.5, min(7.0 * scale, 10.0)), 1)
    h_outer  = round(h_centre * 0.75, 1)
    w        = round(max(_MIN_BRACE_WIDTH_MM, 4.5 * (scale ** 0.2)), 1)
    fan_len  = round(plate_length_mm * 0.45, 0)
    bar_len  = round(plate_width_mm * 0.75, 0)

    return [
        BraceSpec("fan_centre",       BraceStyle.FAN_BRACE, w, h_centre, fan_len,
                  0, 0, "Centre longitudinal fan strut"),
        BraceSpec("fan_bass_inner",   BraceStyle.FAN_BRACE, w, round(h_centre * 0.9, 1),
                  round(fan_len * 0.95, 0), 0, -plate_width_mm * 0.08),
        BraceSpec("fan_treble_inner", BraceStyle.FAN_BRACE, w, round(h_centre * 0.9, 1),
                  round(fan_len * 0.95, 0), 0,  plate_width_mm * 0.08),
        BraceSpec("harmonic_bar_1",   BraceStyle.FAN_BRACE, round(w * 0.85, 1), h_outer,
                  bar_len, 0, -plate_length_mm * 0.05, "Upper harmonic bar"),
        BraceSpec("harmonic_bar_2",   BraceStyle.FAN_BRACE, round(w * 0.85, 1), h_outer,
                  bar_len, 0,  plate_length_mm * 0.18, "Lower harmonic bar"),
    ]


_BRACE_BUILDERS = {
    BraceStyle.X_BRACE:   _x_brace_specs,
    BraceStyle.FAN_BRACE: _fan_brace_specs,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def prescribe_bracing(
    inputs: "PlateInputs",
    solver_result: "InverseSolverResult",
    style: str = "x_brace",
) -> BracePrescription:
    """
    Produce a BracePrescription from PlateInputs and an InverseSolverResult.

    Args:
        inputs:         PlateInputs from viewer_pack_bridge.plate_inputs_from_pack()
        solver_result:  InverseSolverResult from inverse_solver.solve_for_thickness()
                        or InverseDesignProblem.solve()
        style:          Brace pattern: "x_brace" | "fan_brace" | "ladder" | "modified_x"

    Returns:
        BracePrescription with physical brace dimensions and manufacturability check.
    """
    brace_style = BraceStyle(style)
    builder = _BRACE_BUILDERS.get(brace_style)

    if builder is None:
        # Ladder and modified_x not yet implemented — return empty prescription
        # with a note rather than raising
        return BracePrescription(
            style=brace_style,
            braces=[],
            plate_species=inputs.species,
            plate_E_L_GPa=inputs.E_L_GPa,
            plate_E_C_GPa=inputs.E_C_GPa,
            plate_thickness_mm=solver_result.thickness_mm,
            converged=solver_result.converged,
            rms_error_Hz=solver_result.rms_error_Hz,
            notes=inputs.notes + [
                f"Brace style '{style}' geometry not yet implemented. "
                f"X-brace and fan-brace are available."
            ],
        )

    braces = builder(
        plate_length_mm=inputs.plate_length_mm,
        plate_width_mm=inputs.plate_width_mm,
        target_h_mm=solver_result.thickness_mm,
        E_L=inputs.E_L_GPa,
    )

    warnings, score = _check_manufacturability(
        braces, inputs.plate_length_mm, inputs.plate_width_mm
    )

    # Extract target and achieved frequency lists
    target_hz = [hz for _, hz in inputs.target_frequencies]
    achieved_hz = list(getattr(solver_result, "achieved_frequencies_Hz", []))

    return BracePrescription(
        style=brace_style,
        braces=braces,
        plate_species=inputs.species,
        plate_E_L_GPa=inputs.E_L_GPa,
        plate_E_C_GPa=inputs.E_C_GPa,
        plate_thickness_mm=solver_result.thickness_mm,
        target_frequencies_Hz=target_hz,
        achieved_frequencies_Hz=achieved_hz,
        rms_error_Hz=solver_result.rms_error_Hz,
        converged=solver_result.converged,
        manufacturability_warnings=warnings,
        manufacturability_score=score,
        source_session=inputs.source_session,
        bending_measured=inputs.bending_measured,
        notes=inputs.notes,
    )
