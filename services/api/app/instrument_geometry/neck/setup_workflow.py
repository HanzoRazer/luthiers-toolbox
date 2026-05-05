"""
Setup Workflow Models and Evaluators.

V1 Vertical Slice: Relief measurement workflow only.
Path to expansion: nut, action, intonation (not in v1).
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SetupWorkflowStep(str, Enum):
    """Setup workflow steps (v1: only RELIEF implemented)."""
    RELIEF = "relief"
    NUT = "nut"          # v2
    ACTION = "action"    # v2
    INTONATION = "intonation"  # v2
    VALIDATION = "validation"  # v2


class DiagnosticGate(str, Enum):
    """Diagnostic gate levels."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class DiagnosticResult(BaseModel):
    """Single diagnostic evaluation result."""
    id: str = Field(description="Unique rule identifier")
    gate: DiagnosticGate = Field(description="GREEN/YELLOW/RED")
    message: str = Field(description="Human-readable message")
    measurement: Optional[float] = Field(default=None, description="Measured value")
    target_min: Optional[float] = Field(default=None, description="Target minimum")
    target_max: Optional[float] = Field(default=None, description="Target maximum")
    probable_causes: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)


class SetupWorkflowState(BaseModel):
    """Current state of the setup workflow."""
    current_step: SetupWorkflowStep
    measurements: dict[str, float] = Field(default_factory=dict)
    diagnostics: List[DiagnosticResult] = Field(default_factory=list)
    completed_steps: List[SetupWorkflowStep] = Field(default_factory=list)


# ─── V1 Default Thresholds ────────────────────────────────────────────────────

DEFAULT_RELIEF_TARGET_MIN_MM = 0.10
DEFAULT_RELIEF_TARGET_MAX_MM = 0.30
YELLOW_TOLERANCE_MM = 0.05


# ─── Relief Evaluator ─────────────────────────────────────────────────────────

def evaluate_relief(
    measured_relief_mm: float,
    target_min_mm: float = DEFAULT_RELIEF_TARGET_MIN_MM,
    target_max_mm: float = DEFAULT_RELIEF_TARGET_MAX_MM,
) -> DiagnosticResult:
    """
    Evaluate neck relief measurement.

    Gate logic:
        GREEN:  target_min <= measured <= target_max
        YELLOW: within YELLOW_TOLERANCE_MM outside range
        RED:    beyond YELLOW_TOLERANCE_MM outside range

    Args:
        measured_relief_mm: Measured relief at 7th/8th fret (mm)
        target_min_mm: Minimum acceptable relief (default 0.10mm)
        target_max_mm: Maximum acceptable relief (default 0.30mm)

    Returns:
        DiagnosticResult with gate, message, and recommendations
    """
    yellow_low = target_min_mm - YELLOW_TOLERANCE_MM  # 0.05
    yellow_high = target_max_mm + YELLOW_TOLERANCE_MM  # 0.35

    # Determine gate
    if target_min_mm <= measured_relief_mm <= target_max_mm:
        gate = DiagnosticGate.GREEN
        message = "Neck relief is within target range."
        probable_causes = []
        recommended_actions = []
        rule_id = "relief_ok"
    elif measured_relief_mm < yellow_low:
        # RED: far too low
        gate = DiagnosticGate.RED
        message = "Neck relief is too low — likely to cause fret buzz."
        probable_causes = ["Truss rod too tight", "Back-bowed neck"]
        recommended_actions = ["Loosen truss rod 1/4 turn and re-measure after 24 hours"]
        rule_id = "relief_too_low_severe"
    elif measured_relief_mm < target_min_mm:
        # YELLOW: slightly too low
        gate = DiagnosticGate.YELLOW
        message = "Neck relief is slightly low — may cause buzz on lower frets."
        probable_causes = ["Truss rod slightly tight"]
        recommended_actions = ["Loosen truss rod 1/8 turn and re-measure"]
        rule_id = "relief_too_low"
    elif measured_relief_mm > yellow_high:
        # RED: far too high
        gate = DiagnosticGate.RED
        message = "Neck relief is too high — action will feel high, intonation affected."
        probable_causes = ["Truss rod too loose", "Neck settling", "High string tension"]
        recommended_actions = ["Tighten truss rod 1/4 turn and re-measure after 24 hours"]
        rule_id = "relief_too_high_severe"
    else:
        # YELLOW: slightly too high (target_max < measured <= yellow_high)
        gate = DiagnosticGate.YELLOW
        message = "Neck relief is slightly high — action may feel elevated."
        probable_causes = ["Truss rod slightly loose"]
        recommended_actions = ["Tighten truss rod 1/8 turn and re-measure"]
        rule_id = "relief_too_high"

    return DiagnosticResult(
        id=rule_id,
        gate=gate,
        message=message,
        measurement=measured_relief_mm,
        target_min=target_min_mm,
        target_max=target_max_mm,
        probable_causes=probable_causes,
        recommended_actions=recommended_actions,
    )


__all__ = [
    "SetupWorkflowStep",
    "DiagnosticGate",
    "DiagnosticResult",
    "SetupWorkflowState",
    "evaluate_relief",
    "DEFAULT_RELIEF_TARGET_MIN_MM",
    "DEFAULT_RELIEF_TARGET_MAX_MM",
]
