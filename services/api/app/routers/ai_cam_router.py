"""
AI-CAM Router (Wave 11)

FastAPI endpoints for:
- CAM operation analysis
- G-code explanation
- Parameter optimization
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..ai_cam.advisor import CAMAdvisor
from ..ai_cam.explain_gcode import GCodeExplainer
from ..ai_cam.optimize import CAMOptimizer


router = APIRouter(prefix="/ai-cam", tags=["AI-CAM"])


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class CutOperationPayload(BaseModel):
    """Payload for cut operation analysis."""
    tool_id: str = Field(..., description="Tool identifier")
    material_id: str = Field(..., description="Material identifier")
    tool_kind: str = Field(..., description="Tool type: 'router_bit' or 'saw_blade'")
    feed_mm_min: float = Field(..., gt=0, description="Feed rate in mm/min")
    rpm: float = Field(..., gt=0, description="Spindle speed in RPM")
    depth_of_cut_mm: float = Field(..., gt=0, description="Depth of cut in mm")
    width_of_cut_mm: Optional[float] = Field(None, gt=0, description="Width of cut in mm")
    machine_id: Optional[str] = Field(None, description="Machine profile ID")


class GCodePayload(BaseModel):
    """Payload for G-code explanation."""
    gcode_text: str = Field(..., description="Raw G-code text to explain")
    safe_z: float = Field(5.0, description="Z height considered safe (mm)")


class OptimizePayload(BaseModel):
    """Payload for parameter optimization."""
    tool_id: str
    material_id: str
    tool_kind: str
    feed_mm_min: float = Field(..., gt=0)
    rpm: float = Field(..., gt=0)
    depth_of_cut_mm: float = Field(..., gt=0)
    width_of_cut_mm: Optional[float] = Field(None, gt=0)
    machine_id: Optional[str] = None
    search_pct: float = Field(0.10, ge=0.01, le=0.50, description="Search range (0.10 = ±10%)")


class AdvisoryResponse(BaseModel):
    """Single advisory in response."""
    message: str
    severity: str
    context: Optional[Dict[str, Any]] = None


class AnalyzeResponse(BaseModel):
    """Response from analyze-operation endpoint."""
    advisories: List[AdvisoryResponse]
    recommended_changes: Dict[str, Any]
    physics: Dict[str, Any]


class GCodeLineResponse(BaseModel):
    """Single G-code line explanation."""
    line_number: int
    raw: str
    explanation: str
    risk: Optional[str] = None


class ExplainGCodeResponse(BaseModel):
    """Response from explain-gcode endpoint."""
    overall_risk: str
    explanations: List[GCodeLineResponse]


class OptimizationCandidateResponse(BaseModel):
    """Single optimization candidate."""
    feed_mm_min: float
    rpm: float
    depth_of_cut_mm: float
    width_of_cut_mm: Optional[float]
    score: float
    physics: Dict[str, Any]
    notes: List[str]


class OptimizeResponse(BaseModel):
    """Response from optimize endpoint."""
    candidates: List[OptimizationCandidateResponse]
    best: Optional[OptimizationCandidateResponse] = None


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/analyze-operation", response_model=AnalyzeResponse)
def analyze_operation(payload: CutOperationPayload) -> AnalyzeResponse:
    """
    Analyze a cut operation and return physics-based advisories.
    
    Uses the Calculator Spine to evaluate:
    - Chipload range
    - Heat risk
    - Tool deflection
    - Kickback (for saw operations)
    
    Returns advisories with severity levels and recommended parameter changes.
    """
    advisor = CAMAdvisor()
    result = advisor.analyze_operation(
        tool_id=payload.tool_id,
        material_id=payload.material_id,
        tool_kind=payload.tool_kind,
        feed_mm_min=payload.feed_mm_min,
        rpm=payload.rpm,
        depth_of_cut_mm=payload.depth_of_cut_mm,
        width_of_cut_mm=payload.width_of_cut_mm,
        machine_id=payload.machine_id,
    )
    
    return AnalyzeResponse(
        advisories=[
            AdvisoryResponse(
                message=a.message,
                severity=a.severity,
                context=a.context,
            )
            for a in result.advisories
        ],
        recommended_changes=result.recommended_changes,
        physics=result.physics_results,
    )


@router.post("/explain-gcode", response_model=ExplainGCodeResponse)
def explain_gcode(payload: GCodePayload) -> ExplainGCodeResponse:
    """
    Explain G-code line by line.
    
    Analyzes:
    - Motion commands (G0, G1, G2, G3)
    - Coordinate changes
    - Z-height safety
    - Feed rate changes
    - Spindle state
    
    Returns explanations with risk annotations.
    """
    if not payload.gcode_text.strip():
        raise HTTPException(status_code=400, detail="G-code text cannot be empty")
    
    explainer = GCodeExplainer(safe_z=payload.safe_z)
    result = explainer.explain_gcode(payload.gcode_text)
    
    return ExplainGCodeResponse(
        overall_risk=result.overall_risk,
        explanations=[
            GCodeLineResponse(
                line_number=e.line_number,
                raw=e.raw,
                explanation=e.explanation,
                risk=e.risk,
            )
            for e in result.explanations
        ],
    )


@router.post("/optimize", response_model=OptimizeResponse)
def optimize_parameters(payload: OptimizePayload) -> OptimizeResponse:
    """
    Search for optimized cutting parameters.
    
    Explores ±search_pct variations in feed and RPM to find
    combinations with better physics outcomes.
    
    Returns ranked candidates with scores and physics evaluations.
    """
    optimizer = CAMOptimizer(search_pct=payload.search_pct)
    candidates = optimizer.search(
        tool_id=payload.tool_id,
        material_id=payload.material_id,
        tool_kind=payload.tool_kind,
        feed_mm_min=payload.feed_mm_min,
        rpm=payload.rpm,
        depth_of_cut_mm=payload.depth_of_cut_mm,
        width_of_cut_mm=payload.width_of_cut_mm,
        machine_id=payload.machine_id,
    )
    
    candidate_responses = [
        OptimizationCandidateResponse(
            feed_mm_min=c.feed_mm_min,
            rpm=c.rpm,
            depth_of_cut_mm=c.depth_of_cut_mm,
            width_of_cut_mm=c.width_of_cut_mm,
            score=c.score,
            physics=c.physics,
            notes=c.notes,
        )
        for c in candidates
    ]
    
    best = candidate_responses[0] if candidate_responses and candidate_responses[0].score > 0 else None
    
    return OptimizeResponse(
        candidates=candidate_responses,
        best=best,
    )


@router.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "module": "ai-cam", "version": "wave-11"}
