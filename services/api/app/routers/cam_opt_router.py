"""
Module M.2: CAM Optimization Router
API endpoints for what-if optimization and cycle time estimation.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..cam.time_estimator_v2 import estimate_cycle_time_v2
from ..cam.whatif_opt import optimize_feed_stepover
from ..routers.machine_router import get_profile

router = APIRouter(prefix="/cam/opt", tags=["cam-opt"])


class LoopIn(BaseModel):
    pts: List[List[float]]


class OptIn(BaseModel):
    moves: Optional[List[Dict[str, Any]]] = None  # Precomputed moves from /plan
    loops: Optional[List[LoopIn]] = None  # Alternative: compute moves first (not implemented)
    machine_profile_id: str
    z_total: float = -3.0
    stepdown: float = 1.0
    safe_z: float = 5.0
    bounds: Dict[str, List[float]] = Field(
        default={
            "feed": [600, 9000],
            "stepover": [0.25, 0.85],
            "rpm": [8000, 24000]
        }
    )
    tool: Dict[str, Any] = Field(
        default={
            "flutes": 2,
            "chipload_target_mm": 0.05
        }
    )
    grid: List[int] = Field(default=[6, 6])


@router.post("/what_if")
def what_if_opt(body: OptIn) -> Dict[str, Any]:
    """
    What-if optimizer for feed/stepover/RPM parameters.
    
    Performs grid search to find optimal cutting parameters that:
    - Minimize cycle time
    - Honor machine profile limits (feed, accel, jerk)
    - Meet chipload targets for tool longevity
    - Stay within RPM bounds
    
    Args:
        body: OptIn model with:
            - moves: Prebuilt G-code moves from /plan (required)
            - machine_profile_id: Machine profile to optimize for
            - z_total: Total depth (negative, e.g., -3.0)
            - stepdown: Depth per pass (positive, e.g., 1.0)
            - safe_z: Safe retract height (positive, e.g., 5.0)
            - bounds: {feed:[lo,hi], stepover:[lo,hi], rpm:[lo,hi]}
            - tool: {flutes, chipload_target_mm}
            - grid: [feed_steps, stepover_steps]
    
    Returns:
        {
            baseline: {time_s, xy_time_one_pass_s, passes, hop_count, caps}
            opt: {
                best: {feed_mm_min, stepover, rpm, time_s, score}
                neighbors: List of 6 nearby samples
                grid: Grid bounds and step counts
            }
        }
    
    Raises:
        HTTPException 400: If moves not provided or machine profile not found
    """
    # Get machine profile
    profile = get_profile(body.machine_profile_id)
    
    # Validate moves present
    if body.moves is None:
        raise HTTPException(
            400,
            "M.2 expects prebuilt moves for accuracy; call /plan first and pass its moves."
        )
    
    # Run optimizer
    res = optimize_feed_stepover(
        body.moves,
        profile,
        z_total=body.z_total,
        stepdown=body.stepdown,
        safe_z=body.safe_z,
        bounds={k: tuple(v) for k, v in body.bounds.items()},
        tool=body.tool,
        grid=tuple(body.grid)
    )
    
    # Calculate baseline with current move settings for comparison
    baseline = estimate_cycle_time_v2(
        body.moves,
        profile,
        z_total=body.z_total,
        stepdown=body.stepdown,
        safe_z=body.safe_z
    )
    
    return {"baseline": baseline, "opt": res}
