"""
Saddle force decomposition calculator — ACOUSTIC-002.

Decomposes saddle break angle into vertical downbearing force component
(bridge plate load) and computes total saddle force from string tensions.

Formula:
    F_saddle_i = T_i × (sin(θ_front_i) + sin(θ_behind_i))

Where:
    T_i = string tension (N)
    θ_front_i = break angle over saddle (from bridge_break_angle.py)
    θ_behind_i = arctan(body_depth_mm / pin_to_tailblock_mm)

Gate thresholds (Carruth-derived):
    GREEN:  total < 500 N  (normal range for light/medium strings)
    YELLOW: 500 <= total < 700 N  (heavy strings, monitor bridge plate)
    RED:    total >= 700 N  (excessive load, risk of bridge plate failure)

See: docs/BACKLOG.md ACOUSTIC-002
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Literal, Optional

# Conversion factor
N_TO_LBS = 0.224809


@dataclass
class StringForce:
    """Force contribution from a single string."""

    string_name: str
    tension_n: float
    break_angle_deg: float
    behind_angle_deg: float
    vertical_force_n: float


@dataclass
class SaddleForceResult:
    """Result of saddle force computation with gate and notes."""

    string_forces: List[StringForce]
    total_vertical_force_n: float
    total_vertical_force_lbs: float
    gate: Literal["GREEN", "YELLOW", "RED"]
    notes: List[str] = field(default_factory=list)


def _compute_behind_angle_deg(
    body_depth_at_bridge_mm: float,
    pin_to_tailblock_mm: float,
) -> float:
    """
    Compute the "behind angle" — angle from saddle down to bridge pin/tailblock.

    θ_behind = arctan(body_depth / pin_to_tailblock_distance)

    For a typical dreadnought:
        body_depth ~100mm, pin_to_tailblock ~250mm → ~21.8°
    """
    if pin_to_tailblock_mm <= 0:
        return 0.0
    ratio = body_depth_at_bridge_mm / pin_to_tailblock_mm
    return math.degrees(math.atan(ratio))


def compute_saddle_force(
    string_tensions_n: List[float],
    break_angles_deg: List[float],
    body_depth_at_bridge_mm: float = 100.0,
    pin_to_tailblock_mm: float = 250.0,
    string_names: Optional[List[str]] = None,
) -> SaddleForceResult:
    """
    Compute total saddle force from string tensions and break angles.

    F_saddle_i = T_i × (sin(θ_front_i) + sin(θ_behind_i))

    Args:
        string_tensions_n: Tension for each string in Newtons.
        break_angles_deg: Break angle over saddle for each string (degrees).
        body_depth_at_bridge_mm: Depth of body at bridge location.
        pin_to_tailblock_mm: Distance from bridge pins to tailblock.
        string_names: Optional names for each string (e.g., ["E2", "A2", ...]).

    Returns:
        SaddleForceResult with per-string forces, total, gate, and notes.
    """
    notes: List[str] = []

    # Validate inputs
    if len(string_tensions_n) != len(break_angles_deg):
        raise ValueError(
            f"Mismatched lengths: {len(string_tensions_n)} tensions vs "
            f"{len(break_angles_deg)} break angles"
        )

    if not string_tensions_n:
        return SaddleForceResult(
            string_forces=[],
            total_vertical_force_n=0.0,
            total_vertical_force_lbs=0.0,
            gate="GREEN",
            notes=["No strings provided"],
        )

    # Default string names
    if string_names is None:
        string_names = [f"String {i+1}" for i in range(len(string_tensions_n))]
    elif len(string_names) != len(string_tensions_n):
        string_names = [f"String {i+1}" for i in range(len(string_tensions_n))]
        notes.append("String names length mismatch, using defaults")

    # Compute behind angle (same for all strings on acoustic)
    behind_angle_deg = _compute_behind_angle_deg(
        body_depth_at_bridge_mm, pin_to_tailblock_mm
    )
    behind_angle_rad = math.radians(behind_angle_deg)

    string_forces: List[StringForce] = []
    total_force_n = 0.0

    for i, (tension_n, break_deg, name) in enumerate(
        zip(string_tensions_n, break_angles_deg, string_names)
    ):
        # Convert break angle to radians
        break_rad = math.radians(break_deg)

        # F_saddle = T × (sin(θ_front) + sin(θ_behind))
        vertical_force_n = tension_n * (math.sin(break_rad) + math.sin(behind_angle_rad))

        string_forces.append(
            StringForce(
                string_name=name,
                tension_n=round(tension_n, 2),
                break_angle_deg=round(break_deg, 2),
                behind_angle_deg=round(behind_angle_deg, 2),
                vertical_force_n=round(vertical_force_n, 2),
            )
        )
        total_force_n += vertical_force_n

    # Convert to lbs
    total_force_lbs = total_force_n * N_TO_LBS

    # Gate determination
    if total_force_n < 500:
        gate: Literal["GREEN", "YELLOW", "RED"] = "GREEN"
        notes.append("Total saddle force in normal range for light/medium strings.")
    elif total_force_n < 700:
        gate = "YELLOW"
        notes.append(
            "Elevated saddle force — typical for heavy strings. "
            "Monitor bridge plate for signs of distortion."
        )
    else:
        gate = "RED"
        notes.append(
            "Excessive saddle force (>700N). Risk of bridge plate failure. "
            "Consider lighter strings or reinforced bridge plate."
        )

    return SaddleForceResult(
        string_forces=string_forces,
        total_vertical_force_n=round(total_force_n, 2),
        total_vertical_force_lbs=round(total_force_lbs, 2),
        gate=gate,
        notes=notes,
    )


def compute_saddle_force_simple(
    total_string_tension_n: float,
    break_angle_deg: float,
    body_depth_at_bridge_mm: float = 100.0,
    pin_to_tailblock_mm: float = 250.0,
) -> dict:
    """
    Simplified saddle force calculation for single aggregate tension value.

    Returns dict with vertical_force_n, horizontal_force_n, torque_Nm estimates.
    """
    behind_angle_deg = _compute_behind_angle_deg(
        body_depth_at_bridge_mm, pin_to_tailblock_mm
    )

    break_rad = math.radians(break_angle_deg)
    behind_rad = math.radians(behind_angle_deg)

    # Vertical component (downward into bridge plate)
    vertical_force_n = total_string_tension_n * (
        math.sin(break_rad) + math.sin(behind_rad)
    )

    # Horizontal component (forward pull on bridge)
    horizontal_force_n = total_string_tension_n * (
        math.cos(break_rad) - math.cos(behind_rad)
    )

    # Simple torque estimate (N·m) at bridge plate
    # Moment arm ~ saddle height / 1000 (convert mm to m)
    # Using typical saddle height of 3mm
    saddle_height_m = 0.003
    torque_nm = vertical_force_n * saddle_height_m

    # Gate
    if vertical_force_n < 500:
        gate = "GREEN"
    elif vertical_force_n < 700:
        gate = "YELLOW"
    else:
        gate = "RED"

    return {
        "vertical_force_n": round(vertical_force_n, 2),
        "horizontal_force_n": round(horizontal_force_n, 2),
        "torque_nm": round(torque_nm, 4),
        "break_angle_deg": round(break_angle_deg, 2),
        "behind_angle_deg": round(behind_angle_deg, 2),
        "gate": gate,
    }
