"""
AI Graphics Schemas - Ring-Aware AI Suggestions

Extended AI suggestion system with:
- Ring-level feasibility diagnostics
- RMOS feedback loop integration
- Refinement rounds for iterative improvement
- Session-based deduplication support
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple
from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Risk bucket (shared with RMOS)
# ---------------------------------------------------------------------------

class RiskBucket(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


# ---------------------------------------------------------------------------
# Ring-level summary for AI diagnostics
# ---------------------------------------------------------------------------

class AiRingSummary(BaseModel):
    """
    Per-ring feasibility summary for AI feedback loop.
    """
    ring_index: int
    width_mm: float
    risk_bucket: RiskBucket
    utilization_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="How well the ring utilizes material (0-100)"
    )


# ---------------------------------------------------------------------------
# Feasibility snapshot for AI suggestions
# ---------------------------------------------------------------------------

class AiFeasibilitySnapshot(BaseModel):
    """
    Compact feasibility snapshot attached to each AI suggestion.
    Includes ring-level diagnostics for feedback loop.
    """
    overall_score: float = Field(..., ge=0.0, le=100.0)
    risk_bucket: RiskBucket
    estimated_cut_time_min: Optional[float] = None
    material_efficiency: Optional[float] = None

    # Ring-level diagnostics (NEW in L.2+ integration)
    worst_ring_index: Optional[int] = None
    worst_ring_risk: Optional[RiskBucket] = None
    rings: List[AiRingSummary] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Ring parameter spec (for AI-generated designs)
# ---------------------------------------------------------------------------

class RingParam(BaseModel):
    """Single ring parameter within a rosette design."""
    ring_index: int
    width_mm: float = Field(..., gt=0.0, le=50.0)
    material_id: Optional[str] = None
    pattern_type: Optional[str] = None


class RosetteParamSpec(BaseModel):
    """
    Parametric rosette specification for AI generation.
    This is what the AI generates; RMOS validates it.
    """
    outer_diameter_mm: float = Field(..., gt=0.0, le=300.0)
    inner_diameter_mm: float = Field(..., ge=0.0)
    ring_params: List[RingParam] = Field(default_factory=list)
    pattern_type: Optional[str] = "herringbone"
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# AI suggestion models
# ---------------------------------------------------------------------------

class AiRosetteSuggestion(BaseModel):
    """
    Single AI-generated rosette suggestion with feasibility metadata.
    """
    suggestion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    params: RosetteParamSpec
    summary: str = ""
    notes: Optional[str] = None
    feasibility: Optional[AiFeasibilitySnapshot] = None
    ai_score: float = Field(default=0.0, ge=0.0, le=100.0)
    recommended: bool = True  # False if any ring is RED


class AiRosetteSuggestionBatch(BaseModel):
    """Batch of AI suggestions returned from the suggester."""
    suggestions: List[AiRosetteSuggestion] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# AI prompt input with refinement controls
# ---------------------------------------------------------------------------

class AiRosettePromptInput(BaseModel):
    """
    Input for AI rosette suggestion requests.
    
    Includes:
    - Basic prompt and count
    - Material/tool preset IDs for RMOS context
    - Refinement controls for feedback loop
    - Session ID for deduplication
    """
    prompt: str = Field(..., min_length=1, max_length=2000)
    count: int = Field(default=3, ge=1, le=10)
    
    # RMOS context (optional, for feasibility scoring)
    material_preset_id: Optional[str] = None
    tool_preset_id: Optional[str] = None
    
    # Refinement controls (NEW)
    refine_rounds: int = Field(
        default=0,
        ge=0,
        le=3,
        description="Number of RMOS-feedback refinement passes (0-3)"
    )
    target_min_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Target minimum score for refinement passes"
    )
    
    # Session deduplication (NEW)
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for tracking explored designs"
    )


# ---------------------------------------------------------------------------
# Scoring helper
# ---------------------------------------------------------------------------

def score_suggestion_from_feasibility(snap: AiFeasibilitySnapshot) -> float:
    """
    Compute AI score from feasibility snapshot.
    
    Scoring rules:
    - Base: overall_score
    - Penalty: -10 per YELLOW ring, -25 per RED ring
    - Bonus: +5 for high material efficiency (>80%)
    """
    if snap is None:
        return 50.0  # Neutral score if no feasibility data
    
    score = snap.overall_score
    
    # Ring penalties
    for ring in snap.rings:
        if ring.risk_bucket == RiskBucket.YELLOW:
            score -= 10.0
        elif ring.risk_bucket == RiskBucket.RED:
            score -= 25.0
    
    # Efficiency bonus
    if snap.material_efficiency and snap.material_efficiency > 0.80:
        score += 5.0
    
    # Clamp to valid range
    return max(0.0, min(100.0, score))


# ---------------------------------------------------------------------------
# Mutation helper for refinement loop
# ---------------------------------------------------------------------------

def mutate_design_from_feasibility(
    spec: RosetteParamSpec,
    snap: AiFeasibilitySnapshot,
    tool_diameter_mm: float = 3.175,
) -> RosetteParamSpec:
    """
    Create a "safer" variant of a design based on ring diagnostics.
    
    Rules:
    - RED rings: increase width by ~50% of tool diameter
    - YELLOW rings: increase width by ~25% of tool diameter
    - Keeps outer diameter fixed; widens inward
    
    This does NOT touch geometry or CAM; just adjusts parametric ring widths.
    """
    # Deep copy to avoid mutating original
    new_spec = spec.model_copy(deep=True)
    
    if tool_diameter_mm <= 0:
        return new_spec
    
    if not snap.rings:
        return new_spec
    
    # Find problematic rings
    problematic = [r for r in snap.rings if r.risk_bucket in (RiskBucket.YELLOW, RiskBucket.RED)]
    if not problematic:
        return new_spec
    
    # Map ring_index → ring param
    ring_map = {rp.ring_index: rp for rp in new_spec.ring_params}
    
    for rd in problematic:
        if rd.ring_index not in ring_map:
            continue
        
        rp = ring_map[rd.ring_index]
        current_width = float(rp.width_mm or 0.0)
        
        if rd.risk_bucket == RiskBucket.RED:
            delta = 0.5 * tool_diameter_mm  # Aggressive widen
        else:
            delta = 0.25 * tool_diameter_mm  # Moderate widen
        
        rp.width_mm = max(current_width, current_width + delta)
    
    return new_spec
