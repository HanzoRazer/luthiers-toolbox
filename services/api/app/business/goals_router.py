"""Goals Router — Endpoints for pricing goals management.

Provides:
- GET / - List pricing goals
- POST / - Create pricing goal
- GET /{goal_id} - Get goal by ID
- PATCH /{goal_id} - Update goal
- DELETE /{goal_id} - Delete goal
- POST /{goal_id}/link-estimate/{estimate_id} - Link estimate to goal

LANE: UTILITY (business planning operations)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .schemas import GoalCreateRequest, GoalUpdateRequest
from .goals_service import goals_store

router = APIRouter(tags=["Goals", "Business"])


@router.get("", summary="List pricing goals")
async def list_goals():
    """List all pricing goals."""
    goals = goals_store.list_goals()
    return {"ok": True, "goals": goals, "total": len(goals)}


@router.post("", summary="Create pricing goal")
async def create_goal(request: GoalCreateRequest):
    """Create a new pricing goal."""
    goal = goals_store.create_goal(request)
    return {"ok": True, "goal": goal}


@router.get("/{goal_id}", summary="Get goal by ID")
async def get_goal(goal_id: str):
    """Get a specific goal."""
    goal = goals_store.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"ok": True, "goal": goal}


@router.patch("/{goal_id}", summary="Update goal")
async def update_goal(goal_id: str, request: GoalUpdateRequest):
    """Update a goal."""
    goal = goals_store.update_goal(goal_id, request)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"ok": True, "goal": goal}


@router.delete("/{goal_id}", summary="Delete goal")
async def delete_goal(goal_id: str):
    """Delete a goal."""
    if not goals_store.delete_goal(goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"ok": True}


@router.post("/{goal_id}/link-estimate/{estimate_id}", summary="Link estimate to goal")
async def link_estimate_to_goal(goal_id: str, estimate_id: str):
    """Link an estimate to a goal."""
    goal = goals_store.link_estimate(goal_id, estimate_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"ok": True, "goal": goal}


__all__ = ["router", "goals_store"]
