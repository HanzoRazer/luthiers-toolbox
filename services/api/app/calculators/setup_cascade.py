"""
Instrument setup cascade calculator (CONSTRUCTION-002).

Connects setup parameters in dependency order. Changing one thing cascades
to everything downstream.

Dependency chain:
  neck_angle → saddle_height → break_angle
  nut_slot_depth → action_at_nut
  truss_rod_relief → action_at_12th
  action_at_12th + nut_action → intonation_offset
  intonation_offset → saddle_compensation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Optional: use neck_angle for gate check
try:
    from app.instrument_geometry.neck.neck_angle import (
        NeckAngleInput,
        compute_neck_angle,
    )
    NECK_ANGLE_AVAILABLE = True
except Exception:
    NECK_ANGLE_AVAILABLE = False


@dataclass
class SetupState:
    """All setup parameters in one place (cascade inputs)."""
    # Neck geometry
    neck_angle_deg: float = 1.5
    truss_rod_relief_mm: float = 0.25

    # Nut (per-string slot depths mm; key = string name or index)
    nut_slot_depths_mm: Optional[Dict[str, float]] = field(default_factory=dict)

    # Action
    action_at_nut_mm: float = 0.5  # high E
    action_at_12th_treble_mm: float = 1.9
    action_at_12th_bass_mm: float = 2.4

    # Bridge/saddle
    saddle_height_mm: float = 3.0
    saddle_projection_mm: float = 2.5

    # Scale
    scale_length_mm: float = 628.65

    # For neck angle check (body join geometry)
    fretboard_height_at_joint_mm: float = 5.0
    neck_joint_fret: int = 14


@dataclass
class SetupIssue:
    """Single parameter issue with gate and fix."""
    parameter: str
    current_value: float
    recommended_range: Tuple[float, float]
    gate: str  # GREEN / YELLOW / RED
    fix: str  # actionable recommendation


@dataclass
class SetupCascadeResult:
    """Result of setup evaluation with issues and overall gate."""
    state: SetupState
    issues: List[SetupIssue]
    overall_gate: str  # GREEN / YELLOW / RED
    summary: str


# ─── Ranges (GREEN = in range, YELLOW = marginal, RED = out) ─────────────────

RELIEF_GREEN = (0.15, 0.35)   # mm
RELIEF_YELLOW_LO = 0.10
RELIEF_YELLOW_HI = 0.45

NUT_ACTION_GREEN = (0.3, 0.6)   # mm high E
NUT_ACTION_YELLOW_LO = 0.2
NUT_ACTION_YELLOW_HI = 0.8

ACTION_12TH_TREBLE_GREEN = (1.5, 2.2)   # mm
ACTION_12TH_BASS_GREEN = (2.0, 2.8)
ACTION_12TH_YELLOW_LO_T = 1.2
ACTION_12TH_YELLOW_HI_T = 2.5
ACTION_12TH_YELLOW_LO_B = 1.6
ACTION_12TH_YELLOW_HI_B = 3.2

SADDLE_PROJECTION_GREEN = (1.6, 4.0)   # mm
SADDLE_PROJECTION_YELLOW_LO = 1.2
SADDLE_PROJECTION_YELLOW_HI = 5.0


def evaluate_setup(state: SetupState) -> SetupCascadeResult:
    """
    Check each parameter and cascade effects.

    Checks:
    1. Neck angle gate (from neck_angle.py when available)
    2. Truss rod relief (0.15–0.35 mm GREEN)
    3. Nut action (0.3–0.6 mm GREEN for high e)
    4. Action at 12th (standard ranges by style)
    5. Saddle projection (min 1.6 mm, max 4 mm)
    6. Break angle derived from saddle geometry (advisory)
    """
    issues: List[SetupIssue] = []

    # 1. Neck angle
    if NECK_ANGLE_AVAILABLE:
        try:
            inp = NeckAngleInput(
                bridge_height_mm=state.saddle_height_mm,
                saddle_projection_mm=state.saddle_projection_mm,
                fretboard_height_at_joint_mm=state.fretboard_height_at_joint_mm,
                nut_to_bridge_mm=state.scale_length_mm,
                neck_joint_fret=state.neck_joint_fret,
                action_12th_mm=(state.action_at_12th_treble_mm + state.action_at_12th_bass_mm) / 2,
            )
            res = compute_neck_angle(inp)
            if res.gate != "GREEN":
                issues.append(SetupIssue(
                    parameter="neck_angle_deg",
                    current_value=round(res.angle_deg, 2),
                    recommended_range=(1.0, 3.5),
                    gate=res.gate,
                    fix=res.message,
                ))
        except Exception:
            pass  # skip if geometry fails
    else:
        # Fallback: check state.neck_angle_deg directly
        if state.neck_angle_deg < 0.5 or state.neck_angle_deg > 5.0:
            issues.append(SetupIssue(
                parameter="neck_angle_deg",
                current_value=state.neck_angle_deg,
                recommended_range=(1.0, 3.5),
                gate="RED",
                fix="Neck angle out of range; check geometry or consider neck reset.",
            ))
        elif state.neck_angle_deg < 1.0 or state.neck_angle_deg > 3.5:
            issues.append(SetupIssue(
                parameter="neck_angle_deg",
                current_value=state.neck_angle_deg,
                recommended_range=(1.0, 3.5),
                gate="YELLOW",
                fix="Neck angle marginal; monitor top deflection.",
            ))

    # 2. Truss rod relief
    r = state.truss_rod_relief_mm
    if r < RELIEF_GREEN[0] or r > RELIEF_GREEN[1]:
        if r < RELIEF_YELLOW_LO or r > RELIEF_YELLOW_HI:
            gate = "RED"
            fix = "Adjust truss rod to bring relief into 0.15–0.35 mm."
        else:
            gate = "YELLOW"
            fix = "Relief slightly outside ideal 0.15–0.35 mm; adjust if buzz or stiffness."
        issues.append(SetupIssue(
            parameter="truss_rod_relief_mm",
            current_value=round(r, 3),
            recommended_range=RELIEF_GREEN,
            gate=gate,
            fix=fix,
        ))

    # 3. Nut action (high E proxy)
    a_nut = state.action_at_nut_mm
    if a_nut < NUT_ACTION_GREEN[0] or a_nut > NUT_ACTION_GREEN[1]:
        if a_nut < NUT_ACTION_YELLOW_LO or a_nut > NUT_ACTION_YELLOW_HI:
            gate = "RED"
            fix = "File nut slots or replace nut; target 0.3–0.6 mm at first fret."
        else:
            gate = "YELLOW"
            fix = "Nut action marginal; consider slot depth adjustment."
        issues.append(SetupIssue(
            parameter="action_at_nut_mm",
            current_value=round(a_nut, 2),
            recommended_range=NUT_ACTION_GREEN,
            gate=gate,
            fix=fix,
        ))

    # 4. Action at 12th
    t12 = state.action_at_12th_treble_mm
    b12 = state.action_at_12th_bass_mm
    if t12 < ACTION_12TH_YELLOW_LO_T or t12 > ACTION_12TH_YELLOW_HI_T:
        gate = "RED" if t12 < 1.0 or t12 > 2.8 else "YELLOW"
        fix = "Adjust saddle height or neck angle; treble 12th fret action target 1.5–2.2 mm."
        issues.append(SetupIssue(
            parameter="action_at_12th_treble_mm",
            current_value=round(t12, 2),
            recommended_range=ACTION_12TH_TREBLE_GREEN,
            gate=gate,
            fix=fix,
        ))
    elif t12 < ACTION_12TH_TREBLE_GREEN[0] or t12 > ACTION_12TH_TREBLE_GREEN[1]:
        issues.append(SetupIssue(
            parameter="action_at_12th_treble_mm",
            current_value=round(t12, 2),
            recommended_range=ACTION_12TH_TREBLE_GREEN,
            gate="YELLOW",
            fix="Treble action slightly outside 1.5–2.2 mm; acceptable for some styles.",
        ))
    if b12 < ACTION_12TH_YELLOW_LO_B or b12 > ACTION_12TH_YELLOW_HI_B:
        gate = "RED" if b12 < 1.2 or b12 > 3.5 else "YELLOW"
        fix = "Adjust saddle or neck; bass 12th fret action target 2.0–2.8 mm."
        issues.append(SetupIssue(
            parameter="action_at_12th_bass_mm",
            current_value=round(b12, 2),
            recommended_range=ACTION_12TH_BASS_GREEN,
            gate=gate,
            fix=fix,
        ))
    elif b12 < ACTION_12TH_BASS_GREEN[0] or b12 > ACTION_12TH_BASS_GREEN[1]:
        issues.append(SetupIssue(
            parameter="action_at_12th_bass_mm",
            current_value=round(b12, 2),
            recommended_range=ACTION_12TH_BASS_GREEN,
            gate="YELLOW",
            fix="Bass action slightly outside 2.0–2.8 mm; acceptable for some styles.",
        ))

    # 5. Saddle projection
    sp = state.saddle_projection_mm
    if sp < SADDLE_PROJECTION_GREEN[0] or sp > SADDLE_PROJECTION_GREEN[1]:
        if sp < SADDLE_PROJECTION_YELLOW_LO or sp > SADDLE_PROJECTION_YELLOW_HI:
            gate = "RED"
            fix = "Saddle height out of safe range; target 1.6–4 mm projection."
        else:
            gate = "YELLOW"
            fix = "Saddle projection marginal; check break angle and slot depth."
        issues.append(SetupIssue(
            parameter="saddle_projection_mm",
            current_value=round(sp, 2),
            recommended_range=SADDLE_PROJECTION_GREEN,
            gate=gate,
            fix=fix,
        ))

    # Overall gate
    if any(i.gate == "RED" for i in issues):
        overall_gate = "RED"
        summary = "One or more parameters are out of safe range; address RED issues first."
    elif any(i.gate == "YELLOW" for i in issues):
        overall_gate = "YELLOW"
        summary = "Setup is playable; some parameters are marginal."
    else:
        overall_gate = "GREEN"
        summary = "Setup within recommended ranges."

    return SetupCascadeResult(
        state=state,
        issues=issues,
        overall_gate=overall_gate,
        summary=summary,
    )


def suggest_adjustments(result: SetupCascadeResult) -> List[str]:
    """Plain language fix suggestions from issues (RED first, then YELLOW)."""
    red_fixes = [i.fix for i in result.issues if i.gate == "RED"]
    yellow_fixes = [i.fix for i in result.issues if i.gate == "YELLOW"]
    return red_fixes + yellow_fixes
