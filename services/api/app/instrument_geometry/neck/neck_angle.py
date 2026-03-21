"""
Neck angle calculator - derives correct neck angle from geometry.

theta = arctan((H_saddle + H_bridge - H_fretboard) / L_body)

Gate:
  GREEN:  1.0 <= theta <= 3.5 (normal range)
  YELLOW: 0.5 <= theta < 1.0 (too flat - neck reset risk)
          3.5 < theta <= 5.0 (steep - high saddle needed)
  RED:    theta < 0.5 or theta > 5.0

0.5 error approx 2.6mm height error over 300mm = neck reset territory.

ACOUSTIC-001: Added solve_for_target_action() inverse function and fixed
saddle_height_required_mm calculation to use exact geometry formula:
  H_saddle = L_body * tan(theta_target) + H_fretboard - H_bridge
"""
from __future__ import annotations

from dataclasses import dataclass
from math import atan, tan, degrees

from .fret_math import compute_fret_to_bridge_mm, compute_fret_positions_mm


@dataclass
class NeckAngleInput:
    """Input geometry for neck angle calculation (all mm)."""
    bridge_height_mm: float  # top of bridge to soundboard
    saddle_projection_mm: float  # saddle height above bridge top
    fretboard_height_at_joint_mm: float  # fretboard plane at body join
    nut_to_bridge_mm: float  # scale length (approx)
    neck_joint_fret: int = 14  # where neck meets body
    action_12th_mm: float = 2.0  # string height at 12th fret (advisory)


@dataclass
class NeckAngleResult:
    """Result of neck angle computation with gate and message."""
    angle_deg: float
    gate: str  # GREEN / YELLOW / RED
    message: str
    saddle_height_required_mm: float


@dataclass
class TargetActionResult:
    """Result of solve_for_target_action() inverse calculation."""
    neck_angle_deg: float
    saddle_height_mm: float
    relief_contribution_mm: float
    gate: str  # GREEN / YELLOW / RED
    message: str
    nut_to_12th_mm: float
    body_length_mm: float


def _compute_nut_to_fret_mm(scale_length_mm: float, fret_number: int) -> float:
    """Distance from nut to the specified fret."""
    if fret_number <= 0:
        return 0.0
    if scale_length_mm <= 0:
        return 0.0
    try:
        positions = compute_fret_positions_mm(scale_length_mm, fret_number)
        return positions[fret_number - 1]
    except (ValueError, IndexError):
        return 0.0


def compute_neck_angle(inp: NeckAngleInput) -> NeckAngleResult:
    """
    Compute neck angle from bridge height, fretboard height, and body length.

    theta = arctan((H_saddle + H_bridge - H_fretboard) / L_body)

    L_body = distance from neck joint fret to bridge (from equal-tempered scale).
    """
    # Body length: joint fret to bridge
    body_length_mm = compute_fret_to_bridge_mm(inp.nut_to_bridge_mm, inp.neck_joint_fret)
    if body_length_mm <= 0:
        return NeckAngleResult(
            angle_deg=0.0,
            gate="RED",
            message="Invalid geometry: body length from joint to bridge must be positive",
            saddle_height_required_mm=inp.saddle_projection_mm,
        )

    # Height difference: saddle top above fretboard plane at joint
    total_saddle_height_mm = inp.bridge_height_mm + inp.saddle_projection_mm
    height_diff_mm = total_saddle_height_mm - inp.fretboard_height_at_joint_mm

    angle_rad = atan(height_diff_mm / body_length_mm)
    angle_deg = degrees(angle_rad)

    # ACOUSTIC-001: Proper saddle height calculation using exact formula
    saddle_height_required_mm = (
        body_length_mm * tan(angle_rad)
        + inp.fretboard_height_at_joint_mm
        - inp.bridge_height_mm
    )

    # Gate
    if angle_deg >= 1.0 and angle_deg <= 3.5:
        gate = "GREEN"
        message = "Neck angle in normal range."
    elif angle_deg >= 0.5 and angle_deg < 1.0:
        gate = "YELLOW"
        message = "Neck angle flat - neck reset risk if top deflects."
    elif angle_deg > 3.5 and angle_deg <= 5.0:
        gate = "YELLOW"
        message = "Neck angle steep - high saddle required."
    elif angle_deg < 0.5:
        gate = "RED"
        message = "Neck angle too flat; likely to need neck reset."
    else:
        gate = "RED"
        message = "Neck angle too steep; geometry may be incorrect."

    return NeckAngleResult(
        angle_deg=round(angle_deg, 4),
        gate=gate,
        message=message,
        saddle_height_required_mm=round(saddle_height_required_mm, 2),
    )


