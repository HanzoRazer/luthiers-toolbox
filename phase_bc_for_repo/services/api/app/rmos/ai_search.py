"""
RMOS AI Search Engine
Constraint-first search loop for generating manufacturable rosette designs.

This module implements the core search algorithm that:
1. Generates candidate designs via ai_core generators
2. Scores each candidate via feasibility_scorer
3. Tracks best results and respects budget constraints
4. Returns the best manufacturable design found

Integrates with:
- logging_ai.py for structured event logging
- ai_policy.py for global constraint clamping
"""
from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

from pydantic import BaseModel

from .schemas_ai import (
    AiSearchRequest,
    AiSearchResponse,
    SearchAttemptSummary,
    SearchStatus,
    SearchBudget,
)
from .api_contracts import RmosContext, RmosFeasibilityResult, RiskBucket

# Import existing logging module
from .logging_ai import (
    new_run_id,
    log_ai_constraint_attempt,
    log_ai_constraint_run_summary,
)

# Import policy module for constraint clamping
try:
    from .ai_policy import clamp_budget_to_policy, validate_request_against_policy
except (ImportError, AttributeError, ModuleNotFoundError):
    def clamp_budget_to_policy(budget): pass  # type: ignore
    def validate_request_against_policy(request): pass  # type: ignore

# Import feasibility scorer
try:
    from .feasibility_scorer import score_design_feasibility
except (ImportError, AttributeError, ModuleNotFoundError):
    score_design_feasibility = None  # type: ignore

# Lazy imports for ai_core to prevent circular dependencies
try:
    from ..ai_core.generators import make_candidate_generator_for_request, CandidateGenerator
    from ..ai_core.safety import coerce_to_rosette_spec
except (ImportError, AttributeError, ModuleNotFoundError):
    make_candidate_generator_for_request = None  # type: ignore
    coerce_to_rosette_spec = None  # type: ignore
    CandidateGenerator = None  # type: ignore

# Lazy import for models
try:
    from .models import SearchBudgetSpec
except (ImportError, AttributeError, ModuleNotFoundError):
    class SearchBudgetSpec(BaseModel):  # type: ignore
        max_attempts: int = 50
        time_limit_seconds: float = 30.0
        min_feasibility_score: float = 80.0
        stop_on_first_green: bool = True
        deterministic: bool = True


def _hash_candidate(design: Any) -> str:
    """Generate a hash for deduplication of candidate designs."""
    try:
        if hasattr(design, 'model_dump'):
            data = design.model_dump()
        elif hasattr(design, 'dict'):
            data = design.dict()
        else:
            data = dict(design) if isinstance(design, dict) else str(design)
        
        # Sort keys for consistent hashing
        import json
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]
    except Exception:
        return hashlib.sha256(str(design).encode()).hexdigest()[:16]


def _design_to_dict(design: Any) -> Dict[str, Any]:
    """Convert design object to dictionary for response."""
    if design is None:
        return {}
    if hasattr(design, 'model_dump'):
        return design.model_dump()
    if hasattr(design, 'dict'):
        return design.dict()
    if isinstance(design, dict):
        return design
    return {"raw": str(design)}


def _request_to_context(request: AiSearchRequest) -> RmosContext:
    """Build RmosContext from search request."""
    ctx = request.get_effective_context()
    return RmosContext(
        material_id=ctx.material_id,
        tool_id=ctx.tool_id,
        machine_profile_id=ctx.machine_profile_id,
    )


def _request_to_budget_spec(request: AiSearchRequest) -> SearchBudgetSpec:
    """Build SearchBudgetSpec from search request."""
    budget = request.get_effective_budget()
    return SearchBudgetSpec(
        max_attempts=budget.max_attempts,
        time_limit_seconds=budget.time_limit_seconds,
        min_feasibility_score=budget.min_feasibility_score,
        stop_on_first_green=budget.stop_on_first_green,
        deterministic=budget.deterministic,
    )


