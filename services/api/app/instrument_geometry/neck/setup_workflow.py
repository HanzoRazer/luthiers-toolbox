"""
Setup Workflow Models and Evaluators.

V1 Vertical Slice: Relief measurement workflow.
V2 Expansion: Action measurement workflow (Phase 4).
Path to expansion: nut, intonation (not yet implemented).
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


class ActionWorkflowResponse(BaseModel):
    """Response from action workflow evaluation (Phase 4)."""
    current_step: str = Field(default="action", description="Workflow step identifier")
    overall_gate: DiagnosticGate = Field(description="Worst-case gate across all diagnostics")
    diagnostics: List[DiagnosticResult] = Field(description="Individual diagnostic results")


# ─── V1 Default Thresholds (Relief) ──────────────────────────────────────────

DEFAULT_RELIEF_TARGET_MIN_MM = 0.10
DEFAULT_RELIEF_TARGET_MAX_MM = 0.30
YELLOW_TOLERANCE_MM = 0.05

# ─── V2 Default Thresholds (Action) ──────────────────────────────────────────

DEFAULT_TREBLE_ACTION_TARGET_MIN_MM = 1.25
DEFAULT_TREBLE_ACTION_TARGET_MAX_MM = 1.75
DEFAULT_BASS_ACTION_TARGET_MIN_MM = 1.75
DEFAULT_BASS_ACTION_TARGET_MAX_MM = 2.25
ACTION_YELLOW_TOLERANCE_MM = 0.25


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


# ─── Action Evaluator (Phase 4) ──────────────────────────────────────────────

def _worst_gate(gates: List[DiagnosticGate]) -> DiagnosticGate:
    """Return the worst gate from a list. RED > YELLOW > GREEN."""
    if DiagnosticGate.RED in gates:
        return DiagnosticGate.RED
    if DiagnosticGate.YELLOW in gates:
        return DiagnosticGate.YELLOW
    return DiagnosticGate.GREEN


def _evaluate_single_action(
    measured_mm: float,
    target_min_mm: float,
    target_max_mm: float,
    position: str,  # "treble" or "bass"
    yellow_tolerance: float = ACTION_YELLOW_TOLERANCE_MM,
) -> DiagnosticResult:
    """Evaluate a single action measurement (treble or bass)."""
    yellow_low = target_min_mm - yellow_tolerance
    yellow_high = target_max_mm + yellow_tolerance

    if target_min_mm <= measured_mm <= target_max_mm:
        gate = DiagnosticGate.GREEN
        message = f"{position.capitalize()} action at 12th fret is within target range."
        probable_causes = []
        recommended_actions = []
        rule_id = f"action_{position}_in_range"
    elif measured_mm < yellow_low:
        gate = DiagnosticGate.RED
        message = f"{position.capitalize()} action is too low — fret buzz likely."
        probable_causes = ["Saddle too low", "Neck relief too low", "Worn frets"]
        recommended_actions = [f"Raise saddle or check neck relief before adjusting {position} action"]
        rule_id = f"action_{position}_too_low_severe"
    elif measured_mm < target_min_mm:
        gate = DiagnosticGate.YELLOW
        message = f"{position.capitalize()} action is slightly low — may buzz on aggressive playing."
        probable_causes = ["Saddle slightly low"]
        recommended_actions = [f"Consider raising saddle slightly for {position} side"]
        rule_id = f"action_{position}_too_low"
    elif measured_mm > yellow_high:
        gate = DiagnosticGate.RED
        message = f"{position.capitalize()} action is too high — playability affected."
        probable_causes = ["Saddle too high", "Neck angle too steep", "Excessive relief"]
        recommended_actions = [f"Lower saddle or check neck angle for {position} side"]
        rule_id = f"action_{position}_too_high_severe"
    else:
        gate = DiagnosticGate.YELLOW
        message = f"{position.capitalize()} action is slightly high — may feel stiff."
        probable_causes = ["Saddle slightly high"]
        recommended_actions = [f"Consider lowering saddle slightly for {position} side"]
        rule_id = f"action_{position}_too_high"

    return DiagnosticResult(
        id=rule_id,
        gate=gate,
        message=message,
        measurement=measured_mm,
        target_min=target_min_mm,
        target_max=target_max_mm,
        probable_causes=probable_causes,
        recommended_actions=recommended_actions,
    )


def evaluate_action(
    treble_action_mm: float,
    bass_action_mm: float,
    treble_target_min_mm: float = DEFAULT_TREBLE_ACTION_TARGET_MIN_MM,
    treble_target_max_mm: float = DEFAULT_TREBLE_ACTION_TARGET_MAX_MM,
    bass_target_min_mm: float = DEFAULT_BASS_ACTION_TARGET_MIN_MM,
    bass_target_max_mm: float = DEFAULT_BASS_ACTION_TARGET_MAX_MM,
) -> ActionWorkflowResponse:
    """
    Evaluate action height at 12th fret for treble and bass sides.

    Gate logic per side:
        GREEN:  target_min <= measured <= target_max
        YELLOW: within ACTION_YELLOW_TOLERANCE_MM (0.25mm) outside range
        RED:    beyond ACTION_YELLOW_TOLERANCE_MM outside range

    Overall gate is worst-case: RED > YELLOW > GREEN.

    Args:
        treble_action_mm: Measured action at 12th fret, treble side (mm)
        bass_action_mm: Measured action at 12th fret, bass side (mm)
        treble_target_min_mm: Minimum acceptable treble action (default 1.25mm)
        treble_target_max_mm: Maximum acceptable treble action (default 1.75mm)
        bass_target_min_mm: Minimum acceptable bass action (default 1.75mm)
        bass_target_max_mm: Maximum acceptable bass action (default 2.25mm)

    Returns:
        ActionWorkflowResponse with overall gate and individual diagnostics
    """
    treble_result = _evaluate_single_action(
        measured_mm=treble_action_mm,
        target_min_mm=treble_target_min_mm,
        target_max_mm=treble_target_max_mm,
        position="treble",
    )

    bass_result = _evaluate_single_action(
        measured_mm=bass_action_mm,
        target_min_mm=bass_target_min_mm,
        target_max_mm=bass_target_max_mm,
        position="bass",
    )

    diagnostics = [treble_result, bass_result]
    overall_gate = _worst_gate([d.gate for d in diagnostics])

    return ActionWorkflowResponse(
        current_step="action",
        overall_gate=overall_gate,
        diagnostics=diagnostics,
    )


__all__ = [
    # Models
    "SetupWorkflowStep",
    "DiagnosticGate",
    "DiagnosticResult",
    "SetupWorkflowState",
    "ActionWorkflowResponse",
    # Relief (Phase 3)
    "evaluate_relief",
    "DEFAULT_RELIEF_TARGET_MIN_MM",
    "DEFAULT_RELIEF_TARGET_MAX_MM",
    # Action (Phase 4)
    "evaluate_action",
    "DEFAULT_TREBLE_ACTION_TARGET_MIN_MM",
    "DEFAULT_TREBLE_ACTION_TARGET_MAX_MM",
    "DEFAULT_BASS_ACTION_TARGET_MIN_MM",
    "DEFAULT_BASS_ACTION_TARGET_MAX_MM",
]
