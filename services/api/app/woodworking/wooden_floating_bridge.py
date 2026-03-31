"""
Floating bridge / tremolo geometry (electric guitar).

Approximate shop math for saddle height vs. 12th-fret action and string break angle
behind the bridge. Not a substitute for full setup — uses small-angle similarity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FloatingBridgeResult:
    """Computed values for a floating-style bridge / tremolo."""

    scale_length_mm: float
    action_12th_mm: float
    saddle_height_above_plane_mm: float
    distance_12th_to_bridge_mm: float
    notes: str


def compute_saddle_height_from_twelfth_action(
    scale_length_mm: float,
    action_12th_mm: float,
) -> FloatingBridgeResult:
    """
    Estimate extra string height at the bridge plane vs. the fretboard extension,
    from target string height at the 12th fret.

    Uses linear extrapolation along the string path: the 12th fret is at half
    scale from the nut; the bridge sits at full scale. For a straight string,
    nominal clearance at the bridge is ~2× the clearance at the 12th fret.

    Parameters
    ----------
    scale_length_mm:
        Nominal scale (nut to saddle).
    action_12th_mm:
        Target string height at 12th fret, measured from fret top (typ. 1.5–2.5 mm low E).

    Returns
    -------
    FloatingBridgeResult
    """
    if scale_length_mm <= 0 or action_12th_mm < 0:
        return FloatingBridgeResult(
            scale_length_mm=scale_length_mm,
            action_12th_mm=action_12th_mm,
            saddle_height_above_plane_mm=0.0,
            distance_12th_to_bridge_mm=0.0,
            notes="Invalid scale or action; expected positive scale and non-negative action.",
        )

    d_12 = scale_length_mm * 0.5
    # Height at bridge relative to fret plane (straight string, no relief modeled).
    h_bridge = 2.0 * action_12th_mm
    notes = (
        "Straight-string model; add neck relief and witness points separately. "
        "Locking nut / stagger changes effective break angle."
    )
    return FloatingBridgeResult(
        scale_length_mm=scale_length_mm,
        action_12th_mm=action_12th_mm,
        saddle_height_above_plane_mm=h_bridge,
        distance_12th_to_bridge_mm=d_12,
        notes=notes,
    )


def compute_break_angle_deg(
    height_delta_mm: float,
    horizontal_run_mm: float,
) -> float:
    """
    Break angle (degrees) from vertical drop and horizontal run (e.g. string behind bridge).

    atan(height / run) in degrees.
    """
    if horizontal_run_mm <= 0:
        return 0.0
    return math.degrees(math.atan(height_delta_mm / horizontal_run_mm))
