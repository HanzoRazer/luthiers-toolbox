"""
Neck angle calculator — derives correct neck angle from geometry.

θ = arctan((H_saddle + H_bridge - H_fretboard) / L_body)

Gate:
  GREEN:  1.0° <= θ <= 3.5° (normal range)
  YELLOW: 0.5° <= θ < 1.0° (too flat — neck reset risk)
          3.5° < θ <= 5.0° (steep — high saddle needed)
  RED:    θ < 0.5° or θ > 5.0°

0.5° error ≈ 2.6mm height error over 300mm = neck reset territory.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import atan, degrees

from .fret_math import compute_fret_to_bridge_mm


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


def compute_neck_angle(inp: NeckAngleInput) -> NeckAngleResult:
    """
    Compute neck angle from bridge height, fretboard height, and body length.

    θ = arctan((H_saddle + H_bridge - H_fretboard) / L_body)

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

    # Gate
    if angle_deg >= 1.0 and angle_deg <= 3.5:
        gate = "GREEN"
        message = "Neck angle in normal range."
    elif angle_deg >= 0.5 and angle_deg < 1.0:
        gate = "YELLOW"
        message = "Neck angle flat — neck reset risk if top deflects."
    elif angle_deg > 3.5 and angle_deg <= 5.0:
        gate = "YELLOW"
        message = "Neck angle steep — high saddle required."
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
        saddle_height_required_mm=round(inp.saddle_projection_mm, 2),
    )