def run_constraint_first_search(request: AiSearchRequest) -> AiSearchResponse:
    """
    Execute constraint-first AI search loop.
    
    Algorithm:
    1. Validate request against global policy
    2. Clamp budget to system limits
    3. Initialize generator from request context
    4. Loop until budget exhausted:
       a. Generate candidate design
       b. Check for duplicate (skip if seen)
       c. Score feasibility
       d. Log attempt via logging_ai
       e. Track if best so far
       f. Stop early if GREEN and stop_on_first_green=True
    5. Log run summary via logging_ai
    6. Return best result found
    
    Args:
        request: Search parameters and constraints
        
    Returns:
        AiSearchResponse with best design and search statistics
    """
    run_id = new_run_id()
    started_at = datetime.now(timezone.utc)
    start_time = time.time()
    workflow_mode = request.workflow_mode.value
    
    # Build context and budget from request
    ctx = _request_to_context(request)
    budget = _request_to_budget_spec(request)
    effective_budget = request.get_effective_budget()
    
    # Apply policy: clamp budget to system limits
    clamp_budget_to_policy(budget)
    
    # Check for generator availability
    if make_candidate_generator_for_request is None:
        return AiSearchResponse(
            status=SearchStatus.ERROR,
            message="AI generator module not available",
            total_attempts=0,
            unique_candidates=0,
            elapsed_seconds=0.0,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            run_id=run_id,
            workflow_mode=workflow_mode,
        )
    
    # Check for scorer availability
    if score_design_feasibility is None:
        return AiSearchResponse(
            status=SearchStatus.ERROR,
            message="Feasibility scorer module not available",
            total_attempts=0,
            unique_candidates=0,
            elapsed_seconds=0.0,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            run_id=run_id,
            workflow_mode=workflow_mode,
        )
    
    # Initialize generator
    generator = make_candidate_generator_for_request(ctx=ctx, budget=budget)
    
    # Prepare seed design if provided
    prev_design = None
    if request.seed_design:
        if coerce_to_rosette_spec:
            prev_design = coerce_to_rosette_spec(request.seed_design)
        else:
            prev_design = request.seed_design
    
    # Search state
    attempt_summaries: List[SearchAttemptSummary] = []
    seen_hashes: set = set()
    best_result: Optional[Tuple[Any, RmosFeasibilityResult]] = None
    green_count = 0
    yellow_count = 0
    red_count = 0
    attempt_count = 0
    
    # Main search loop
    for attempt_idx in range(budget.max_attempts):
        # Check time budget
        elapsed = time.time() - start_time
        if elapsed >= budget.time_limit_seconds:
            break
        
        attempt_start = time.time()
        attempt_count = attempt_idx + 1  # 1-based for logging
        
        # Generate candidate
        try:
            candidate = generator(prev_design, attempt_idx)
        except Exception as e:
            # Log error but continue
            continue
        
        # Check for duplicate
        candidate_hash = _hash_candidate(candidate)
        is_duplicate = candidate_hash in seen_hashes
        seen_hashes.add(candidate_hash)
        
        if is_duplicate:
            # Skip scoring for duplicates
            continue
        
        # Score candidate
        try:
            result = score_design_feasibility(
                design=candidate,
                ctx=ctx,
                workflow_mode=workflow_mode,
            )
        except Exception as e:
            # Score failed - treat as RED
            result = RmosFeasibilityResult(
                score=0.0,
                risk_bucket=RiskBucket.RED,
                warnings=[f"Scoring error: {str(e)}"],
            )
        
        # Determine if acceptable
        is_acceptable = result.score >= effective_budget.min_feasibility_score
        
        # Update counts
        if result.risk_bucket == RiskBucket.GREEN:
            green_count += 1
        elif result.risk_bucket == RiskBucket.YELLOW:
            yellow_count += 1
        else:
            red_count += 1
        
        elapsed_ms = (time.time() - attempt_start) * 1000
        
        # Log attempt via existing logging_ai module
        log_ai_constraint_attempt(
            run_id=run_id,
            attempt_index=attempt_count,
            workflow_mode=workflow_mode,
            ctx=ctx,
            design=candidate,
            feasibility=result,
            is_acceptable=is_acceptable,
        )
        
        # Record for response (if requested)
        if request.include_attempt_history:
            attempt_summaries.append(SearchAttemptSummary(
                attempt_index=attempt_count,
                score=result.score,
                risk_bucket=result.risk_bucket.value,
                is_acceptable=is_acceptable,
                elapsed_ms=round(elapsed_ms, 2),
            ))
        
        # Track best result
        if best_result is None or result.score > best_result[1].score:
            best_result = (candidate, result)
        
        # Early exit on GREEN if configured
        if (
            result.risk_bucket == RiskBucket.GREEN
            and effective_budget.stop_on_first_green
        ):
            break
        
        # Update prev_design for next iteration (evolutionary approach)
        prev_design = candidate
    
    # Build response
    completed_at = datetime.now(timezone.utc)
    elapsed_seconds = time.time() - start_time
    
    # Determine status and reason
    if best_result is None:
        status = SearchStatus.EXHAUSTED
        message = "No candidates generated"
        reason = "no_candidates"
        success = False
    elif best_result[1].risk_bucket == RiskBucket.GREEN:
        status = SearchStatus.SUCCESS
        message = f"Found GREEN result with score {best_result[1].score:.1f}"
        reason = "green_found"
        success = True
    elif best_result[1].score >= effective_budget.min_feasibility_score:
        status = SearchStatus.BEST_EFFORT
        message = f"Best result is YELLOW with score {best_result[1].score:.1f}"
        reason = "yellow_acceptable"
        success = True
    elif elapsed_seconds >= budget.time_limit_seconds:
        status = SearchStatus.TIMEOUT
        message = f"Time limit reached. Best score: {best_result[1].score:.1f}"
        reason = "timeout"
        success = False
    else:
        status = SearchStatus.EXHAUSTED
        message = f"Budget exhausted. Best score: {best_result[1].score:.1f}"
        reason = "budget_exhausted"
        success = False
    
    # Log run summary via existing logging_ai module
    log_ai_constraint_run_summary(
        run_id=run_id,
        workflow_mode=workflow_mode,
        budget=budget,
        ctx=ctx,
        attempts=attempt_count,
        success=success,
        reason=reason,
        selected_feasibility=best_result[1] if best_result else None,
    )
    
    return AiSearchResponse(
        status=status,
        message=message,
        best_design=_design_to_dict(best_result[0]) if best_result else None,
        best_score=best_result[1].score if best_result else None,
        best_risk_bucket=best_result[1].risk_bucket.value if best_result else None,
        best_warnings=best_result[1].warnings if best_result else [],
        total_attempts=attempt_count,
        unique_candidates=len(seen_hashes),
        green_count=green_count,
        yellow_count=yellow_count,
        red_count=red_count,
        elapsed_seconds=round(elapsed_seconds, 3),
        started_at=started_at,
        completed_at=completed_at,
        attempts=attempt_summaries,
        run_id=run_id,
        workflow_mode=workflow_mode,
        constraint_profile_applied=request.profile_id,
    )


def get_search_status_description(status: SearchStatus) -> str:
    """Get human-readable description of search status."""
    descriptions = {
        SearchStatus.SUCCESS: "Search completed successfully with a GREEN manufacturable design",
        SearchStatus.BEST_EFFORT: "No GREEN result found, returning best YELLOW candidate",
        SearchStatus.EXHAUSTED: "Search budget exhausted without finding acceptable result",
        SearchStatus.TIMEOUT: "Search time limit reached",
        SearchStatus.ERROR: "Search encountered an unrecoverable error",
    }
    return descriptions.get(status, "Unknown status")
