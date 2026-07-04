"""Optimization Router — Feed/speed optimization endpoints.

Provides:
- POST /opt/what_if - What-if optimizer for feed/stepover/RPM
- POST /opt/feeds-speeds - Calculate optimal feeds and speeds
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...time_estimator_v2 import estimate_cycle_time_v2
from ...whatif_opt import optimize_feed_stepover
from ....routers.machines_consolidated_router import get_profile
from ....cam_core.feeds_speeds import calculate_feed_plan
from ....core.safety import safety_critical

router = APIRouter(prefix="/opt")

# Upper bound on each what-if grid axis. optimize_feed_stepover() clones the
# full moves list and re-runs the cycle-time estimate once PER GRID CELL, so
# cost is O(grid[0] * grid[1] * len(moves)). An uncapped grid (e.g. 20x20)
# on a multi-thousand-move toolpath runs for ~10s on the request thread.
# 12x12 = 144 cells keeps the default 6x6 untouched while bounding worst case.
MAX_WHATIF_GRID_AXIS = 12


class LoopIn(BaseModel):
    pts: List[List[float]]


class OptIn(BaseModel):
    moves: Optional[List[Dict[str, Any]]] = None
    loops: Optional[List[LoopIn]] = None
    machine_profile_id: str
    z_total: float = -3.0
    stepdown: float = 1.0
    safe_z: float = 5.0
    bounds: Dict[str, List[float]] = Field(
        default={"feed": [600, 9000], "stepover": [0.25, 0.85], "rpm": [8000, 24000]}
    )
    tool: Dict[str, Any] = Field(default={"flutes": 2, "chipload_target_mm": 0.05})
    grid: List[int] = Field(default=[6, 6])


@router.post("/what_if")
def what_if_opt(body: OptIn) -> Dict[str, Any]:
    """What-if optimizer for feed/stepover/RPM parameters."""
    profile = get_profile(body.machine_profile_id)
    if body.moves is None:
        raise HTTPException(400, "M.2 expects prebuilt moves; call /plan first.")

    if len(body.grid) != 2 or any(g < 1 for g in body.grid):
        raise HTTPException(400, "grid must be [axis_feed, axis_stepover] with each >= 1.")
    if any(g > MAX_WHATIF_GRID_AXIS for g in body.grid):
        raise HTTPException(
            400,
            f"grid axis exceeds cap {MAX_WHATIF_GRID_AXIS} "
            f"(cost is O(grid[0]*grid[1]*len(moves)); refine bounds instead of the grid).",
        )

    res = optimize_feed_stepover(
        body.moves,
        profile,
        z_total=body.z_total,
        stepdown=body.stepdown,
        safe_z=body.safe_z,
        bounds={k: tuple(v) for k, v in body.bounds.items()},
        tool=body.tool,
        grid=tuple(body.grid),
    )
    baseline = estimate_cycle_time_v2(
        body.moves, profile, z_total=body.z_total, stepdown=body.stepdown, safe_z=body.safe_z
    )
    return {"baseline": baseline, "opt": res}


class FeedsSpeedsRequest(BaseModel):
    tool_id: str
    material: str
    strategy: str = "roughing"
    flutes: Optional[int] = None
    diameter_mm: Optional[float] = None
    stickout_mm: Optional[float] = None


class FeedsSpeedsResponse(BaseModel):
    tool_id: str
    material: str
    strategy: str
    feed_xy: float
    feed_z: float
    rpm: int
    stepdown_mm: float
    stepover_mm: float
    chipload_mm: float
    heat_rating: str
    deflection_mm: float
    notes: str


@router.post("/feeds-speeds", response_model=FeedsSpeedsResponse)
@safety_critical
def calculate_feeds_speeds(body: FeedsSpeedsRequest) -> FeedsSpeedsResponse:
    """Calculate optimal feeds and speeds for tool/material/strategy."""
    tool: Dict[str, Any] = {"id": body.tool_id}
    if body.flutes is not None:
        tool["flutes"] = body.flutes
    if body.diameter_mm is not None:
        tool["diameter_mm"] = body.diameter_mm
    if body.stickout_mm is not None:
        tool["stickout_mm"] = body.stickout_mm
    result = calculate_feed_plan(tool, body.material, body.strategy)
    return FeedsSpeedsResponse(**result)


__all__ = [
    "router",
    "LoopIn",
    "OptIn",
    "FeedsSpeedsRequest",
    "FeedsSpeedsResponse",
]
