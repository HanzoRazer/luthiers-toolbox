"""Optimization Router — Feed/speed optimization endpoints.

Provides:
- POST /opt/what_if - What-if optimizer for feed/stepover/RPM
- POST /opt/feeds-speeds - Calculate optimal feeds and speeds
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...time_estimator_v2 import estimate_cycle_time_v2
from ...whatif_opt import optimize_feed_stepover
from ....routers.machines_consolidated_router import get_profile
from ....cam_core.feeds_speeds import calculate_feed_plan
from ....core.safety import safety_critical

router = APIRouter(prefix="/opt")

# optimize_feed_stepover() clones the full moves list and re-runs the cycle-time
# estimate once per grid cell. Guard both the grid shape and the actual
# cells*moves workload; rectangular grids like 16x4 can be cheap, while 12x12
# can still be too expensive on a very large move list.
DEFAULT_WHATIF_MAX_GRID_CELLS = 144
DEFAULT_WHATIF_MAX_WORK_UNITS = 500_000
WHATIF_MAX_GRID_CELLS_ENV = "LTB_WHATIF_MAX_GRID_CELLS"
WHATIF_MAX_WORK_UNITS_ENV = "LTB_WHATIF_MAX_WORK_UNITS"


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


def _whatif_limits() -> tuple[int, int]:
    return (
        _env_int(WHATIF_MAX_GRID_CELLS_ENV, DEFAULT_WHATIF_MAX_GRID_CELLS),
        _env_int(WHATIF_MAX_WORK_UNITS_ENV, DEFAULT_WHATIF_MAX_WORK_UNITS),
    )


def _validate_whatif_grid(grid: List[int], move_count: int) -> tuple[int, int]:
    if len(grid) != 2:
        raise HTTPException(
            400,
            "grid must contain exactly two positive integers: "
            "[feed_steps, stepover_steps].",
        )

    feed_steps, stepover_steps = grid
    if feed_steps < 1 or stepover_steps < 1:
        raise HTTPException(
            400,
            "grid values must be positive integers: [feed_steps, stepover_steps].",
        )

    max_cells, max_work_units = _whatif_limits()
    cells = feed_steps * stepover_steps
    if cells > max_cells:
        raise HTTPException(
            400,
            f"grid has {cells} cells; maximum is {max_cells}. "
            "Reduce feed/stepover steps or split the analysis into smaller runs.",
        )

    work_units = cells * move_count
    if work_units > max_work_units:
        raise HTTPException(
            400,
            f"grid would evaluate {work_units} move-cells "
            f"({cells} cells x {move_count} moves); maximum is {max_work_units}. "
            "Reduce grid steps or optimize a smaller toolpath segment.",
        )

    return feed_steps, stepover_steps


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
    grid: List[int] = Field(
        default_factory=lambda: [6, 6],
        description=(
            "Two positive integers [feed_steps, stepover_steps]. Default [6, 6]. "
            f"The API enforces {DEFAULT_WHATIF_MAX_GRID_CELLS} total grid cells "
            f"and {DEFAULT_WHATIF_MAX_WORK_UNITS} move-cells by default; tune with "
            f"{WHATIF_MAX_GRID_CELLS_ENV} and {WHATIF_MAX_WORK_UNITS_ENV}."
        ),
    )


@router.post("/what_if")
def what_if_opt(body: OptIn) -> Dict[str, Any]:
    """What-if optimizer for feed/stepover/RPM parameters."""
    profile = get_profile(body.machine_profile_id)
    if body.moves is None:
        raise HTTPException(400, "M.2 expects prebuilt moves; call /plan first.")

    grid = _validate_whatif_grid(body.grid, len(body.moves))

    res = optimize_feed_stepover(
        body.moves,
        profile,
        z_total=body.z_total,
        stepdown=body.stepdown,
        safe_z=body.safe_z,
        bounds={k: tuple(v) for k, v in body.bounds.items()},
        tool=body.tool,
        grid=grid,
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
    "DEFAULT_WHATIF_MAX_GRID_CELLS",
    "DEFAULT_WHATIF_MAX_WORK_UNITS",
    "FeedsSpeedsRequest",
    "FeedsSpeedsResponse",
]
