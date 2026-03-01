# services/api/app/business/estimator_router.py
"""Estimator Router - API endpoints for cost estimation."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from .schemas import EstimateRequest, EstimateResponse, GoalCreateRequest, GoalUpdateRequest, Goal, GoalResponse, GoalListResponse
from .estimator_service import compute_estimate
from .goals_service import goals_store

router = APIRouter(prefix="/api/business/estimator", tags=["business"])

@router.post("/estimate", response_model=EstimateResponse)
async def create_estimate(request: EstimateRequest) -> EstimateResponse:
    """Generate a cost estimate for an instrument build."""
    try:
        result = compute_estimate(request)
        return EstimateResponse(ok=True, estimate=result)
    except (ValueError, TypeError, KeyError, AttributeError) as e:  # WP-1: narrowed from except Exception
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/goals", response_model=GoalListResponse)
async def list_goals() -> GoalListResponse:
    """List all pricing goals."""
    goals = goals_store.list_goals()
    return GoalListResponse(ok=True, goals=goals, total=len(goals))

@router.post("/goals", response_model=GoalResponse)
async def create_goal(request: GoalCreateRequest) -> GoalResponse:
    """Create a new pricing goal."""
    goal = goals_store.create_goal(request)
    return GoalResponse(ok=True, goal=goal)

@router.get("/goals/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: str) -> GoalResponse:
    """Get a specific goal by ID."""
    goal = goals_store.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return GoalResponse(ok=True, goal=goal)

@router.patch("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(goal_id: str, request: GoalUpdateRequest) -> GoalResponse:
    """Update a pricing goal."""
    goal = goals_store.update_goal(goal_id, request)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return GoalResponse(ok=True, goal=goal)

@router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: str) -> dict:
    """Delete a pricing goal."""
    if not goals_store.delete_goal(goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"ok": True}

@router.post("/goals/{goal_id}/link-estimate/{estimate_id}", response_model=GoalResponse)
async def link_estimate_to_goal(goal_id: str, estimate_id: str) -> GoalResponse:
    """Link an estimate to a goal for progress tracking."""
    goal = goals_store.link_estimate(goal_id, estimate_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return GoalResponse(ok=True, goal=goal)