def solve_for_target_action(
    target_action_12th_mm: float,
    bridge_height_mm: float,
    fretboard_height_at_joint_mm: float,
    nut_to_bridge_mm: float,
    relief_mm: float = 0.25,
    nut_slot_depth_mm: float = 0.5,
    neck_joint_fret: int = 14,
) -> TargetActionResult:
    """
    ACOUSTIC-001: Inverse solver - given target action at 12th fret,
    compute the required neck angle and saddle height.
    """
    # Distance from nut to 12th fret
    nut_to_12th_mm = _compute_nut_to_fret_mm(nut_to_bridge_mm, 12)
    if nut_to_12th_mm <= 0:
        return TargetActionResult(
            neck_angle_deg=0.0,
            saddle_height_mm=0.0,
            relief_contribution_mm=0.0,
            gate="RED",
            message="Invalid scale length: nut to 12th fret distance must be positive",
            nut_to_12th_mm=0.0,
            body_length_mm=0.0,
        )

    # Body length: joint fret to bridge
    body_length_mm = compute_fret_to_bridge_mm(nut_to_bridge_mm, neck_joint_fret)
    if body_length_mm <= 0:
        return TargetActionResult(
            neck_angle_deg=0.0,
            saddle_height_mm=0.0,
            relief_contribution_mm=0.0,
            gate="RED",
            message="Invalid geometry: body length must be positive",
            nut_to_12th_mm=nut_to_12th_mm,
            body_length_mm=0.0,
        )

    # Relief contributes ~60% at 12th fret (parabolic approximation)
    relief_contribution_mm = relief_mm * 0.6

    # Action at 12th minus relief contribution = geometric action
    geometric_action_mm = target_action_12th_mm - relief_contribution_mm

    # Compute target angle
    angle_rad = atan(geometric_action_mm / nut_to_12th_mm)
    angle_deg = degrees(angle_rad)

    # Compute required saddle height using exact formula
    saddle_height_mm = (
        body_length_mm * tan(angle_rad)
        + fretboard_height_at_joint_mm
        - bridge_height_mm
    )

    # Gate based on angle and saddle height
    if angle_deg >= 1.0 and angle_deg <= 3.5:
        if saddle_height_mm >= 3.0 and saddle_height_mm <= 12.0:
            gate = "GREEN"
            message = "Neck angle and saddle height in normal range."
        elif saddle_height_mm < 3.0:
            gate = "YELLOW"
            message = f"Saddle height {saddle_height_mm:.1f}mm may be too low for adjustment."
        else:
            gate = "YELLOW"
            message = f"Saddle height {saddle_height_mm:.1f}mm is high; verify geometry."
    elif angle_deg >= 0.5 and angle_deg < 1.0:
        gate = "YELLOW"
        message = "Neck angle flat - neck reset risk if top deflects."
    elif angle_deg > 3.5 and angle_deg <= 5.0:
        gate = "YELLOW"
        message = "Neck angle steep - high saddle required."
    elif angle_deg < 0.5:
        gate = "RED"
        message = "Neck angle too flat; geometry will not achieve target action."
    else:
        gate = "RED"
        message = "Neck angle too steep; geometry may be incorrect."

    return TargetActionResult(
        neck_angle_deg=round(angle_deg, 4),
        saddle_height_mm=round(saddle_height_mm, 2),
        relief_contribution_mm=round(relief_contribution_mm, 3),
        gate=gate,
        message=message,
        nut_to_12th_mm=round(nut_to_12th_mm, 2),
        body_length_mm=round(body_length_mm, 2),
    )