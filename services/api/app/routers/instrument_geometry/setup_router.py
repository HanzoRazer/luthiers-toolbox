"""
Setup Cascade Router — Instrument setup evaluation.

Endpoints:
- POST /setup/evaluate — Evaluate instrument setup

Total: 1 endpoint
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.setup_cascade import (
    SetupState,
    evaluate_setup,
    suggest_adjustments,
)

router = APIRouter(tags=["instrument-geometry", "setup"])


# ─── Models ────────────────────────────────────────────────────────────────────

class SetupStateRequest(BaseModel):
    """Request body for setup cascade evaluation."""
    neck_angle_deg: float = Field(default=1.5, description="Neck angle (degrees)")
    truss_rod_relief_mm: float = Field(default=0.25, description="Relief at 7th fret (mm)")
    nut_slot_depths_mm: Optional[Dict[str, float]] = Field(default_factory=dict)
    action_at_nut_mm: float = Field(default=0.5, description="High E at nut (mm)")
    action_at_12th_treble_mm: float = Field(default=1.9, description="Treble 12th (mm)")
    action_at_12th_bass_mm: float = Field(default=2.4, description="Bass 12th (mm)")
    saddle_height_mm: float = Field(default=3.0)
    saddle_projection_mm: float = Field(default=2.5)
    scale_length_mm: float = Field(default=628.65)
    fretboard_height_at_joint_mm: float = Field(default=5.0)
    neck_joint_fret: int = Field(default=14)


class SetupIssueResponse(BaseModel):
    """Single setup issue for API response."""
    parameter: str
    current_value: float
    recommended_range: List[float]  # [min, max]
    gate: str
    fix: str


class SetupCascadeResponse(BaseModel):
    """Response from setup cascade evaluation."""
    state: Dict[str, Any]  # serialized SetupState fields
    issues: List[SetupIssueResponse]
    overall_gate: str
    summary: str
    suggestions: List[str] = Field(default_factory=list)


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/setup/evaluate",
    response_model=SetupCascadeResponse,
    summary="Evaluate instrument setup (CONSTRUCTION-002)",
    description="""
    Run setup cascade: check neck angle, relief, nut action, 12th fret action,
    saddle projection. Returns GREEN/YELLOW/RED per parameter and overall,
    plus plain-language fix suggestions.
    """,
)
def evaluate_instrument_setup(req: SetupStateRequest) -> SetupCascadeResponse:
    """Evaluate setup state and return cascade result with issues and suggestions."""
    state = SetupState(
        neck_angle_deg=req.neck_angle_deg,
        truss_rod_relief_mm=req.truss_rod_relief_mm,
        nut_slot_depths_mm=req.nut_slot_depths_mm or {},
        action_at_nut_mm=req.action_at_nut_mm,
        action_at_12th_treble_mm=req.action_at_12th_treble_mm,
        action_at_12th_bass_mm=req.action_at_12th_bass_mm,
        saddle_height_mm=req.saddle_height_mm,
        saddle_projection_mm=req.saddle_projection_mm,
        scale_length_mm=req.scale_length_mm,
        fretboard_height_at_joint_mm=req.fretboard_height_at_joint_mm,
        neck_joint_fret=req.neck_joint_fret,
    )
    result = evaluate_setup(state)
    # Serialize state as dict (simple fields only)
    state_dict = {
        "neck_angle_deg": state.neck_angle_deg,
        "truss_rod_relief_mm": state.truss_rod_relief_mm,
        "action_at_nut_mm": state.action_at_nut_mm,
        "action_at_12th_treble_mm": state.action_at_12th_treble_mm,
        "action_at_12th_bass_mm": state.action_at_12th_bass_mm,
        "saddle_height_mm": state.saddle_height_mm,
        "saddle_projection_mm": state.saddle_projection_mm,
        "scale_length_mm": state.scale_length_mm,
    }
    issues_resp = [
        SetupIssueResponse(
            parameter=i.parameter,
            current_value=i.current_value,
            recommended_range=list(i.recommended_range),
            gate=i.gate,
            fix=i.fix,
        )
        for i in result.issues
    ]
    suggestions = suggest_adjustments(result)
    return SetupCascadeResponse(
        state=state_dict,
        issues=issues_resp,
        overall_gate=result.overall_gate,
        summary=result.summary,
        suggestions=suggestions,
    )


__all__ = ["router"]
