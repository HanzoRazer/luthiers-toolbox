# services/api/app/business/goals_service.py
"""Goals Service - Pricing target tracking."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from .schemas import Goal, GoalCreateRequest, GoalUpdateRequest, GoalStatus

class GoalsStore:
    """In-memory goals store (production would use database)."""
    
    def __init__(self):
        self._goals: dict[str, Goal] = {}
    
    def list_goals(self) -> list[Goal]:
        return list(self._goals.values())
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        return self._goals.get(goal_id)
    
    def create_goal(self, request: GoalCreateRequest) -> Goal:
        goal = Goal(
            name=request.name,
            instrument_type=request.instrument_type.value,
            target_cost=request.target_cost,
            target_hours=request.target_hours,
            deadline=request.deadline,
            notes=request.notes
        )
        self._goals[goal.id] = goal
        return goal
    
    def update_goal(self, goal_id: str, request: GoalUpdateRequest) -> Optional[Goal]:
        goal = self._goals.get(goal_id)
        if not goal:
            return None
        
        if request.name is not None:
            goal.name = request.name
        if request.target_cost is not None:
            goal.target_cost = request.target_cost
        if request.target_hours is not None:
            goal.target_hours = request.target_hours
        if request.status is not None:
            goal.status = request.status
        if request.deadline is not None:
            goal.deadline = request.deadline
        if request.notes is not None:
            goal.notes = request.notes
        
        goal.updated_at = datetime.utcnow().isoformat()
        self._update_progress(goal)
        return goal
    
    def delete_goal(self, goal_id: str) -> bool:
        if goal_id in self._goals:
            del self._goals[goal_id]
            return True
        return False
    
    def link_estimate(self, goal_id: str, estimate_id: str) -> Optional[Goal]:
        goal = self._goals.get(goal_id)
        if not goal:
            return None
        if estimate_id not in goal.estimate_ids:
            goal.estimate_ids.append(estimate_id)
        goal.updated_at = datetime.utcnow().isoformat()
        return goal
    
    def update_best(self, goal_id: str, cost: float, hours: float) -> Optional[Goal]:
        goal = self._goals.get(goal_id)
        if not goal:
            return None
        
        if goal.current_best_cost is None or cost < goal.current_best_cost:
            goal.current_best_cost = cost
        if goal.current_best_hours is None or hours < goal.current_best_hours:
            goal.current_best_hours = hours
        
        self._update_progress(goal)
        goal.updated_at = datetime.utcnow().isoformat()
        return goal
    
    def _update_progress(self, goal: Goal) -> None:
        if goal.current_best_cost is None or goal.current_best_hours is None:
            goal.progress_pct = 0.0
            return
        
        cost_progress = min(100.0, (goal.target_cost / goal.current_best_cost) * 100) if goal.current_best_cost > 0 else 0
        hours_progress = min(100.0, (goal.target_hours / goal.current_best_hours) * 100) if goal.current_best_hours > 0 else 0
        goal.progress_pct = (cost_progress + hours_progress) / 2
        
        if goal.progress_pct >= 100.0:
            goal.status = GoalStatus.ACHIEVED

# Singleton instance
goals_store = GoalsStore()

