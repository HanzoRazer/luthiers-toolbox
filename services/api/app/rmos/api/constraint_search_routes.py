# services/api/app/rmos/api/constraint_search_routes.py
"""
Constraint-First Search API routes for RMOS 2.0.

Provides endpoint for generating feasible rosette designs from operator constraints.

Part of Directional Workflow 2.0 (Mode B: Constraint-First).
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..api_contracts import RiskBucket
from ..services.constraint_search import (
    ConstraintSearchParams,
    ConstraintSearchResult,
    search_constraint_first,
    RosetteParamSpec,
)

router = APIRouter(tags=["RMOS Constraint Search"])


class ConstraintSearchRequest(BaseModel):
    """
    Request body for constraint-first search.
    
    Operator specifies:
    - Material and tool to use
    - Diameter range for designs
    - Optional ring count range
    - Optional production constraints (cut time, waste)
    """
    
    material_id: str = Field(
        ...,
        description="Material identifier (e.g., 'mahogany', 'ebony')"
    )
    tool_id: str = Field(
        ...,
        description="Tool identifier (e.g., 'router:6_2_6.35', 'saw:10_24_3.0')"
    )
    
    outer_diameter_mm_min: float = Field(
        80.0,
        ge=20.0,
        le=500.0,
        description="Minimum outer diameter (mm)"
    )
    outer_diameter_mm_max: float = Field(
        120.0,
        ge=20.0,
        le=500.0,
        description="Maximum outer diameter (mm)"
    )
    
    ring_count_min: int = Field(
        1,
        ge=1,
        le=10,
        description="Minimum number of rings"
    )
    ring_count_max: int = Field(
        4,
        ge=1,
        le=10,
        description="Maximum number of rings"
    )
    
    max_candidates: int = Field(
        12,
        ge=1,
        le=50,
        description="Maximum number of designs to return"
    )
    max_trials: int = Field(
        40,
        ge=10,
        le=200,
        description="Maximum designs to evaluate before stopping"
    )
    
    max_cut_time_min: Optional[float] = Field(
        None,
        ge=0.1,
        description="Maximum acceptable cut time (minutes)"
    )
    waste_tolerance: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Maximum acceptable waste fraction (0-1)"
    )


class FeasibilitySnapshot(BaseModel):
    """Snapshot of feasibility result for API response."""
    
    score: float = Field(..., description="Feasibility score 0-100")
    risk_bucket: str = Field(..., description="Risk level: GREEN, YELLOW, RED")
    efficiency: float = Field(..., description="Material efficiency 0-1")
    estimated_cut_time_seconds: float = Field(..., description="Estimated cut time")
    warnings: List[str] = Field(default_factory=list, description="Warnings")


class ConstraintSearchCandidate(BaseModel):
    """Single candidate in search response."""
    
    rank: int = Field(..., description="Rank by score (1 = best)")
    design: Dict[str, Any] = Field(..., description="RosetteParamSpec as dict")
    feasibility: FeasibilitySnapshot = Field(..., description="Feasibility result")


class ConstraintSearchResponse(BaseModel):
    """Response from constraint-first search."""
    
    candidates: List[ConstraintSearchCandidate] = Field(
        default_factory=list,
        description="Feasible design candidates, sorted by score"
    )
    total_trials: int = Field(..., description="Number of designs evaluated")
    total_passed: int = Field(..., description="Number passing constraints")


@router.post("/search", response_model=ConstraintSearchResponse)
async def search_designs(request: ConstraintSearchRequest) -> ConstraintSearchResponse:
    """
    Search for feasible rosette designs given operator constraints.
    
    This endpoint implements Mode B (Constraint-First) of Directional Workflow 2.0:
    1. Takes production constraints as input
    2. Generates candidate designs within bounds
    3. Evaluates each through RMOS feasibility scoring
    4. Returns ranked list of feasible designs
    
    Use cases:
    - Production planning: "What rosettes can I make with this material/tool?"
    - Batch optimization: "Generate designs that meet my time/waste targets"
    - Learning: "Show me what parameters work for these constraints"
    """
    
    # Validate diameter range
    if request.outer_diameter_mm_min > request.outer_diameter_mm_max:
        raise HTTPException(
            status_code=400,
            detail="outer_diameter_mm_min must be <= outer_diameter_mm_max"
        )
    
    # Validate ring count range
    if request.ring_count_min > request.ring_count_max:
        raise HTTPException(
            status_code=400,
            detail="ring_count_min must be <= ring_count_max"
        )
    
    # Build search params
    params = ConstraintSearchParams(
        material_id=request.material_id,
        tool_id=request.tool_id,
        outer_diameter_mm_min=request.outer_diameter_mm_min,
        outer_diameter_mm_max=request.outer_diameter_mm_max,
        ring_count_min=request.ring_count_min,
        ring_count_max=request.ring_count_max,
        max_candidates=request.max_candidates,
        max_trials=request.max_trials,
        max_cut_time_min=request.max_cut_time_min,
        waste_tolerance=request.waste_tolerance,
    )
    
    # Run search
    try:
        results = search_constraint_first(params)
    except HTTPException:
        raise  # WP-1: pass through HTTPException
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    
    # Convert to response format
    candidates = []
    for result in results:
        # Convert design to dict
        if hasattr(result.design, 'dict'):
            design_dict = result.design.dict()
        elif hasattr(result.design, 'model_dump'):
            design_dict = result.design.model_dump()
        else:
            design_dict = {
                "outer_diameter_mm": result.design.outer_diameter_mm,
                "inner_diameter_mm": result.design.inner_diameter_mm,
                "ring_params": [
                    {"ring_index": r.ring_index, "width_mm": r.width_mm, "tile_length_mm": r.tile_length_mm}
                    for r in result.design.ring_params
                ],
                "depth_mm": getattr(result.design, 'depth_mm', 3.0)
            }
        
        candidates.append(ConstraintSearchCandidate(
            rank=result.rank,
            design=design_dict,
            feasibility=FeasibilitySnapshot(
                score=result.feasibility.score,
                risk_bucket=result.feasibility.risk_bucket.value if hasattr(result.feasibility.risk_bucket, 'value') else str(result.feasibility.risk_bucket),
                efficiency=result.feasibility.efficiency,
                estimated_cut_time_seconds=result.feasibility.estimated_cut_time_seconds,
                warnings=result.feasibility.warnings,
            )
        ))
    
    return ConstraintSearchResponse(
        candidates=candidates,
        total_trials=params.max_trials,
        total_passed=len(results),
    )
