"""
RMOS AI Search API Routes
FastAPI router for AI-assisted design generation endpoints.

Integrates with:
- ai_search.py for the constraint-first search loop
- ai_policy.py for request validation
- schemas_logs_ai.py for log query endpoints
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional, List

# AI availability gate (H8.4)
from app.ai.availability import require_anthropic_available, get_ai_status

from .schemas_ai import (
    AiSearchRequest,
    AiSearchResponse,
    AiSearchSummary,
    SearchStatus,
    WorkflowMode,
)
from .schemas_logs_ai import (
    AiAttemptLogView,
    AiRunSummaryLogView,
    AiLogQueryParams,
)
from .ai_search import run_constraint_first_search, get_search_status_description

# Import policy validation
try:
    from .ai_policy import validate_request_against_policy, PolicyViolationError
except (ImportError, AttributeError, ModuleNotFoundError):
    def validate_request_against_policy(request): pass  # type: ignore
    PolicyViolationError = Exception  # type: ignore


router = APIRouter(
    prefix="/ai",
    tags=["rmos-ai"],
)


@router.post(
    "/constraint-search",
    response_model=AiSearchResponse,
    summary="Run constraint-first AI search",
    description="""
    Execute an AI-driven search for manufacturable rosette designs.
    
    The search loop:
    1. Generates candidate designs using constraint-aware generators
    2. Scores each candidate for manufacturing feasibility
    3. Returns the best result found within the budget
    
    **Budget Controls (clamped to system limits):**
    - `max_attempts`: Maximum candidate generations (1-200, capped)
    - `time_limit_seconds`: Wall-clock time limit (1-60s, capped)
    - `min_feasibility_score`: Minimum acceptable score (0-100)
    - `stop_on_first_green`: Exit early when GREEN result found
    
    **Request Format:**
    ```json
    {
        "workflow_mode": "constraint_first",
        "context": { "tool_id": "T1", "material_id": "M1" },
        "search_budget": { "max_attempts": 50, "time_limit_seconds": 30 }
    }
    ```
    
    **Response Status Codes:**
    - `success`: Found a GREEN manufacturable design
    - `best_effort`: No GREEN, returning best YELLOW result
    - `exhausted`: Budget used, no acceptable result
    - `timeout`: Time limit reached
    - `error`: Unrecoverable error occurred
    """,
)
async def constraint_search(
    request: AiSearchRequest,
    background_tasks: BackgroundTasks,
) -> AiSearchResponse:
    """
    POST /api/rmos/ai/constraint-search
    
    Run constraint-first AI search for manufacturable designs.
    """
    # AI availability gate (returns 503 if not configured)
    require_anthropic_available(feature="RMOS AI Search")
    
    # Validate against global policy
    try:
        validate_request_against_policy(request)
    except PolicyViolationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Policy violation: {str(e)}",
        )
    except Exception:
        pass  # Policy module not available, continue
    
    try:
        response = run_constraint_first_search(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search engine error: {str(e)}",
        )


@router.get(
    "/status/{status_code}",
    summary="Get status description",
    description="Get human-readable description for a search status code.",
)
async def get_status_info(status_code: str) -> dict:
    """
    GET /api/rmos/ai/status/{status_code}
    
    Returns description for a given status code.
    """
    try:
        status = SearchStatus(status_code)
        return {
            "status": status.value,
            "description": get_search_status_description(status),
        }
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status code: {status_code}. Valid: {[s.value for s in SearchStatus]}",
        )


@router.post(
    "/quick-check",
    response_model=AiSearchSummary,
    summary="Quick feasibility check",
    description="""
    Run a fast feasibility check with minimal attempts.
    Useful for UI feedback before full search.
    """,
)
async def quick_check(
    request: AiSearchRequest,
) -> AiSearchSummary:
    """
    POST /api/rmos/ai/quick-check
    
    Run abbreviated search (max 5 attempts, 5 second limit).
    Returns lightweight summary for UI feedback.
    """
    # AI availability gate (returns 503 if not configured)
    require_anthropic_available(feature="RMOS AI Quick Check")
    
    from .schemas_ai import SearchBudget, SearchContext
    
    # Override budget for quick check
    quick_request = AiSearchRequest(
        workflow_mode=request.workflow_mode,
        seed_design=request.seed_design,
        context=request.get_effective_context(),
        search_budget=SearchBudget(
            max_attempts=5,
            time_limit_seconds=5.0,
            min_feasibility_score=request.get_effective_budget().min_feasibility_score,
            stop_on_first_green=True,
            deterministic=True,
        ),
        include_attempt_history=False,
        profile_id=request.profile_id,
    )
    
    try:
        response = run_constraint_first_search(quick_request)
        return AiSearchSummary(
            run_id=response.run_id,
            status=response.status,
            best_score=response.best_score,
            best_risk_bucket=response.best_risk_bucket,
            total_attempts=response.total_attempts,
            elapsed_seconds=response.elapsed_seconds,
            started_at=response.started_at,
            workflow_mode=response.workflow_mode,
            profile_id=response.constraint_profile_applied,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Quick check error: {str(e)}",
        )


@router.get(
    "/workflows",
    summary="List available workflow modes",
    description="Get list of supported workflow modes for AI search.",
)
async def list_workflows() -> dict:
    """
    GET /api/rmos/ai/workflows
    
    Returns list of available workflow modes.
    """
    return {
        "workflows": [
            {
                "mode": mode.value,
                "description": {
                    "constraint_first": "Hard limits enforced upfront, safe parameters only",
                    "ai_assisted": "AI-driven suggestions based on goal weights",
                    "design_first": "No upfront constraints, feasibility checked after changes",
                }.get(mode.value, "")
            }
            for mode in WorkflowMode
        ]
    }


# Health check for AI subsystem
@router.get(
    "/health",
    summary="AI subsystem health check",
)
async def ai_health() -> dict:
    """
    GET /api/rmos/ai/health
    
    Check if AI search subsystem is operational.
    Returns 200 even when AI is disabled (for monitoring).
    """
    # Get centralized AI status
    ai_status = get_ai_status()
    
    # Check internal components
    try:
        from ..ai_core.generators import make_candidate_generator_for_request
        generator_available = make_candidate_generator_for_request is not None
    except (ImportError, AttributeError, ModuleNotFoundError):
        generator_available = False
    
    try:
        from .feasibility_scorer import score_design_feasibility
        scorer_available = score_design_feasibility is not None
    except (ImportError, AttributeError, ModuleNotFoundError):
        scorer_available = False
    
    try:
        from .logging_ai import log_ai_constraint_attempt
        logging_available = True
    except (ImportError, AttributeError, ModuleNotFoundError):
        logging_available = False
    
    try:
        from .ai_policy import apply_global_policy_to_constraints
        policy_available = True
    except (ImportError, AttributeError, ModuleNotFoundError):
        policy_available = False
    
    # Determine overall status
    api_key_configured = ai_status["providers"].get("anthropic", False)
    all_core = generator_available and scorer_available and api_key_configured
    
    if not api_key_configured:
        status = "disabled"  # AI explicitly not available
    elif all_core:
        status = "healthy"
    else:
        status = "degraded"
    
    return {
        "status": status,
        "ai": ai_status,
        "components": {
            "generator": "available" if generator_available else "unavailable",
            "scorer": "available" if scorer_available else "unavailable",
            "logging": "available" if logging_available else "unavailable",
            "policy": "available" if policy_available else "unavailable",
        },
    }
