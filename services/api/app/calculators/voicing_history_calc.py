"""
Acoustic voicing history calculator (CONSTRUCTION-009).

Tracks tap tone measurements across build stages and predicts
final frequency based on thickness changes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional, Tuple


# ─── Constants ───────────────────────────────────────────────────────────────

# Build stages in order
BUILD_STAGES = [
    "rough_thicknessed",
    "braced_free_plate",
    "assembled_in_box",
    "strung_up",
]

# Typical target frequencies by body style (Hz)
TARGET_FREQUENCIES = {
    "dreadnought": {"top": 180, "back": 200},
    "om_000": {"top": 195, "back": 215},
    "classical": {"top": 170, "back": 190},
    "parlor": {"top": 210, "back": 230},
    "jumbo": {"top": 165, "back": 185},
}

# Frequency tolerance for "on target" (Hz)
FREQUENCY_TOLERANCE_HZ = 5.0

# Minimum plate thickness (mm) - below this is over-thinned
MIN_TOP_THICKNESS_MM = 2.2
MIN_BACK_THICKNESS_MM = 2.5


@dataclass
class TapToneMeasurement:
    """Single tap tone measurement at a build stage."""

    stage: str                    # Build stage
    thickness_mm: float           # Plate thickness at measurement
    tap_frequency_hz: float       # Measured fundamental frequency
    timestamp: str                # ISO format timestamp
    notes: str = ""               # Optional notes

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "stage": self.stage,
            "thickness_mm": round(self.thickness_mm, 2),
            "tap_frequency_hz": round(self.tap_frequency_hz, 1),
            "timestamp": self.timestamp,
            "notes": self.notes,
        }


@dataclass
class VoicingSession:
    """Complete voicing session for an instrument."""

    instrument_id: str
    top_species: str
    back_species: str
    body_style: str
    measurements: List[TapToneMeasurement]
    target_top_hz: float
    target_back_hz: float

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "instrument_id": self.instrument_id,
            "top_species": self.top_species,
            "back_species": self.back_species,
            "body_style": self.body_style,
            "measurements": [m.to_dict() for m in self.measurements],
            "target_top_hz": self.target_top_hz,
            "target_back_hz": self.target_back_hz,
        }


@dataclass
class VoicingReport:
    """Analysis report for voicing progress."""

    instrument_id: str
    current_stage: str
    top_status: str              # "on_target" | "above_target" | "below_target" | "over_thinned"
    back_status: str
    top_frequency_hz: Optional[float]
    back_frequency_hz: Optional[float]
    top_delta_hz: float          # Current - target (positive = above)
    back_delta_hz: float
    predicted_top_hz: Optional[float]   # If thickness change proposed
    predicted_back_hz: Optional[float]
    trend_slope: float           # Hz per mm thickness (from regression)
    gate: str                    # GREEN/YELLOW/RED
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "instrument_id": self.instrument_id,
            "current_stage": self.current_stage,
            "top_status": self.top_status,
            "back_status": self.back_status,
            "top_frequency_hz": round(self.top_frequency_hz, 1) if self.top_frequency_hz else None,
            "back_frequency_hz": round(self.back_frequency_hz, 1) if self.back_frequency_hz else None,
            "top_delta_hz": round(self.top_delta_hz, 1),
            "back_delta_hz": round(self.back_delta_hz, 1),
            "predicted_top_hz": round(self.predicted_top_hz, 1) if self.predicted_top_hz else None,
            "predicted_back_hz": round(self.predicted_back_hz, 1) if self.predicted_back_hz else None,
            "trend_slope": round(self.trend_slope, 2),
            "gate": self.gate,
            "notes": self.notes,
        }


def _linear_regression(points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Simple linear regression on (x, y) points.
    Returns (slope, intercept).
    """
    n = len(points)
    if n < 2:
        return 0.0, points[0][1] if points else 0.0

    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_x2 = sum(p[0] ** 2 for p in points)

    denom = n * sum_x2 - sum_x ** 2
    if abs(denom) < 1e-10:
        return 0.0, sum_y / n

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    return slope, intercept


def predict_final_frequency(
    current_thickness_mm: float,
    current_frequency_hz: float,
    target_thickness_mm: float,
) -> float:
    """
    Predict frequency at target thickness.

    For thin plates: f ∝ h (linear in thickness)
    More accurately: f ∝ h for constant stiffness/mass ratio

    Args:
        current_thickness_mm: Current plate thickness
        current_frequency_hz: Current measured frequency
        target_thickness_mm: Target thickness after thinning

    Returns:
        Predicted frequency at target thickness
    """
    if current_thickness_mm <= 0:
        return current_frequency_hz

    # Linear approximation: f = k × h
    # k = f_current / h_current
    k = current_frequency_hz / current_thickness_mm

    predicted = k * target_thickness_mm
    return predicted


def predict_frequency_from_removal(
    current_thickness_mm: float,
    current_frequency_hz: float,
    removal_mm: float,
) -> float:
    """
    Predict frequency after removing material.

    Args:
        current_thickness_mm: Current thickness
        current_frequency_hz: Current frequency
        removal_mm: Amount to remove (positive)

    Returns:
        Predicted frequency after removal
    """
    new_thickness = current_thickness_mm - removal_mm
    if new_thickness <= 0:
        return 0.0

    return predict_final_frequency(
        current_thickness_mm=current_thickness_mm,
        current_frequency_hz=current_frequency_hz,
        target_thickness_mm=new_thickness,
    )


