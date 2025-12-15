# services/api/app/rmos/services/constraint_search.py
"""
Constraint-First Search Service for RMOS 2.0.

Given operator constraints, proposes feasible rosette designs by:
1. Generating candidate designs within parameter ranges
2. Evaluating each through RMOS feasibility scoring
3. Returning filtered, ranked results

Part of Directional Workflow 2.0 (Mode B: Constraint-First).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

from ..api_contracts import RmosContext, RmosFeasibilityResult, RiskBucket


# Fallback RosetteParamSpec if art_studio not available
class RosetteRingParam(BaseModel):
    """Single ring parameter specification."""
    ring_index: int = 0
    width_mm: float = 2.0
    tile_length_mm: Optional[float] = None


class RosetteParamSpec(BaseModel):
    """Rosette design parameters (local fallback)."""
    outer_diameter_mm: float = 100.0
    inner_diameter_mm: float = 90.0
    ring_params: List[RosetteRingParam] = Field(default_factory=list)
    depth_mm: float = 3.0


# Try to import real schemas
try:
    from ...art_studio.schemas import RosetteParamSpec as ArtStudioRosetteParamSpec
    RosetteParamSpec = ArtStudioRosetteParamSpec  # type: ignore
except ImportError:
    pass  # Use local fallback


@dataclass
class ConstraintSearchParams:
    """
    Operator/production constraints for Mode B (Constraint-First) search.
    
    This is a lightweight container used by the internal search routine.
    """
    material_id: str
    tool_id: str
    
    outer_diameter_mm_min: float
    outer_diameter_mm_max: float
    
    ring_count_min: int = 1
    ring_count_max: int = 4
    
    max_candidates: int = 12  # how many designs to *return*
    max_trials: int = 40      # how many designs to *evaluate* before stopping
    
    max_cut_time_min: Optional[float] = None
    waste_tolerance: Optional[float] = None


@dataclass
class ConstraintSearchResult:
    """
    A single candidate from constraint-first search.
    """
    design: RosetteParamSpec
    feasibility: RmosFeasibilityResult
    rank: int = 0


def _generate_candidate_design(
    idx: int,
    params: ConstraintSearchParams,
) -> RosetteParamSpec:
    """
    Generate a single candidate design within the constraint bounds.
    
    Uses deterministic seeding based on idx for reproducibility.
    """
    random.seed(idx * 1337)
    
    # Random outer diameter within range
    outer_d = random.uniform(
        params.outer_diameter_mm_min,
        params.outer_diameter_mm_max
    )
    
    # Inner diameter: 85-95% of outer
    inner_ratio = random.uniform(0.85, 0.95)
    inner_d = outer_d * inner_ratio
    
    # Ring count within bounds
    ring_count = random.randint(params.ring_count_min, params.ring_count_max)
    
    # Generate ring params
    ring_width = (outer_d - inner_d) / (2 * ring_count) if ring_count > 0 else 2.0
    ring_params = []
    for i in range(ring_count):
        ring_params.append(RosetteRingParam(
            ring_index=i,
            width_mm=round(ring_width, 2),
            tile_length_mm=round(ring_width * random.uniform(1.2, 2.0), 2)
        ))
    
    return RosetteParamSpec(
        outer_diameter_mm=round(outer_d, 2),
        inner_diameter_mm=round(inner_d, 2),
        ring_params=ring_params,
        depth_mm=3.0
    )


def _evaluate_candidate(
    design: RosetteParamSpec,
    params: ConstraintSearchParams,
) -> RmosFeasibilityResult:
    """
    Evaluate a candidate design through RMOS feasibility scoring.
    """
    from ..feasibility_scorer import score_design_feasibility
    from ..logs import log_feasibility_event
    
    # Build context from search params
    ctx = RmosContext(
        material_id=params.material_id,
        tool_id=params.tool_id,
        max_cut_time_min=params.max_cut_time_min,
    )
    
    # Score using constraint_first workflow mode
    result = score_design_feasibility(
        design,
        ctx,
        workflow_mode="constraint_first"
    )
    
    # Log the evaluation
    try:
        log_feasibility_event(
            source="constraint_search",
            mode="constraint_first",
            design=design,
            context=ctx,
            result=result,
        )
    except Exception:
        pass  # Don't fail search if logging fails
    
    return result


def _passes_constraints(
    result: RmosFeasibilityResult,
    params: ConstraintSearchParams,
) -> bool:
    """
    Check if a feasibility result passes the search constraints.
    """
    # Must not be RED risk
    if result.risk_bucket == RiskBucket.RED:
        return False
    
    # Check cut time constraint if specified
    if params.max_cut_time_min is not None:
        cut_time_min = result.estimated_cut_time_seconds / 60.0
        if cut_time_min > params.max_cut_time_min:
            return False
    
    # Check waste tolerance if specified
    if params.waste_tolerance is not None:
        waste = 1.0 - result.efficiency
        if waste > params.waste_tolerance:
            return False
    
    return True


def search_constraint_first(
    params: ConstraintSearchParams,
) -> List[ConstraintSearchResult]:
    """
    Search for feasible rosette designs given operator constraints.
    
    Algorithm:
    1. Generate up to max_trials candidate designs
    2. Evaluate each through RMOS feasibility (Mode B)
    3. Filter by constraints (risk, cut time, waste)
    4. Sort by score descending
    5. Return top max_candidates
    
    Args:
        params: Search constraints
    
    Returns:
        List of ConstraintSearchResult, sorted by score descending
    """
    candidates: List[ConstraintSearchResult] = []
    
    for trial_idx in range(params.max_trials):
        # Early exit if we have enough candidates
        if len(candidates) >= params.max_candidates * 2:
            break
        
        # Generate candidate
        design = _generate_candidate_design(trial_idx, params)
        
        # Evaluate through RMOS
        try:
            result = _evaluate_candidate(design, params)
        except Exception as e:
            # Skip failed evaluations
            continue
        
        # Check constraints
        if not _passes_constraints(result, params):
            continue
        
        # Add to candidates
        candidates.append(ConstraintSearchResult(
            design=design,
            feasibility=result,
            rank=0  # Will be set after sorting
        ))
    
    # Sort by score descending
    candidates.sort(key=lambda c: c.feasibility.score, reverse=True)
    
    # Assign ranks and trim to max_candidates
    for i, candidate in enumerate(candidates[:params.max_candidates]):
        candidate.rank = i + 1
    
    return candidates[:params.max_candidates]
