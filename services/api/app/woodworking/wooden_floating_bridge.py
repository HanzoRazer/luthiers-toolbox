"""
Floating bridge geometry — compatibility module for tests and legacy imports.

Canonical archtop bridge math lives under app.instrument_geometry.bridge;
this module preserves the small straight-string saddle-height helper.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FloatingBridgeResult:
    scale_length_mm: float
    action_12th_mm: float
    saddle_height_above_plane_mm: float
    distance_12th_to_bridge_mm: float
    notes: str


def compute_saddle_height_from_twelfth_action(
    scale_length_mm: float,
    action_12th_mm: float,
) -> FloatingBridgeResult:
    if scale_length_mm <= 0 or action_12th_mm < 0:
        return FloatingBridgeResult(
            scale_length_mm=scale_length_mm,
            action_12th_mm=action_12th_mm,
            saddle_height_above_plane_mm=0.0,
            distance_12th_to_bridge_mm=0.0,
            notes="Invalid scale or action; expected positive scale and non-negative action.",
        )

    d_12 = scale_length_mm * 0.5
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


def compute_break_angle_deg(height_delta_mm: float, horizontal_run_mm: float) -> float:
    if horizontal_run_mm <= 0:
        return 0.0
    return math.degrees(math.atan(height_delta_mm / horizontal_run_mm))