def thickness_for_target_frequency(
    current_thickness_mm: float,
    current_frequency_hz: float,
    target_frequency_hz: float,
) -> float:
    """
    Calculate required thickness to achieve target frequency.

    Args:
        current_thickness_mm: Current thickness
        current_frequency_hz: Current frequency
        target_frequency_hz: Desired frequency

    Returns:
        Required thickness (may be less than current)
    """
    if current_frequency_hz <= 0:
        return current_thickness_mm

    # From f = k × h: h_target = h_current × (f_target / f_current)
    ratio = target_frequency_hz / current_frequency_hz
    required_thickness = current_thickness_mm * ratio

    return required_thickness


def _determine_status(
    current_hz: Optional[float],
    target_hz: float,
    thickness_mm: float,
    min_thickness_mm: float,
) -> str:
    """Determine status based on frequency and thickness."""
    if thickness_mm < min_thickness_mm:
        return "over_thinned"
    if current_hz is None:
        return "no_data"
    if abs(current_hz - target_hz) <= FREQUENCY_TOLERANCE_HZ:
        return "on_target"
    elif current_hz > target_hz:
        return "above_target"
    else:
        return "below_target"


def analyze_voicing_progress(session: VoicingSession) -> VoicingReport:
    """
    Analyze voicing progress for an instrument.

    Args:
        session: VoicingSession with measurements

    Returns:
        VoicingReport with analysis and predictions
    """
    notes: List[str] = []
    gate = "GREEN"

    # Separate measurements by plate type (inferred from notes or stage)
    top_measurements: List[TapToneMeasurement] = []
    back_measurements: List[TapToneMeasurement] = []

    for m in session.measurements:
        note_lower = m.notes.lower()
        if "back" in note_lower:
            back_measurements.append(m)
        elif "top" in note_lower:
            top_measurements.append(m)
        else:
            # Default: assign to both or use stage hints
            top_measurements.append(m)

    # Get current stage (latest measurement)
    current_stage = "rough_thicknessed"
    if session.measurements:
        current_stage = session.measurements[-1].stage

    # Get latest frequencies
    top_freq = top_measurements[-1].tap_frequency_hz if top_measurements else None
    back_freq = back_measurements[-1].tap_frequency_hz if back_measurements else None

    # Get latest thicknesses
    top_thickness = top_measurements[-1].thickness_mm if top_measurements else 3.0
    back_thickness = back_measurements[-1].thickness_mm if back_measurements else 3.5

    # Calculate deltas
    top_delta = (top_freq - session.target_top_hz) if top_freq else 0.0
    back_delta = (back_freq - session.target_back_hz) if back_freq else 0.0

    # Determine status
    top_status = _determine_status(top_freq, session.target_top_hz, top_thickness, MIN_TOP_THICKNESS_MM)
    back_status = _determine_status(back_freq, session.target_back_hz, back_thickness, MIN_BACK_THICKNESS_MM)

    # Calculate trend from regression (thickness vs frequency)
    trend_slope = 0.0
    if len(top_measurements) >= 2:
        points = [(m.thickness_mm, m.tap_frequency_hz) for m in top_measurements]
        trend_slope, _ = _linear_regression(points)

    # Predict final frequencies (assuming no more changes)
    predicted_top = top_freq
    predicted_back = back_freq

    # Gate logic
    if top_status == "over_thinned" or back_status == "over_thinned":
        gate = "RED"
        notes.append("CRITICAL: Plate is over-thinned — cannot recover")
    elif top_status == "below_target" or back_status == "below_target":
        gate = "RED"
        notes.append("Frequency below target — plate may be over-thinned")
    elif top_status == "above_target" or back_status == "above_target":
        if abs(top_delta) > 20 or abs(back_delta) > 20:
            gate = "YELLOW"
            notes.append("Significant voicing work remaining")
        else:
            notes.append("Minor voicing adjustment needed")

    # Add recommendations
    if top_status == "above_target" and top_freq:
        required_thickness = thickness_for_target_frequency(
            current_thickness_mm=top_thickness,
            current_frequency_hz=top_freq,
            target_frequency_hz=session.target_top_hz,
        )
        removal = top_thickness - required_thickness
        if removal > 0:
            notes.append(f"Top: remove ~{removal:.2f}mm to reach {session.target_top_hz}Hz")

    if back_status == "above_target" and back_freq:
        required_thickness = thickness_for_target_frequency(
            current_thickness_mm=back_thickness,
            current_frequency_hz=back_freq,
            target_frequency_hz=session.target_back_hz,
        )
        removal = back_thickness - required_thickness
        if removal > 0:
            notes.append(f"Back: remove ~{removal:.2f}mm to reach {session.target_back_hz}Hz")

    if top_status == "on_target" and back_status == "on_target":
        gate = "GREEN"
        notes.append("Both plates on target — ready for assembly")

    return VoicingReport(
        instrument_id=session.instrument_id,
        current_stage=current_stage,
        top_status=top_status,
        back_status=back_status,
        top_frequency_hz=top_freq,
        back_frequency_hz=back_freq,
        top_delta_hz=top_delta,
        back_delta_hz=back_delta,
        predicted_top_hz=predicted_top,
        predicted_back_hz=predicted_back,
        trend_slope=trend_slope,
        gate=gate,
        notes=notes,
    )


def get_target_frequencies(body_style: str) -> dict:
    """
    Get typical target frequencies for a body style.

    Args:
        body_style: Guitar body style

    Returns:
        Dict with top and back target frequencies
    """
    style_key = body_style.lower().replace("-", "_").replace(" ", "_")
    if style_key in TARGET_FREQUENCIES:
        return TARGET_FREQUENCIES[style_key]
    # Default to OM targets
    return TARGET_FREQUENCIES["om_000"]


def list_build_stages() -> List[str]:
    """Return list of build stages in order."""
    return BUILD_STAGES.copy()
