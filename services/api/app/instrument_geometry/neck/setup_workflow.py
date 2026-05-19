"""
Setup Workflow Models and Evaluators.

V1 Vertical Slice: Relief measurement workflow.
V2 Expansion: Action measurement workflow (Phase 4).
V3 Expansion: Nut slot measurement workflow (Phase 5).
V4 Expansion: Combined diagnostics (Phase 6).
V5 Expansion: Expert symptom-based diagnostics (Phase 7).
Path to expansion: intonation (not yet implemented).
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


class NutWorkflowResponse(BaseModel):
    """Response from nut slot workflow evaluation (Phase 5)."""
    current_step: str = Field(default="nut", description="Workflow step identifier")
    overall_gate: DiagnosticGate = Field(description="Worst-case gate across all diagnostics")
    diagnostics: List[DiagnosticResult] = Field(description="Per-string diagnostic results")


class CombinedDiagnostic(BaseModel):
    """Single combined cross-step diagnostic result (Phase 6)."""
    id: str = Field(description="Rule identifier")
    gate: DiagnosticGate = Field(description="GREEN/YELLOW/RED")
    message: str = Field(description="Human-readable insight")
    contributing_factors: List[str] = Field(default_factory=list, description="Steps contributing to this diagnostic")
    recommendation: str = Field(default="", description="Actionable recommendation")


class CombinedDiagnosticsResponse(BaseModel):
    """Response from combined setup diagnostics evaluation (Phase 6)."""
    overall_gate: DiagnosticGate = Field(description="Worst-case gate across all combined diagnostics")
    diagnostics: List[CombinedDiagnostic] = Field(description="Cross-step diagnostic insights")


class PlayerSymptom(str, Enum):
    """Player-reported symptoms for expert diagnosis (Phase 7)."""
    BUZZ_OPEN_STRINGS = "buzz_open_strings"
    BUZZ_LOW_FRETS = "buzz_low_frets"
    BUZZ_MIDDLE_FRETS = "buzz_middle_frets"
    BUZZ_UPPER_FRETS = "buzz_upper_frets"
    FRETTED_NOTES_BUZZ = "fretted_notes_buzz"
    FIRST_POSITION_HARD = "first_position_hard"
    FEELS_STIFF = "feels_stiff"
    FEELS_SLINKY = "feels_slinky"
    FIRST_POSITION_SHARP = "first_position_sharp"


class ExpertDiagnostic(BaseModel):
    """Single expert diagnostic result based on symptoms (Phase 7)."""
    id: str = Field(description="Rule identifier")
    gate: DiagnosticGate = Field(description="Inherited from triggering measurement")
    symptom: PlayerSymptom = Field(description="Player-reported symptom this addresses")
    message: str = Field(description="Human-readable diagnosis")
    probable_causes: List[str] = Field(default_factory=list)
    recommended_checks: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in diagnosis (0-1)")


class ExpertDiagnosticsResponse(BaseModel):
    """Response from expert symptom-based diagnostics evaluation (Phase 7)."""
    overall_gate: DiagnosticGate = Field(description="Worst-case gate across all expert diagnostics")
    diagnostics: List[ExpertDiagnostic] = Field(description="Symptom-based diagnostic insights")


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

# ─── V3 Default Thresholds (Nut Slots) ───────────────────────────────────────

DEFAULT_NUT_TREBLE_TARGET_MIN_MM = 0.20
DEFAULT_NUT_TREBLE_TARGET_MAX_MM = 0.30
DEFAULT_NUT_BASS_TARGET_MIN_MM = 0.25
DEFAULT_NUT_BASS_TARGET_MAX_MM = 0.40
NUT_YELLOW_TOLERANCE_MM = 0.05

# String names for 6-string guitar (index 0 = string 1 = high E)
STRING_NAMES = ["1 (high E)", "2 (B)", "3 (G)", "4 (D)", "5 (A)", "6 (low E)"]


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


# ─── Nut Slot Evaluator (Phase 5) ────────────────────────────────────────────

def _evaluate_single_nut_slot(
    clearance_mm: float,
    target_min_mm: float,
    target_max_mm: float,
    string_num: int,
    yellow_tolerance: float = NUT_YELLOW_TOLERANCE_MM,
) -> DiagnosticResult:
    """Evaluate a single nut slot clearance measurement."""
    yellow_low = target_min_mm - yellow_tolerance
    yellow_high = target_max_mm + yellow_tolerance
    string_name = STRING_NAMES[string_num - 1] if 1 <= string_num <= 6 else f"{string_num}"

    if target_min_mm <= clearance_mm <= target_max_mm:
        gate = DiagnosticGate.GREEN
        message = f"String {string_name} nut slot clearance is in range."
        probable_causes = []
        recommended_actions = []
        rule_id = f"nut_slot_s{string_num}_in_range"
    elif clearance_mm < yellow_low:
        gate = DiagnosticGate.RED
        message = f"String {string_name} nut slot is too low — open string buzz likely."
        probable_causes = ["Nut slot cut too deep", "Nut wear", "Incorrect previous setup"]
        recommended_actions = ["Nut slot may be cut too deep. Consider filling/repairing slot or replacing nut."]
        rule_id = f"nut_slot_s{string_num}_too_low_severe"
    elif clearance_mm < target_min_mm:
        gate = DiagnosticGate.YELLOW
        message = f"String {string_name} nut slot is slightly low — may buzz on open string."
        probable_causes = ["Nut slot slightly deep", "Minor nut wear"]
        recommended_actions = ["Monitor for buzz. Consider nut repair if buzzing occurs."]
        rule_id = f"nut_slot_s{string_num}_too_low"
    elif clearance_mm > yellow_high:
        gate = DiagnosticGate.RED
        message = f"String {string_name} nut slot is too high — first fret action excessive."
        probable_causes = ["Nut slot not cut deep enough", "New/oversized nut blank", "String not fully seated"]
        recommended_actions = ["Carefully file slot lower and re-measure."]
        rule_id = f"nut_slot_s{string_num}_too_high_severe"
    else:
        gate = DiagnosticGate.YELLOW
        message = f"String {string_name} nut slot is slightly high — first fret may feel stiff."
        probable_causes = ["Nut slot slightly shallow"]
        recommended_actions = ["Consider filing slot slightly lower for easier first-fret play."]
        rule_id = f"nut_slot_s{string_num}_too_high"

    return DiagnosticResult(
        id=rule_id,
        gate=gate,
        message=message,
        measurement=clearance_mm,
        target_min=target_min_mm,
        target_max=target_max_mm,
        probable_causes=probable_causes,
        recommended_actions=recommended_actions,
    )


def evaluate_nut_slots(
    clearances_mm: List[float],
    treble_target_min_mm: float = DEFAULT_NUT_TREBLE_TARGET_MIN_MM,
    treble_target_max_mm: float = DEFAULT_NUT_TREBLE_TARGET_MAX_MM,
    bass_target_min_mm: float = DEFAULT_NUT_BASS_TARGET_MIN_MM,
    bass_target_max_mm: float = DEFAULT_NUT_BASS_TARGET_MAX_MM,
) -> NutWorkflowResponse:
    """
    Evaluate nut slot clearance (first-fret height) for each string.

    Gate logic per string:
        GREEN:  target_min <= clearance <= target_max
        YELLOW: within NUT_YELLOW_TOLERANCE_MM (0.05mm) outside range
        RED:    beyond NUT_YELLOW_TOLERANCE_MM outside range

    Overall gate is worst-case: RED > YELLOW > GREEN.

    V1: Fixed 6-string support. Strings 1-3 (high E, B, G) use treble targets,
    strings 4-6 (D, A, low E) use bass targets.
    TODO: Make string count and treble/bass split configurable for arbitrary string counts.

    Args:
        clearances_mm: List of 6 clearance measurements, index 0 = string 1 (high E)
        treble_target_min_mm: Minimum acceptable treble clearance (default 0.20mm)
        treble_target_max_mm: Maximum acceptable treble clearance (default 0.30mm)
        bass_target_min_mm: Minimum acceptable bass clearance (default 0.25mm)
        bass_target_max_mm: Maximum acceptable bass clearance (default 0.40mm)

    Returns:
        NutWorkflowResponse with overall gate and per-string diagnostics

    Raises:
        ValueError: If clearances_mm does not contain exactly 6 values
    """
    if len(clearances_mm) != 6:
        raise ValueError(f"Expected 6 clearance values, got {len(clearances_mm)}")

    diagnostics = []
    for i, clearance in enumerate(clearances_mm):
        string_num = i + 1  # 1-indexed string number
        # Strings 1-3 are treble, strings 4-6 are bass
        if string_num <= 3:
            target_min = treble_target_min_mm
            target_max = treble_target_max_mm
        else:
            target_min = bass_target_min_mm
            target_max = bass_target_max_mm

        result = _evaluate_single_nut_slot(
            clearance_mm=clearance,
            target_min_mm=target_min,
            target_max_mm=target_max,
            string_num=string_num,
        )
        diagnostics.append(result)

    overall_gate = _worst_gate([d.gate for d in diagnostics])

    return NutWorkflowResponse(
        current_step="nut",
        overall_gate=overall_gate,
        diagnostics=diagnostics,
    )


# ─── Combined Setup Evaluator (Phase 6) ─────────────────────────────────────

def _has_low_diagnostic(diagnostic_ids: List[str]) -> bool:
    """Check if any diagnostic ID indicates a 'too low' condition."""
    return any("too_low" in did for did in diagnostic_ids)


def _has_high_diagnostic(diagnostic_ids: List[str]) -> bool:
    """Check if any diagnostic ID indicates a 'too high' condition."""
    return any("too_high" in did for did in diagnostic_ids)


def evaluate_combined_setup(
    relief_gate: DiagnosticGate,
    relief_diagnostic_ids: List[str],
    action_gate: DiagnosticGate,
    action_diagnostic_ids: List[str],
    nut_gate: DiagnosticGate,
    nut_diagnostic_ids: List[str],
) -> CombinedDiagnosticsResponse:
    """
    Evaluate combined setup diagnostics across Relief, Action, and Nut workflows.

    V1: Hardcoded rules only. No JSON config.

    Rules:
        1. Fret Buzz Likely: relief RED (too low) + action RED/YELLOW (too low)
        2. High Action Compound: action RED (too high) + nut RED (too high)
        3. Nut Dominant: nut RED + relief GREEN + action GREEN/YELLOW
        4. Balanced Setup: all GREEN
        5. Mixed Moderate: 2+ YELLOW across steps, no RED

    Args:
        relief_gate: Overall gate from relief workflow
        relief_diagnostic_ids: List of diagnostic IDs from relief workflow
        action_gate: Overall gate from action workflow
        action_diagnostic_ids: List of diagnostic IDs from action workflow
        nut_gate: Overall gate from nut workflow
        nut_diagnostic_ids: List of diagnostic IDs from nut workflow

    Returns:
        CombinedDiagnosticsResponse with overall gate and cross-step diagnostics
    """
    diagnostics: List[CombinedDiagnostic] = []
    gates = [relief_gate, action_gate, nut_gate]

    relief_low = _has_low_diagnostic(relief_diagnostic_ids)
    action_low = _has_low_diagnostic(action_diagnostic_ids)
    action_high = _has_high_diagnostic(action_diagnostic_ids)
    nut_high = _has_high_diagnostic(nut_diagnostic_ids)

    # Rule 1: Fret Buzz Likely
    # relief = RED (too low) AND action = RED or YELLOW (too low)
    if (
        relief_gate == DiagnosticGate.RED
        and relief_low
        and action_gate in (DiagnosticGate.RED, DiagnosticGate.YELLOW)
        and action_low
    ):
        diagnostics.append(CombinedDiagnostic(
            id="combined_fret_buzz_likely",
            gate=DiagnosticGate.RED,
            message="Likely fret buzz due to low neck relief combined with low string action.",
            contributing_factors=["Relief too low", "Action too low"],
            recommendation="Address relief first by loosening truss rod, then re-evaluate action.",
        ))

    # Rule 2: High Action Compound Issue
    # action = RED (too high) AND nut = RED (too high)
    if (
        action_gate == DiagnosticGate.RED
        and action_high
        and nut_gate == DiagnosticGate.RED
        and nut_high
    ):
        diagnostics.append(CombinedDiagnostic(
            id="combined_high_action_compound",
            gate=DiagnosticGate.RED,
            message="High action is compounded by high nut slots.",
            contributing_factors=["Action too high", "Nut slots too high"],
            recommendation="Address nut slots first, then re-evaluate 12th fret action.",
        ))

    # Rule 3: Nut Dominant Issue
    # nut = RED AND relief = GREEN AND action = GREEN or YELLOW
    if (
        nut_gate == DiagnosticGate.RED
        and relief_gate == DiagnosticGate.GREEN
        and action_gate in (DiagnosticGate.GREEN, DiagnosticGate.YELLOW)
    ):
        diagnostics.append(CombinedDiagnostic(
            id="combined_nut_dominant",
            gate=DiagnosticGate.YELLOW,
            message="Nut slot height is the primary contributor to playability issues.",
            contributing_factors=["Nut slots out of range"],
            recommendation="Focus on adjusting nut slots; neck and saddle setup are acceptable.",
        ))

    # Rule 4: Balanced Setup
    # all steps = GREEN
    if all(g == DiagnosticGate.GREEN for g in gates):
        diagnostics.append(CombinedDiagnostic(
            id="combined_balanced",
            gate=DiagnosticGate.GREEN,
            message="Setup is well balanced across all parameters.",
            contributing_factors=[],
            recommendation="No adjustments needed.",
        ))

    # Rule 5: Mixed Moderate Issues
    # 2+ YELLOW across steps AND no RED
    yellow_count = sum(1 for g in gates if g == DiagnosticGate.YELLOW)
    has_red = any(g == DiagnosticGate.RED for g in gates)
    if yellow_count >= 2 and not has_red:
        contributing = []
        if relief_gate == DiagnosticGate.YELLOW:
            contributing.append("Relief slightly off")
        if action_gate == DiagnosticGate.YELLOW:
            contributing.append("Action slightly off")
        if nut_gate == DiagnosticGate.YELLOW:
            contributing.append("Nut slots slightly off")
        diagnostics.append(CombinedDiagnostic(
            id="combined_mixed_moderate",
            gate=DiagnosticGate.YELLOW,
            message="Multiple moderate setup deviations detected.",
            contributing_factors=contributing,
            recommendation="Consider addressing each parameter incrementally.",
        ))

    # Sort by severity: RED first, then YELLOW, then GREEN
    severity_order = {DiagnosticGate.RED: 0, DiagnosticGate.YELLOW: 1, DiagnosticGate.GREEN: 2}
    diagnostics.sort(key=lambda d: severity_order[d.gate])

    # Overall gate is worst-case across all diagnostics
    if diagnostics:
        overall_gate = diagnostics[0].gate
    else:
        # No rules matched — derive from individual gates
        overall_gate = _worst_gate(gates)

    return CombinedDiagnosticsResponse(
        overall_gate=overall_gate,
        diagnostics=diagnostics,
    )


# ─── Expert Symptom-Based Evaluator (Phase 7) ───────────────────────────────

def evaluate_expert_symptoms(
    symptoms: List[PlayerSymptom],
    relief_gate: DiagnosticGate,
    relief_diagnostic_ids: List[str],
    action_gate: DiagnosticGate,
    action_diagnostic_ids: List[str],
    nut_gate: DiagnosticGate,
    nut_diagnostic_ids: List[str],
) -> ExpertDiagnosticsResponse:
    """
    Evaluate expert diagnostics based on player-reported symptoms and setup measurements.

    V1: One diagnostic per symptom. No symptom-combining.

    Rules:
        1. Open String Buzz: buzz_open_strings + nut too_low → RED
        2. Low Fret Buzz: buzz_low_frets + relief too_low → RED
        3. Middle Fret Buzz: buzz_middle_frets + (relief too_low OR action too_low) → YELLOW/RED
        4. Upper Fret Buzz: buzz_upper_frets + action too_low → YELLOW/RED
        5. First Position Hard: first_position_hard + nut too_high → RED
        6. First Position Sharp: first_position_sharp + nut too_high → YELLOW/RED
        7. Feels Stiff: feels_stiff + (action high OR nut high) → YELLOW
        8. Feels Slinky: feels_slinky + action low → YELLOW
        Fallback: symptom with no strong match → YELLOW, confidence 0.4

    Args:
        symptoms: List of player-reported symptoms
        relief_gate: Overall gate from relief workflow
        relief_diagnostic_ids: Diagnostic IDs from relief workflow
        action_gate: Overall gate from action workflow
        action_diagnostic_ids: Diagnostic IDs from action workflow
        nut_gate: Overall gate from nut workflow
        nut_diagnostic_ids: Diagnostic IDs from nut workflow

    Returns:
        ExpertDiagnosticsResponse with overall gate and per-symptom diagnostics
    """
    diagnostics: List[ExpertDiagnostic] = []

    # Pre-compute directional flags
    relief_low = _has_low_diagnostic(relief_diagnostic_ids)
    relief_high = _has_high_diagnostic(relief_diagnostic_ids)
    action_low = _has_low_diagnostic(action_diagnostic_ids)
    action_high = _has_high_diagnostic(action_diagnostic_ids)
    nut_low = _has_low_diagnostic(nut_diagnostic_ids)
    nut_high = _has_high_diagnostic(nut_diagnostic_ids)

    for symptom in symptoms:
        matched = False

        # Rule 1: Open String Buzz
        if symptom == PlayerSymptom.BUZZ_OPEN_STRINGS and nut_low:
            diagnostics.append(ExpertDiagnostic(
                id="expert_open_string_buzz_nut",
                gate=nut_gate,
                symptom=symptom,
                message="Open string buzz is likely caused by nut slots cut too deep.",
                probable_causes=["Nut slot too deep", "Nut wear", "String not seated properly"],
                recommended_checks=["Inspect nut slot depth for each string", "Check for nut cracks or wear"],
                recommended_actions=["Fill and re-cut nut slots or replace nut"],
                confidence=0.9,
            ))
            matched = True

        # Rule 2: Low Fret Buzz
        if symptom == PlayerSymptom.BUZZ_LOW_FRETS and relief_low:
            diagnostics.append(ExpertDiagnostic(
                id="expert_low_fret_buzz_relief",
                gate=relief_gate,
                symptom=symptom,
                message="Low-fret buzz is likely caused by insufficient neck relief.",
                probable_causes=["Neck too straight or back-bowed", "Truss rod too tight"],
                recommended_checks=["Re-check relief at 7th-9th fret with capo at 1st"],
                recommended_actions=["Loosen truss rod 1/4 turn and re-measure after 24 hours"],
                confidence=0.85,
            ))
            matched = True

        # Rule 3: Middle Fret Buzz
        if symptom == PlayerSymptom.BUZZ_MIDDLE_FRETS and (relief_low or action_low):
            # Inherit gate from the worse of relief/action
            gate = relief_gate if relief_low else action_gate
            if relief_low and action_low:
                gate = _worst_gate([relief_gate, action_gate])
            diagnostics.append(ExpertDiagnostic(
                id="expert_middle_fret_buzz_interaction",
                gate=gate,
                symptom=symptom,
                message="Middle-fret buzz is likely caused by relief/action interaction.",
                probable_causes=["Insufficient relief", "Low action", "Uneven frets in middle region"],
                recommended_checks=["Check relief", "Check action at 12th fret", "Sight neck for twists"],
                recommended_actions=["Address relief first, then action if buzz persists"],
                confidence=0.75,
            ))
            matched = True

        # Rule 4: Upper Fret Buzz
        if symptom == PlayerSymptom.BUZZ_UPPER_FRETS and action_low:
            diagnostics.append(ExpertDiagnostic(
                id="expert_upper_fret_buzz_action",
                gate=action_gate,
                symptom=symptom,
                message="Upper-fret buzz is likely caused by low bridge/saddle action.",
                probable_causes=["Saddle too low", "Upper frets may need leveling"],
                recommended_checks=["Check action at 12th and 17th frets", "Check for high frets near body joint"],
                recommended_actions=["Raise saddle or shim bridge; level frets if necessary"],
                confidence=0.75,
            ))
            matched = True

        # Rule 5: First Position Hard
        if symptom == PlayerSymptom.FIRST_POSITION_HARD and nut_high:
            diagnostics.append(ExpertDiagnostic(
                id="expert_first_position_hard_nut",
                gate=nut_gate,
                symptom=symptom,
                message="First position feels hard to play due to high nut slots.",
                probable_causes=["Nut slots not cut deep enough", "New nut not fully shaped"],
                recommended_checks=["Measure clearance at 1st fret with capo at 3rd"],
                recommended_actions=["Carefully file nut slots to proper depth"],
                confidence=0.9,
            ))
            matched = True

        # Rule 6: First Position Sharp
        if symptom == PlayerSymptom.FIRST_POSITION_SHARP and nut_high:
            diagnostics.append(ExpertDiagnostic(
                id="expert_first_position_sharp_nut",
                gate=nut_gate if nut_gate == DiagnosticGate.RED else DiagnosticGate.YELLOW,
                symptom=symptom,
                message="First position plays sharp due to excessive string stretch from high nut.",
                probable_causes=["Nut slots too high cause extra string stretch when fretting"],
                recommended_checks=["Check intonation at 1st and 12th frets", "Compare open vs fretted pitch"],
                recommended_actions=["Lower nut slots to reduce string stretch"],
                confidence=0.85,
            ))
            matched = True

        # Rule 7: Feels Stiff
        if symptom == PlayerSymptom.FEELS_STIFF and (action_high or nut_high):
            gate = DiagnosticGate.YELLOW
            causes = []
            if action_high:
                causes.append("High action increases finger pressure needed")
            if nut_high:
                causes.append("High nut slots increase first-position effort")
            diagnostics.append(ExpertDiagnostic(
                id="expert_feels_stiff_action_nut",
                gate=gate,
                symptom=symptom,
                message="Guitar feels stiff to play due to high action or nut slots.",
                probable_causes=causes,
                recommended_checks=["Measure action at 12th fret", "Measure nut slot clearance"],
                recommended_actions=["Lower saddle and/or nut slots as needed"],
                confidence=0.7,
            ))
            matched = True

        # Rule 8: Feels Slinky
        if symptom == PlayerSymptom.FEELS_SLINKY and action_low:
            diagnostics.append(ExpertDiagnostic(
                id="expert_feels_slinky_action",
                gate=DiagnosticGate.YELLOW,
                symptom=symptom,
                message="Guitar feels slinky/loose due to low action.",
                probable_causes=["Low action reduces string resistance", "May also indicate light gauge strings"],
                recommended_checks=["Verify action measurements", "Check string gauge"],
                recommended_actions=["Raise saddle slightly if buzz-free playability is desired"],
                confidence=0.6,
            ))
            matched = True

        # Rule: Fretted Notes Buzz (general)
        if symptom == PlayerSymptom.FRETTED_NOTES_BUZZ:
            # This is a general symptom - check multiple causes
            if relief_low or action_low:
                gate = _worst_gate([g for g, low in [(relief_gate, relief_low), (action_gate, action_low)] if low])
                diagnostics.append(ExpertDiagnostic(
                    id="expert_fretted_buzz_general",
                    gate=gate,
                    symptom=symptom,
                    message="Fretted notes buzz, likely due to low relief or action.",
                    probable_causes=["Insufficient relief", "Low action", "Possible fret irregularities"],
                    recommended_checks=["Check relief", "Check action", "Look for worn or lifted frets"],
                    recommended_actions=["Adjust relief first, then action"],
                    confidence=0.7,
                ))
                matched = True

        # Fallback: symptom reported but no strong measurement match
        if not matched:
            diagnostics.append(ExpertDiagnostic(
                id=f"expert_fallback_{symptom.value}",
                gate=DiagnosticGate.YELLOW,
                symptom=symptom,
                message=f"Symptom reported ({symptom.value.replace('_', ' ')}), but measurements do not strongly indicate a cause.",
                probable_causes=["Cause may not be captured by current measurements"],
                recommended_checks=["Verify all measurements are accurate", "Check for fret wear or uneven frets"],
                recommended_actions=["Consider professional fret level/dress if issue persists"],
                confidence=0.4,
            ))

    # Sort by severity (RED > YELLOW > GREEN), then by confidence (descending)
    severity_order = {DiagnosticGate.RED: 0, DiagnosticGate.YELLOW: 1, DiagnosticGate.GREEN: 2}
    diagnostics.sort(key=lambda d: (severity_order[d.gate], -d.confidence))

    # Overall gate is worst-case across all diagnostics
    if diagnostics:
        overall_gate = diagnostics[0].gate
    else:
        overall_gate = DiagnosticGate.GREEN

    return ExpertDiagnosticsResponse(
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
    "NutWorkflowResponse",
    "CombinedDiagnostic",
    "CombinedDiagnosticsResponse",
    "PlayerSymptom",
    "ExpertDiagnostic",
    "ExpertDiagnosticsResponse",
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
    # Nut Slots (Phase 5)
    "evaluate_nut_slots",
    "DEFAULT_NUT_TREBLE_TARGET_MIN_MM",
    "DEFAULT_NUT_TREBLE_TARGET_MAX_MM",
    "DEFAULT_NUT_BASS_TARGET_MIN_MM",
    "DEFAULT_NUT_BASS_TARGET_MAX_MM",
    # Combined (Phase 6)
    "evaluate_combined_setup",
    # Expert (Phase 7)
    "evaluate_expert_symptoms",
]
